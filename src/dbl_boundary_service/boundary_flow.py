from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional, Awaitable, Callable
from time import perf_counter
from uuid import uuid4

from kl_kernel_logic import PsiDefinition
from dbl_policy import DecisionOutcome, PolicyContext, PolicyDecision, TenantId

from .config import BoundaryConfig
from .llm_adapter import LlmPayload, LlmResult, call_openai_chat, dry_run_llm
from .pipeline_factory import create_pipeline, PolicyPipeline


# ---------------------------------------------------------------------------
# BoundaryRequest / BoundaryResponse
# Typed structures for the /run endpoint.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BoundaryRequest:
    """Incoming request to the boundary service."""
    prompt: str
    tenant_id: Optional[str] = None
    channel: Optional[str] = None
    max_tokens: int = 1024
    temperature: float = 0.7
    pipeline_mode: str = "basic_safety"  # minimal, basic_safety, standard, enterprise
    enabled_policies: Optional[list[str]] = None  # Explicit policy override


@dataclass(frozen=True)
class RequestEnvelope:
    """
    Envelope wrapping the LLM request for policy evaluation.
    Contains all information policies need to make decisions.
    """
    prompt: str
    model: str
    max_tokens: int
    temperature: float
    caller_id: str
    tenant_id: Optional[str]
    channel: Optional[str]
    
    def to_metadata(self) -> dict[str, Any]:
        """Convert to metadata dict for BoundaryContext."""
        return {
            "prompt": self.prompt,
            "prompt_length": len(self.prompt),
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }


@dataclass
class BoundarySnapshot:
    """
    Complete snapshot of a boundary execution.
    Used by the insights panel to show the full flow.
    """
    request_id: str
    timestamp: str
    
    # DBL layer
    boundary_context: dict[str, Any]
    policy_decisions: list[dict[str, Any]]
    dbl_outcome: str  # allow / modify / block
    
    # KL layer
    psi_definition: dict[str, Any]
    execution_trace_id: Optional[str] = None
    
    # LLM layer
    llm_payload: Optional[dict[str, Any]] = None
    llm_result: Optional[dict[str, Any]] = None
    
    # Meta
    was_blocked: bool = False
    block_reason: Optional[str] = None
    dry_run: bool = False


@dataclass
class BoundaryResponse:
    """Response from the boundary service."""
    content: str
    blocked: bool
    snapshot: BoundarySnapshot
    policy_eval_ms: float
    llm_call_ms: Optional[float]
    prompt_length: int
    model: str
    max_tokens: int
    pipeline_mode: str
    dbl_outcome: str
    block_reason: Optional[str]


# ---------------------------------------------------------------------------
# Pipeline selection
# ---------------------------------------------------------------------------

def _get_pipeline(mode: str, enabled_policies: Optional[list[str]] = None) -> PolicyPipeline:
    """
    Select pipeline based on mode and optional policy override.
    
    Args:
        mode: Preset mode (minimal, basic_safety, standard, enterprise)
        enabled_policies: Optional explicit list of policies (overrides preset)
    """
    return create_pipeline(mode=mode, enabled_policies=enabled_policies)


# ---------------------------------------------------------------------------
# run_boundary_flow
# The main orchestration function that ties DBL, KL, and LLM together.
# ---------------------------------------------------------------------------

async def run_boundary_flow(
    request: BoundaryRequest,
    config: BoundaryConfig,
    dry_run: bool = False,
    request_id: Optional[str] = None,
    event_emitter: Optional[Callable[[str, str, Optional[dict[str, Any]]], Awaitable[None]]] = None,
) -> BoundaryResponse:
    """
    Executes the full boundary flow:
    
    1. Build PsiDefinition for the LLM operation
    2. Build BoundaryContext for DBL
    3. Run DBL pipeline (policies)
    4. If allowed: run KL execution with LLM effector
    5. Return response + snapshot
    """
    request_id = request_id or str(uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # -------------------------------------------------------------------------
    # Step 1: Build RequestEnvelope
    # Contains all information for policy evaluation.
    # -------------------------------------------------------------------------
    envelope = RequestEnvelope(
        prompt=request.prompt,
        model=config.model,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        caller_id="boundary_service",
        tenant_id=request.tenant_id,
        channel=request.channel,
    )
    
    # -------------------------------------------------------------------------
    # Step 2: Build PsiDefinition
    # This defines WHAT we want to execute (an LLM chat completion).
    # -------------------------------------------------------------------------
    psi = PsiDefinition(
        psi_type="llm",
        name="openai_chat",
        metadata={
            "model": config.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "prompt_preview": request.prompt[:100] if len(request.prompt) > 100 else request.prompt,
        },
    )
    
    # -------------------------------------------------------------------------
    # Step 3: Build PolicyContext for DBL
    # This is what the policies will evaluate.
    # The 'prompt' key is required by ContentSafetyPolicy.
    # -------------------------------------------------------------------------
    tenant_value = request.tenant_id or "default"
    policy_context = PolicyContext(
        tenant_id=TenantId(tenant_value),
        inputs={
            **envelope.to_metadata(),
            "caller_id": envelope.caller_id,
            "tenant_id": tenant_value,
            "channel": envelope.channel,
        },
    )
    if event_emitter:
        await event_emitter(request_id, "boundary_context_built", {"tenant_id": request.tenant_id, "channel": request.channel})
    
    # -------------------------------------------------------------------------
    # Step 4: Select and run DBL pipeline
    # Policies decide: allow / modify / block
    # User can override with enabled_policies
    # -------------------------------------------------------------------------
    pipeline = _get_pipeline(request.pipeline_mode, request.enabled_policies)
    policy_start = perf_counter()
    dbl_result = pipeline.evaluate(policy_context)
    policy_eval_ms = (perf_counter() - policy_start) * 1000.0
    
    policy_decisions = [
        _decision_to_snapshot(d) for d in dbl_result.decisions
    ]
    if event_emitter:
        await event_emitter(request_id, "policy_decision", {"count": len(policy_decisions)})
        await event_emitter(request_id, "dbl_outcome", {"outcome": dbl_result.final_outcome})
    
    # -------------------------------------------------------------------------
    # Prepare snapshot (partial, before LLM)
    # -------------------------------------------------------------------------
    snapshot = BoundarySnapshot(
        request_id=request_id,
        timestamp=timestamp,
        boundary_context={
            "psi_type": psi.psi_type,
            "psi_name": psi.name,
            "tenant_id": request.tenant_id,
            "channel": request.channel,
            "metadata": dict(envelope.to_metadata()),
        },
        policy_decisions=policy_decisions,
        dbl_outcome=dbl_result.final_outcome,
        psi_definition={
            "psi_type": psi.psi_type,
            "name": psi.name,
            "metadata": dict(psi.metadata),
        },
        dry_run=dry_run,
    )
    
    # -------------------------------------------------------------------------
    # Step 4: Check DBL decision
    # -------------------------------------------------------------------------
    if dbl_result.final_outcome == "block":
        snapshot.was_blocked = True
        snapshot.block_reason = _block_reason_from_decisions(dbl_result.decisions)
        if event_emitter:
            await event_emitter(request_id, "blocked", {"reason": snapshot.block_reason})

        return BoundaryResponse(
            content=f"Request blocked: {snapshot.block_reason}",
            blocked=True,
            snapshot=snapshot,
            policy_eval_ms=policy_eval_ms,
            llm_call_ms=None,
            prompt_length=len(request.prompt),
            model=config.model,
            max_tokens=request.max_tokens,
            pipeline_mode=request.pipeline_mode,
            dbl_outcome=dbl_result.final_outcome,
            block_reason=snapshot.block_reason,
        )
    
    # -------------------------------------------------------------------------
    # Step 5: Apply modifications from DBL (if any)
    # -------------------------------------------------------------------------
    effective_max_tokens = dbl_result.effective_metadata.get("max_tokens", request.max_tokens)
    
    llm_payload = LlmPayload(
        model=config.model,
        prompt=request.prompt,
        max_tokens=effective_max_tokens,
        temperature=request.temperature,
    )
    
    snapshot.llm_payload = {
        "model": llm_payload.model,
        "prompt_length": len(llm_payload.prompt),
        "max_tokens": llm_payload.max_tokens,
        "temperature": llm_payload.temperature,
    }
    if event_emitter:
        await event_emitter(request_id, "llm_payload_ready", {"model": llm_payload.model, "max_tokens": llm_payload.max_tokens})
    
    # -------------------------------------------------------------------------
    # Step 6: Execute LLM
    # The LLM call is the KL effector operation.
    # Note: Full KL Kernel integration (Kernel.execute) is synchronous.
    # For async LLM calls, we trace manually here.
    # -------------------------------------------------------------------------
    if event_emitter:
        await event_emitter(request_id, "llm_called", {"dry_run": dry_run})
    llm_start = perf_counter()
    if dry_run:
        llm_result = await dry_run_llm(llm_payload)
    else:
        llm_result = await call_openai_chat(llm_payload)
    llm_call_ms = (perf_counter() - llm_start) * 1000.0
    
    # Generate trace ID (KL-style)
    trace_id = str(uuid4())
    
    snapshot.execution_trace_id = trace_id
    snapshot.llm_result = {
        "content_preview": llm_result.content[:200] if len(llm_result.content) > 200 else llm_result.content,
        "model": llm_result.model,
        "usage": llm_result.usage,
    }
    if event_emitter:
        await event_emitter(request_id, "llm_result_received", {"model": llm_result.model})
    
    return BoundaryResponse(
        content=llm_result.content,
        blocked=False,
        snapshot=snapshot,
        policy_eval_ms=policy_eval_ms,
        llm_call_ms=llm_call_ms,
        prompt_length=len(request.prompt),
        model=config.model,
        max_tokens=request.max_tokens,
        pipeline_mode=request.pipeline_mode,
        dbl_outcome=dbl_result.final_outcome,
        block_reason=None,
    )


def _decision_to_snapshot(decision: PolicyDecision) -> dict[str, Any]:
    outcome = "block" if decision.outcome == DecisionOutcome.DENY else "allow"
    reason = decision.reason_message or decision.reason_code
    return {
        "policy": decision.policy_id.value,
        "outcome": outcome,
        "reason": reason,
        "details": {
            "policy_version": decision.policy_version.value,
            "tenant_id": decision.tenant_id.value,
            "reason_code": decision.reason_code,
        },
    }


def _block_reason_from_decisions(decisions: tuple[PolicyDecision, ...]) -> str:
    if not decisions:
        return "Blocked by policy"
    last = decisions[-1]
    return last.reason_message or last.reason_code


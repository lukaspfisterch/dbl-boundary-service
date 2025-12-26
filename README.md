# DBL Boundary Service Demo

This repository exists to make a boundary decision model concrete and testable. The service is a reference implementation that makes decision timing and replayability explicit.

Guiding question: What happens when every Allow or Deny decision is explicit, replayable, and made before execution?

## Core invariant

- DECISION is the only normative effect.
- DECISION is produced before any execution.
- Observations are visible, but not normative.

## Quick Start

```bash
pip install dbl-boundary-service
dbl-boundary
```

Open http://127.0.0.1:8787

## Execution flow

Input -> Boundary admission (L) -> Policy evaluation (G) -> DECISION event written to V -> Optional execution -> Observations

## Boundary configurations

Presets are concrete boundary configurations, not toggles. Each preset is a policy envelope with a fixed intent.

| Configuration | Boundary intent |
|--------|---------|
| minimal | admit everything, record decision only |
| basic_safety | reject prompt injection patterns |
| standard | add rate limiting to safety checks |
| enterprise | strict safety with tight rate limits |

For identical input and configuration, the same DECISION is produced.

## Dry run (no LLM)

Dry run demonstrates governance without execution. The outcome is INTENT plus DECISION, and no EXECUTION event. This isolates G from the kernel by design.

## Normative vs observational outputs

Normative outputs (part of V):

- DECISION events

Observational outputs (not part of V):

- request ids
- timestamps
- traces
- LLM output

Observations MUST NOT affect decisions.

The UI surfaces both to make the separation explicit.

![DBL Boundary Service UI](screenshots/dbl-boundary-ui-example.png)

## API usage

```bash
curl -X POST http://127.0.0.1:8787/run \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello, how are you?",
    "pipeline_mode": "standard",
    "dry_run": true
  }'
```

pipeline_mode selects the boundary configuration. dry_run prevents execution, not decision.

## Theory and contracts

This repo is the reference UI and service. The theory, axioms, and contracts live in the landing repository:

Deterministic Boundary Layer: https://github.com/lukaspfisterch/deterministic-boundary-layer

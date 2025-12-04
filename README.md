# DBL Boundary Service

Reference service exposing a governed LLM boundary via DBL and KL.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web UI (FastAPI)                         │
│  - API Key                                                  │
│  - Prompt                                                   │
│  - Run / Dry Run                                            │
│  - Insights Panel (Context / Policies / LLM / Trace)        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               DBL Main (Pipelines + Policies)               │
│  - Builds BoundaryContext                                   │
│  - Applies policies                                         │
│  - Decides: allow / modify / block                          │
│  - Passes allowed calls to KL                               │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               KL Kernel (Deterministic Core)                │
│  - Fixed PsiDefinition                                      │
│  - Deterministic execution                                  │
│  - Complete trace                                           │
│  - No intelligence, no heuristics                           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      OpenAI / LLM                           │
│  - Pure effector                                            │
│  - No governance layer                                      │
│  - Output → back into DBL trace                             │
└─────────────────────────────────────────────────────────────┘
```

## Install

```bash
pip install -e .
```

## Run

```bash
dbl-boundary
# or
python -m dbl_boundary_service.main
```

Opens http://127.0.0.1:8787

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web UI |
| `/health` | GET | Health check |
| `/set-key` | PATCH | Set OpenAI API key |
| `/run` | POST | Execute prompt through boundary |

## Test

```bash
pytest tests/ -v
```

## Dependencies

- `dbl-main==0.1.0` - Policy pipelines
- `dbl-core==0.2.0` - Boundary primitives
- `kl-kernel-logic==0.4.0` - Deterministic execution

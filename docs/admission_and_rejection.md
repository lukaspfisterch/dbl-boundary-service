# Admission and rejection

This document specifies admission rules for boundary requests. Admission is part of L and occurs before V.

## Principles

- Admission is a boundary check. If admission fails, no INTENT is appended to V.
- A rejected request MUST return an HTTP error with a reason code.
- Admission failures MAY emit an observational trace, but that trace is not part of V.
- No DECISION is allowed without a prior admitted INTENT.

## Admission checks

- prompt MUST be non-empty.
- max_tokens MUST be between 1 and 8192.
- temperature MUST be between 0.0 and 2.0.
- pipeline_mode MUST be a known preset.
- enabled_policies, if provided, MUST all be known policy names.
- An API key MUST be set for non-dry-run requests.

## Reason codes

Examples of admission reason codes:

- admission.invalid_prompt
- admission.invalid_max_tokens
- admission.invalid_temperature
- admission.invalid_pipeline_mode
- admission.invalid_policy_override
- admission.missing_api_key

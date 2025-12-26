# Boundary versioning

This document defines the boundary versioning rules for the service.

## Requirements

- The boundary configuration MUST be versioned.
- Each admitted request MUST record boundary_id, boundary_version, and boundary_config_digest in the INTENT metadata.
- boundary_config_digest MUST be a deterministic hash of the canonical boundary configuration.
- Presets (pipeline_mode) are aliases only. The authoritative identifiers are boundary_id and boundary_version.

## Canonical boundary configuration

The canonical boundary configuration MUST include:

- boundary_id
- boundary_version
- pipeline_mode
- policy list with policy_id, policy_version, and policy config
- model (LLM model selection)

The canonicalization MUST be stable (sorted keys, stable list order).

## Replay invariant

Given the same authoritative input and the same boundary_id, boundary_version, and boundary_config_digest, the DECISION outcome MUST be identical. All other data is observational.

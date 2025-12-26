# Authoritative context contract

This document defines the authoritative context schema used by governance (G).

## Authoritative inputs

Only the following fields are allowed as policy inputs:

- prompt
- prompt_length
- model
- max_tokens
- temperature
- caller_id
- tenant_id
- channel

These fields are the sole inputs to PolicyContext. Policies MUST NOT read any data outside this schema.

## Explicit exclusions

The following categories are observational and MUST NOT be used as policy inputs:

- timestamps
- request IDs
- traces and trace digests
- LLM outputs or usage data
- UI state or user interface details

## Determinism rule

Given the same authoritative inputs and policy configuration, the DECISION outcome MUST be identical. Observational data MUST NOT affect decisions.

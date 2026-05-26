# Test Fixtures

Fixtures create temporary target repositories and fake ProofSignal Core
executables. They avoid real network access and never persist credential values.

Workflow guardrail fixtures under `tests/fixtures/workflows/` create small
temporary `.proofsignal/` workspaces for CLI contract, persistence, readiness,
and migration tests. They intentionally use non-secret placeholder values only.

Real-run guardrail fixtures in `tests/fixtures/workflows/real_run_guardrails.py`
model the profile-page regression that motivated this feature: planned main
skill selection, explicit `gateId` mappings, rendered-result UI assertions,
declared backend checks, weak navigation-only artifacts, and use-case-scoped
visual profiles such as `visual-15s`.

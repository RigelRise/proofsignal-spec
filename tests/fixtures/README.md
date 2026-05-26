# Test Fixtures

Fixtures create temporary target repositories and fake ProofSignal Core
executables. They avoid real network access and never persist credential values.

Workflow guardrail fixtures under `tests/fixtures/workflows/` create small
temporary `.proofsignal/` workspaces for CLI contract, persistence, readiness,
and migration tests. They intentionally use non-secret placeholder values only.

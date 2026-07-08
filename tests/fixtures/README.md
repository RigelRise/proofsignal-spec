# Test Fixtures

Fixtures create temporary target repositories and fake VerifySignal Core
executables. They avoid real network access and never persist credential values.

Workflow guardrail fixtures under `tests/fixtures/workflows/` create small
temporary `.verifysignal/` workspaces for CLI contract, persistence, readiness,
and migration tests. They intentionally use non-secret placeholder values only.

Real-run guardrail fixtures in `tests/fixtures/workflows/real_run_guardrails.py`
model the profile-page regression that motivated this feature: planned main
skill selection, explicit `gateId` mappings, rendered-result UI assertions,
declared backend checks, weak navigation-only artifacts, and use-case-scoped
visual profiles such as `visual-15s`.

Browser workflow guardrail fixtures in
`tests/fixtures/workflows/browser_workflow_guardrails.py` model target
environment decisions, runtime readiness payloads, Core public contract fields,
and repair-classification cases. They use `https://app.example.test` as non-secret
browser target data and keep credential-like values out of persisted records.

Live write readiness fixtures in
`tests/fixtures/workflows/live_write_readiness.py` model the latest real-run
findings: historical pass versus current readiness, credentialed use cases with
missing current-process credentials, legacy write artifacts, structured
confirmation requirements, generated per-run identity inputs, and cleanup
lifecycle state. The fixture stores only env var names such as
`APP_TEST_EMAIL` and `APP_TEST_PASSWORD`, never values.

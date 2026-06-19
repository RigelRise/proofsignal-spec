# ProofSignal Spec Agent Guidance

Use `proofsignal-spec` from the target repository root. Keep generated project
artifacts and guidance in English, write run requests under
`.proofsignal/run-requests/`, write reusable skills under `.proofsignal/skills/`,
and never persist credential values.

Use red/green TDD for behavior changes whenever feasible: write the expected
test first, run it and confirm it fails for the intended reason, then implement
the smallest coherent change that makes it pass. Do not weaken assertions,
delete meaningful coverage, or rewrite tests merely to match the current
implementation; if expected behavior changed, update the spec/plan first and
make that intent explicit.

Preserve existing features by default. Treat existing tests, documented
behavior, CLI flags, schemas, templates, commands, run-request formats, skill
formats, and workspace semantics as compatibility contracts. New changes should
be additive or intentionally migrated; do not remove, narrow, or silently
replace existing behavior without explicit product direction and regression
coverage for the old and new paths.

Evaluate version impact after code, behavior, CLI, schema, template, or
packaging changes. Check the current version in `pyproject.toml` and
`src/proofsignal_spec/__init__.py`, decide whether the completed work requires a
patch/minor/major bump, and update all version declarations consistently when a
bump is required. If the version remains unchanged, state why.

For write and external-notification ProofSignal use cases, keep rerun recovery
inside the public workflow/CLI contract. Do not hand-edit `.proofsignal/`
`lastRun`, registry, readiness, or run-history state to bypass a write-safety
guard. Repair the authored `resourceIdentity`, generated runtime input,
collision policy, side-effect policy, or rerun policy through
`proofsignal workflow persist implement`, then validate and rerun.

Author write policies with canonical `sideEffectPolicy.allowed[]` and
`sideEffectPolicy.forbidden[]`; do not author
`sideEffectPolicy.rules[].effect/match`. Use only runtime-supported
confirmation signals, route reviewed false-positive write outcomes through
`proofsignal workflow supersede-write-outcome`, and treat generated identity
bindings as `prepared/committed/discarded`.

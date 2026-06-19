# ProofSignal Spec Agent Guidance

Use `proofsignal-spec` from the target repository root. Keep generated project
artifacts and guidance in English, write run requests under
`.proofsignal/run-requests/`, write reusable skills under `.proofsignal/skills/`,
and never persist credential values.

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

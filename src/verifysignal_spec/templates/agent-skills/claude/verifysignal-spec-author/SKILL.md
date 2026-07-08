---
name: "verifysignal-spec-author"
description: "Author a VerifySignal browser use case."
---

Use `.verifysignal/` workspace state. Ask focused questions when product
knowledge is missing. Confirm the browser target environment before planning
executable artifacts; do not allow empty `baseUrl` or equivalent target values
to flow into the plan after the user supplies them.

Before authoring executable artifacts, run `verifysignal workflow info
verifysignal-use-case --json`. Use `stagePayloadContracts` for Spec payloads,
`coreExecutableContract` for Core-owned run request, skill, credential,
placeholder, report, and redaction sections, and `browserAuthoringContract`
for browser actions, assertions, target rules, and network match keys. Treat
selector/action/match key names in examples as non-authoritative examples, not
as local allowlists. Regenerate the agent integration after upgrading the CLI
or Core contract.

Generate one run request and reusable skills, then run
`verifysignal-spec validate <alias> --runtime-readiness` before marking the use
case ready.

For write use cases, author canonical `sideEffectPolicy.allowed[]` and
`sideEffectPolicy.forbidden[]`, never `sideEffectPolicy.rules[].effect/match`.
Use runtime-supported confirmation signals only, and preserve generated
identity binding status as `prepared/committed/discarded`. Fresh generated
write values preserve the seed plus a run-attempt token. Resolve
`{{parameters.*}}` confirmation expected values before Core execution, and
route unresolved or credential placeholders through the managed workflow.

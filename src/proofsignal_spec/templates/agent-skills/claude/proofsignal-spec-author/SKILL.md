---
name: "proofsignal-spec-author"
description: "Author a ProofSignal browser use case."
---

Use `.proofsignal/` workspace state. Ask focused questions when product
knowledge is missing. Confirm the browser target environment before planning
executable artifacts; do not allow empty `baseUrl` or equivalent target values
to flow into the plan after the user supplies them.

Before authoring executable artifacts, run `proofsignal workflow info
proofsignal-use-case --json`. Use `stagePayloadContracts` for Spec payloads,
`coreExecutableContract` for Core-owned run request, skill, credential,
placeholder, report, and redaction sections, and `browserAuthoringContract`
for browser actions, assertions, target rules, and network match keys. Treat
selector/action/match key names in examples as non-authoritative examples, not
as local allowlists. Regenerate the agent integration after upgrading the CLI
or Core contract.

Generate one run request and reusable skills, then run
`proofsignal-spec validate <alias> --runtime-readiness` before marking the use
case ready.

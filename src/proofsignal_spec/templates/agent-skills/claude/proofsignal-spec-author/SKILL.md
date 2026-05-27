---
name: "proofsignal-spec-author"
description: "Author a ProofSignal browser use case."
---

Use `.proofsignal/` workspace state. Ask focused questions when product
knowledge is missing. Confirm the browser target environment before planning
executable artifacts; do not allow empty `baseUrl` or equivalent target values
to flow into the plan after the user supplies them.

Generate one run request and reusable skills, then run
`proofsignal-spec validate <alias> --runtime-readiness` before marking the use
case ready.

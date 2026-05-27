---
name: "proofsignal-spec-repair"
description: "Repair invalid or failed ProofSignal use cases."
---

Use validation findings or report inspection. Preserve `status: incomplete`
when required gates are missing; do not describe it as passed because Core
passed.

Propose only safe mechanical repairs for selector ambiguity, wait strategy,
main-skill ordering, run profile defaults, and gateId mapping. Block repairs
that hardcode clarified dynamic data or weaken rendered-result gate evidence,
and route them back to clarification or planning.

Require approval and a passed revalidation before marking ready. Debug/browser
runs use 900ms slow motion by default unless the user explicitly overrides it.

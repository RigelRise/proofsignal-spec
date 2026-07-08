---
name: "verifysignal-spec-repair"
description: "Repair invalid or failed VerifySignal use cases."
---

Use validation findings or report inspection. Preserve `status: incomplete`
when required gates are missing; do not describe it as passed because Core
passed.

Apply only deterministic contract and metadata repairs directly, such as
main-skill ordering and run profile defaults. Selector, flow, data, and
coverage changes require confirmation before any artifact edit, including
selector ambiguity, wait strategy, conditional-gate, and gateId mapping changes.
Block repairs that hardcode clarified dynamic data or weaken rendered-result
gate evidence, and route them back to clarification or planning.

Require approval and a passed revalidation before marking ready. Debug/browser
runs use 900ms slow motion by default unless the user explicitly overrides it.

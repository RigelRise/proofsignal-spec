---
name: "verifysignal-spec-validate"
description: "Validate VerifySignal artifacts."
---

Run `verifysignal-spec validate <alias> --runtime-readiness` and report Core
findings without rewriting Core verdicts. Runtime readiness verifies target
resolution, target reachability, required runtime prerequisites, and Core
authoring readiness without executing the full browser flow.

Use shared CLI JSON and `.verifysignal/` workspace state as the only source of
truth. Report `lastRun` separately from current readiness snapshots, surface
credential readiness hints as non-executable guidance, and never read or print
secret values. If `workflow check run` returns a structured confirmation
requirement, stop until the owner confirms that exact id/scope. For write and
external-notification use cases, report cleanup lifecycle and conservative
write activity confidence; absence of a Core side-effect envelope is not proof
that no side effect occurred.

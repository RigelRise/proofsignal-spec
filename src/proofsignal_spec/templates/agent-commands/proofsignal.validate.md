# proofsignal.validate

Validate draft artifacts through ProofSignal Spec and the managed ProofSignal runtime.

- Start by running `proofsignal-spec workflow check validate --alias <alias> --json`.
- Prefer the public `proofsignal` CLI for user-facing commands. The backward-compatible `proofsignal-spec` executable remains valid in generated guardrails. Do not use `npx proofsignal-spec`.
- Continue only when the result includes `requiredCapability: workflow.guardrails/v1` and `supported: true`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal-spec` and regenerate the agent integration.
- If the check does not allow continuation, name the missing artifact or decision, point to `nextCommand`, and stop.
- Do not perform stage-specific work until the check allows it.
- If validation is blocked during the Golden Path first run, present a blocker stage card with category, primary evidence, recovery command, and next action.
- Review `structuralValidation` before Core validation. If structural validation is blocked, report the exact finding and do not call Core.
- If recoverable migration plans are present, ask the developer before invoking `proofsignal-spec workflow migrate --approve <migration-id> --json`.
- If the managed runtime is missing or blocked, state that structural validation can still run, but a verified ProofSignal runtime is required for complete validation and browser execution. Route happy-path recovery to `proofsignal init --here --integration codex`; use `proofsignal core setup --core-cmd <path>` only for diagnostics, offline environments, and development overrides. Do not suggest artifact repair for this environment issue.
- Backward-compatible wording may still state: "ProofSignal Core is required for the complete ProofSignal validation and browser execution experience"; interpret that as the private runtime boundary, not a manual happy-path install step.
- Delegate Core-dependent behavior through `proofsignal validate <alias> --runtime-readiness` (or the alias `proofsignal-spec validate <alias> --runtime-readiness`).
- `runtime readiness verifies target resolution, target reachability, required runtime prerequisites, and Core authoring readiness` without executing the full browser validation flow.
- Treat validation output as static readiness: `authoredEvidenceCoverageStatus` means required gates have mapped authored evidence, and `fullBrowserFlowExecuted: false` means the browser flow has not run yet.
- Report the selected main skill shown by validation output before discussing Core results.
- For later browser inspection, remind users that `proofsignal run <alias> --profile debug` uses 900ms slow motion by default unless `--slow-mo` is explicitly set.
- Review `authoringCoherence`. If it is blocked, treat the artifact as not ready even if individual browser steps look executable.
- Distinguish coherent planned validation from a narrow technical pass. A page-view validation requires mapped rendered-result UI evidence and declared backend checks, not only navigation or HTTP 200.
- Preserve Core verdicts exactly and do not reinterpret passed, failed, blocked, or error outcomes.
- Record redacted validation summaries in workflow state and stage documents.
- Do not write managed `.proofsignal/` artifacts directly. Persist managed artifacts through ProofSignal Spec CLI operations only.
- Do not use `proofsignal-spec author`, nonexistent schema/scaffold commands, or manual file edits to repair workflow-managed artifacts. Route schema fixes through `/proofsignal-repair` or `proofsignal-spec workflow persist implement`.
- Do not parse raw report internals or import private ProofSignal Core packages.
- Suggest `/proofsignal-run` when readiness passes or `/proofsignal-repair` only when actionable artifact/runtime findings exist.

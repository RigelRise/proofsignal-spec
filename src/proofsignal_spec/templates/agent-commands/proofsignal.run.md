# proofsignal.run

Run a validated use case by alias.

- Start by running `proofsignal-spec workflow check run --alias <alias> --json`.
- Use the installed `proofsignal-spec` executable directly. Do not use `npx proofsignal-spec`.
- Continue only when the result includes `requiredCapability: workflow.guardrails/v1` and `supported: true`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal-spec` and regenerate the agent integration.
- If the check does not allow continuation, name the missing artifact or decision, point to `nextCommand`, and stop.
- If a Golden Path first run is blocked by target, credential, stale inventory, stale workspace, or Core compatibility, present a blocker stage card with the exact recovery command.
- Do not perform stage-specific work until the check allows it.
- Resolve the alias to exactly one run request, main skill, and supporting reusable skills.
- Use parameter values already declared in the run request. Prompt only for runtime values that are still missing.
- Never persist credential values.
- Do not write managed `.proofsignal/` artifacts directly. Persist managed artifacts through ProofSignal Spec CLI operations only.
- Delegate execution through `proofsignal-spec run <alias> --profile normal` unless the user requests another profile. Use-case-specific profile names are allowed when declared by that use case; unknown profiles must block and list available profiles.
- For human-observable browser debugging, use `--profile debug`; the default debug pacing is `--slow-mo 900` unless the user explicitly overrides it.
- Report Core/browser status separately from Spec coverage status using `coreBrowserStatus` and `specCoverageStatus`. A Core `passed` result can still be `specCoverageStatus: incomplete` when planned gates are missing, network-only, screenshot-only, or unmapped.
- Backward-compatible summary wording may still mention that a Core `passed` result can still be `coverageStatus: incomplete`; interpret that as Spec coverage, not browser execution.
- When Core/browser execution fails, call Spec coverage diagnostic; do not summarize diagnostic coverage as browser validation passed.
- Do not summarize `status: incomplete` as passed, even when `coreStatus` is `passed`; name the missing required gates and next action.
- Include selected main skill, profile settings, gate coverage, and runtime contradiction recommendations in the run summary.
- For an accepted Golden Path first run, present the structured stage cards from output using clear separators, status marker, one-line summary, why it matters, primary evidence, repair details when present, and next action.
- Treat `firstRunStatus: passed` and `firstRunStatus: repaired-passed` with `strictPass: true` as Golden Path success. Treat `skipped`, `failed`, `blocked`, and `incomplete` as distinct non-success states.
- Record report and evidence references, not raw report internals.
- Suggest `/proofsignal-repair` when execution fails or when Spec coverage reports runtime contradictions or incomplete planned gates.
- Use `proofsignal-spec workflow inspect-golden-path-state --json` when the first-run state appears stale or interrupted.

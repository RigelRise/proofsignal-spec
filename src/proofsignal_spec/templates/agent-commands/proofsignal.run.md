# proofsignal.run

Run a validated use case by alias.

- Start by running `proofsignal-spec workflow check run --alias <alias> --json`.
- Use the installed `proofsignal-spec` executable directly. Do not use `npx proofsignal-spec`.
- Continue only when the result includes `requiredCapability: workflow.guardrails/v1` and `supported: true`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal-spec` and regenerate the agent integration.
- If the check does not allow continuation, name the missing artifact or decision, point to `nextCommand`, and stop.
- Do not perform stage-specific work until the check allows it.
- Resolve the alias to exactly one run request, main skill, and supporting reusable skills.
- Use parameter values already declared in the run request. Prompt only for runtime values that are still missing.
- Never persist credential values.
- Do not write managed `.proofsignal/` artifacts directly. Persist managed artifacts through ProofSignal Spec CLI operations only.
- Delegate execution through `proofsignal-spec run <alias> --profile normal` unless the user requests another profile. Use-case-specific profile names are allowed when declared by that use case; unknown profiles must block and list available profiles.
- Report Core/browser status separately from Spec coverage status. A Core `passed` result can still be `coverageStatus: incomplete` when planned gates are missing, network-only, screenshot-only, or unmapped.
- Include selected main skill, profile settings, gate coverage, and runtime contradiction recommendations in the run summary.
- Record report and evidence references, not raw report internals.
- Suggest `/proofsignal-repair` when execution fails or when Spec coverage reports runtime contradictions or incomplete planned gates.

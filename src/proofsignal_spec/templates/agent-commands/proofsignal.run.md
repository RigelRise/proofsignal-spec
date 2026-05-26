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
- Delegate execution through `proofsignal-spec run <alias> --profile normal` unless the user requests another profile.
- Record report and evidence references, not raw report internals.
- Suggest `/proofsignal-repair` when execution fails with actionable findings.

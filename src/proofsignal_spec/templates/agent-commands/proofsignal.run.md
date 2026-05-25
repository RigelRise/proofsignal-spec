# proofsignal.run

Run a validated use case by alias.

- Start by running `proofsignal-spec workflow check run --alias <alias> --json`.
- Use the installed `proofsignal-spec` executable directly. Do not use `npx proofsignal-spec`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal-spec` and regenerate the agent integration.
- If the check does not allow continuation, name the missing artifact or decision, point to `nextCommand`, and stop.
- Do not perform stage-specific work until the check allows it.
- Resolve the alias to exactly one run request, main skill, and supporting reusable skills.
- Prompt for missing runtime values when needed.
- Never persist credential values.
- Delegate execution through `proofsignal-spec run <alias> --profile normal` unless the user requests another profile.
- Record report and evidence references, not raw report internals.
- Suggest `/proofsignal-repair` when execution fails with actionable findings.

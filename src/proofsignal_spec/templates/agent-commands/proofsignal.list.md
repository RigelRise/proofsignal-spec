# proofsignal.list

List use cases and workflow status.

- No repository understanding prerequisite is required for this command.
- Start by running `proofsignal-spec workflow check list --json` for a deterministic no-prerequisite status before listing.
- Use the installed `proofsignal-spec` executable directly. Do not use `npx proofsignal-spec`.
- Continue only when the result includes `requiredCapability: workflow.guardrails/v1` and `supported: true`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal-spec` and regenerate the agent integration.
- Use deterministic CLI commands such as `proofsignal-spec list` and `proofsignal-spec workflow list`.
- Do not write managed `.proofsignal/` artifacts directly. Persist managed artifacts through ProofSignal Spec CLI operations only.
- Summarize aliases, current workflow stage, runnable status, runtime requirements, and latest result.
- Do not inspect sensitive files.
- Surface the next recommended `/proofsignal-*` command when a use case is blocked.

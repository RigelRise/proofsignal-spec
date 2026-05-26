# proofsignal.understand

Capture repository and product understanding before authoring run requests.

- No prior repository understanding is required for this command.
- Start by running `proofsignal-spec workflow check understand --json` to verify that the installed CLI supports the current workflow contract.
- Use the installed `proofsignal-spec` executable directly. Do not use `npx proofsignal-spec`.
- Continue only when the result includes `requiredCapability: workflow.guardrails/v1` and `supported: true`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal-spec` and regenerate the agent integration. Do not inspect the repository or write `.proofsignal/product-context.yaml` with an unknown CLI contract.
- This command may be used for the initial understanding pass or after a stale-understanding refresh is accepted.
- Work inside the target repository.
- Keep generated docs, workflow prompts, run requests, and skills in English.
- Use pt-BR only for conversation with the project owner when appropriate.
- Use `.proofsignal/` as the workspace.
- Avoid sensitive files by default and ask before reading local environment or secret-bearing configuration.
- Build a systematic coverage inventory when feasible. Cover user-facing routes and pages first, then flows, forms, actions, permissions, loading/empty/error states, integrations, and supporting modules.
- Support scoped passes with `--scope all`, `--scope changed`, `--scope continue`, `--scope route:<path>`, or `--scope area:<name>`.
- Mark the inventory as `complete` only when every discoverable user-facing surface is covered or explicitly excluded with a reason. Otherwise mark it `partial`; mark changed areas `stale` when repository changes affect them.
- Prepare a structured payload with repository summary, start instructions, safe paths, blocked sensitive paths, coverage inventory, candidate use cases, generated time, and git hash or git-unavailable reason.
- Do not write managed `.proofsignal/` artifacts directly. Persist managed artifacts through `proofsignal-spec workflow persist understand --scope <scope> --payload <payload.json> --json`.
- Report whether inventory is complete, partial, or stale before recommending scenarios.
- Never persist credential values.
- Suggest `/proofsignal-specify` as the next command when understanding is sufficient.

# proofsignal.understand

Capture repository and product understanding before authoring run requests.

- No prior repository understanding is required for this command.
- Start by running `proofsignal-spec workflow check understand --json` to verify that the installed CLI supports the current workflow contract.
- Use the installed `proofsignal-spec` executable directly. Do not use `npx proofsignal-spec`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal-spec` and regenerate the agent integration. Do not inspect the repository or write `.proofsignal/product-context.yaml` with an unknown CLI contract.
- This command may be used for the initial understanding pass or after a stale-understanding refresh is accepted.
- Work inside the target repository.
- Keep generated docs, workflow prompts, run requests, and skills in English.
- Use pt-BR only for conversation with the project owner when appropriate.
- Use `.proofsignal/` as the workspace.
- Avoid sensitive files by default and ask before reading local environment or secret-bearing configuration.
- Record reusable product context globally and write a per-use-case `understanding.md` snapshot when an alias exists.
- Never persist credential values.
- Suggest `/proofsignal-specify` as the next command when understanding is sufficient.

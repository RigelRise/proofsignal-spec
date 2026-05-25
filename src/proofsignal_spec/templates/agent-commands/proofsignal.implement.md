# proofsignal.implement

Create or update only planned draft artifacts.

- Start by running `proofsignal-spec workflow check implement --alias <alias> --json`.
- Use the installed `proofsignal-spec` executable directly. Do not use `npx proofsignal-spec`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal-spec` and regenerate the agent integration.
- If the check does not allow continuation, name the missing artifact or decision, point to `nextCommand`, and stop.
- Do not perform stage-specific work until the check allows it.
- Follow `.proofsignal/workflows/use-cases/<alias>/tasks.md`.
- Write generated run requests under `.proofsignal/run-requests/`.
- Write reusable skills under `.proofsignal/skills/`.
- Do not change artifacts that are not named by the approved plan and tasks.
- Keep generated run requests and skills as drafts until validation passes.
- Never persist credential values.
- Suggest `/proofsignal-validate` after draft artifacts are created.

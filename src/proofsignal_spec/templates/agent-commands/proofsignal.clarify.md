# proofsignal.clarify

Resolve only high-impact unknowns before planning.

- Start by running `proofsignal-spec workflow check clarify --alias <alias> --json`.
- Use the installed `proofsignal-spec` executable directly. Do not use `npx proofsignal-spec`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal-spec` and regenerate the agent integration.
- If the check does not allow continuation, name the missing artifact or decision, point to `nextCommand`, and stop.
- Do not perform stage-specific work until the check allows it.
- Ask focused questions only when missing information materially affects scope, runtime requirements, security, or user-visible validation behavior.
- Record question, answer, rationale, and affected stage in `.proofsignal/workflows/use-cases/<alias>/clarifications.md`.
- Do not ask for credential values. Ask for credential group names or environment variable names only.
- Block planning when unresolved clarification items would change the run request or reusable skill structure.
- Suggest `/proofsignal-plan` after clarification is sufficient.

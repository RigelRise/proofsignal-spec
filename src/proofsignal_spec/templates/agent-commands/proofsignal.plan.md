# proofsignal.plan

Plan one run request and reusable skills before implementation.

- Start by running `proofsignal-spec workflow check plan --alias <alias> --json`.
- Use the installed `proofsignal-spec` executable directly. Do not use `npx proofsignal-spec`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal-spec` and regenerate the agent integration.
- If the check does not allow continuation, name the missing artifact or decision, point to `nextCommand`, and stop.
- Do not perform stage-specific work until the check allows it.
- Require exactly one planned run request for the use case.
- Plan skills as decoupled reusable artifacts under `.proofsignal/skills/`.
- Identify the main skill, supporting skills, runtime input names, credential groups, expected app state, and validation gates.
- Reuse existing skills when appropriate instead of nesting or duplicating skills under a use case.
- Store the artifact plan in `.proofsignal/workflows/use-cases/<alias>/plan.md`.
- Block implementation when the plan lacks a run request or skill relationship.
- Suggest `/proofsignal-tasks` after the plan is approved.

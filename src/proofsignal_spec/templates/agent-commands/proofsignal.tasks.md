# proofsignal.tasks

Generate ordered authoring tasks from the approved artifact plan.

- Start by running `proofsignal-spec workflow check tasks --alias <alias> --json`.
- Use the installed `proofsignal-spec` executable directly. Do not use `npx proofsignal-spec`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal-spec` and regenerate the agent integration.
- If the check does not allow continuation, name the missing artifact or decision, point to `nextCommand`, and stop.
- Do not perform stage-specific work until the check allows it.
- Translate each planned artifact, runtime declaration, skill reuse relationship, and validation gate into a reviewable task.
- Preserve traceability to `.proofsignal/workflows/use-cases/<alias>/plan.md`.
- Do not widen scope beyond the approved plan.
- Store tasks in `.proofsignal/workflows/use-cases/<alias>/tasks.md`.
- If the plan changed since tasks were generated, require regeneration or explicit confirmation.
- Suggest `/proofsignal-implement` after tasks are approved.

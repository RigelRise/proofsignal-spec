# proofsignal.tasks

Generate ordered authoring tasks from the approved artifact plan.

- Start by running `proofsignal-spec workflow check tasks --alias <alias> --json`.
- Before constructing the payload, read the public workflow contract with `proofsignal-spec workflow info proofsignal-use-case --json` and use `stagePayloadContracts.tasks` as the source of truth. Do not inspect installed package source to infer payload schemas.
- Use the installed `proofsignal-spec` executable directly. Do not use `npx proofsignal-spec`.
- Continue only when the result includes `requiredCapability: workflow.guardrails/v1` and `supported: true`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal-spec` and regenerate the agent integration. Regenerate the agent integration after upgrading.
- If the check does not allow continuation, name the missing artifact or decision, point to `nextCommand`, and stop.
- Do not perform stage-specific work until the check allows it.
- Read the approved plan and persisted context with `proofsignal-spec workflow show --alias <alias> --json`.
- Translate each planned artifact, runtime declaration, skill reuse relationship, and validation gate into a reviewable task.
- Preserve traceability to `.proofsignal/workflows/use-cases/<alias>/plan.md`.
- Do not widen scope beyond the approved plan.
- Do not write managed `.proofsignal/` artifacts directly. Persist managed artifacts through `proofsignal-spec workflow persist tasks --alias <alias> --payload <payload.json> --json`.
- If the plan changed since tasks were generated, require regeneration or explicit confirmation.
- Suggest `/proofsignal-implement` after tasks are approved.

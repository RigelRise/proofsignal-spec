# proofsignal.repair

Repair invalid or failed use cases through the workflow.

- Start by running `proofsignal-spec workflow check repair --alias <alias> --json`.
- Use the installed `proofsignal-spec` executable directly. Do not use `npx proofsignal-spec`.
- Continue only when the result includes `requiredCapability: workflow.guardrails/v1` and `supported: true`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal-spec` and regenerate the agent integration.
- If the check does not allow continuation, name the missing artifact or decision, point to `nextCommand`, and stop.
- Do not perform stage-specific work until the check allows it.
- Use Core validation findings or public report inspection through `proofsignal-spec repair <alias>`.
- Decide whether the finding should return to clarification, planning, task generation, or implementation before proposing edits.
- Identify every use case affected by an edit to a reusable skill.
- Require user approval before applying edits.
- Do not write managed `.proofsignal/` artifacts directly. Persist managed artifacts through ProofSignal Spec CLI operations only.
- Preserve original specification, plan, task history, and skill reuse relationships.
- Never persist credential values.

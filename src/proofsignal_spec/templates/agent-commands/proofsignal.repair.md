# proofsignal.repair

Repair invalid or failed use cases through the workflow.

- Start by running `proofsignal-spec workflow check repair --alias <alias> --json`.
- Use the installed `proofsignal-spec` executable directly. Do not use `npx proofsignal-spec`.
- Continue only when the result includes `requiredCapability: workflow.guardrails/v1` and `supported: true`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal-spec` and regenerate the agent integration.
- If the check does not allow continuation, name the missing artifact or decision, point to `nextCommand`, and stop.
- Do not perform stage-specific work until the check allows it.
- Use Core validation findings or public report inspection through `proofsignal-spec repair <alias>`.
- Treat runtime contradictions and incomplete planned gate coverage as repair/replan inputs. Do not silently weaken browser skills when a planned gate is absent in the target product state.
- Only safe mechanical categories may be applied directly: selector ambiguity, wait strategy, main-skill ordering, run profile defaults, and gateId mapping.
- If a repair would replace dynamic discovery with fixed data, weaken a rendered-result gate, or remove required evidence, route it to clarification or planning instead of applying it.
- After any approved safe repair, require the CLI `revalidation.status` to be `passed` and `readyForRun: true` before a trusted rerun.
- Decide whether the finding should return to clarification, planning, task generation, or implementation before proposing edits.
- For absent planned gates, propose one of: update target data/runtime assumptions, mark the gate conditional with an explicit condition, or replan the use case.
- Identify every use case affected by an edit to a reusable skill.
- Require user approval before applying edits.
- Do not write managed `.proofsignal/` artifacts directly. Persist managed artifacts through ProofSignal Spec CLI operations only.
- Preserve original specification, plan, task history, and skill reuse relationships.
- Never persist credential values.

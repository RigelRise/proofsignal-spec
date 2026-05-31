# proofsignal.repair

Repair invalid or failed use cases through the workflow.

- Start by running `proofsignal-spec workflow check repair --alias <alias> --json`.
- Use the installed `proofsignal-spec` executable directly. Do not use `npx proofsignal-spec`.
- Continue only when the result includes `requiredCapability: workflow.guardrails/v1` and `supported: true`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal-spec` and regenerate the agent integration.
- If the check does not allow continuation, name the missing artifact or decision, point to `nextCommand`, and stop.
- If the only blocker is missing ProofSignal Core, classify it as environment setup, report that repair is not applicable without a deterministic finding, and point to `proofsignal-spec core setup --json`.
- If repair is blocked by stale workspace state or ambiguous ownership, inspect Golden Path state before proposing cleanup.
- Do not perform stage-specific work until the check allows it.
- Use Core validation findings or public report inspection through `proofsignal-spec repair <alias>`.
- Do not edit artifacts when no deterministic validation/run finding exists; missing Core must remain a no-op repair result.
- Classify the root cause before proposing edits. Name whether the finding is a missing prerequisite, environment recovery, wait/flow issue, selector issue, data/product-state issue, coverage-mapping issue, or unsupported feedback.
- Treat missing coverage from an aborted Core/browser run as diagnostic. Required gates remain required unless clarify/plan or an explicit gate-intent confirmation changes product intent.
- Treat runtime contradictions and incomplete planned gate coverage as repair/replan inputs. Do not silently weaken browser skills when a planned gate is absent in the target product state.
- Safe mechanical selector, wait strategy, step ordering, target specificity, equivalent-flow, and run-profile repairs may auto-apply only when the result classifies them as intent-preserving.
- If a safe mechanical repair is auto-applied, show before/after repair feedback, revalidation status, rerun status, and the next command. Do not report success until validate and rerun produce strict pass.
- Data assumptions, credentials, required gates, target selection, dynamic-versus-fixed data, and expected product behavior changes still require explicit confirmation.
- Conditional-gate and gateId mapping changes require confirmation before any artifact edit.
- If a repair would replace dynamic discovery with fixed data, weaken a rendered-result gate, or remove required evidence, route it to clarification or planning instead of applying it.
- After any auto-applied or approved repair, require revalidation and rerun before a trusted success report.
- Decide whether the finding should return to clarification, planning, task generation, or implementation before proposing edits.
- For absent planned gates, propose one of: update target data/runtime assumptions, mark the gate conditional with an explicit condition, or replan the use case.
- Identify every use case affected by an edit to a reusable skill.
- Require user approval before applying edits.
- Do not write managed `.proofsignal/` artifacts directly. Persist managed artifacts through ProofSignal Spec CLI operations only.
- Preserve original specification, plan, task history, and skill reuse relationships.
- Never persist credential values.

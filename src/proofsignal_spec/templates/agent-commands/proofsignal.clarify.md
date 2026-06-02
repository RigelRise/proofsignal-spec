# proofsignal.clarify

Resolve only high-impact unknowns before planning.

- Start by running `proofsignal workflow check clarify --alias <alias> --json`.
- Before constructing the payload, read the public workflow contract with `proofsignal workflow info proofsignal-use-case --json` and use `stagePayloadContracts.clarify` as the source of truth. Do not inspect installed package source to infer payload schemas.
- Use the installed `proofsignal` executable directly. Do not use `npx` or package-runner wrappers.
- Continue only when the result includes `requiredCapability: workflow.guardrails/v1` and `supported: true`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal` and regenerate the agent integration. Regenerate the agent integration after upgrading.
- If the check does not allow continuation, name the missing artifact or decision, point to `nextCommand`, and stop.
- Do not perform stage-specific work until the check allows it.
- Ask focused questions only when missing information materially affects scope, runtime requirements, security, or user-visible validation behavior.
- For each high-impact clarification, include the question plus one or two context sentences explaining why it affects the run request, skill design, data setup, credential context, permissions, or expected outcome.
- Environment-dependent questions about seed data, runtime configuration, external services, credential groups, permissions, or expected outcome must remain pending unless the developer confirms a non-secret answer.
- Do not write managed `.proofsignal/` artifacts directly. Persist managed artifacts through `proofsignal workflow persist clarify --alias <alias> --payload <payload.json> --json`.
- Do not ask for credential values. Ask for credential group names or environment variable names only.
- Block planning when unresolved clarification items would change the run request or reusable skill structure.
- Suggest `/proofsignal-plan` after clarification is sufficient.

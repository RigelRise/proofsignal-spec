# proofsignal.plan

Plan one run request and reusable skills before implementation.

- Start by running `proofsignal workflow check plan --alias <alias> --json`.
- Before constructing the payload, read the public workflow contract with `proofsignal workflow info proofsignal-use-case --json` and use `stagePayloadContracts.plan` as the source of truth. Use `coreExecutableContract` for Core-owned executable artifact/report sections. Do not inspect installed package source to infer payload schemas.
- Use the installed `proofsignal` executable directly. Do not use `npx` or package-runner wrappers.
- Continue only when the result includes `requiredCapability: workflow.guardrails/v1` and `supported: true`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal` and regenerate the agent integration. Regenerate the agent integration after upgrading.
- If the check does not allow continuation, name the missing artifact or decision, point to `nextCommand`, and stop.
- Do not perform stage-specific work until the check allows it.
- Read existing persisted context with `proofsignal workflow show --alias <alias> --json`. Do not invent `workflow show` alternatives or use `workflow status` as a use-case reader.
- Stop when unresolved runtime, data, credential, permission, or expected-outcome clarifications remain. Route back to `/proofsignal-clarify`.
- Do not leave `baseUrl` or equivalent target parameters empty after the user has supplied a target. Treat an empty target after clarification as a stage-handoff defect, not as a runtime prompt workaround.
- Require exactly one planned run request for the use case.
- Plan skills as decoupled reusable artifacts under `.proofsignal/skills/<name>.browser.md`; one skill may be referenced by multiple run requests.
- Make the main skill executable by Core for the complete planned validation path. Supporting skills can capture reusable intent, but Core v0.1 may execute only the main browser skill during a run.
- Identify the main skill, supporting skills, runtime input names, credential groups, expected app state, and validation gates.
- For write and external-notification use cases, plan `sideEffects` with `mode: enforce` unless explicitly selected otherwise, explicit `resourceIdentity`, the commit step id, allowed local envelope rules or confirmation signals, `runtimeOutputs` needed for follow-up validation, and `rerunPolicy`.
- Express local envelopes with canonical `sideEffectPolicy.allowed[]` and `sideEffectPolicy.forbidden[]`; do not author `sideEffectPolicy.rules[].effect/match`. Use only runtime-supported confirmation signals proven by public capability data or accepted runtime outcomes.
- When the owner accepts duplicate accumulation, record `collisionPolicy: allow-duplicates`; otherwise prefer a refreshable generated identity input or post-commit binding that can be checked locally on rerun.
- Generated runtime inputs must use generic use-case-owned names and preserve the seed plus a run-attempt token when freshness is required; do not hard-code target-project-specific parameter names into guidance.
- When a generated value must be validated later in the same run, plan it as a runtime input reference and, when Core supports it, a use-case-owned runtime output.
- Resolve `{{parameters.*}}` confirmation expected values before Core execution by planning runtime inputs that can safely materialize every placeholder; do not plan credential placeholders inside confirmation expected values.
- For browser page-view use cases, every required validation gate must have a stable `id`, `description`, and `required` flag. Conditional gates must include a human-readable `condition`.
- Plan explicit gate evidence: each UI assertion, backend request check, and screenshot intended to prove coverage must declare `gateId`.
- A page-view gate is not complete with only navigation, URL matching, body text, screenshots, or HTTP 200. Plan a specific rendered-result UI assertion with target and expected text/state/count.
- Backend checks must use Core-declared public network match keys from `coreExecutableContract.sections.browserWorkflow.validNetworkMatchKeys`; method/status may be metadata when Core declares them that way. Treat any key names in examples as non-authoritative examples, not as a local allowlist. Checks still need expected status and `gateId`; `operationName` is optional metadata only.
- Persist both `mainSkill` and `reusableSkills`. `supportingSkills` is accepted for compatibility, but `reusableSkills` is the canonical payload field.
- Reuse existing skills when appropriate instead of nesting or duplicating skills under a use case.
- Do not write managed `.proofsignal/` artifacts directly. Persist managed artifacts through `proofsignal workflow persist plan --alias <alias> --payload <payload.json> --json`.
- Block implementation when the plan lacks a run request or skill relationship.
- Suggest `/proofsignal-tasks` after the plan is approved.

# proofsignal.plan

Plan one run request and reusable skills before implementation.

- Start by running `proofsignal-spec workflow check plan --alias <alias> --json`.
- Use the installed `proofsignal-spec` executable directly. Do not use `npx proofsignal-spec`.
- Continue only when the result includes `requiredCapability: workflow.guardrails/v1` and `supported: true`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal-spec` and regenerate the agent integration.
- If the check does not allow continuation, name the missing artifact or decision, point to `nextCommand`, and stop.
- Do not perform stage-specific work until the check allows it.
- Read existing persisted context with `proofsignal-spec workflow show --alias <alias> --json`. Do not invent `workflow show` alternatives or use `workflow status` as a use-case reader.
- Stop when unresolved runtime, data, credential, permission, or expected-outcome clarifications remain. Route back to `/proofsignal-clarify`.
- Do not leave `baseUrl` or equivalent target parameters empty after the user has supplied a target. Treat an empty target after clarification as a stage-handoff defect, not as a runtime prompt workaround.
- Require exactly one planned run request for the use case.
- Plan skills as decoupled reusable artifacts under `.proofsignal/skills/<name>.browser.md`; one skill may be referenced by multiple run requests.
- Make the main skill executable by Core for the complete planned validation path. Supporting skills can capture reusable intent, but Core v0.1 may execute only the main browser skill during a run.
- Identify the main skill, supporting skills, runtime input names, credential groups, expected app state, and validation gates.
- For browser page-view use cases, every required validation gate must have a stable `id`, `description`, and `required` flag. Conditional gates must include a human-readable `condition`.
- Plan explicit gate evidence: each UI assertion, backend request check, and screenshot intended to prove coverage must declare `gateId`.
- A page-view gate is not complete with only navigation, URL matching, body text, screenshots, or HTTP 200. Plan a specific rendered-result UI assertion with target and expected text/state/count.
- Backend checks must declare method, public match keys such as `urlContains`, `status`, `requestBodyContains`, or `responseBodyContains`, expected status, and `gateId`. `operationName` is optional metadata only.
- Persist both `mainSkill` and `reusableSkills`. `supportingSkills` is accepted for compatibility, but `reusableSkills` is the canonical payload field.
- Reuse existing skills when appropriate instead of nesting or duplicating skills under a use case.
- Do not write managed `.proofsignal/` artifacts directly. Persist managed artifacts through `proofsignal-spec workflow persist plan --alias <alias> --payload <payload.json> --json`.
- Block implementation when the plan lacks a run request or skill relationship.
- Suggest `/proofsignal-tasks` after the plan is approved.

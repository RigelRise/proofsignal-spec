# proofsignal.specify

Define one browser validation use case before artifact planning.

- Start by running `proofsignal workflow check specify --json`.
- Before constructing the payload, read the public workflow contract with `proofsignal workflow info proofsignal-use-case --json` and use `stagePayloadContracts.specify` as the source of truth. Do not inspect installed package source to infer payload schemas.
- Use the installed `proofsignal` executable directly. Do not use `npx` or package-runner wrappers.
- Continue only when the result includes `requiredCapability: workflow.guardrails/v1` and `supported: true`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal` and regenerate the agent integration. Regenerate the agent integration after upgrading. Do not fall back to `proofsignal check`, directory listing, repository inspection, or use-case questions.
- repository understanding is required before use case specification can be grounded.
- If the check returns `missing` with `recommendedAction: auto-prepare-understanding`, treat it as the Golden Path onboarding auto-prepare path, not as a terminal blocker.
- For missing understanding, state that safe repository understanding will inspect public project structure and non-sensitive context, give an approximate time expectation, run the understand workflow, and then resume the original specify flow without requiring the user to manually restart `/proofsignal-specify`.
- Use `onboardingPreparation.nextCommand`, `onboardingPreparation.resumeCommand`, `resumeCommand`, and `stageCards` from the check result as the source of truth for the next action. Ask once only when the result says host permissions or sensitive boundaries require approval.
- If auto-prepare succeeds, return to first-run recommendation in the same conversation instead of asking the developer to invoke `/proofsignal-specify` again.
- Do not ask for alias, target behavior, expected outcome, run request details, or skill details while repository understanding is missing.
- If the check returns `stale`, explain the stale reason from the result and why refresh is important for accurate run requests and skills.
- When stale refresh is accepted, run `proofsignal workflow check specify --refresh-decision accepted --json`, route through `/proofsignal-understand`, then return to candidate selection.
- When stale refresh is declined, run `proofsignal workflow check specify --refresh-decision declined --json` and continue with the stale-context warning.
- When the check returns `ready`, immediately run `proofsignal workflow recommend-first-run --json` and use that response as the product-owned first-run recommendation source of truth.
- Do not present candidateUseCases or recommendedCandidate from workflow check as the product-owned first-run recommendation; those fields are inventory context only. The first recommendation must come from `workflow recommend-first-run`.
- Present the project overview, the recommended first-run candidate from `workflow recommend-first-run`, branchRelevantCandidates separately, and then other candidate validation use cases before asking what to specify.
- Prefer the product-owned real-target first-run recommendation when the developer is new to the project. Canonical examples may be mentioned as learning aids after that recommendation, not as fake/demo fallbacks.
- If the coverage inventory is `partial`, state that more scenarios may exist and offer `/proofsignal-understand` with `--scope continue` or a focused scope before listing speculative additions.
- If the coverage inventory is `complete`, list additional scenarios from inventory when the developer asks for more.
- Let the developer choose a candidate or provide a custom use case.
- Record exactly one validation intent with alias, purpose, target surface, expected outcome, runtime assumptions, acceptance scenarios, and unresolved questions.
- Browser validation use cases require a resolved target application environment before executable planning. If the target URL, local start command, or equivalent browser target is not known, record it as a high-impact unresolved question and route to `/proofsignal-clarify`.
- If the request contains multiple behaviors, split or ask for clarification before planning.
- Do not write managed `.proofsignal/` artifacts directly. Persist managed artifacts through `proofsignal workflow persist specify --alias <alias> --payload <payload.json> --json`.
- Keep the use case mapped to exactly one future run request.
- Do not create run request or skill files in this stage.
- Suggest `/proofsignal-clarify` as the next command when high-impact unknowns remain.

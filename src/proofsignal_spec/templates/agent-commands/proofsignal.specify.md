# proofsignal.specify

Define one browser validation use case before artifact planning.

- Start by running `proofsignal-spec workflow check specify --json`.
- Use the installed `proofsignal-spec` executable directly. Do not use `npx proofsignal-spec`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal-spec` and regenerate the agent integration. Do not fall back to `proofsignal-spec check`, directory listing, repository inspection, or use-case questions.
- If the check returns `missing`, explain that repository understanding is required before use case specification can be grounded.
- For missing understanding, state that safe repository understanding will inspect public project structure and non-sensitive context, give an approximate time expectation, and point to `/proofsignal-understand`.
- Do not ask for alias, target behavior, expected outcome, run request details, or skill details while repository understanding is missing.
- If the check returns `stale`, explain the stale reason from the result and why refresh is important for accurate run requests and skills.
- When stale refresh is accepted, run `proofsignal-spec workflow check specify --refresh-decision accepted --json`, route through `/proofsignal-understand`, then return to candidate selection.
- When stale refresh is declined, run `proofsignal-spec workflow check specify --refresh-decision declined --json` and continue with the stale-context warning.
- When the check returns `ready`, present the project overview, candidate validation use cases, and one recommended starting candidate before asking what to specify.
- Let the developer choose a candidate or provide a custom use case.
- Record exactly one validation intent with alias, purpose, target surface, expected outcome, runtime assumptions, acceptance scenarios, and unresolved questions.
- If the request contains multiple behaviors, split or ask for clarification before planning.
- Store the stage document in `.proofsignal/workflows/use-cases/<alias>/spec.md`.
- Keep the use case mapped to exactly one future run request.
- Do not create run request or skill files in this stage.
- Suggest `/proofsignal-clarify` as the next command when high-impact unknowns remain.

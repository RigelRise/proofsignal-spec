# proofsignal.list

List use cases and workflow status.

- No repository understanding prerequisite is required for this command.
- Start by running `proofsignal workflow check list --json` for a deterministic no-prerequisite status before listing.
- Use the installed `proofsignal` executable directly. Do not use `npx` or package-runner wrappers.
- Continue only when the result includes `requiredCapability: workflow.guardrails/v1` and `supported: true`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal` and regenerate the agent integration.
- Use deterministic CLI commands such as `proofsignal list` and `proofsignal workflow list`.
- Do not write managed `.proofsignal/` artifacts directly. Persist managed artifacts through ProofSignal Spec CLI operations only.
- Summarize aliases with `lastRun` separate from `current` readiness. A historical passed run is not current readiness.
- Treat `current.status` as local metadata only: `not-checked`, `stale`, `needs-validate`, `blocked`, or `ready` from a persisted readiness snapshot.
- The normal list view must remain metadata-only. Do not call Core, network, credential, entitlement, target reachability, or browser checks from list.
- Include the compact row facts: alias, last run, current state, requirements, and risk.
- For credentialed rows, show credential group and required runtime names only; never show values.
- For write/external-notification rows, show side-effect class, cleanup policy, and confirmation/rerun risk when present.
- Show normalized readiness/risk labels rather than raw post-commit field names. A historical passed write run is not proof that a rerun will use a fresh resource identity.
- Do not inspect sensitive files.
- Surface the next recommended `/proofsignal-*` command when a use case is blocked.

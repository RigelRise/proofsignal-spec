# proofsignal.validate

Validate draft artifacts through ProofSignal Spec and Core.

- Start by running `proofsignal-spec workflow check validate --alias <alias> --json`.
- Use the installed `proofsignal-spec` executable directly. Do not use `npx proofsignal-spec`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal-spec` and regenerate the agent integration.
- If the check does not allow continuation, name the missing artifact or decision, point to `nextCommand`, and stop.
- Do not perform stage-specific work until the check allows it.
- Delegate Core-dependent behavior through `proofsignal-spec validate <alias> --runtime-readiness`.
- Preserve Core verdicts exactly and do not reinterpret passed, failed, blocked, or error outcomes.
- Record redacted validation summaries in workflow state and stage documents.
- Do not parse raw report internals or import private ProofSignal Core packages.
- Suggest `/proofsignal-run` when validation passes or `/proofsignal-repair` when actionable findings exist.

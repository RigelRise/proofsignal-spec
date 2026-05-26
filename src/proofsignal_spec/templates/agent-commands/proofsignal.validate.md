# proofsignal.validate

Validate draft artifacts through ProofSignal Spec and Core.

- Start by running `proofsignal-spec workflow check validate --alias <alias> --json`.
- Use the installed `proofsignal-spec` executable directly. Do not use `npx proofsignal-spec`.
- Continue only when the result includes `requiredCapability: workflow.guardrails/v1` and `supported: true`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal-spec` and regenerate the agent integration.
- If the check does not allow continuation, name the missing artifact or decision, point to `nextCommand`, and stop.
- Do not perform stage-specific work until the check allows it.
- Review `structuralValidation` before Core validation. If structural validation is blocked, report the exact finding and do not call Core.
- If recoverable migration plans are present, ask the developer before invoking `proofsignal-spec workflow migrate --approve <migration-id> --json`.
- If Core is missing, state that structural validation can still run, but ProofSignal Core is required for the complete ProofSignal validation and browser execution experience. Explain how to configure it with `proofsignal-spec init --core-cmd /path/to/proofsignal` or `PROOFSIGNAL_CORE_CMD`.
- Delegate Core-dependent behavior through `proofsignal-spec validate <alias> --runtime-readiness`.
- Preserve Core verdicts exactly and do not reinterpret passed, failed, blocked, or error outcomes.
- Record redacted validation summaries in workflow state and stage documents.
- Do not write managed `.proofsignal/` artifacts directly. Persist managed artifacts through ProofSignal Spec CLI operations only.
- Do not use `proofsignal-spec author`, nonexistent schema/scaffold commands, or manual file edits to repair workflow-managed artifacts. Route schema fixes through `/proofsignal-repair` or `proofsignal-spec workflow persist implement`.
- Do not parse raw report internals or import private ProofSignal Core packages.
- Suggest `/proofsignal-run` when validation passes or `/proofsignal-repair` when actionable findings exist.

# Bundled Templates

Templates are copied into target repositories by `proofsignal-spec init`.
Generated text is English-only and points agents at the `.proofsignal/`
workspace and public ProofSignal Core CLI boundary.

Every staged `/proofsignal-*` template must start with the installed
`proofsignal-spec workflow check <stage>` command and require the
`workflow.guardrails/v1` capability before repository inspection or stage work.
Templates must not suggest package-manager fallbacks, and they must route all
managed `.proofsignal/` writes through canonical CLI operations such as
`proofsignal-spec workflow persist`.

Stage authoring templates must point agents to the public workflow contract from
`proofsignal-spec workflow info proofsignal-use-case --json`. Payload shape
guidance comes from `stagePayloadContracts`, not installed package source.

Real-run guardrail templates must also preserve the planned main skill, require
explicit `gateId` evidence mappings, distinguish Core technical status from
Spec planned coverage status, and route runtime contradictions through repair or
replan instead of weakening skills live.

Browser workflow guardrail templates must require target environment
confirmation before executable planning, preserve resolved target decisions
through plan and implementation, and require
`proofsignal-spec validate <alias> --runtime-readiness` before reporting
browser artifacts ready.

Validation output describes authored evidence mapping and must keep
`fullBrowserFlowExecuted: false` until `/proofsignal-run` executes. Run output
must treat `status` as the authoritative use-case verdict and keep
`coreBrowserStatus` separate from `specCoverageStatus`. A Core pass with missing
required gates is `status: incomplete`; a failed Core/browser run makes coverage
diagnostic and must not be summarized as passed.

Repair guidance must classify the root cause before edits. Missing prerequisite,
environment recovery, wait/flow, selector, data/product-state, coverage mapping,
and unsupported feedback have different next actions. Selector, wait/flow, data,
and coverage changes require confirmation before any artifact edit. Changes that
alter clarified data decisions or weaken required gates must return to
clarification or planning.

Human-observable debug/browser runs default to `slowMoMs: 900`; explicit
`--slow-mo` values still win.

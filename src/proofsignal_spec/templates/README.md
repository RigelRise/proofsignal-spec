# Bundled Templates

Templates are copied into target repositories by `proofsignal init`.
Generated text is English-only and points agents at the `.proofsignal/`
workspace and public ProofSignal Core CLI boundary.

Every staged `/proofsignal-*` template must start with the installed
`proofsignal workflow check <stage>` command and require the
`workflow.guardrails/v1` capability before repository inspection or stage work.
Templates must not suggest package-manager fallbacks, and they must route all
managed `.proofsignal/` writes through canonical CLI operations such as
`proofsignal workflow persist`.

Stage authoring templates must point agents to the public workflow contract from
`proofsignal workflow info proofsignal-use-case --json`. Payload shape
guidance comes from `stagePayloadContracts`, not installed package source.

Executable skill boundary guidance must distinguish executable skills from
source-only reusable skills. A run request lists only the skills that Spec has
resolved as executable for the current Core public contract. When Core does not
declare deterministic multi-skill roles, ordering, and evidence semantics,
agents must compose required reusable behavior into the main skill and preserve
helper skills only as source-only metadata.

Real-run guardrail templates must also preserve the planned main skill, require
explicit `gateId` evidence mappings, distinguish Core technical status from
Spec planned coverage status, and route runtime contradictions through repair or
replan instead of weakening skills live.

Browser workflow guardrail templates must require target environment
confirmation before executable planning, preserve resolved target decisions
through plan and implementation, and require
`proofsignal validate <alias> --runtime-readiness` before reporting
browser artifacts ready.

Validation output describes authored evidence mapping and must keep
`fullBrowserFlowExecuted: false` until `/proofsignal-run` executes. Run output
must treat `status` as the authoritative use-case verdict and keep
`coreBrowserStatus` separate from `specCoverageStatus`. A Core pass with missing
required gates is `status: incomplete`; a failed Core/browser run makes coverage
diagnostic and must not be summarized as passed.

Golden Path guidance must recommend a real-target first run before optional
examples, render recommendation/run/repair/blocker results as stage cards, and
never use fake/demo targets as a user-facing fallback.

Repair guidance must classify the root cause before edits. Missing prerequisite,
environment recovery, wait/flow, selector, data/product-state, coverage mapping,
and unsupported feedback have different next actions. Safe mechanical selector,
wait, ordering, target-specificity, equivalent-flow, and run-profile repairs may
auto-apply only when validation intent is preserved. Data, credential, required
gate, target-selection, and expected-behavior changes still require
confirmation.

Execution-boundary repair guidance must not weaken required gates when a helper
or source-only skill passed without mapped evidence. The correct recovery is to
compose helper behavior into the main executable skill, reclassify the helper as
source-only, or use a Core runtime whose public contract declares supported
multi-skill execution.

Human-observable debug/browser runs default to `slowMoMs: 900`; explicit
`--slow-mo` values still win.

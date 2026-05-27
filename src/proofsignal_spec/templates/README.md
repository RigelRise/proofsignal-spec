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

Real-run guardrail templates must also preserve the planned main skill, require
explicit `gateId` evidence mappings, distinguish Core technical status from
Spec planned coverage status, and route runtime contradictions through repair or
replan instead of weakening skills live.

Browser workflow guardrail templates must require target environment
confirmation before executable planning, preserve resolved target decisions
through plan and implementation, and require
`proofsignal-spec validate <alias> --runtime-readiness` before reporting
browser artifacts ready.

Run output must treat `status` as the authoritative use-case verdict and keep
`coreStatus` separate. A Core pass with missing required gates is
`status: incomplete` and must not be summarized as a passed validation.

Repair guidance may apply only deterministic contract and metadata fixes
directly, such as main-skill ordering and run profile defaults. Selector, flow,
data, and coverage changes require confirmation before any artifact edit.
Changes that alter clarified data decisions or weaken required gates must return
to clarification or planning.

Human-observable debug/browser runs default to `slowMoMs: 900`; explicit
`--slow-mo` values still win.

# verifysignal (default one-pass loop)

Drive one browser validation use case end to end in a single pass: discover
grounded selectors, author, validate, run, and apply safe repairs — stopping only
when a real unknown or a write side-effect needs the developer. This command
orchestrates the existing staged workflow; it does not replace it. `workflow
persist` remains the only path that writes managed `.verifysignal/` artifacts.

## Preconditions

- Use the installed `verifysignal` executable directly. Do not use `npx` or package-runner wrappers.
- Read the public workflow contract with `verifysignal workflow info verifysignal-use-case --json` and use `stagePayloadContracts`, `coreExecutableContract`, and `browserAuthoringContract` as the source of truth for payload shapes, actions, assertions, and target rules.
- Confirm Core supports dynamic grounding: read `verifysignal core version --json` and check the `data.operations` array for an entry `{ name: "discover", schema: "verifysignal.discover/v1" }`. If absent, tell the developer their VerifySignal Core predates dynamic grounding and either (a) recommend upgrading Core, or (b) proceed source-only WITHOUT the grounding step (state that selectors will not be DOM-verified before the first run). Do not fail opaquely.
- Detect live-authoring capability — an agent self-check, NOT a CLI probe (a Playwright MCP is your own tool, so there is no `verifysignal` command to detect it): if you have Playwright MCP browser tools (`browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type`), you will author and repair selectors against the live page using the live protocol in steps 2–3 and 8. If you do not, author from source as today. Either way `discover` (confirm) and `run` (gate) are unchanged and remain the authority.
- If repository understanding is missing or stale, route through `/verifysignal-understand` (or the Golden Path auto-prepare path) first, then resume here. Do not guess product structure.

## Loop

1. Resolve the target application environment (the `baseUrl` / live URL). If no target URL or local start command is known and cannot be derived from repository signals, STOP and ask the developer for it (escalation 1). Never invent a URL.
2. Draft the use case from source and — if you have Playwright MCP tools — from a live accessibility snapshot: read the relevant product source and the developer's goal. If a Playwright MCP is available, scope it to the target app only (e.g. `--allowed-hosts`/`--blocked-origins` for the target host), navigate to the `baseUrl`, take an accessibility snapshot, and read the role/name/text of the elements your steps will touch; translate each into a `browser.targets` entry using the contract priority — prefer a stable `testId`; else map the accessibility role+name onto `label`/`text`/`semanticLocator`; use `css` only as a last resort. Do NOT copy raw MCP node refs (e.g. `ref=e17`) into targets — those refs are valid only within a single snapshot and are not a VerifySignal selector signal. On write surfaces, walk the live flow only up to the planned commit step (`commitStepId`); never click through the commit. On authenticated surfaces, source auth from the environment or a developer-controlled `--storage-state`; never persist it. Then prepare the staged payloads (specify → clarify → plan → tasks → implement) as in the normal workflow, including the browser skill `targets`/`steps`/`assertions`. Do NOT persist credential values, MCP snapshots, screenshots, or DOM. Do NOT persist yet.
3. Ground the drafted selectors against the live DOM — run this regardless of whether selectors were authored from source or from a live MCP snapshot; the MCP snapshot is never the confirmation, `discover` is, and if a `discover` correction disagrees with what an MCP snapshot implied, take the `discover` correction (`discover` wins): write the drafted skill to a temporary path and run `verifysignal discover --url <baseUrl> --skill <drafted-skill> --json`. For every target whose `status` is `not-found` or `resolved-ambiguous` that carries a `suggestedCorrection`, replace that target's selector in the draft with the suggested correction. Use ONLY selectors that `discover` confirmed against the live DOM or that you declared and `discover` reported `resolved-unique`; never invent a selector. If any target remains `not-found`/`resolved-ambiguous` with no confident correction (overall stays `needs-correction`), STOP and ask the developer which element is meant (escalation 4).
4. Persist the corrected use case through the staged commands in one pass: run `verifysignal workflow persist specify|clarify|plan|tasks|implement` in order, supplying the prepared payloads, with the grounded `browser.targets` in the implement payload. Do not return to the developer between stages unless a stage result is `blocked` or an escalation fires. `workflow persist` is the only artifact-write path.
5. Classify side effects before any run that could mutate product state. If `sideEffects.class` is `write` or `external-notification` and no resolved `resourceIdentity` exists, STOP and require explicit developer confirmation plus a resource identity before running (escalation 3). Author canonical `sideEffectPolicy.allowed[]`/`forbidden[]` only.
6. Validate: run `verifysignal validate <alias> --runtime-readiness`. If it blocks on a missing required credential, STOP and ask the developer to provide it through their environment; never persist credential values (escalation 2).
7. Run: `verifysignal run <alias> --profile normal`.
8. Observe and repair: if the run fails, run `verifysignal repair <alias>` to classify the finding, then read each recommendation's `autonomy` field and act on THAT — do not assume a category is automatic. `auto-applied` (step ordering) is the only kind `verifysignal repair <alias> --approve` actually edits on disk; run it, then rerun. `propose-only` (selector re-scoping, wait strategy, run-profile) is DESCRIBED, not applied: `--approve` will report it `proposed` and change nothing, so make the edit yourself — re-scope selectors using the `discover` candidates/alternates, re-ground with `verifysignal discover`, persist through `workflow persist implement` — then rerun. Bound this to 2 repair attempts. On the 3rd failure, or any repair the classifier routes to clarify/plan (a real requirement or product-state gap), STOP and surface the report path and the recommended stage (escalation 5).

## Escalation rules (STOP and ask the developer)

1. Unresolved target URL / local start command.
2. Missing required credential at validation or run preparation (never persist values).
3. Write / external-notification side-effect class without a resolved `resourceIdentity`.
4. Grounding still `not-found`/ambiguous after correction (no confident selector).
5. Run still failing after 2 safe auto-repairs, or a repair routed to clarify/plan.

## Guardrails (verbatim)

- `workflow persist` is the ONLY way to write managed `.verifysignal/` artifacts; never edit them directly.
- Never persist or print credential values, email unlock tokens, signed download URLs, receipt payloads, cookies, browser storage, screenshots, or product source snapshots.
- Targets must come from the draft or from `discover` output; assertions must map to meaningful gates, not generic body text or a bare 200/navigation/screenshot.
- The Playwright MCP is an authoring/repair aid only — never the validator. Every selector it produces is laundered through `discover` (confirm) and `run` (gate); if the MCP and `discover` disagree, `discover` wins.
- Never persist or print MCP accessibility snapshots, DOM, screenshots, cookies, or storage state. On write surfaces, MCP exploration stops before `commitStepId`; only the deterministic `run` crosses the commit, under existing side-effect gates.
- Keep the use case mapped to exactly one run request; skills remain decoupled reusable artifacts.
- On a strict pass (direct or after safe repair + revalidation + rerun), report the single outcome summary and the evidence/report path.

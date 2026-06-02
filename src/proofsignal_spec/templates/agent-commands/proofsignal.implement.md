# proofsignal.implement

Create or update only planned draft artifacts.

- Start by running `proofsignal workflow check implement --alias <alias> --json`.
- Before constructing the payload, read the public workflow contract with `proofsignal workflow info proofsignal-use-case --json` and use `stagePayloadContracts.implement` as the source of truth. Do not inspect installed package source to infer payload schemas.
- Use the installed `proofsignal` executable directly. Do not use `npx` or package-runner wrappers.
- Continue only when the result includes `requiredCapability: workflow.guardrails/v1` and `supported: true`.
- If `workflow check` is unavailable, unsupported, or exits with an invalid subcommand error, stop immediately and tell the developer to upgrade `proofsignal` and regenerate the agent integration. Regenerate the agent integration after upgrading.
- If the check does not allow continuation, name the missing artifact or decision, point to `nextCommand`, and stop.
- Do not perform stage-specific work until the check allows it.
- Read approved tasks and persisted context with `proofsignal workflow show --alias <alias> --json`.
- Read the browser authoring contract with `proofsignal workflow info proofsignal-use-case --json` before drafting browser skill intent. Use `browserAuthoringContract.validActions`, `browserAuthoringContract.validAssertionKinds`, and `browserAuthoringContract.validNetworkMatchKeys` as the source of truth.
- Follow `.proofsignal/workflows/use-cases/<alias>/tasks.md`.
- Prepare structured artifact intent for `.proofsignal/run-requests/<alias>.yaml` and `.proofsignal/skills/<name>.browser.md`; the CLI owns the final `qa-run-request/v1` and `qa-skill/v1` envelopes.
- Preserve the planned `mainSkill` from the artifact plan. Do not rely on `skills[0]`; reusable helper skills may appear before the main skill in submitted payloads.
- Browser skills with detailed validation intent must include executable Core browser actions under `intent.browser.steps` and final checks under `intent.browser.assertions`. Natural-language `intent.body` or `intent.steps` are preserved as notes, but they are not a substitute for executable browser steps.
- Browser step `target` values must reference named entries under `intent.browser.targets`; do not put inline selectors such as `input#search`, `text=Teams`, `placeholder=Search people`, XPath, or role syntax directly in a step target.
- Each named browser target should use one primary selector signal (`testId`, `label`, `text`, `css`, `semanticLocator`, or `all`). Do not combine `label` and `css` as fallback signals; Core uses priority order and ignores later signals.
- `navigate` uses `value` for the URL, not `target`. `checkText` and `waitForText` require both a named `target` and a string `value`. `awaitNetwork` requires a `match` object using supported keys such as `method` or `urlContains`.
- Evidence used for planned coverage must declare `gateId` on the relevant browser step/assertion. Required page-view gates need specific UI assertions mapped by `gateId`; screenshots, URL checks, generic body text, and successful backend responses are supporting evidence only.
- Declared backend checks for coverage must include method, a public match key, expected status, and `gateId`. Keep `operationName` only as optional non-sensitive metadata; do not make it the sole runtime matcher.
- If a use case needs visual inspection, submit use-case-scoped profiles such as `visual-15s` with non-secret `headed` and `slowMoMs` settings. Do not change global debug defaults.
- Browser assertions use `expected`, not `value`, and run after all steps complete. Put intermediate gate checks in step-level `checkText`/`checkLocation` actions or captured screenshot evidence.
- For debounced inputs, avoid `awaitNetwork` immediately after `fill`; use `checkText` or `waitForText` with a long enough `timeoutMs` to cover debounce, API response, and render.
- Do not iterate on schema errors manually. If artifact content is partial, send the intent through `workflow persist implement` so the CLI can normalize the canonical envelope or block unsafe no-op artifacts.
- Do not write managed `.proofsignal/` artifacts directly. Persist managed artifacts through `proofsignal workflow persist implement --alias <alias> --payload <payload.json> --json`.
- The CLI must update canonical use-case records and registry entries; never manually author registry entries or canonical use-case records.
- Do not use `proofsignal author`, `proofsignal core schema` as fallbacks inside this staged workflow.
- Do not change artifacts that are not named by the approved plan and tasks.
- Keep generated run requests and skills as drafts until validation passes.
- Run `proofsignal validate <alias> --runtime-readiness` before reporting browser artifacts ready.
- Never persist credential values.
- Suggest `/proofsignal-validate` after draft artifacts are created.

# Contract: Agent-Chat Stage Card

## Purpose

Define the primary UX contract for Codex and Claude first-run chat output.
Stage cards make the first run visually clear, consistent, and testable without
requiring a web dashboard or raw log reading.

## Required fields

Each first-run stage card must include:

- `stageId`
- `title`
- `statusMarker`
- `summary`
- `whyItMatters`
- `primaryEvidence`
- `repairDetails` when repair occurred
- `nextAction`

## Status markers

Allowed markers:

- `[RECOMMENDED]`
- `[ACCEPTED]`
- `[RUNNING]`
- `[PASS]`
- `[REPAIR]`
- `[SKIPPED]`
- `[BLOCKED]`
- `[FAIL]`

## Rendering requirements

Agent guidance must render each card with:

- A clear separator before the card.
- A short title line containing the status marker.
- A one-line summary before details.
- At most one primary evidence block before secondary references.
- A clear next action line.
- No raw logs as the primary content.
- No credential values, browser storage values, cookie values, or raw sensitive
  payloads in card content.

Recommended chat shape:

```text
---
[PASS] Stage Title
Summary: ...
Why it matters: ...
Evidence: ...
Repair: ...
Next: ...
```

`Repair:` is omitted when no repair occurred.

## Validation requirements

Tests must verify that generated Codex and Claude guidance names the required
fields and that first-run-related command output can supply enough structured
data to populate the cards.

## Non-AI CLI equivalence

CLI output does not need to mimic chat formatting, but JSON and text summaries
must expose equivalent status, evidence, repair, and next-action semantics.

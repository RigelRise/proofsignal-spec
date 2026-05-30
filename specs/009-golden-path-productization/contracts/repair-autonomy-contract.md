# Contract: Repair Autonomy

## Purpose

Define which first-run repairs may be applied automatically and which require
explicit user confirmation.

## Auto-applicable safe mechanical repairs

The repair flow may auto-apply a repair only when it preserves validation
intent and belongs to one of these categories:

- selector specificity or ambiguity fix
- wait strategy adjustment
- step ordering fix
- target specificity fix
- equivalent flow fix that validates the same product behavior
- run profile default correction

Auto-applied repairs must include before/after feedback and must be followed by
revalidation and rerun before success is reported.

## Confirmation-required repairs

The repair flow must request and record user confirmation before changing:

- expected product behavior
- required gate intent
- required evidence type
- data assumptions or seeded state
- credential requirements or credential references
- target environment selection
- dynamic discovery vs fixed data decisions

## Blocked repairs

The repair flow must block and route to clarification or planning when a repair
would:

- weaken required rendered-result evidence
- remove a required gate
- replace a real target with a fake/demo target
- persist credential values
- persist browser storage values, cookie values, or raw sensitive payloads
- rely on private Core internals

## Feedback requirements

Each repair feedback record must include:

- root-cause category
- autonomy decision: `auto-applied`, `confirmation-required`, or `blocked`
- before summary
- after summary when changed
- reason validation intent was preserved
- revalidation status
- rerun status when rerun occurred
- next action

Repair feedback must summarize sensitive contexts without including credential
values, browser storage values, cookie values, or raw sensitive payloads.

## Compatibility note

This contract intentionally narrows the previous conservative policy from
feature 008. Selector and wait/flow fixes no longer always require confirmation;
they may auto-apply only when classified as safe mechanical repairs that
preserve intent.

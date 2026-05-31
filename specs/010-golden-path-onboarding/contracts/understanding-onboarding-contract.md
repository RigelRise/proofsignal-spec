# Contract: Understanding Onboarding

## Purpose

Define how missing or stale repository understanding is handled during the
first-run onboarding path.

## CLI surfaces

```text
proofsignal-spec workflow check specify --project <path> --json
proofsignal-spec workflow persist understand --scope all --payload <path> --project <path> --json
proofsignal-spec workflow recommend-first-run --project <path> --json
```

Agents may orchestrate these commands, but the state and validation semantics
come from ProofSignal Spec.

## Missing understanding behavior

When specify starts and no understanding exists:

- Safe repository understanding should be prepared automatically when host
  permissions allow it.
- The user should be asked once only when host permission or sensitive access
  boundaries require approval.
- After understanding is prepared, the user should return to first-run
  recommendation without restarting the original flow.

## Inventory completion rules

Understanding should attempt to complete the full discoverable use-case
inventory whenever possible. If it remains partial:

- `coverageInventory.status` must be `partial` or `stale`.
- `partialInventoryReasons` or equivalent warnings must explain the gap.
- First-run recommendation may proceed only with clear partial-inventory
  labeling.

## Source traceability rules

Each candidate must include source inventory items before it can be recommended.
Persistence should normalize traceability when it can be safely inferred from
inventory paths or candidate surfaces. If traceability cannot be inferred, the
blocker must name the candidate and required field in user-readable language.

## Public metadata secret-safety allowlist

The following are safe public metadata unless they contain secret-bearing
context:

- normal commit identifiers
- branch names
- route paths
- file paths
- inventory item IDs
- candidate aliases

Secret detection still blocks credential fields, URLs with secret-bearing query
parameters, auth headers, tokens, private keys, local env values, browser
storage values, cookie values, and raw sensitive payloads.

## Stale understanding rules

Golden Path must respect existing understanding freshness rules. It must not
define a separate stale policy. If existing rules require refresh or label the
inventory partial, first-run recommendation must surface that status before the
user accepts.

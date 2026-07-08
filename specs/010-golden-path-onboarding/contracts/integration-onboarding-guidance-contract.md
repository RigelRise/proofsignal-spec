# Contract: Integration Onboarding Guidance

## Purpose

Define the install-time experience for agent integrations so a new user knows
what to do immediately after installation and can revisit the guidance locally.

## CLI surface

```text
verifysignal-spec integration install codex --project <path> --json
verifysignal-spec integration install claude --project <path> --json
verifysignal-spec integration upgrade [codex|claude] --project <path> --json
```

## JSON shape

Install and upgrade results must include:

- `integration`: Installed integration state.
- `installedFiles`: Managed files installed or updated.
- `onboardingGuide`: Object describing the user-facing guidance.

`onboardingGuide` fields:

- `terminalTitle`
- `terminalSummary`
- `generatedGuidePath`
- `nextCommand`
- `stageMarkers`
- `safetyBoundaries`
- `successSemantics`
- `plainTextFallback`

## Terminal rendering requirements

Text output should be visually scannable and include:

- A clear title or separator.
- Current status marker.
- Recommended next command.
- What the Golden Path first run will do.
- What files or data will not be inspected without approval.
- Meaning of pass, repaired pass, skip, blocked, and failed.

Color or emphasis may be used when available. The same information must remain
readable without color.

## Generated local guidance requirements

The installed integration must include durable local guidance that explains:

- How to start the Golden Path.
- Why accepting the first run is highly recommended.
- How to skip and what skip means.
- How safe repair is surfaced.
- How to continue with ordinary use cases after the first run.
- Secret-safety boundaries.

## Safety requirements

Guidance must not include credential values, local environment values, browser
storage values, cookie values, or raw sensitive payloads.

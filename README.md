# ProofSignal Spec

ProofSignal Spec is the public/open interface layer for writing, validating,
running, and repairing ProofSignal browser use cases. The user-facing command is
`proofsignal`; `proofsignal-spec` remains a backward-compatible alias.

The CLI creates a `.proofsignal/` workspace in a target repository, installs
Codex or Claude Code agent skills, stores use case records, resolves aliases to
explicit ProofSignal run requests and reusable skills, and delegates validation,
run execution, and report inspection to the private ProofSignal runtime through
the public `proofsignal-public-cli-json/v1` CLI JSON contract.

## Installation

Install directly from the official Git repository, pinned to a release tag:

```sh
uv tool install proofsignal --from git+https://github.com/<ORG>/proofsignal-spec.git@vX.Y.Z
```

Or install the latest commit from the default branch:

```sh
uv tool install proofsignal --from git+https://github.com/<ORG>/proofsignal-spec.git
```

Then verify the tool:

```sh
proofsignal --version
```

Upgrade by reinstalling from the desired tag:

```sh
uv tool install proofsignal --force --from git+https://github.com/<ORG>/proofsignal-spec.git@vX.Y.Z
```

Run once without a persistent install:

```sh
uvx --from git+https://github.com/<ORG>/proofsignal-spec.git@vX.Y.Z proofsignal init --here --integration codex
```

If this repository has not been published yet, install from a local checkout:

```sh
uv tool install proofsignal --from /path/to/proofsignal-spec
```

For development:

```sh
python -m pip install -e ".[dev]"
```

## Common Commands

```sh
proofsignal init --here --integration codex
proofsignal check
proofsignal workflow info proofsignal-use-case --json
proofsignal workflow check specify --json
proofsignal workflow run proofsignal-use-case --goal "Validate that a QA user can sign in." --alias login
proofsignal workflow status
proofsignal author login "Validate that a QA user can sign in."
proofsignal list
proofsignal validate login --json
proofsignal run login --profile normal --json
proofsignal repair login --json
proofsignal integration install claude
proofsignal core version --json
```

## Guided Workflow Commands

After initialization, Codex and Claude Code integrations install the staged
`/proofsignal-*` workflow commands:

```text
/proofsignal-understand
/proofsignal-specify login Validate that a QA user can sign in.
/proofsignal-clarify login
/proofsignal-plan login
/proofsignal-tasks login
/proofsignal-implement login
/proofsignal-validate login
/proofsignal-run login
/proofsignal-repair login
```

The canonical command identity uses dot notation, such as
`proofsignal.plan`, while skill-based integrations render the invocable command
as `/proofsignal-plan`. Legacy `proofsignal-spec-*` skills may remain installed
for compatibility, but the preferred workflow commands are `/proofsignal-*`.

The workflow stores reusable repository understanding globally and use-case
snapshots under `.proofsignal/workflows/use-cases/<alias>/`. Structured state,
not Markdown body text, drives status and resume behavior.

Every staged `/proofsignal-*` command starts from the deterministic prerequisite
check instead of guessing local state:

```sh
proofsignal workflow check specify --json
proofsignal workflow check plan --alias login --json
proofsignal workflow check run --alias login --json
```

`/proofsignal-specify` requires `.proofsignal/workflows/understanding.md` and
`.proofsignal/product-context.yaml` before collecting use-case details. On a new
workspace, the check returns Golden Path onboarding metadata so the integration
can prepare safe repository understanding and resume first-run recommendation
without asking the user to manually restart. If the understanding is stale by
age or Git commit distance, the check recommends refreshing through
`/proofsignal-understand`; declined refresh decisions are recorded without
persisting credential values.

Browser validation use cases must resolve the target application environment
before executable planning. A staging URL, local start target, or equivalent
browser target is treated as a prerequisite, so downstream planning and
implementation should not emit empty `baseUrl`-style parameters after the target
has been supplied.

Validation supports a bounded runtime readiness check:

```sh
proofsignal validate login --runtime-readiness --json
```

Runtime readiness checks target resolution, syntactic target reachability,
required runtime prerequisites, runtime authoring readiness, and public contract
compatibility without running the full browser flow. If no override is
configured, ProofSignal attempts to use a verified managed runtime from the user
cache or acquire one through the official `https://proofsignal.io/api`
entitlement and runtime-download contract after email-token unlock.

`proofsignal list` is intentionally metadata-only. It separates historical
`lastRun` from current readiness snapshots and never performs Core, network,
credential, entitlement, target reachability, or browser checks in the normal
list view. Use `proofsignal validate <alias> --runtime-readiness --json` or
`proofsignal workflow check run --alias <alias> --json` for volatile readiness.

Credentialed use cases may store non-secret readiness hints such as credential
group names, required runtime variable names, or user-managed preparation
guidance. Hints are not executed automatically and must not contain credential
values or env-file contents.

Write and external-notification use cases declare side-effect lifecycle
expectations, including cleanup policy and manual/external cleanup instructions
when needed. Legacy side-effecting artifacts missing lifecycle or safety
capability metadata require structured owner confirmation before run. When Core
does not emit a structured side-effect envelope for a write run, Spec reports
write activity conservatively as unknown or inferred rather than treating the
absence as proof that no side effect occurred.

## Golden Path

The Golden Path applies to the first run only. It recommends the simplest stable
real-target validation first, keeps branch-relevant or setup-heavy candidates as
secondary choices, and strongly recommends accepting the first run before
choosing deeper validations. Accepting starts a guided flow through authoring,
validation, run, safe repair when needed, and final outcome. Direct strict pass
and repaired strict pass both count as first-run success; skip returns the user
to ordinary manual use-case selection. Integration install also prints next
steps and writes local onboarding guidance.

See [docs/golden-path.md](docs/golden-path.md) for Golden Path semantics,
[docs/golden-path-troubleshooting.md](docs/golden-path-troubleshooting.md) for
recovery guidance, and [docs/release-readiness.md](docs/release-readiness.md)
for demo and release criteria.

## Managed Runtime And Development Overrides

The happy path does not require a separate Core install:

```sh
proofsignal init --here --integration codex
proofsignal check
```

During onboarding, ProofSignal may ask for an email address, request token
delivery through the official backend, then ask for the email unlock token. The
backend owns token generation, email delivery, expiry, exchange limits,
throttling, receipt signing, and runtime download authorization. The current
public/free policy allows up to 3 token exchanges, at most 3 exchanges per hour,
with a 30-day default token TTL. The raw email and token are process-local only;
the token is exchanged for a signed entitlement receipt in the user cache and is
not written to `.proofsignal/`, generated guides, blockers, logs, or cache
metadata. Managed runtime packages are cached outside the target project, by
default under `~/.cache/proofsignal/core/<version>/<platform>/`.

The production API base URL defaults to:

```text
https://proofsignal.io/api
```

Use `--api-base-url` or `PROOFSIGNAL_API_BASE_URL` only for staging, local
backend development, and tests:

```sh
proofsignal init --here --integration codex --api-base-url http://localhost:3000/api
```

For local development with the private ProofSignal Core repository, pass the
repository directory directly. ProofSignal will run Core through
`npm --silent --prefix <repo> run proofsignal:dev -- ...`.

```sh
proofsignal init --here --integration codex \
  --core-cmd /path/to/proofsignal

proofsignal core version --json
proofsignal check
```

Do not run `proofsignal version --json` in this setup unless you have installed
a separate internal runtime executable intentionally named that way. Use
`proofsignal core version --json` to verify the configured runtime.

You can also use an explicit command string:

```sh
export PROOFSIGNAL_CORE_CMD="npm --silent --prefix /path/to/proofsignal run proofsignal:dev --"
proofsignal check
```

`PROOFSIGNAL_CORE_CMD` is read by `proofsignal`; it does not create a shell
command named `proofsignal-core`.

Core overrides are execution/discovery conveniences for development,
diagnostics, CI, and restricted-network environments. They do not count as
managed entitlement success. If an override-selected runtime enforces
entitlement for a protected operation, ProofSignal passes the cached receipt
reference when available or reports Core's public entitlement rejection as a
non-repairable runtime blocker.

## Workspace Rules

- The canonical workspace is `.proofsignal/`.
- Each use case record lives under `.proofsignal/use-cases/`.
- Generated run requests live under `.proofsignal/run-requests/`.
- Generated reusable skills live under `.proofsignal/skills/` and can be shared
  by multiple run requests.
- Guided workflow state lives under `.proofsignal/workflows/`.
- Each use case references exactly one run request.
- Linked external artifacts are marked `generated: false` and are not copied or
  overwritten by default.
- Credential values are never persisted.

## Core Boundary

ProofSignal Spec does not import private ProofSignal Core packages or inspect
undocumented report internals. Runtime-dependent workflows check the selected
runtime with `proofsignal-core version --json` through the adapter and require
the `proofsignal-public-cli-json/v1` operations:
`version`, `authoring-check`, `run`, and `report.inspect`.

Repair classifies validation and runtime feedback before proposing edits.
Deterministic contract or metadata repairs can be auto-applied with approval;
selector, flow, data, and coverage changes require explicit confirmation and
must not be used as random rewrites around unclear product state.

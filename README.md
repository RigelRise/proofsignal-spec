# ProofSignal Spec

ProofSignal Spec is a project-local CLI and coding-agent interface for writing,
validating, running, and repairing ProofSignal browser use cases.

The CLI creates a `.proofsignal/` workspace in a target repository, installs
Codex or Claude Code agent skills, stores use case records, resolves aliases to
explicit ProofSignal run requests and reusable skills, and delegates validation,
run execution, and report inspection to ProofSignal Core through the public
`proofsignal-public-cli-json/v1` CLI JSON contract.

## Installation

Install directly from the official Git repository, pinned to a release tag:

```sh
uv tool install proofsignal-spec --from git+https://github.com/<ORG>/proofsignal-spec.git@vX.Y.Z
```

Or install the latest commit from the default branch:

```sh
uv tool install proofsignal-spec --from git+https://github.com/<ORG>/proofsignal-spec.git
```

Then verify the tool:

```sh
proofsignal-spec --version
```

Upgrade by reinstalling from the desired tag:

```sh
uv tool install proofsignal-spec --force --from git+https://github.com/<ORG>/proofsignal-spec.git@vX.Y.Z
```

Run once without a persistent install:

```sh
uvx --from git+https://github.com/<ORG>/proofsignal-spec.git@vX.Y.Z proofsignal-spec init --here --integration codex
```

If this repository has not been published yet, install from a local checkout:

```sh
uv tool install proofsignal-spec --from /path/to/proofsignal-spec
```

For development:

```sh
python -m pip install -e ".[dev]"
```

## Common Commands

```sh
proofsignal-spec init --here --integration codex
proofsignal-spec check
proofsignal-spec workflow info proofsignal-use-case --json
proofsignal-spec workflow check specify --json
proofsignal-spec workflow run proofsignal-use-case --goal "Validate that a QA user can sign in." --alias login
proofsignal-spec workflow status
proofsignal-spec author login "Validate that a QA user can sign in."
proofsignal-spec list
proofsignal-spec validate login --json
proofsignal-spec run login --profile normal --json
proofsignal-spec repair login --json
proofsignal-spec integration install claude
proofsignal-spec core version --json
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
proofsignal-spec workflow check specify --json
proofsignal-spec workflow check plan --alias login --json
proofsignal-spec workflow check run --alias login --json
```

`/proofsignal-specify` requires `.proofsignal/workflows/understanding.md` and
`.proofsignal/product-context.yaml` before collecting use-case details. If the
understanding is stale by age or Git commit distance, the check recommends
refreshing through `/proofsignal-understand`; declined refresh decisions are
recorded without persisting credential values.

Browser validation use cases must resolve the target application environment
before executable planning. A staging URL, local start target, or equivalent
browser target is treated as a prerequisite, so downstream planning and
implementation should not emit empty `baseUrl`-style parameters after the target
has been supplied.

Validation supports a bounded runtime readiness check:

```sh
proofsignal-spec validate login --runtime-readiness --json
```

Runtime readiness checks target resolution, syntactic target reachability,
required runtime prerequisites, Core authoring readiness, and Core public
contract compatibility without running the full browser flow.

## ProofSignal Core Configuration

For a published Core executable on `PATH`, no extra configuration is needed:

```sh
proofsignal-spec check
```

For local development with the private ProofSignal Core repository, pass the
repository directory directly. ProofSignal Spec will run Core through
`npm --silent --prefix <repo> run proofsignal:dev -- ...`.

```sh
proofsignal-spec init --here --integration codex \
  --core-cmd /path/to/proofsignal

proofsignal-spec core version --json
proofsignal-spec check
```

Do not run `proofsignal version --json` in this setup unless you have installed
a separate Core executable named `proofsignal`. Use `proofsignal-spec core
version --json` to verify the configured Core.

You can also use an explicit command string:

```sh
export PROOFSIGNAL_CORE_CMD="npm --silent --prefix /path/to/proofsignal run proofsignal:dev --"
proofsignal-spec check
```

`PROOFSIGNAL_CORE_CMD` is read by `proofsignal-spec`; it does not create a shell
command named `proofsignal`.

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
undocumented report internals. Core-dependent workflows check `proofsignal
version --json` and require the `proofsignal-public-cli-json/v1` operations:
`version`, `authoring-check`, `run`, and `report.inspect`.

Repair classifies validation and runtime feedback before proposing edits.
Deterministic contract or metadata repairs can be auto-applied with approval;
selector, flow, data, and coverage changes require explicit confirmation and
must not be used as random rewrites around unclear product state.

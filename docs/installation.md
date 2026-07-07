# Installation

ProofSignal uses the public `proofsignal` CLI as the user-facing command.
`proofsignal-spec` remains a backward-compatible alias for existing projects and
generated guidance.

## Persistent Installation

Install a tagged release:

```sh
uv tool install proofsignal-spec --from git+https://github.com/RigelRise/proofsignal-spec.git@vX.Y.Z
```

Install the latest commit from the default branch:

```sh
uv tool install proofsignal-spec --from git+https://github.com/RigelRise/proofsignal-spec.git
```

Verify:

```sh
proofsignal --version
proofsignal --help
```

Upgrade:

```sh
uv tool install proofsignal-spec --force --from git+https://github.com/RigelRise/proofsignal-spec.git@vX.Y.Z
```

Uninstall:

```sh
uv tool uninstall proofsignal
```

## One-Time Usage

Run without installing permanently:

```sh
uvx --from git+https://github.com/RigelRise/proofsignal-spec.git@vX.Y.Z proofsignal init --here --integration codex
```

## Initialize A Real Project

```sh
cd /path/to/target-project
proofsignal init --here --integration codex
proofsignal check
proofsignal workflow info proofsignal-use-case --json
```

For Claude Code:

```sh
proofsignal init --here --integration claude
```

After initialization, supported agents expose staged workflow commands using the
native skill invocation style:

```text
/proofsignal-understand
/proofsignal-specify
/proofsignal-clarify
/proofsignal-plan
/proofsignal-tasks
/proofsignal-implement
/proofsignal-validate
/proofsignal-list
/proofsignal-run
/proofsignal-repair
```

Installed workflow commands use `proofsignal workflow check <stage> --json`
before stage-specific work. After upgrading ProofSignal, rerun integration
installation so regenerated agent skills receive the latest prerequisite
guidance:

```sh
proofsignal integration upgrade codex
proofsignal integration upgrade claude
```

Use the same deterministic check outside an agent conversation:

```sh
proofsignal workflow check specify --json
proofsignal workflow check plan --alias login --json
```

The deterministic runner is available without an active agent conversation:

```sh
proofsignal workflow run proofsignal-use-case \
  --goal "Validate that a QA user can sign in." \
  --alias login \
  --integration codex

proofsignal workflow status
proofsignal workflow resume <run-id>
```

Existing legacy `proofsignal-spec-*` skills may be left in place for projects
that already installed the earlier thin CLI flow. New installations prefer
`/proofsignal-*` workflow commands.

## Managed Runtime And Development Overrides

The normal onboarding path automatically ensures a compatible private runtime:

```sh
proofsignal init --here --integration codex
```

When no override or verified cache exists, ProofSignal asks for the email unlock
token from the official unlock flow, exchanges it for a signed entitlement
receipt through `https://proofsignal.io/api`, requests authorized runtime
metadata/download from the backend, verifies the package, and stores the runtime
in the user cache. The backend owns email delivery, token expiry, exchange
limits, refresh policy, throttling, receipt signing, and runtime download
authorization. The current public/free token policy allows up to 3 exchanges,
at most 3 exchanges per hour, with a 30-day default token TTL. The target
project's `.proofsignal/` workspace stays portable and does not store raw
emails, raw tokens, receipt payloads, signed URLs, credentials, screenshots,
browser storage, or private runtime contents.

For staging, local backend development, and tests, use an explicit API override:

```sh
proofsignal init --here --integration codex --api-base-url http://localhost:3000/api
```

or:

```sh
export PROOFSIGNAL_API_BASE_URL=http://localhost:3000/api
```

Do not put credentials, tokens, signed URLs, or query secrets in the API base
URL.

For local development, CI, or offline diagnostics, pass the private Core
repository directory during initialization:

```sh
proofsignal init --here --integration codex \
  --core-cmd /path/to/proofsignal
```

That value is stored in `.proofsignal/workspace.yaml` and reused by `check`,
`validate`, `run`, `repair`, and `core version`. Diagnostic setup remains
available:

```sh
proofsignal core setup --core-cmd /path/to/proofsignal --json
proofsignal core version --json
```

You can also configure the command through an environment variable:

```sh
export PROOFSIGNAL_CORE_CMD=/path/to/proofsignal
proofsignal core version --json
```

When the value points to a directory with `package.json`, ProofSignal runs:

```sh
npm --silent --prefix <repo> run proofsignal:dev -- <proofsignal-args>
```

Use an explicit command string if needed:

```sh
export PROOFSIGNAL_CORE_CMD="npm --silent --prefix /path/to/proofsignal run proofsignal:dev --"
```

Overrides are not entitlement success. They only select a Core executable for
development, CI, diagnostics, or offline environments. If the selected runtime
requires entitlement for `authoring-check`, `run`, or `report.inspect`,
ProofSignal provides the cached receipt reference when available or reports the
runtime's public entitlement rejection as a non-repairable blocker.

## Local Checkout Before Publishing

If the repository has not been published yet:

```sh
uv tool install proofsignal-spec --from /path/to/proofsignal-spec
```

For development inside this repository:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Core Runtime Resolution Order

The runtime command is resolved in this order:

1. Explicit `--core-cmd` flag.
2. Workspace-persisted command (`proofsignal core setup`).
3. `PROOFSIGNAL_CORE_CMD` environment variable.
4. `proofsignal-core` on `PATH`.
5. A local Core development checkout (maintainers only).
6. Managed download from the entitlement API, pinned by
   `PROOFSIGNAL_CORE_VERSION` or the workspace-persisted core version.

Overrides are development and CI conveniences; they do not count as managed
entitlement success. If an override-selected runtime enforces entitlement for a
protected operation, the CLI passes the cached receipt when available or
surfaces the runtime's public entitlement blocker.

The CLI requires the public contract operations `version`, `contracts`,
`authoring-check`, `run`, and `report.inspect`; `discover` is used when the
runtime advertises it.

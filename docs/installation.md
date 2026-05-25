# Installation

ProofSignal Spec follows the same Git-based tool installation model as Spec Kit.
Install the CLI from the official repository instead of relying on a package with
the same name on PyPI.

## Persistent Installation

Install a tagged release:

```sh
uv tool install proofsignal-spec --from git+https://github.com/<ORG>/proofsignal-spec.git@vX.Y.Z
```

Install the latest commit from the default branch:

```sh
uv tool install proofsignal-spec --from git+https://github.com/<ORG>/proofsignal-spec.git
```

Verify:

```sh
proofsignal-spec --version
proofsignal-spec --help
```

Upgrade:

```sh
uv tool install proofsignal-spec --force --from git+https://github.com/<ORG>/proofsignal-spec.git@vX.Y.Z
```

Uninstall:

```sh
uv tool uninstall proofsignal-spec
```

## One-Time Usage

Run without installing permanently:

```sh
uvx --from git+https://github.com/<ORG>/proofsignal-spec.git@vX.Y.Z proofsignal-spec init --here --integration codex
```

## Initialize A Real Project

```sh
cd /path/to/target-project
proofsignal-spec init --here --integration codex
proofsignal-spec check
proofsignal-spec workflow info proofsignal-use-case --json
```

For Claude Code:

```sh
proofsignal-spec init --here --integration claude
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

Installed workflow commands use `proofsignal-spec workflow check <stage> --json`
before stage-specific work. After upgrading ProofSignal Spec, rerun integration
installation so regenerated agent skills receive the latest prerequisite
guidance:

```sh
proofsignal-spec integration upgrade codex
proofsignal-spec integration upgrade claude
```

Use the same deterministic check outside an agent conversation:

```sh
proofsignal-spec workflow check specify --json
proofsignal-spec workflow check plan --alias login --json
```

The deterministic runner is available without an active agent conversation:

```sh
proofsignal-spec workflow run proofsignal-use-case \
  --goal "Validate that a QA user can sign in." \
  --alias login \
  --integration codex

proofsignal-spec workflow status
proofsignal-spec workflow resume <run-id>
```

Existing legacy `proofsignal-spec-*` skills may be left in place for projects
that already installed the earlier thin CLI flow. New installations prefer
`/proofsignal-*` workflow commands.

## Configure ProofSignal Core

If the `proofsignal` executable is already on `PATH`, ProofSignal Spec can use
it directly. In local development, you do not need a shell command named
`proofsignal`; pass the Core repository directory during initialization:

```sh
proofsignal-spec init --here --integration codex \
  --core-cmd /path/to/proofsignal
```

That value is stored in `.proofsignal/workspace.yaml` and reused by `check`,
`validate`, `run`, `repair`, and `core version`.

Do not run `proofsignal version --json` unless you have installed a separate
Core executable with that name. Use ProofSignal Spec's readiness command:

```sh
proofsignal-spec core version --json
```

You can also configure the command through an environment variable:

```sh
export PROOFSIGNAL_CORE_CMD=/path/to/proofsignal
proofsignal-spec core version --json
```

When the value points to a directory with `package.json`, ProofSignal Spec runs:

```sh
npm --silent --prefix <repo> run proofsignal:dev -- <proofsignal-args>
```

Use an explicit command string if needed:

```sh
export PROOFSIGNAL_CORE_CMD="npm --silent --prefix /path/to/proofsignal run proofsignal:dev --"
```

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

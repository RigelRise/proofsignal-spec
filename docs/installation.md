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
```

For Claude Code:

```sh
proofsignal-spec init --here --integration claude
```

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

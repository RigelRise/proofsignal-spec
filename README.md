# ProofSignal

**AI writes the validation. A deterministic runtime proves it.**

ProofSignal turns product flows — login, checkout, onboarding — into approved,
repeatable browser validations with evidence, starting from your repository.
Your coding agent (Claude Code or Codex) authors and repairs the validation;
the ProofSignal runtime executes it deterministically and leaves an auditable
evidence trail. There is no AI at execution time: pass/fail comes only from
validated, explicit instructions.

This repository is the open-source half of ProofSignal (Apache-2.0): the
`proofsignal` CLI, the project-local `.proofsignal/` workspace, and the agent
skills. The execution engine (ProofSignal Core) is a signed package the CLI
downloads and caches automatically on first run — a free email unlock, no
account and no separate install.

## Why ProofSignal

AI-assisted development ships changes faster than anyone can manually recheck
the flows they touch. The existing answers trade away either speed or trust:
hand-written browser suites become a maintenance backlog, and an AI agent
clicking around your app gives you speed without stable, reviewable proof.

ProofSignal splits the work by what each side is good at:

- **Agents author, humans approve.** Your coding agent drafts use cases,
  grounds selectors against the live DOM, and proposes repairs — through
  contract-driven, staged commands with explicit escalation stops.
- **Execution is deterministic.** Runs execute a fixed, validated action set
  with no inference, so a green result means the same thing every time.
- **Evidence over green checkmarks.** Every run produces a structured report,
  screenshots, and a network log — proof you can review, share, and audit.
- **Side-effect safety.** Write flows require declared side-effect policies,
  are observed at runtime, and gate reruns on previous outcomes, so a
  validation never silently mutates data it should not.

ProofSignal does not replace your test suite or CI. It turns manual product
validation into repeatable proof.

## Quickstart

You will need:

- [uv](https://docs.astral.sh/uv/) (or pipx) and Python 3.11+
- Node.js 24+ (runs the downloaded runtime)
- Playwright Chromium for browser execution
  (`npx playwright install chromium` if you do not already have it)
- A valid email address for the free runtime unlock — no account required

Install the CLI:

```sh
uv tool install proofsignal-spec --from git+https://github.com/RigelRise/proofsignal-spec.git
proofsignal --version
```

(With pipx: `pipx install 'proofsignal-spec @ git+https://github.com/RigelRise/proofsignal-spec.git'`.)

Initialize a workspace in your project. `init` asks for your email, sends a
free unlock code, then downloads the runtime once and caches it under
`~/.cache/proofsignal/` — outside your project:

```sh
cd your-project
proofsignal init --here --integration claude   # or: --integration codex
proofsignal check
```

`init` also installs ProofSignal skills into your coding agent. In the agent,
run the whole flow with one command:

```text
/proofsignal "Validate that a user can sign in against https://staging.example.com"
```

The agent drafts the use case from your source, grounds its selectors against
the live app, validates, runs, and repairs — stopping only for real unknowns,
missing credentials, or write side-effects. If the flow needs credentials,
export them as environment variables before the run (for example `QA_USER` /
`QA_PASSWORD`); ProofSignal reads them at run time and never writes them to
disk. You can also drive the stages yourself:

```text
/proofsignal-understand
/proofsignal-specify login "Validate that a QA user can sign in."
/proofsignal-plan login
/proofsignal-implement login
/proofsignal-validate login
/proofsignal-run login
/proofsignal-repair login
```

On a fresh workspace, ProofSignal first walks a *Golden Path*: it suggests the
simplest stable flow in your repository and gets it to a green run before you
add deeper coverage ([details](docs/golden-path.md)). When a run goes green,
evidence lands in `.proofsignal/runs/<alias>/<run-id>/`:

```text
.proofsignal/runs/login/request_login_1780303629096/
├── report.md            # human-readable result, step by step
├── report.json          # machine-readable result (qa-report/v1)
├── browser/screenshots/ # captured evidence per step
└── browser/network.ndjson
```

`report.md` explains what passed, what failed and why, which gates were
covered, and links each claim to its evidence — a result you can review and
share, not just a green checkmark.

## How it works

```
your repository
└── .proofsignal/            project-local workspace (use cases, skills, state)
      │
      ▼
proofsignal CLI (this repo, Apache-2.0)
  authoring · validation gates · workflow state · side-effect policy · repair
      │  versioned public JSON contract
      ▼
ProofSignal Core runtime (signed managed download)
  deterministic browser execution · evidence capture · redaction
      │
      ▼
.proofsignal/runs/<alias>/<run-id>/   report.md · report.json · screenshots · network log
```

- **This repo** owns authoring, guided workflows, use-case records, readiness
  checks, side-effect and credential guardrails, and repair orchestration. It
  talks to the runtime only through the versioned
  `proofsignal-public-cli-json/v1` contract — never private internals.
- **The Core runtime** owns execution: it validates artifacts, drives the
  browser through a fixed action set, enforces declared side-effect policies
  at runtime, and writes redacted evidence.
- Every subcommand supports `--json`. Exit codes are stable: `0` success,
  `2` validation failed, `3` core failed, `4` approval required,
  `5` input missing.

## Safety guarantees

- **Secret safety.** Credential values are resolved from your environment at
  run time and are never persisted — not in `.proofsignal/`, reports, logs,
  guides, or cache metadata. Tokens, receipts, and signed URLs are redacted
  from all output.
- **Write-flow guardrails.** Write and external-notification use cases declare
  `sideEffectPolicy.allowed[]`/`forbidden[]`, a resource identity, and cleanup
  expectations. Violations block or fail the run; reruns after a committed
  write require explicit approval.
- **The runtime wins.** When the deterministic runtime and the agent disagree,
  grounded selectors and run results override anything the agent believes it
  saw in the browser. Agents are instructed to stop and ask rather than invent
  selectors or skip failed coverage.

## CLI overview

| Command | Purpose |
| --- | --- |
| `proofsignal init --here --integration claude\|codex` | Create `.proofsignal/` and install agent skills |
| `proofsignal check` | Workspace, runtime, and entitlement readiness |
| `proofsignal author <alias> "<description>"` | Register a use case |
| `proofsignal list` | List use cases (metadata only, no network) |
| `proofsignal validate <alias> [--runtime-readiness]` | Authoring gates; optional runtime readiness |
| `proofsignal run <alias> [--profile <name>]` | Execute and capture evidence (default profiles: `normal`, `debug`, `browser`) |
| `proofsignal repair <alias> [--from-report ...]` | Classify findings and propose repairs |
| `proofsignal discover --url <url> --skill <path>` | Ground drafted selectors against the live DOM |
| `proofsignal workflow ...` | Staged workflow engine (check/run/persist/status/...) |
| `proofsignal core version\|setup` | Inspect or configure the Core runtime |
| `proofsignal integration ...` | Manage installed agent integrations |

## The managed runtime

The happy path needs no separate Core install: the CLI downloads a signed
runtime package after the email unlock and caches it per version and platform
under `~/.cache/proofsignal/core/`. Unlock tokens are single-use and
rate-limited; the raw email and token stay process-local and are never written
into your project.

The runtime can be overridden for development and CI (`--core-cmd`,
`proofsignal core setup`, `PROOFSIGNAL_CORE_CMD`) — see the
[installation reference](docs/installation.md) for the full resolution order.
Custom runtimes still go through the same entitlement check; the CLI reuses
your cached receipt automatically.

Everything ProofSignal manages lives under `.proofsignal/`: use cases,
generated run requests, reusable skills, guided workflow state, and run
evidence. Linked external artifacts are marked `generated: false` and never
overwritten, and agents write staged workflow artifacts only through
`proofsignal workflow persist` — never by hand-editing managed files.

## Documentation

- [Golden Path](docs/golden-path.md) — first-run semantics and guarantees
- [Golden Path troubleshooting](docs/golden-path-troubleshooting.md)
- [Installation reference](docs/installation.md) — installs, upgrades, runtime overrides
- [Managed runtime and entitlement architecture](docs/managed-runtime-entitlement-handoff.md)
- [Release readiness criteria](docs/release-readiness.md)

## Getting help

- Bugs and feature requests: [GitHub Issues](https://github.com/RigelRise/proofsignal-spec/issues)
- First-run problems: start with [Golden Path troubleshooting](docs/golden-path-troubleshooting.md)
- Security reports: please use
  [GitHub private vulnerability reporting](https://github.com/RigelRise/proofsignal-spec/security/advisories/new)
  instead of a public issue

## Development

```sh
python -m pip install -e ".[dev]"
python -m pytest
```

The test suite includes a full fake Core implementing the public contract, so
this repo develops and tests against the contract without the private runtime.
An optional integration test exercises a real Core package when one is present.

## License

[Apache License 2.0](LICENSE)

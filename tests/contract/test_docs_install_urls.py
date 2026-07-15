from __future__ import annotations

import re
from pathlib import Path

# RATCHET (onboarding honesty). The ProofSignal -> VerifySignal rebrand rewrote every advertised
# install URL to github.com/RigelRise/verifysignal-spec while the actual GitHub repository was still
# named proofsignal-spec — so the documented Quickstart install 404'd for every new user, and no test
# noticed because docs are not type-checked or executed.
#
# This guard pins the canonical repository path across every doc that advertises it, so a future
# rename/rebrand cannot silently split the docs from the real remote again. It does NOT (and cannot)
# prove the remote exists: creating/renaming the GitHub repo and cutting a release tag is an ops
# action. What it does prove is that the docs all point at ONE agreed URL.

CANONICAL_REPO = "github.com/RigelRise/verifysignal-spec"
STALE_REPO_PATTERN = re.compile(r"github\.com/[\w.-]+/proofsignal[\w.-]*")
GITHUB_URL_PATTERN = re.compile(r"github\.com/[\w.-]+/[\w.-]+")

ROOT = Path(__file__).resolve().parents[2]
DOC_PATHS = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]


def _docs_with_text() -> list[tuple[Path, str]]:
    return [(path, path.read_text(encoding="utf-8")) for path in DOC_PATHS if path.exists()]


def test_docs_have_no_stale_proofsignal_repo_urls() -> None:
    offenders = [
        f"{path.relative_to(ROOT)}: {match.group(0)}"
        for path, text in _docs_with_text()
        for match in STALE_REPO_PATTERN.finditer(text)
    ]
    assert offenders == [], f"docs still advertise the pre-rebrand repository: {offenders}"


def test_every_advertised_github_repo_url_is_the_canonical_one() -> None:
    # Any GitHub repo URL in the docs must be the canonical VerifySignal Spec repo. This is what makes
    # a half-finished rename (docs moved, remote didn't — or vice versa) fail loudly instead of 404ing
    # only for users.
    offenders = [
        f"{path.relative_to(ROOT)}: {match.group(0)}"
        for path, text in _docs_with_text()
        for match in GITHUB_URL_PATTERN.finditer(text)
        if not match.group(0).startswith(CANONICAL_REPO)
    ]
    assert offenders == [], f"docs advertise a non-canonical GitHub repo: {offenders}"


def test_install_docs_still_advertise_an_installable_command() -> None:
    # Guards the other direction: the URL fix must not quietly delete the documented install path.
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"git+https://{CANONICAL_REPO}.git" in readme
    assert "uv tool install verifysignal-spec" in readme

from __future__ import annotations

import re
from pathlib import Path

import pytest

from verifysignal_spec.workflows.repair_recommendations import (
    MUTABLE_SAFE_CATEGORIES,
    classify_repair_findings,
)

# RATCHET (the prose must not out-promise the mechanism).
#
# `autonomy` is derived from MUTABLE_SAFE_CATEGORIES — the same set the real on-disk mutator
# dispatches off — so the FIELD cannot lie. The PROSE could: `_safe_action` was a parallel hardcoded
# dict, and its selector-ambiguity / wait-strategy entries opened with "Auto-apply" while those are
# exactly the two categories whose autonomy is `propose-only`. Inverted, and set on adjacent lines at
# the call site. Meanwhile main-skill-ordering — the ONLY category with a mutator — promised nothing.
#
# It survived a green suite because every existing test asserts `autonomy` and NONE reads `action`
# (test_repair_autonomy.py, test_repair_autonomy_contract.py). A field nobody asserts drifts free.
#
# This bites twice, because the same claim ships INTO the user's repo: the agent-command templates are
# rendered into `.claude/skills/**/SKILL.md` on every `verifysignal init` and are read by the user's
# agent as instruction. A template telling an agent to auto-apply a category with no mutator sends it
# looping over a fix that can never land.

AUTO_APPLY_WORDING = re.compile(r"auto[-\s]?appl(?:y|ies|ied)", re.IGNORECASE)

# Every safe category the classifier can emit, with a finding that provokes it.
FINDINGS_BY_CATEGORY: dict[str, dict[str, str]] = {
    "wait-strategy": {"code": "wait-timeout", "message": "Step timed out waiting for a rendered slider."},
    "selector-ambiguity": {"code": "strict-mode-violation", "message": "Locator matched multiple elements."},
    "main-skill-ordering": {"code": "main-skill-ordering", "message": "Helper skill executed before main skill."},
    "run-profile-defaults": {"code": "debug-slowmo-default", "message": "Debug run has slowMoMs 0."},
    "gateid-mapping": {"code": "missing-gateid", "message": "assertion lacks gateId"},
}


def _recommendations_by_safe_category() -> dict[str, object]:
    items = classify_repair_findings(list(FINDINGS_BY_CATEGORY.values()))
    return {item.safeCategory: item for item in items if item.safeCategory}


def test_the_finding_corpus_still_provokes_every_safe_category() -> None:
    # Anti-vacuous guard. Every assertion below iterates recommendations; if the corpus stopped
    # producing them the whole ratchet would pass by iterating nothing. Fix the corpus, not this.
    produced = set(_recommendations_by_safe_category())
    assert produced == set(FINDINGS_BY_CATEGORY), (
        f"the corpus produced {sorted(produced)}, expected {sorted(FINDINGS_BY_CATEGORY)} — "
        f"a category that stops being provoked is a category this ratchet stops guarding."
    )


@pytest.mark.parametrize("safe_category", sorted(FINDINGS_BY_CATEGORY))
def test_action_prose_promises_automation_only_where_a_mutator_exists(safe_category: str) -> None:
    item = _recommendations_by_safe_category()[safe_category]
    promises_automation = bool(AUTO_APPLY_WORDING.search(item.action))
    has_mutator = safe_category in MUTABLE_SAFE_CATEGORIES

    assert promises_automation == has_mutator, (
        f"{safe_category}: autonomy={item.autonomy!r} but action reads {item.action!r}. "
        f"The prose and the mechanism must agree — derive the prose from autonomy, do not "
        f"hand-write it beside the field."
    )


@pytest.mark.parametrize("safe_category", sorted(FINDINGS_BY_CATEGORY))
def test_action_prose_agrees_with_the_autonomy_field_it_ships_beside(safe_category: str) -> None:
    # The tighter statement: `action` must track `autonomy`, whatever autonomy happens to be. This
    # holds gateid-mapping (`confirmation-required`, set at the call site rather than derived) to the
    # same rule, so the guard does not quietly exempt the categories set by hand.
    item = _recommendations_by_safe_category()[safe_category]
    promises_automation = bool(AUTO_APPLY_WORDING.search(item.action))

    assert promises_automation == (item.autonomy == "auto-applied"), (
        f"{safe_category}: action={item.action!r} contradicts autonomy={item.autonomy!r}."
    )


# --- The template corpus: prose that ships into the user's repo and is read as instruction. --------

TEMPLATE_ROOT = Path(__file__).resolve().parents[2] / "src" / "verifysignal_spec" / "templates"

# How the shipped prose NAMES each category. Keyed by category so the ban is derived from
# MUTABLE_SAFE_CATEGORIES: give a category a real mutator and its prose becomes legal automatically.
CATEGORY_PROSE_ALIASES: dict[str, tuple[str, ...]] = {
    "selector-ambiguity": ("selector",),
    "wait-strategy": ("wait strategy", "wait/ordering", "wait,"),
    "run-profile-defaults": ("run-profile", "run profile"),
    "gateid-mapping": ("gateid mapping", "coverage mapping"),
    # Named in the shipped prose but not a category the classifier can even emit. There is no
    # mechanism at all behind these words, which is strictly worse than an overstated one.
    "target-specificity": ("target specificity",),
    "equivalent-flow": ("equivalent-flow", "equivalent flow"),
}


def _template_files() -> list[Path]:
    return sorted(p for p in TEMPLATE_ROOT.rglob("*.md") if p.is_file())


def _sentences(text: str) -> list[str]:
    return [part for chunk in text.splitlines() for part in re.split(r"(?<=[.;])\s+", chunk) if part.strip()]


def test_the_template_corpus_is_actually_readable() -> None:
    # Anti-vacuous guard: a glob that matches nothing would pass every template assertion below.
    files = _template_files()
    assert len(files) >= 3, f"found {len(files)} templates under {TEMPLATE_ROOT} — the corpus parser is broken."
    assert any("repair" in p.name for p in files), "the repair template is the whole point of this guard."


@pytest.mark.parametrize("category,aliases", sorted(CATEGORY_PROSE_ALIASES.items()))
def test_no_shipped_template_tells_an_agent_to_auto_apply_a_category_with_no_mutator(
    category: str, aliases: tuple[str, ...]
) -> None:
    if category in MUTABLE_SAFE_CATEGORIES:
        pytest.skip(f"{category} has a real mutator, so auto-apply prose is honest for it")

    offenders: list[str] = []
    for path in _template_files():
        for sentence in _sentences(path.read_text(encoding="utf-8")):
            if not AUTO_APPLY_WORDING.search(sentence):
                continue
            lowered = sentence.lower()
            if any(alias in lowered for alias in aliases):
                offenders.append(f"{path.relative_to(TEMPLATE_ROOT)}: {sentence.strip()[:140]}")

    assert offenders == [], (
        f"these shipped templates instruct the user's agent to auto-apply {category!r}, which has no "
        f"mutator — `verifysignal repair --approve` reports it `proposed` and changes nothing, so the "
        f"agent loops on a fix that can never land:\n  " + "\n  ".join(offenders)
    )

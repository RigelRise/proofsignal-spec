from __future__ import annotations

from verifysignal_spec.workflows.models import ArtifactPlan


def test_artifact_plan_keeps_skills_as_references() -> None:
    plan = ArtifactPlan(
        useCaseAlias="checkout",
        runRequest=".verifysignal/run-requests/checkout.yaml",
        mainSkill=".verifysignal/skills/checkout.browser.md",
        supportingSkills=[".verifysignal/skills/login.browser.md"],
    )
    data = plan.to_dict()
    assert data["supportingSkills"] == [".verifysignal/skills/login.browser.md"]
    assert "skills" not in data or isinstance(data.get("supportingSkills"), list)


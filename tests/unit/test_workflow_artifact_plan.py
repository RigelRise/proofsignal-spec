from __future__ import annotations

from proofsignal_spec.workflows.models import ArtifactPlan


def test_artifact_plan_keeps_skills_as_references() -> None:
    plan = ArtifactPlan(
        useCaseAlias="checkout",
        runRequest=".proofsignal/run-requests/checkout.yaml",
        mainSkill=".proofsignal/skills/checkout.browser.md",
        supportingSkills=[".proofsignal/skills/login.browser.md"],
    )
    data = plan.to_dict()
    assert data["supportingSkills"] == [".proofsignal/skills/login.browser.md"]
    assert "skills" not in data or isinstance(data.get("supportingSkills"), list)


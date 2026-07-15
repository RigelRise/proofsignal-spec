from __future__ import annotations

import json

from helpers import CliTestCase

from tests.fixtures.workflows.main_skill_run_coverage import create_main_skill_coverage_workspace
from verifysignal_spec.workspace.repository import load_use_case, save_use_case

_RUN_REQUEST_PATH = ".verifysignal/run-requests/profile-view-unauth.yaml"
_EXECUTION_BOUNDARY_FINDING = {
    "code": "skill-execution.legacy-migration-required",
    "message": "Helper skill executed as an unintended executable participant while required gates were missing.",
    "artifact": _RUN_REQUEST_PATH,
    "path": "skills",
}


class RepairMutationTests(CliTestCase):
    def _inject_ordering_finding(self) -> None:
        record = load_use_case(self.project, "profile-view-unauth")
        record.validation = {"findings": [dict(_EXECUTION_BOUNDARY_FINDING)]}
        save_use_case(self.project, record)

    def _skill_bodies(self) -> dict[str, str]:
        skills_dir = self.project / ".verifysignal" / "skills"
        return {path.name: path.read_text(encoding="utf-8") for path in sorted(skills_dir.glob("*.md"))}

    def _run_request(self) -> dict:
        return json.loads((self.project / _RUN_REQUEST_PATH).read_text(encoding="utf-8"))

    def test_applied_reorders_only_the_skills_array_and_preserves_authored_content(self) -> None:
        # The invariant: repair returns `applied` ONLY after a real artifact mutation proven by
        # before/after SHA-256, and that mutation must NEVER destroy authored content while
        # claiming applied. `main-skill-ordering` surgically reorders only the run-request's
        # `skills` array; authored `parameters` VALUES (baseUrl), `mainSkill`, `target`,
        # `validationScope`, `schemaVersion` and the skill `.browser.md` bodies must all survive
        # byte-for-byte. (Regression guard: re-rendering the run-request from the record wiped the
        # parameter values, and re-rendering skills gutted their assertions.)
        create_main_skill_coverage_workspace(self.project)
        record = load_use_case(self.project, "profile-view-unauth")
        main_id = record.mainSkill.id

        # Simulate ordering drift: the helper leads the executable list, main is second. Authored
        # parameters carry a real target URL the record does not hold.
        drifted = {
            "schemaVersion": "qa-run-request/v1",
            "request": {"id": "request.profile-view-unauth", "name": "Profile View Unauth"},
            "target": "browser",
            "validationScope": "feature-level",
            "mainSkill": main_id,
            "skills": [
                {"id": "skill.helper-open", "version": "1.0.0"},
                {"id": main_id, "version": "2.1.0"},
            ],
            "parameters": {"baseUrl": "https://app.example.test"},
        }
        (self.project / _RUN_REQUEST_PATH).write_text(json.dumps(drifted), encoding="utf-8")
        skills_before = self._skill_bodies()
        self._inject_ordering_finding()

        # The mutation now requires explicit --approve (see the no-approve test below). The reorder
        # is genuinely applied and preserves authored content, but this fixture's use case still
        # blocks on revalidation (coverage/runtime readiness), so the honest outcome is
        # `revalidation-failed` + exit 2 — NOT a false `applied`/exit-0 that hides the still-failing
        # artifact (that was the P0 this fix closes).
        code, out, err = self.cli(["repair", "profile-view-unauth", "--project", str(self.project), "--approve", "--json"])

        self.assertEqual(code, 2, err)
        repair = json.loads(out)["repair"]
        self.assertEqual(repair["approvalStatus"], "revalidation-failed")
        application = next(item for item in repair["applications"] if item["applied"])
        self.assertEqual(application["changedArtifacts"], [_RUN_REQUEST_PATH])
        self.assertNotEqual(
            application["beforeSha256"][_RUN_REQUEST_PATH],
            application["afterSha256"][_RUN_REQUEST_PATH],
        )

        after = self._run_request()
        # The executable order was actually fixed (main now leads).
        self.assertEqual([ref["id"] for ref in after["skills"]], [main_id, "skill.helper-open"])
        # Every authored field survived — nothing was regenerated from the record.
        self.assertEqual(after["parameters"], {"baseUrl": "https://app.example.test"})
        self.assertEqual(after["mainSkill"], main_id)
        self.assertEqual(after["schemaVersion"], "qa-run-request/v1")
        self.assertEqual(after["target"], "browser")
        self.assertEqual(after["validationScope"], "feature-level")
        # Skill bodies were never touched.
        self.assertEqual(self._skill_bodies(), skills_before)

    def _write_drifted_run_request(self, main_id: str) -> None:
        drifted = {
            "schemaVersion": "qa-run-request/v1",
            "request": {"id": "request.profile-view-unauth", "name": "Profile View Unauth"},
            "target": "browser",
            "validationScope": "feature-level",
            "mainSkill": main_id,
            "skills": [
                {"id": "skill.helper-open", "version": "1.0.0"},
                {"id": main_id, "version": "2.1.0"},
            ],
            "parameters": {"baseUrl": "https://app.example.test"},
        }
        (self.project / _RUN_REQUEST_PATH).write_text(json.dumps(drifted), encoding="utf-8")

    def test_repair_does_not_mutate_the_artifact_without_approve(self) -> None:
        # An auto-applicable safe repair must NOT rewrite the artifact unless --approve is passed.
        # Without it, repair reports `proposed` (exit 4) and leaves every artifact byte-for-byte
        # unchanged — the fix must be explicitly approved before any on-disk write.
        create_main_skill_coverage_workspace(self.project)
        record = load_use_case(self.project, "profile-view-unauth")
        self._write_drifted_run_request(record.mainSkill.id)
        run_request_before = (self.project / _RUN_REQUEST_PATH).read_text(encoding="utf-8")
        skills_before = self._skill_bodies()
        self._inject_ordering_finding()

        code, out, err = self.cli(["repair", "profile-view-unauth", "--project", str(self.project), "--json"])

        self.assertEqual(code, 4, err)
        repair = json.loads(out)["repair"]
        self.assertEqual(repair["approvalStatus"], "proposed")
        self.assertTrue(all(not item["applied"] for item in repair["applications"]))
        # Nothing on disk changed — the reorder was proposed, not written.
        self.assertEqual((self.project / _RUN_REQUEST_PATH).read_text(encoding="utf-8"), run_request_before)
        self.assertEqual(self._skill_bodies(), skills_before)

    def test_applied_but_failed_revalidation_exits_nonzero_with_gaps(self) -> None:
        # When an approved mutation IS applied but revalidation afterward FAILS, repair must NOT
        # report success: exit is non-zero, approvalStatus is not "applied", and the mutated gap is
        # still listed as remaining. (Regression: applied=True + remainingGaps=[] + exit 0 hid a
        # still-failing artifact behind a green repair.)
        import os

        create_main_skill_coverage_workspace(self.project)
        record = load_use_case(self.project, "profile-view-unauth")
        self._write_drifted_run_request(record.mainSkill.id)
        self._inject_ordering_finding()

        os.environ["FAKE_VERIFYSIGNAL_MODE"] = "blocked"
        code, out, err = self.cli(["repair", "profile-view-unauth", "--project", str(self.project), "--approve", "--json"])

        self.assertNotEqual(code, 0, err)
        repair = json.loads(out)["repair"]
        # A mutation was genuinely applied (the reorder happened)...
        applied = [item for item in repair["applications"] if item["applied"]]
        self.assertTrue(applied)
        # ...but revalidation failed, so it is NOT reported as a clean success.
        self.assertNotEqual(repair["approvalStatus"], "applied")
        self.assertEqual(repair["revalidation"]["status"], "failed")
        # The mutated recommendation is still an open gap despite the write.
        self.assertTrue(any(item["remainingGaps"] for item in repair["applications"]))

    def test_applied_but_unavailable_revalidation_exits_nonzero_with_gaps(self) -> None:
        # Same fail-open CLASS as the failed-revalidation case above, via the OTHER path: when
        # revalidation CRASHES, _revalidate_after_mutation swallows the exception and returns
        # status "not-run". A predicate that only checks == "failed" therefore treats a crash as
        # success → approvalStatus "applied", remainingGaps [], exit 0. A mutation whose revalidation
        # could not run has NOT been proven to close the gap and must never report clean success.
        from unittest.mock import patch

        create_main_skill_coverage_workspace(self.project)
        record = load_use_case(self.project, "profile-view-unauth")
        self._write_drifted_run_request(record.mainSkill.id)
        self._inject_ordering_finding()

        with patch("verifysignal_spec.commands.validate.run", side_effect=RuntimeError("revalidation boom")):
            code, out, err = self.cli(["repair", "profile-view-unauth", "--project", str(self.project), "--approve", "--json"])

        self.assertNotEqual(code, 0, err)
        repair = json.loads(out)["repair"]
        # The mutation was genuinely applied...
        self.assertTrue([item for item in repair["applications"] if item["applied"]])
        # ...but revalidation could not run, so it is NOT a clean success.
        self.assertNotEqual(repair["approvalStatus"], "applied")
        self.assertEqual(repair["revalidation"]["status"], "not-run")
        # The mutated recommendation stays an open gap despite the write.
        self.assertTrue(any(item["remainingGaps"] for item in repair["applications"]))

    def test_yaml_native_run_request_degrades_to_proposed_without_crashing(self) -> None:
        # A run-request that is valid YAML but not JSON (here an unquoted date scalar) must not
        # crash the repair command — the mutator leaves it untouched and reports `proposed`
        # (exit 4), never exit 1. (Regression guard: re-serializing a YAML-native `date` raised
        # TypeError and crashed `repair` with no session.)
        create_main_skill_coverage_workspace(self.project)
        (self.project / _RUN_REQUEST_PATH).write_text(
            "schemaVersion: qa-run-request/v1\n"
            "releaseDate: 2026-07-14\n"
            "mainSkill: skill.validate-profile-view-unauth-flow\n"
            "skills:\n"
            "  - id: skill.helper-open\n"
            "  - id: skill.validate-profile-view-unauth-flow\n"
            "parameters:\n"
            "  baseUrl: https://app.example.test\n",
            encoding="utf-8",
        )
        run_request_before = (self.project / _RUN_REQUEST_PATH).read_text(encoding="utf-8")
        self._inject_ordering_finding()

        code, out, err = self.cli(["repair", "profile-view-unauth", "--project", str(self.project), "--json"])

        self.assertEqual(code, 4, err)
        self.assertEqual(json.loads(out)["repair"]["approvalStatus"], "proposed")
        self.assertEqual((self.project / _RUN_REQUEST_PATH).read_text(encoding="utf-8"), run_request_before)

    def test_null_main_skill_id_does_not_spuriously_reorder(self) -> None:
        # If the main skill has no id, it must not match an id-less run-request ref (ref.get("id")
        # == None), which would produce a spurious reorder + false `applied`.
        from types import SimpleNamespace

        from verifysignal_spec.commands.repair import _apply_safe_artifact_repair

        create_main_skill_coverage_workspace(self.project)
        (self.project / _RUN_REQUEST_PATH).write_text(
            json.dumps(
                {
                    "schemaVersion": "qa-run-request/v1",
                    "skills": [{"id": "skill.x", "version": "1.0.0"}, {"version": "1.0.0"}],
                }
            ),
            encoding="utf-8",
        )
        record = SimpleNamespace(
            mainSkill=SimpleNamespace(id=None),
            runRequest=SimpleNamespace(generated=True, path=_RUN_REQUEST_PATH),
        )
        recommendation = SimpleNamespace(safeCategory="main-skill-ordering")

        self.assertIsNone(_apply_safe_artifact_repair(self.project, record, recommendation))

    def test_already_ordered_run_request_is_proposed_not_applied(self) -> None:
        # When the run-request already has the main skill first (nothing to reorder), repair must
        # fall back to `proposed` (applied=false) — never a false `applied` produced by a spurious
        # re-render/reformat — and the CLI must exit 4. No artifact may change.
        create_main_skill_coverage_workspace(self.project)
        run_request_before = (self.project / _RUN_REQUEST_PATH).read_text(encoding="utf-8")
        skills_before = self._skill_bodies()
        self._inject_ordering_finding()

        code, out, err = self.cli(["repair", "profile-view-unauth", "--project", str(self.project), "--json"])

        self.assertEqual(code, 4, err)
        repair = json.loads(out)["repair"]
        self.assertEqual(repair["approvalStatus"], "proposed")
        self.assertTrue(all(not item["applied"] for item in repair["applications"]))
        # Nothing on disk changed.
        self.assertEqual((self.project / _RUN_REQUEST_PATH).read_text(encoding="utf-8"), run_request_before)
        self.assertEqual(self._skill_bodies(), skills_before)

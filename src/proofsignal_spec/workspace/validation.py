from __future__ import annotations

import math
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from . import layout
from .models import ArtifactReference, UseCaseRecord
from .repository import load_document, load_registry, load_use_case

SECRET_FIELD_RE = re.compile(r"(password|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|client[_-]?secret|authorization)", re.I)
BEARER_RE = re.compile(r"\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]{12,}", re.I)
HIGH_ENTROPY_RE = re.compile(r"^[A-Za-z0-9_./+=-]{32,}$")
DUMMY_VALUES = {"example", "dummy", "placeholder", "changeme", "test", "sample", "qa@example.com"}


def looks_secret(value: Any, field_name: str = "") -> bool:
    if value is None:
        return False
    text = str(value).strip()
    if not text:
        return False
    if text.lower() in DUMMY_VALUES or text.startswith("${") or text.startswith("<"):
        return False
    normalized_field = field_name.lower()
    if field_name in {
        "schemaVersion",
        "version",
        "id",
        "path",
        "recordPath",
        "reportPath",
        "evidenceDir",
        "planFingerprint",
        "sha256",
        "generatedGitHash",
    }:
        return False
    if any(term in normalized_field for term in ["githash", "gitsha", "commithash", "commitsha", "revision", "sha256"]):
        return False
    if SECRET_FIELD_RE.search(field_name) and text.lower() not in DUMMY_VALUES:
        return True
    if BEARER_RE.search(text):
        return True
    if HIGH_ENTROPY_RE.match(text) and not re.search(r"[-/\s]", text) and _entropy(text) > 3.5:
        return True
    return False


def _entropy(text: str) -> float:
    if not text:
        return 0.0
    counts = {ch: text.count(ch) for ch in set(text)}
    return -sum((count / len(text)) * math.log2(count / len(text)) for count in counts.values())


def validate_no_secret_values(data: Any, path: str = "") -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if isinstance(data, dict):
        for key, value in data.items():
            child_path = f"{path}.{key}" if path else str(key)
            if isinstance(value, (dict, list)):
                findings.extend(validate_no_secret_values(value, child_path))
            elif looks_secret(value, str(key)):
                findings.append({"severity": "blocking", "code": "secret-looking-value", "path": child_path, "message": "Secret-looking value must not be persisted."})
    elif isinstance(data, list):
        for index, value in enumerate(data):
            findings.extend(validate_no_secret_values(value, f"{path}[{index}]"))
    return findings


def validate_workspace(project: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    root = layout.workspace_root(project)
    if not root.exists():
        return [{"severity": "blocking", "code": "workspace-missing", "path": str(root), "message": "Workspace does not exist."}]

    registry = load_registry(project)
    aliases: set[str] = set()
    for item in registry.get("useCases", []):
        alias = item.get("alias", "")
        if alias in aliases:
            findings.append({"severity": "blocking", "code": "duplicate-alias", "path": layout.REGISTRY_FILE, "message": f"Duplicate alias: {alias}"})
        aliases.add(alias)
        record_path = item.get("recordPath", "")
        if not record_path:
            findings.append({"severity": "blocking", "code": "missing-record-path", "path": layout.REGISTRY_FILE, "message": f"Registry entry for {alias or '<unknown>'} is missing recordPath."})
            continue
        try:
            path = layout.project_relative_path(project, record_path)
        except Exception:
            findings.append({"severity": "blocking", "code": "invalid-record-path", "path": record_path, "message": "Record path escapes the project."})
            continue
        if not path.exists():
            findings.append({"severity": "blocking", "code": "missing-record", "path": record_path, "message": "Registry entry points to a missing use case record."})
            continue
        try:
            record = UseCaseRecord.from_dict(load_document(path))
            findings.extend(validate_use_case(project, record))
            findings.extend(validate_no_secret_values(record.to_dict(), record_path))
        except Exception as exc:
            findings.append({"severity": "blocking", "code": "invalid-record", "path": record_path, "message": str(exc)})

    findings.extend(validate_no_secret_values(load_document(layout.product_context_path(project), default={}), layout.PRODUCT_CONTEXT_FILE))
    return findings


def validate_use_case(project: Path, record: UseCaseRecord) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not record.runRequest:
        findings.append({"severity": "blocking", "code": "missing-run-request", "path": record.alias, "message": "Use case must reference exactly one run request."})
    else:
        findings.extend(_validate_artifact(project, record.runRequest, generated_dir=layout.RUN_REQUESTS_DIR))
    if not record.mainSkill:
        findings.append({"severity": "blocking", "code": "missing-main-skill", "path": record.alias, "message": "Use case must reference a main skill."})
    else:
        findings.extend(_validate_artifact(project, record.mainSkill, generated_dir=layout.SKILLS_DIR))
    for skill in record.skills:
        findings.extend(_validate_artifact(project, skill, generated_dir=layout.SKILLS_DIR))
    for question in record.authoringQuestions:
        if question.status == "deferred" and record.status == "ready":
            findings.append({"severity": "blocking", "code": "deferred-question-ready", "path": record.alias, "message": "Ready use cases cannot have deferred blocking questions."})
    for profile in record.profiles:
        if profile.slowMoMs < 0:
            findings.append({"severity": "blocking", "code": "invalid-profile-slowmo", "path": record.alias, "message": f"Profile {profile.name} has negative slowMoMs."})
        findings.extend(validate_no_secret_values(profile.to_dict(), f"{record.alias}.profiles.{profile.name}"))
    if record.lastRun:
        findings.extend(validate_no_secret_values(record.lastRun, f"{record.alias}.lastRun"))
    return findings


def _validate_artifact(project: Path, artifact: ArtifactReference, generated_dir: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    try:
        path = layout.project_relative_path(project, artifact.path)
    except Exception:
        return [{"severity": "blocking", "code": "artifact-path-escapes-project", "path": artifact.path, "message": "Artifact path escapes target project."}]
    if not path.exists():
        findings.append({"severity": "blocking", "code": "missing-artifact", "path": artifact.path, "message": "Referenced artifact does not exist."})
    expected_prefix = f"{layout.WORKSPACE_DIR}/{generated_dir}/"
    if artifact.generated and artifact.kind == "skill":
        remainder = artifact.path.removeprefix(f"{layout.WORKSPACE_DIR}/{layout.SKILLS_DIR}/")
        if (
            not artifact.path.startswith(f"{layout.WORKSPACE_DIR}/{layout.SKILLS_DIR}/")
            or not artifact.path.endswith(".browser.md")
            or "/" in remainder
        ):
            findings.append(
                {
                    "severity": "blocking",
                    "code": "non-canonical-generated-skill",
                    "path": artifact.path,
                    "message": "Generated browser skills must be single markdown files at .proofsignal/skills/<name>.browser.md.",
                }
            )
    if artifact.generated and artifact.kind == "run-request":
        if not artifact.path.startswith(f"{layout.WORKSPACE_DIR}/{layout.RUN_REQUESTS_DIR}/"):
            findings.append(
                {
                    "severity": "blocking",
                    "code": "non-canonical-generated-run-request",
                    "path": artifact.path,
                    "message": "Generated run requests must be under .proofsignal/run-requests/.",
                }
            )
    if artifact.generated and not artifact.path.startswith(expected_prefix):
        findings.append({"severity": "blocking", "code": "generated-artifact-outside-canonical-dir", "path": artifact.path, "message": "Generated artifact is outside the canonical directory."})
    if not artifact.generated and artifact.path.startswith(f"{layout.WORKSPACE_DIR}/"):
        findings.append({"severity": "warning", "code": "external-artifact-in-managed-workspace", "path": artifact.path, "message": "External artifact is inside the managed workspace."})
    return findings


def status_from_findings(findings: Iterable[dict[str, Any]]) -> str:
    return "blocked" if any(item.get("severity") == "blocking" for item in findings) else "passed"

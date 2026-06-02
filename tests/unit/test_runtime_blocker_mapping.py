from __future__ import annotations

from proofsignal_spec.runtime.models import RuntimeSetupBlocker


def test_runtime_blockers_map_categories_and_remain_non_repairable() -> None:
    examples = {
        "api.unavailable": "environment",
        "entitlement.exchange-limit": "entitlement",
        "distribution.unauthorized": "distribution",
        "artifact.integrity-failed": "security",
        "core.incompatible": "compatibility",
    }

    for code, category in examples.items():
        payload = RuntimeSetupBlocker(code=code, message="blocked").to_dict()
        assert payload["category"] == category
        assert payload["repairable"] is False


"""Small harness for testing script registry manifest loading."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from .script_registry import ManifestValidationError, ScriptRegistry


def run_registry_demo(
    valid_manifest: str | Path = "manifest/manifest.json",
    broken_manifest: str | Path = "manifest/manifest_broken.json",
) -> Dict[str, object]:
    """Run valid and invalid manifest load checks and return summary."""

    registry = ScriptRegistry()
    valid_ok = registry.load_manifest(valid_manifest)

    categories = registry.get_categories()
    buttons_by_category: Dict[str, List[dict]] = {
        item["id"]: registry.get_buttons_for_category(item["id"]) for item in categories
    }

    broken_error = ""
    try:
        registry.load_manifest(broken_manifest)
    except ManifestValidationError as exc:
        broken_error = str(exc)

    return {
        "valid_ok": valid_ok,
        "categories": categories,
        "buttons_by_category": buttons_by_category,
        "broken_error": broken_error,
    }

"""Small harness for testing script registry manifest loading."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from context_pad.config import DEFAULT_CONFIG, get_active_manifest_path

from .script_registry import ManifestValidationError, ScriptRegistry


def run_registry_demo(
    valid_manifest: str | Path | None = None,
    broken_manifest: str | Path | None = None,
) -> Dict[str, object]:
    """Run valid and invalid manifest load checks and return summary."""

    valid_path = valid_manifest or get_active_manifest_path()
    broken_path = broken_manifest or (DEFAULT_CONFIG.package_manifest_root / "manifest_broken.json")

    registry = ScriptRegistry()
    valid_ok = registry.load_manifest(valid_path)

    categories = registry.get_categories()
    buttons_by_category: Dict[str, List[dict]] = {
        item["id"]: registry.get_buttons_for_category(item["id"]) for item in categories
    }

    broken_error = ""
    try:
        registry.load_manifest(broken_path)
    except ManifestValidationError as exc:
        broken_error = str(exc)

    return {
        "valid_ok": valid_ok,
        "categories": categories,
        "buttons_by_category": buttons_by_category,
        "broken_error": broken_error,
    }

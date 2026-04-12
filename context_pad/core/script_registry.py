"""Disk-backed script library registry for Context Pad launchers."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from context_pad.config import DEFAULT_CONFIG, get_active_manifest_path

_ALLOWED_ACTION_TYPES = {"python_inline", "python_file", "mel_inline", "mel_file", "separator"}


class ManifestValidationError(ValueError):
    """Raised when manifest structure or fields are invalid."""


@dataclass(frozen=True)
class ScriptCategory:
    """Manifest category used to group launcher buttons."""

    id: str
    label: str
    color: str
    sort_order: int


@dataclass(frozen=True)
class ScriptButton:
    """Manifest button entry mapped to executable action payload fields."""

    id: str
    label: str
    category_id: str
    color: str
    action_type: str
    source: str
    tooltip: str
    sort_order: int
    item_type: str = "button"
    button_size: str = "normal"
    submenu_id: Optional[str] = None


class ScriptRegistry:
    """Registry for loading, validating, and querying manifest-backed script data."""

    def __init__(self) -> None:
        """Initialize empty script registry state."""

        self._manifest_path: Optional[Path] = None
        self._categories: List[ScriptCategory] = []
        self._buttons: List[ScriptButton] = []
        self._raw_manifest: Dict[str, Any] = {}

    def load_manifest(self, path: str | Path | None = None) -> bool:
        """Load and validate manifest JSON from disk."""

        manifest_path = self._resolve_manifest_path(path)
        if not manifest_path.exists() or not manifest_path.is_file():
            raise ManifestValidationError(f"manifest file not found: {manifest_path}")

        with manifest_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        self.validate_manifest(data)
        self._manifest_path = manifest_path
        self._raw_manifest = data
        self._categories = self._parse_categories(data)
        self._buttons = self._parse_buttons(data)
        return True

    def validate_manifest(self, data: Dict[str, Any]) -> bool:
        """Validate manifest data and raise readable error when invalid."""

        if not isinstance(data, dict):
            raise ManifestValidationError("manifest must be a dictionary")

        categories = data.get("categories")
        buttons = data.get("buttons")
        submenus = data.get("submenus", [])

        if not isinstance(categories, list) or not categories:
            raise ManifestValidationError("manifest.categories must be a non-empty list")
        if not isinstance(buttons, list) or not buttons:
            raise ManifestValidationError("manifest.buttons must be a non-empty list")
        if not isinstance(submenus, list):
            raise ManifestValidationError("manifest.submenus must be a list when provided")

        category_ids: set[str] = set()
        for index, category in enumerate(categories):
            self._validate_required_fields(category, ["id", "label", "sort_order"], f"categories[{index}]")
            category_id = str(category["id"])
            if category_id in category_ids:
                raise ManifestValidationError(f"duplicate category id: {category_id}")
            category_ids.add(category_id)

        submenu_ids: set[str] = set()
        for index, submenu in enumerate(submenus):
            self._validate_required_fields(submenu, ["id", "label"], f"submenus[{index}]")
            submenu_id = str(submenu["id"])
            if submenu_id in submenu_ids:
                raise ManifestValidationError(f"duplicate submenu id: {submenu_id}")
            submenu_ids.add(submenu_id)

        button_ids: set[str] = set()
        required_button_fields = [
            "id",
            "label",
            "category_id",
            "color",
            "action_type",
            "sort_order",
        ]
        for index, button in enumerate(buttons):
            path = f"buttons[{index}]"
            self._validate_required_fields(button, required_button_fields, path)

            if "source" not in button:
                raise ManifestValidationError(f"{path}.source is required")
            if "tooltip" not in button:
                raise ManifestValidationError(f"{path}.tooltip is required")

            button_id = str(button["id"])
            if button_id in button_ids:
                raise ManifestValidationError(f"duplicate button id: {button_id}")
            button_ids.add(button_id)

            category_id = str(button["category_id"])
            if category_id not in category_ids:
                raise ManifestValidationError(f"{path}.category_id '{category_id}' does not exist")

            action_type = str(button["action_type"])
            if action_type not in _ALLOWED_ACTION_TYPES:
                raise ManifestValidationError(
                    f"{path}.action_type '{action_type}' is unsupported"
                )
            item_type = str(button.get("item_type", "button"))
            if item_type not in {"button", "separator"}:
                raise ManifestValidationError(f"{path}.item_type '{item_type}' is unsupported")
            button_size = str(button.get("button_size", "normal"))
            if button_size not in {"normal", "small", "large"}:
                raise ManifestValidationError(f"{path}.button_size '{button_size}' is unsupported")

            submenu_id = button.get("submenu_id")
            if submenu_id is not None and str(submenu_id) not in submenu_ids:
                raise ManifestValidationError(
                    f"{path}.submenu_id '{submenu_id}' not found in manifest.submenus"
                )

        return True

    def _resolve_manifest_path(self, path: str | Path | None) -> Path:
        """Resolve manifest path across cwd, package-root, and scripts-root forms."""

        if path is None:
            return get_active_manifest_path()

        candidate = Path(path).expanduser()
        if candidate.is_absolute():
            return candidate

        search_paths = [
            candidate,
            DEFAULT_CONFIG.package_manifest_root / candidate,
            DEFAULT_CONFIG.package_manifest_root.parent / candidate,
        ]
        for item in search_paths:
            if item.exists():
                return item

        return DEFAULT_CONFIG.package_manifest_root / candidate

    def get_categories(self) -> List[Dict[str, Any]]:
        """Return categories in stable sorted order."""

        return [
            {"id": item.id, "label": item.label, "color": item.color, "sort_order": item.sort_order}
            for item in self._categories
        ]

    def get_buttons_for_category(self, category_id: str) -> List[Dict[str, Any]]:
        """Return buttons for a category id in stable sorted order."""

        return [
            {
                "id": item.id,
                "label": item.label,
                "category_id": item.category_id,
                "color": item.color,
                "action_type": item.action_type,
                "source": item.source,
                "tooltip": item.tooltip,
                "sort_order": item.sort_order,
                "item_type": item.item_type,
                "button_size": item.button_size,
                "submenu_id": item.submenu_id,
            }
            for item in self._buttons
            if item.category_id == category_id
        ]

    def manifest_path(self) -> Optional[Path]:
        """Return currently loaded manifest path, if available."""

        return self._manifest_path

    def _parse_categories(self, data: Dict[str, Any]) -> List[ScriptCategory]:
        """Parse and sort category records from manifest."""

        items = [
            ScriptCategory(
                id=str(item["id"]),
                label=str(item["label"]),
                color=str(item.get("color", "#6B7280")),
                sort_order=int(item["sort_order"]),
            )
            for item in data.get("categories", [])
        ]
        return sorted(items, key=lambda cat: (cat.sort_order, cat.label.lower()))

    def _parse_buttons(self, data: Dict[str, Any]) -> List[ScriptButton]:
        """Parse and sort button records from manifest."""

        items = [
            ScriptButton(
                id=str(item["id"]),
                label=str(item["label"]),
                category_id=str(item["category_id"]),
                color=str(item["color"]),
                action_type=str(item["action_type"]),
                source=str(item["source"]),
                tooltip=str(item["tooltip"]),
                sort_order=int(item["sort_order"]),
                item_type=str(item.get("item_type", "button")),
                button_size=str(item.get("button_size", "normal")),
                submenu_id=str(item["submenu_id"]) if item.get("submenu_id") is not None else None,
            )
            for item in data.get("buttons", [])
        ]
        return sorted(items, key=lambda btn: (btn.category_id, btn.sort_order, btn.label.lower()))

    def _validate_required_fields(self, entry: Any, fields: List[str], path: str) -> None:
        """Validate required fields are present and non-empty in an entry."""

        if not isinstance(entry, dict):
            raise ManifestValidationError(f"{path} must be an object")

        for field_name in fields:
            value = entry.get(field_name)
            if value is None or (isinstance(value, str) and not value.strip()):
                raise ManifestValidationError(f"{path}.{field_name} is required")

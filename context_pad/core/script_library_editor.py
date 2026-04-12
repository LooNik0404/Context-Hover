"""Editable script library service for manifest category/button management."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

from context_pad.config import get_active_manifest_path
from context_pad.data.io_json import load_json, save_json

from .script_registry import ManifestValidationError, ScriptRegistry


class ScriptLibraryEditor:
    """CRUD helpers for manifest-backed categories and script buttons."""

    def __init__(self, manifest_path: str | Path | None = None) -> None:
        """Initialize editor and load manifest data."""

        self._manifest_path = Path(manifest_path) if manifest_path else get_active_manifest_path()
        self._registry = ScriptRegistry()
        self._data: Dict[str, Any] = {}
        self.reload()

    def reload(self) -> None:
        """Reload manifest from disk."""

        if not self._manifest_path.exists():
            self._data = {"version": 1, "categories": [], "buttons": [], "submenus": []}
            return
        self._data = load_json(self._manifest_path)

    def categories(self) -> List[Dict[str, Any]]:
        """Return categories sorted by sort_order."""

        return sorted(deepcopy(self._data.get("categories", [])), key=lambda item: (int(item.get("sort_order", 1000)), item.get("label", "")))

    def buttons(self) -> List[Dict[str, Any]]:
        """Return buttons sorted by category/sort order."""

        return sorted(
            deepcopy(self._data.get("buttons", [])),
            key=lambda item: (item.get("category_id", ""), int(item.get("sort_order", 1000)), item.get("label", "")),
        )

    def save(self) -> bool:
        """Validate and save manifest to disk."""

        self._registry.validate_manifest(self._data)
        self._manifest_path.parent.mkdir(parents=True, exist_ok=True)
        save_json(self._manifest_path, self._data)
        return True

    def add_category(self, label: str, color: str = "#6B7280") -> Dict[str, Any]:
        """Create and append a category."""

        categories = self._data.setdefault("categories", [])
        new_item = {
            "id": self._next_id("cat", [item.get("id", "") for item in categories]),
            "label": label,
            "color": color,
            "sort_order": self._next_sort(categories),
        }
        categories.append(new_item)
        return new_item

    def rename_category(self, category_id: str, new_label: str) -> bool:
        """Rename existing category."""

        category = self._find_by_id(self._data.get("categories", []), category_id)
        if not category:
            return False
        category["label"] = new_label
        return True

    def delete_category(self, category_id: str) -> bool:
        """Delete category and all linked buttons."""

        categories = self._data.get("categories", [])
        before = len(categories)
        categories[:] = [item for item in categories if item.get("id") != category_id]
        if len(categories) == before:
            return False

        buttons = self._data.get("buttons", [])
        buttons[:] = [item for item in buttons if item.get("category_id") != category_id]
        return True

    def move_category(self, category_id: str, direction: int) -> bool:
        """Move category up/down using sort_order swap."""

        categories = self.categories()
        ids = [item.get("id") for item in categories]
        if category_id not in ids:
            return False
        index = ids.index(category_id)
        target = index + direction
        if target < 0 or target >= len(categories):
            return False

        categories[index]["sort_order"], categories[target]["sort_order"] = categories[target]["sort_order"], categories[index]["sort_order"]
        self._data["categories"] = categories
        return True

    def add_button(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create and append a script button entry."""

        buttons = self._data.setdefault("buttons", [])
        new_item = {
            "id": self._next_id("btn", [item.get("id", "") for item in buttons]),
            "label": payload.get("label", "New Button"),
            "category_id": payload.get("category_id", ""),
            "color": payload.get("color", "#6B7280"),
            "action_type": payload.get("action_type", "python_inline"),
            "source": payload.get("source", ""),
            "tooltip": payload.get("tooltip", ""),
            "item_type": payload.get("item_type", "button"),
            "button_size": payload.get("button_size", "normal"),
            "sort_order": self._next_sort(buttons),
            "submenu_id": payload.get("submenu_id"),
        }
        buttons.append(new_item)
        return new_item

    def update_button(self, button_id: str, payload: Dict[str, Any]) -> bool:
        """Update button fields by id."""

        button = self._find_by_id(self._data.get("buttons", []), button_id)
        if not button:
            return False

        for key in [
            "label",
            "category_id",
            "color",
            "action_type",
            "source",
            "tooltip",
            "submenu_id",
            "item_type",
            "button_size",
        ]:
            if key in payload:
                button[key] = payload[key]
        return True

    def delete_button(self, button_id: str) -> bool:
        """Delete button by id."""

        buttons = self._data.get("buttons", [])
        before = len(buttons)
        buttons[:] = [item for item in buttons if item.get("id") != button_id]
        return len(buttons) != before

    def move_button(self, button_id: str, direction: int, category_id: str | None = None) -> bool:
        """Move button up/down by swapping sort_order with adjacent item."""

        ordered = self.buttons()
        if category_id:
            ordered = [item for item in ordered if item.get("category_id") == category_id]

        ids = [item.get("id") for item in ordered]
        if button_id not in ids:
            return False

        index = ids.index(button_id)
        target = index + direction
        if target < 0 or target >= len(ordered):
            return False

        current_id = str(ordered[index].get("id", ""))
        target_id = str(ordered[target].get("id", ""))

        current = self._find_by_id(self._data.get("buttons", []), current_id)
        neighbor = self._find_by_id(self._data.get("buttons", []), target_id)
        if not current or not neighbor:
            return False

        current["sort_order"], neighbor["sort_order"] = neighbor.get("sort_order", 1000), current.get("sort_order", 1000)
        return True

    def _next_id(self, prefix: str, ids: List[str]) -> str:
        """Generate a unique id with prefix."""

        index = 1
        while True:
            candidate = f"{prefix}_{index:03d}"
            if candidate not in ids:
                return candidate
            index += 1

    def _next_sort(self, items: List[Dict[str, Any]]) -> int:
        """Return next sort_order value."""

        if not items:
            return 10
        return max(int(item.get("sort_order", 0)) for item in items) + 10

    def _find_by_id(self, items: List[Dict[str, Any]], target_id: str) -> Optional[Dict[str, Any]]:
        """Find mutable dict entry by id."""

        for item in items:
            if item.get("id") == target_id:
                return item
        return None

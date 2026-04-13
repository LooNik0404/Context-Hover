"""UI-independent registry facade for scene selection set operations."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from context_pad.maya_integration import maya_scene_meta, maya_sets


class SetRegistry:
    """Facade over Maya set integration functions for launcher/service layers."""

    _SET_COLORS: List[Tuple[str, str]] = [
        ("Steel Blue", "#5D82A8"),
        ("Olive Green", "#6E8F66"),
        ("Muted Purple", "#7A70A3"),
        ("Sky Blue", "#4A90E2"),
        ("Moss Green", "#7EA178"),
        ("Lavender", "#887CB0"),
        ("Amber", "#D9822B"),
        ("Slate Gray", "#6B7280"),
    ]

    def list_scene_sets(self) -> List[str]:
        """List all non-default scene sets."""

        return maya_sets.list_scene_sets()

    def select_set(self, name: str) -> bool:
        """Select members of a set."""

        return maya_sets.select_set(name)

    def select_set_with_saved_order(self, name: str, ordered_members: Optional[List[str]] = None) -> bool:
        """Select members of a set honoring stored member order when available."""

        return maya_sets.select_set_with_saved_order(name, ordered_members=ordered_members)

    def replace_with_set(self, name: str) -> bool:
        """Replace current selection with set members."""

        return maya_sets.replace_with_set(name)

    def add_set_to_selection(self, name: str) -> bool:
        """Add set members to current selection."""

        return maya_sets.add_set_to_selection(name)

    def remove_set_from_selection(self, name: str) -> bool:
        """Remove set members from current selection."""

        return maya_sets.remove_set_from_selection(name)

    def create_set_from_selection(self, name: str, selection: Optional[List[str]] = None) -> str | None:
        """Create new set from current/explicit selection and return created name."""

        return maya_sets.create_set_from_selection(name, selection=selection)

    def ensure_unique_set_name(self, name: str) -> str:
        """Return Maya-safe unique set name using _NN suffix when needed."""

        return maya_sets.ensure_unique_set_name(name)

    def update_set_from_selection(self, name: str) -> bool:
        """Update existing set from current selection."""

        return maya_sets.update_set_from_selection(name)

    def rename_set(self, old_name: str, new_name: str) -> bool:
        """Rename set safely."""

        return maya_sets.rename_set(old_name, new_name)

    def delete_set(self, name: str) -> bool:
        """Delete set safely."""

        return maya_sets.delete_set(name)

    def get_current_selection(self) -> List[str]:
        """Return current scene selection (empty outside Maya)."""

        return maya_sets.get_current_selection()

    def get_ordered_selection(self) -> List[str]:
        """Return ordered scene selection when Maya supports/has it enabled."""

        return maya_sets.get_ordered_selection()

    def get_sets_for_object(self, node_name: str) -> List[str]:
        """Return all sets containing a node."""

        return maya_sets.get_sets_for_object(node_name)

    def get_set_size(self, name: str) -> int:
        """Return set member count."""

        return maya_sets.get_set_size(name)

    def is_referenced_set(self, name: str) -> bool:
        """Return True when set node comes from a Maya reference."""

        return maya_sets.is_referenced_set(name)

    def set_exists(self, name: str) -> bool:
        """Return True when set exists in current Maya scene."""

        return maya_sets.set_exists(name)

    def get_related_sets_for_selection(
        self,
        selection: Optional[List[str]] = None,
        require_all: bool = True,
    ) -> List[str]:
        """Return related sets for single or multi-object selection."""

        return maya_sets.get_related_sets_for_selection(selection=selection, require_all=require_all)

    def list_reference_sets(self, prepared_only: bool = True) -> List[str]:
        """List referenced sets for import into scene-local Context Pad library."""

        return maya_sets.list_reference_sets(prepared_only=prepared_only)

    def ensure_scene_meta_node(self) -> str:
        """Ensure dedicated scene metadata node exists."""

        return maya_scene_meta.ensure_scene_meta_node()

    def load_scene_set_ui_state(self) -> dict:
        """Load scene-local UI metadata for sets."""

        return maya_scene_meta.load_scene_set_ui_state()

    def save_scene_set_ui_state(self, data: dict) -> bool:
        """Save scene-local UI metadata for sets."""

        return maya_scene_meta.save_scene_set_ui_state(data)

    def cleanup_missing_set_metadata(self) -> dict:
        """Remove stale metadata entries for deleted sets."""

        return maya_scene_meta.cleanup_missing_set_metadata()

    def refresh_scene_set_ui_state(self) -> dict:
        """Refresh metadata defaults and cleanup missing sets."""

        return maya_scene_meta.refresh_scene_set_ui_state()

    def sanitize_set_name(self, name: str) -> str:
        """Normalize user-entered set name to Maya-safe identifier."""

        return maya_sets.sanitize_set_name(name)

    def load_scene_set_library(self) -> Dict[str, Dict[str, Any]]:
        """Load scene-local set library entries."""

        return maya_scene_meta.load_scene_set_library()

    def register_set_library_entry(
        self,
        source_ref: str,
        source_kind: str,
        display_label: str | None = None,
        color: str = "#6B7280",
        hidden_in_launcher: bool = False,
        is_referenced: bool = False,
        selection_order: List[str] | None = None,
    ) -> str:
        """Register/update a set entry in scene-local Context Pad library."""

        return maya_scene_meta.register_set_library_entry(
            source_ref=source_ref,
            source_kind=source_kind,
            display_label=display_label,
            color=color,
            hidden_in_launcher=hidden_in_launcher,
            is_referenced=is_referenced,
            selection_order=selection_order,
        )

    def update_set_library_entry(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing scene-local set library entry."""

        return maya_scene_meta.update_set_library_entry(entry_id, updates)

    def delete_set_library_entry(self, entry_id: str) -> bool:
        """Delete a scene-local set library entry."""

        return maya_scene_meta.delete_set_library_entry(entry_id)

    def choose_balanced_color(self, include_gray: bool = True) -> str:
        """Choose practical color by usage balance, avoiding recent repeats."""

        palette_values = [hex_color for _, hex_color in self._SET_COLORS]
        if not include_gray:
            palette_values = [color for color in palette_values if color != "#6B7280"]

        library = self.load_scene_set_library()
        usage = Counter(str(entry.get("button_color", "")) for entry in library.values() if isinstance(entry, dict))
        ordered_entries = sorted(
            [entry for entry in library.values() if isinstance(entry, dict)],
            key=lambda entry: int(entry.get("display_order", 1000)),
        )
        recent_colors = [str(entry.get("button_color", "")) for entry in ordered_entries[-2:]]

        def score(color: str) -> tuple[int, int]:
            repeat_penalty = 1 if color in recent_colors else 0
            return (usage.get(color, 0), repeat_penalty)

        if not palette_values:
            return "#6B7280"
        return sorted(palette_values, key=score)[0]

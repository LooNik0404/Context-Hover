"""UI-independent registry facade for scene selection set operations."""

from __future__ import annotations

from typing import List, Optional

from context_pad.maya_integration import maya_scene_meta, maya_sets


class SetRegistry:
    """Facade over Maya set integration functions for launcher/service layers."""

    def list_scene_sets(self) -> List[str]:
        """List all non-default scene sets."""

        return maya_sets.list_scene_sets()

    def select_set(self, name: str) -> bool:
        """Select members of a set."""

        return maya_sets.select_set(name)

    def replace_with_set(self, name: str) -> bool:
        """Replace current selection with set members."""

        return maya_sets.replace_with_set(name)

    def add_set_to_selection(self, name: str) -> bool:
        """Add set members to current selection."""

        return maya_sets.add_set_to_selection(name)

    def remove_set_from_selection(self, name: str) -> bool:
        """Remove set members from current selection."""

        return maya_sets.remove_set_from_selection(name)

    def create_set_from_selection(self, name: str) -> bool:
        """Create new set from current selection."""

        return maya_sets.create_set_from_selection(name)

    def update_set_from_selection(self, name: str) -> bool:
        """Update existing set from current selection."""

        return maya_sets.update_set_from_selection(name)

    def rename_set(self, old_name: str, new_name: str) -> bool:
        """Rename set safely."""

        return maya_sets.rename_set(old_name, new_name)

    def delete_set(self, name: str) -> bool:
        """Delete set safely."""

        return maya_sets.delete_set(name)

    def get_sets_for_object(self, node_name: str) -> List[str]:
        """Return all sets containing a node."""

        return maya_sets.get_sets_for_object(node_name)

    def get_set_size(self, name: str) -> int:
        """Return set member count."""

        return maya_sets.get_set_size(name)

    def get_related_sets_for_selection(
        self,
        selection: Optional[List[str]] = None,
        require_all: bool = True,
    ) -> List[str]:
        """Return related sets for single or multi-object selection."""

        return maya_sets.get_related_sets_for_selection(selection=selection, require_all=require_all)

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


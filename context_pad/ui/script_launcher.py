"""Script overlay launcher widget."""

from __future__ import annotations

from .launcher_base import LauncherBase


class ScriptLauncher(LauncherBase):
    """Overlay launcher displaying script placeholder items."""

    def __init__(self, parent=None) -> None:
        """Initialize script launcher with demo data."""

        super().__init__(title="Context Pad • Scripts", parent=parent)
        self.set_categories(
            [
                {"id": "anim", "name": "Animation", "color": "#3C78D8"},
                {"id": "rig", "name": "Rig", "color": "#6AA84F"},
                {"id": "util", "name": "Utilities", "color": "#8E7CC3"},
            ]
        )
        self.set_buttons(
            [
                {"id": "scr_1", "name": "Bake Keys", "category_id": "anim", "color": "#4A90E2"},
                {"id": "scr_2", "name": "Mirror Pose", "category_id": "anim", "color": "#357ABD"},
                {"id": "scr_3", "name": "Select Ctrls", "category_id": "rig", "color": "#5DA95D"},
                {"id": "scr_4", "name": "Zero Ctrls", "category_id": "rig", "color": "#4C8D4C"},
                {"id": "scr_5", "name": "Toggle HUD", "category_id": "util", "color": "#9575CD"},
                {"id": "scr_6", "name": "Frame Sel", "category_id": "util", "color": "#7E57C2"},
            ]
        )

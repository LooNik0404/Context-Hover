"""Selection set overlay launcher widget."""

from __future__ import annotations

from .launcher_base import LauncherBase


class SetLauncher(LauncherBase):
    """Overlay launcher displaying scene-set placeholder items."""

    def __init__(self, parent=None) -> None:
        """Initialize set launcher with demo data."""

        super().__init__(title="Context Pad • Sets", parent=parent)
        self.set_categories(
            [
                {"id": "face", "name": "Face", "color": "#E69138"},
                {"id": "body", "name": "Body", "color": "#3D85C6"},
                {"id": "props", "name": "Props", "color": "#B45F06"},
            ]
        )
        self.set_buttons(
            [
                {"id": "set_1", "name": "Face Ctrls", "category_id": "face", "color": "#F6B26B"},
                {"id": "set_2", "name": "Body Main", "category_id": "body", "color": "#6FA8DC"},
                {"id": "set_3", "name": "Sword Rig", "category_id": "props", "color": "#E69138"},
            ]
        )

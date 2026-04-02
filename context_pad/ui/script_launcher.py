"""Script overlay launcher widget."""

from __future__ import annotations

from .launcher_base import LauncherBase
from .widgets.category_bar import CategoryBar


class ScriptLauncher(LauncherBase):
    """Overlay launcher displaying script placeholder items."""

    def __init__(self, parent=None) -> None:
        """Initialize script launcher with compact category+grid layout."""

        super().__init__(parent=parent)
        self.setWindowTitle("Context Pad")
        self.set_button_columns(2)

        category_widget = CategoryBar()
        category_widget.set_title("Categories")
        category_widget.category_changed.connect(self._command_grid.filter_by_category)
        self.set_left_widget(category_widget)

        self.set_categories(
            [
                {"id": "anim", "name": "Animation", "color": "#9DB4D1"},
                {"id": "rig", "name": "Rig", "color": "#B1C7A2"},
                {"id": "util", "name": "Utilities", "color": "#B8AFD1"},
            ]
        )
        self.set_buttons(
            [
                {"id": "scr_1", "name": "Bake Keys", "category_id": "anim", "color": "#5D82A8"},
                {"id": "scr_2", "name": "Mirror Pose", "category_id": "anim", "color": "#6E95BC"},
                {"id": "scr_3", "name": "Select Ctrls", "category_id": "rig", "color": "#6B8F66"},
                {"id": "scr_4", "name": "Zero Ctrls", "category_id": "rig", "color": "#7EA178"},
                {"id": "scr_5", "name": "Toggle HUD", "category_id": "util", "color": "#746A96"},
                {"id": "scr_6", "name": "Frame Sel", "category_id": "util", "color": "#887CB0"},
            ]
        )

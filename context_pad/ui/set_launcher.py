"""Selection set overlay launcher widget."""

from __future__ import annotations

from .launcher_base import LauncherBase
from .widgets.related_sets import RelatedSetsList


class SetLauncher(LauncherBase):
    """Overlay launcher displaying related and all set placeholders."""

    def __init__(self, parent=None) -> None:
        """Initialize set launcher with contextual left column."""

        super().__init__(parent=parent)
        self.setWindowTitle("Context Pad")
        self.set_button_columns(2)

        related_widget = RelatedSetsList()
        related_widget.related_selected.connect(self._command_grid.filter_by_category)
        self.set_left_widget(related_widget)

        related_widget.set_related_sets(
            [
                {"id": "tail", "name": "Tail Set"},
                {"id": "all", "name": "All Ctrls"},
                {"id": "body", "name": "Body Main"},
            ]
        )

        self.set_buttons(
            [
                {"id": "set_1", "name": "Tail FK", "category_id": "tail", "color": "#8D7B69"},
                {"id": "set_2", "name": "Tail IK", "category_id": "tail", "color": "#9A8774"},
                {"id": "set_3", "name": "All Ctrls", "category_id": "all", "color": "#6E7F92"},
                {"id": "set_4", "name": "Body Main", "category_id": "body", "color": "#6B8F9B"},
                {"id": "set_5", "name": "Face Ctrls", "category_id": "all", "color": "#8B7DA8"},
                {"id": "set_6", "name": "Props", "category_id": "all", "color": "#788977"},
            ]
        )

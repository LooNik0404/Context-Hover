"""Grid widget for launcher command placeholders."""

from __future__ import annotations

from typing import Dict, List

from context_pad.maya_integration.qt_helpers import QtCore, QtGui, QtWidgets


class CommandGrid(QtWidgets.QWidget):
    """Grid widget rendering color-coded placeholder buttons."""

    button_clicked = QtCore.Signal(dict)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initialize the command grid."""

        super().__init__(parent)
        self._buttons: List[Dict[str, str]] = []

        self._layout = QtWidgets.QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setHorizontalSpacing(6)
        self._layout.setVerticalSpacing(6)

    def set_buttons(self, buttons: List[Dict[str, str]]) -> None:
        """Populate the grid from button records with id/name/color/category_id keys."""

        self._buttons = buttons
        self._rebuild_grid(buttons)

    def filter_by_category(self, category_id: str) -> None:
        """Display buttons matching a category id, or all when blank."""

        filtered = [b for b in self._buttons if not category_id or b.get("category_id") == category_id]
        self._rebuild_grid(filtered)

    def _rebuild_grid(self, buttons: List[Dict[str, str]]) -> None:
        """Recreate the visible button grid."""

        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for index, item_data in enumerate(buttons):
            button = QtWidgets.QPushButton(item_data.get("name", "Button"))
            button.setObjectName("ContextPadCommandButton")
            color = QtGui.QColor(item_data.get("color", "#4A89DC"))
            button.setStyleSheet(f"background-color: {color.name()};")
            button.clicked.connect(lambda _=False, data=item_data: self.button_clicked.emit(data))
            row = index // 2
            col = index % 2
            self._layout.addWidget(button, row, col)

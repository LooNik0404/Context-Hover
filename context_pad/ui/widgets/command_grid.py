"""Grid widget for launcher command placeholders."""

from __future__ import annotations

from typing import Dict, List

from context_pad.maya_integration.qt_helpers import QtCore, QtGui, QtWidgets


class CommandGrid(QtWidgets.QWidget):
    """Grid widget rendering color-coded buttons."""

    button_clicked = QtCore.Signal(dict)
    button_context_requested = QtCore.Signal(dict, object)

    def __init__(self, parent: QtWidgets.QWidget | None = None, columns: int = 2) -> None:
        """Initialize the command grid."""

        super().__init__(parent)
        self.setAutoFillBackground(False)
        self.setStyleSheet("background: transparent;")
        self._buttons: List[Dict[str, str]] = []
        self._visible_button_ids: List[str] = []
        self._columns = max(1, columns)

        self._layout = QtWidgets.QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setHorizontalSpacing(6)
        self._layout.setVerticalSpacing(6)
        self._layout.setAlignment(QtCore.Qt.AlignTop)

    def set_columns(self, columns: int) -> None:
        """Set number of columns used for button layout."""

        self._columns = max(1, columns)
        self._rebuild_grid(self._buttons)

    def set_buttons(self, buttons: List[Dict[str, str]], rebuild: bool = True) -> None:
        """Populate grid from button records."""

        self._buttons = buttons
        if rebuild:
            self._set_visible_buttons(buttons)

    def filter_by_category(self, category_id: str) -> None:
        """Display buttons matching category id, or all when blank."""

        filtered = [b for b in self._buttons if not category_id or b.get("category_id") == category_id]
        self._set_visible_buttons(filtered)

    def _set_visible_buttons(self, buttons: List[Dict[str, str]]) -> None:
        """Rebuild only when visible ids actually changed."""

        visible_ids = [str(item.get("id", "")) for item in buttons]
        if visible_ids == self._visible_button_ids:
            return
        self._visible_button_ids = visible_ids
        self._rebuild_grid(buttons)

    def _rebuild_grid(self, buttons: List[Dict[str, str]]) -> None:
        """Recreate the visible button grid."""

        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for index, item_data in enumerate(buttons):
            button_name = item_data.get("name", "Button")
            button = QtWidgets.QPushButton(button_name)
            button.setObjectName("ContextPadCommandButton")
            tooltip = str(item_data.get("tooltip", "")).strip()
            button.setToolTip(tooltip or str(button_name))

            background = QtGui.QColor(item_data.get("color", "#4A89DC"))
            foreground = self._contrast_color(background)
            button.setStyleSheet(
                f"background-color: {background.name()}; color: {foreground.name()};"
            )

            button.clicked.connect(lambda _=False, data=item_data: self.button_clicked.emit(data))
            button.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            button.customContextMenuRequested.connect(
                lambda pos, data=item_data, b=button: self.button_context_requested.emit(data, b.mapToGlobal(pos))
            )

            row = index // self._columns
            col = index % self._columns
            self._layout.addWidget(button, row, col)

        self._layout.setRowStretch((len(buttons) // self._columns) + 1, 1)

    def _contrast_color(self, color: QtGui.QColor) -> QtGui.QColor:
        """Return black/white text color based on luminance contrast."""

        luminance = (0.299 * color.red()) + (0.587 * color.green()) + (0.114 * color.blue())
        return QtGui.QColor("#111111") if luminance > 170 else QtGui.QColor("#F4F6FA")

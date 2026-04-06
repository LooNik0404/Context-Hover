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
        self._layout.setVerticalSpacing(4)
        self._layout.setAlignment(QtCore.Qt.AlignTop)
        self._module_width = 82
        self._button_height = 34

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

        visible_fingerprint = [
            "|".join(
                [
                    str(item.get("id", "")),
                    str(item.get("name", "")),
                    str(item.get("color", "")),
                    str(item.get("tooltip", "")),
                    str(item.get("item_type", "button")),
                    str(item.get("button_size", "normal")),
                ]
            )
            for item in buttons
        ]
        if visible_fingerprint == self._visible_button_ids:
            return
        self._visible_button_ids = visible_fingerprint
        self._rebuild_grid(buttons)

    def _rebuild_grid(self, buttons: List[Dict[str, str]]) -> None:
        """Recreate the visible button grid."""

        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        row = 0
        col = 0
        for item_data in buttons:
            item_type = str(item_data.get("item_type", "button"))
            if item_type == "separator":
                if col != 0:
                    row += 1
                    col = 0
                separator = self._make_separator_widget(item_data)
                self._layout.addWidget(separator, row, 0, 1, self._columns)
                row += 1
                continue

            button_name = str(item_data.get("name", "Button"))
            button = QtWidgets.QPushButton()
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

            size_mode = str(item_data.get("button_size", "normal")).lower()
            col_span = 1 if size_mode == "small" else min(2, self._columns)
            if col + col_span > self._columns:
                row += 1
                col = 0

            button_width = self._span_pixel_width(col_span)
            button.setMinimumWidth(button_width)
            button.setMaximumWidth(button_width)
            button.setMinimumHeight(self._button_height)
            button.setMaximumHeight(self._button_height)
            button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            button.setText(self._elide_button_text(button_name, button.fontMetrics(), button_width - 14))

            self._layout.addWidget(button, row, col, 1, col_span)
            col += col_span
            if col >= self._columns:
                row += 1
                col = 0

        self._layout.setRowStretch(row + 1, 1)

    def _make_separator_widget(self, item_data: Dict[str, str]) -> QtWidgets.QWidget:
        """Create subtle full-width separator widget with optional muted label."""

        container = QtWidgets.QWidget(self)
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(2, 1, 2, 1)
        layout.setSpacing(4)
        container.setMinimumHeight(20)
        container.setMaximumHeight(20)

        line_left = QtWidgets.QFrame(container)
        line_left.setFrameShape(QtWidgets.QFrame.HLine)
        line_left.setStyleSheet("color: rgba(220,220,220,35);")
        layout.addWidget(line_left, 1)

        label_text = str(item_data.get("name", "")).strip()
        if label_text:
            label = QtWidgets.QLabel(label_text, container)
            label.setStyleSheet("color: rgba(220,220,220,100); font-size: 9px;")
            layout.addWidget(label, 0)

        line_right = QtWidgets.QFrame(container)
        line_right.setFrameShape(QtWidgets.QFrame.HLine)
        line_right.setStyleSheet("color: rgba(220,220,220,35);")
        layout.addWidget(line_right, 1)
        return container

    def _span_pixel_width(self, span: int) -> int:
        spacing = self._layout.horizontalSpacing()
        return (self._module_width * span) + (spacing * max(0, span - 1))

    def _elide_button_text(self, text: str, metrics: QtGui.QFontMetrics, max_width: int) -> str:
        return metrics.elidedText(text, QtCore.Qt.ElideRight, max(12, int(max_width)))

    def _contrast_color(self, color: QtGui.QColor) -> QtGui.QColor:
        """Return black/white text color based on luminance contrast."""

        luminance = (0.299 * color.red()) + (0.587 * color.green()) + (0.114 * color.blue())
        return QtGui.QColor("#111111") if luminance > 170 else QtGui.QColor("#F4F6FA")

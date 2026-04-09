"""Simple swatch-based color picker widget for manager editing panels."""

from __future__ import annotations

from typing import Dict, List

from context_pad.maya_integration.qt_helpers import QtCore, QtWidgets


class ColorPicker(QtWidgets.QWidget):
    """Small selectable grouped color swatches."""

    color_changed = QtCore.Signal(str)

    def __init__(self, colors: List[str] | None = None, parent: QtWidgets.QWidget | None = None) -> None:
        """Initialize color picker with optional swatch list."""

        super().__init__(parent)
        self._color = "#6B7280"
        self._buttons: Dict[str, QtWidgets.QToolButton] = {}
        grouped_palette: List[tuple[str, List[str]]]
        if colors:
            grouped_palette = [("Palette", colors)]
        else:
            grouped_palette = [
                ("Cool", ["#5B7896", "#667F99", "#70869A", "#7A8EA0"]),
                ("Neutral", ["#656D78", "#747C86", "#858A90", "#948E86"]),
                ("Warm", ["#8C7564", "#997D6A", "#A78670", "#B58F77"]),
            ]

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        for group_name, palette in grouped_palette:
            group_row = QtWidgets.QHBoxLayout()
            group_row.setSpacing(4)

            label = QtWidgets.QLabel(group_name, self)
            label.setMinimumWidth(48)
            label.setStyleSheet("color: rgba(230,230,230,150); font-size: 11px;")
            group_row.addWidget(label)

            for color in palette:
                button = QtWidgets.QToolButton(self)
                button.setCheckable(True)
                button.setFixedSize(18, 18)
                button.clicked.connect(lambda _=False, value=color: self.set_color(value))
                group_row.addWidget(button)
                self._buttons[color] = button

            group_row.addStretch(1)
            layout.addLayout(group_row)

        self.set_color(self._color)

    def set_color(self, color: str) -> None:
        """Set active color and emit change signal."""

        self._color = color
        for value, button in self._buttons.items():
            checked = value == color
            button.setChecked(checked)
            border = "2px solid white" if checked else "1px solid rgba(255,255,255,50)"
            button.setStyleSheet(f"background:{value}; border:{border}; border-radius:4px;")
        self.color_changed.emit(color)

    def color(self) -> str:
        """Return currently selected color value."""

        return self._color

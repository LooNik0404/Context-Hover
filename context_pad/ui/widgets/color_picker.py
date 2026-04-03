"""Simple swatch-based color picker widget for manager editing panels."""

from __future__ import annotations

from typing import Dict, List

from context_pad.maya_integration.qt_helpers import QtCore, QtWidgets


class ColorPicker(QtWidgets.QWidget):
    """Small selectable color swatch row."""

    color_changed = QtCore.Signal(str)

    def __init__(self, colors: List[str] | None = None, parent: QtWidgets.QWidget | None = None) -> None:
        """Initialize color picker with optional swatch list."""

        super().__init__(parent)
        self._color = "#6B7280"
        self._buttons: Dict[str, QtWidgets.QToolButton] = {}
        palette = colors or [
            "#5D82A8",
            "#6E8F66",
            "#7A70A3",
            "#4A90E2",
            "#7EA178",
            "#887CB0",
            "#7E8FA3",
            "#8F7C66",
            "#5E8A8A",
            "#A37A70",
            "#D9822B",
            "#6B7280",
        ]

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        for color in palette:
            button = QtWidgets.QToolButton(self)
            button.setCheckable(True)
            button.setFixedSize(18, 18)
            button.clicked.connect(lambda _=False, value=color: self.set_color(value))
            layout.addWidget(button)
            self._buttons[color] = button

        layout.addStretch(1)
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

"""Base launcher widget for translucent square overlays."""

from __future__ import annotations

from typing import Dict, List

from context_pad.maya_integration.qt_helpers import QtCore, QtGui, QtWidgets
from context_pad.ui.styles import launcher_stylesheet
from context_pad.ui.widgets.category_bar import CategoryBar
from context_pad.ui.widgets.command_grid import CommandGrid
from context_pad.ui.widgets.pin_zone import PinZone


class LauncherBase(QtWidgets.QWidget):
    """Shared launcher implementation for script and set overlays."""

    def __init__(self, title: str, parent: QtWidgets.QWidget | None = None) -> None:
        """Initialize base launcher widget structure."""

        super().__init__(parent)
        self._title = title
        self._is_pinned = False

        self.setWindowTitle(title)
        self.setWindowFlags(
            QtCore.Qt.Tool
            | QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        self._body = QtWidgets.QFrame()
        self._body.setObjectName("ContextPadBody")
        self._body.setStyleSheet(launcher_stylesheet())
        self._body.setMinimumSize(380, 380)
        self._body.setMaximumSize(420, 420)
        root_layout.addWidget(self._body)

        body_layout = QtWidgets.QVBoxLayout(self._body)
        body_layout.setContentsMargins(10, 10, 10, 10)
        body_layout.setSpacing(8)

        self._pin_zone = PinZone()
        self._pin_zone.pin_toggled.connect(self.set_pinned)
        body_layout.addWidget(self._pin_zone)

        title_label = QtWidgets.QLabel(title)
        title_label.setObjectName("ContextPadTitle")
        body_layout.addWidget(title_label)

        content_layout = QtWidgets.QHBoxLayout()
        content_layout.setSpacing(8)
        body_layout.addLayout(content_layout)

        self._category_bar = CategoryBar()
        self._category_bar.setFixedWidth(130)
        self._category_bar.category_changed.connect(self._on_category_changed)
        content_layout.addWidget(self._category_bar)

        self._command_grid = CommandGrid()
        content_layout.addWidget(self._command_grid, 1)

    def show_at_cursor(self) -> None:
        """Show the launcher near cursor and focus it."""

        cursor_pos = QtGui.QCursor.pos()
        self.move(cursor_pos + QtCore.QPoint(12, 12))
        self.show()
        self.raise_()
        self.activateWindow()

    def set_categories(self, data: List[Dict[str, str]]) -> None:
        """Set launcher categories from data records."""

        self._category_bar.set_categories(data)

    def set_buttons(self, data: List[Dict[str, str]]) -> None:
        """Set launcher buttons from data records."""

        self._command_grid.set_buttons(data)
        self._command_grid.filter_by_category(self._category_bar.current_category())

    def set_pinned(self, state: bool) -> None:
        """Set pin state for launcher behavior."""

        self._is_pinned = state
        self._pin_zone.set_pinned(state)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # noqa: N802
        """Close the launcher when ESC is pressed."""

        if event.key() == QtCore.Qt.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def focusOutEvent(self, event: QtGui.QFocusEvent) -> None:  # noqa: N802
        """Auto-close when unpinned and focus is lost."""

        super().focusOutEvent(event)
        if not self._is_pinned:
            self.close()

    def _on_category_changed(self, category_id: str) -> None:
        """Refresh visible buttons for currently selected category."""

        self._command_grid.filter_by_category(category_id)

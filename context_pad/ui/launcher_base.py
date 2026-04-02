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

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initialize base launcher widget structure."""

        super().__init__(parent)
        self._is_pinned = False

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
        self._body.setFixedSize(372, 308)
        root_layout.addWidget(self._body)

        body_layout = QtWidgets.QVBoxLayout(self._body)
        body_layout.setContentsMargins(8, 8, 8, 8)
        body_layout.setSpacing(7)

        top_bar = QtWidgets.QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        self._utility_bar = PinZone()
        self._utility_bar.pin_toggled.connect(self.set_pinned)
        self._utility_bar.add_clicked.connect(self.on_add_requested)
        self._utility_bar.manager_clicked.connect(self.on_manager_requested)
        top_bar.addWidget(self._utility_bar, 1)
        body_layout.addLayout(top_bar)

        content_layout = QtWidgets.QHBoxLayout()
        content_layout.setSpacing(8)
        body_layout.addLayout(content_layout, 1)

        self._left_column = QtWidgets.QVBoxLayout()
        self._left_column.setContentsMargins(0, 0, 0, 0)
        self._left_column.setSpacing(0)
        content_layout.addLayout(self._left_column, 0)

        self._left_widget: QtWidgets.QWidget = CategoryBar()
        self._left_widget.setFixedWidth(116)
        self._left_column.addWidget(self._left_widget)

        self._divider = QtWidgets.QFrame()
        self._divider.setObjectName("ContextPadDivider")
        content_layout.addWidget(self._divider)

        self._command_grid = CommandGrid(columns=2)
        content_layout.addWidget(self._command_grid, 1)

    def set_left_widget(self, widget: QtWidgets.QWidget) -> None:
        """Replace left column widget with a custom widget."""

        if self._left_widget is widget:
            return
        self._left_column.removeWidget(self._left_widget)
        self._left_widget.deleteLater()
        self._left_widget = widget
        self._left_widget.setFixedWidth(116)
        self._left_column.addWidget(self._left_widget)

    def set_button_columns(self, columns: int) -> None:
        """Set number of columns for the right button grid."""

        self._command_grid.set_columns(columns)

    def show_at_cursor(self) -> None:
        """Show launcher near cursor and focus it."""

        cursor_pos = QtGui.QCursor.pos()
        self.move(cursor_pos + QtCore.QPoint(10, 10))
        self.show()
        self.raise_()
        self.activateWindow()

    def set_categories(self, data: List[Dict[str, str]]) -> None:
        """Set categories when default left category widget is active."""

        if isinstance(self._left_widget, CategoryBar):
            self._left_widget.set_categories(data)

    def set_buttons(self, data: List[Dict[str, str]]) -> None:
        """Set launcher buttons from data records."""

        self._command_grid.set_buttons(data)
        if isinstance(self._left_widget, CategoryBar):
            self._command_grid.filter_by_category(self._left_widget.current_category())

    def set_pinned(self, state: bool) -> None:
        """Set pin state for launcher behavior."""

        self._is_pinned = state
        self._utility_bar.set_pinned(state)

    def on_add_requested(self) -> None:
        """Placeholder callback for future quick-create action."""

    def on_manager_requested(self) -> None:
        """Placeholder callback for opening manager window."""

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # noqa: N802
        """Close launcher when ESC is pressed."""

        if event.key() == QtCore.Qt.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def focusOutEvent(self, event: QtGui.QFocusEvent) -> None:  # noqa: N802
        """Auto-close when unpinned and focus is lost."""

        super().focusOutEvent(event)
        if not self._is_pinned:
            self.close()

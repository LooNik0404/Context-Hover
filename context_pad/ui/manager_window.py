"""Manager window scaffolding for editing scripts and sets."""

from __future__ import annotations

from context_pad.core.app_state import AppState
from context_pad.maya_integration.qt_helpers import QtWidgets


class ManagerWindow(QtWidgets.QMainWindow):
    """Main manager window for Context Pad configuration."""

    def __init__(self, app_state: AppState, parent: QtWidgets.QWidget | None = None) -> None:
        """Initialize the manager window with shared app state."""

        super().__init__(parent)
        self._app_state = app_state
        self.setWindowTitle("Context Pad Manager")

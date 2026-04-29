"""Minimal utility controls for launcher pin and quick actions."""

from __future__ import annotations

from context_pad.maya_integration.qt_helpers import QtCore, QtWidgets


class PinZone(QtWidgets.QFrame):
    """Compact top utility zone with icon-style controls."""

    pin_toggled = QtCore.Signal(bool)
    add_clicked = QtCore.Signal()
    add_context_requested = QtCore.Signal(object)
    manager_clicked = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initialize utility controls."""

        super().__init__(parent)
        self.setObjectName("ContextPadUtilityBar")

        self._pin_button = self._make_icon_button("○")
        self._pin_button.setCheckable(True)
        self._pin_button.toggled.connect(self._on_pin_toggled)

        self._add_button = self._make_icon_button("+")
        self._add_button.clicked.connect(self.add_clicked)
        self._add_button.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._add_button.customContextMenuRequested.connect(self._on_add_context_requested)

        self._manager_button = self._make_icon_button("⋯")
        self._manager_button.clicked.connect(self.manager_clicked)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self._add_button)
        layout.addWidget(self._manager_button)
        layout.addStretch(1)
        layout.addWidget(self._pin_button)

    def set_pinned(self, state: bool) -> None:
        """Update pinned visual state."""

        blocker = QtCore.QSignalBlocker(self._pin_button)
        _ = blocker
        self._pin_button.setChecked(state)
        self._pin_button.setText("●" if state else "○")

    def set_add_visible(self, visible: bool) -> None:
        """Show or hide plus utility button."""

        self._add_button.setVisible(visible)

    def set_manager_visible(self, visible: bool) -> None:
        """Show or hide manager utility button."""

        self._manager_button.setVisible(visible)

    def set_manager_text(self, text: str) -> None:
        """Set manager utility button glyph/text."""

        self._manager_button.setText(text)

    def _on_pin_toggled(self, state: bool) -> None:
        """Emit pin changes using a minimal dot-state icon."""

        self._pin_button.setText("●" if state else "○")
        self.pin_toggled.emit(state)

    def _on_add_context_requested(self, local_pos: object) -> None:
        """Emit global position for plus-button RMB menu."""

        global_pos = self._add_button.mapToGlobal(local_pos)
        self.add_context_requested.emit(global_pos)

    def _make_icon_button(self, glyph: str) -> QtWidgets.QToolButton:
        """Create a tiny icon-style utility button."""

        button = QtWidgets.QToolButton(self)
        button.setObjectName("ContextPadIconButton")
        button.setText(glyph)
        return button

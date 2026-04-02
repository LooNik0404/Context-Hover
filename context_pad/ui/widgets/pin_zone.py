"""Pin-zone widget for launcher pin state."""

from __future__ import annotations

from context_pad.maya_integration.qt_helpers import QtCore, QtWidgets


class PinZone(QtWidgets.QFrame):
    """Top strip widget with a toggle button for pin mode."""

    pin_toggled = QtCore.Signal(bool)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initialize the pin zone UI."""

        super().__init__(parent)
        self.setObjectName("ContextPadPinZone")

        self._pin_button = QtWidgets.QPushButton("📌 Unpinned")
        self._pin_button.setObjectName("ContextPadPinButton")
        self._pin_button.setCheckable(True)
        self._pin_button.toggled.connect(self._on_toggled)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(self._pin_button)
        layout.addStretch(1)

    def set_pinned(self, state: bool) -> None:
        """Update the pin button state without duplicate signal emissions."""

        blocker = QtCore.QSignalBlocker(self._pin_button)
        _ = blocker
        self._pin_button.setChecked(state)
        self._set_pin_label(state)

    def _on_toggled(self, state: bool) -> None:
        """Emit pin toggled and refresh label."""

        self._set_pin_label(state)
        self.pin_toggled.emit(state)

    def _set_pin_label(self, state: bool) -> None:
        """Set visible pin label based on current state."""

        self._pin_button.setText("📌 Pinned" if state else "📌 Unpinned")

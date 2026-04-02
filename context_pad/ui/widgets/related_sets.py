"""Compact related-sets button rail for set launcher context."""

from __future__ import annotations

from typing import Dict, List

from context_pad.maya_integration.qt_helpers import QtCore, QtWidgets


class RelatedSetsList(QtWidgets.QWidget):
    """Minimal vertical button rail for contextual related sets."""

    related_selected = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initialize related sets rail."""

        super().__init__(parent)
        self._buttons: List[QtWidgets.QPushButton] = []

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._label = QtWidgets.QLabel("Related")
        self._label.setObjectName("ContextPadLeftLabel")
        layout.addWidget(self._label)

        self._rail = QtWidgets.QVBoxLayout()
        self._rail.setSpacing(4)
        layout.addLayout(self._rail)
        layout.addStretch(1)

    def set_related_sets(self, records: List[Dict[str, str]]) -> None:
        """Populate related set rail from id/name records."""

        while self._rail.count():
            item = self._rail.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._buttons = []
        for index, record in enumerate(records):
            button = QtWidgets.QPushButton(record.get("name", "Set"))
            button.setObjectName("ContextPadRailButton")
            button.setCheckable(False)
            button.setFocusPolicy(QtCore.Qt.NoFocus)
            button.setMinimumHeight(26)
            button.clicked.connect(lambda _=False, rid=record.get("id", ""): self.related_selected.emit(rid))
            self._rail.addWidget(button)
            self._buttons.append(button)

        has_records = bool(records)
        self._label.setVisible(has_records)
        self.setVisible(True)

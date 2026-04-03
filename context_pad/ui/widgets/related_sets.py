"""Compact related-sets rail for contextual shortcuts."""

from __future__ import annotations

from typing import Dict, List

from context_pad.maya_integration.qt_helpers import QtCore, QtGui, QtWidgets


class RelatedSetsList(QtWidgets.QWidget):
    """Minimal vertical button rail for contextual related sets."""

    related_selected = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
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

        self.setFixedWidth(108)

    def set_related_sets(self, records: List[Dict[str, str]]) -> None:
        """Populate related set rail from id/name/color records."""

        while self._rail.count():
            item = self._rail.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._buttons = []
        for record in records:
            raw_name = str(record.get("name", "Set"))
            metrics = QtGui.QFontMetrics(self.font())
            short_name = metrics.elidedText(raw_name, QtCore.Qt.ElideRight, 96)
            button = QtWidgets.QPushButton(short_name)
            button.setObjectName("ContextPadRelatedButton")
            button.setCheckable(False)
            button.setFocusPolicy(QtCore.Qt.NoFocus)
            button.setMinimumHeight(24)
            button.setToolTip(raw_name)

            color = record.get("color")
            if color:
                button.setStyleSheet(f"background-color:{color};")

            button.clicked.connect(lambda _=False, rid=record.get("id", ""): self.related_selected.emit(rid))
            self._rail.addWidget(button)
            self._buttons.append(button)

        has_records = bool(records)
        self._label.setVisible(has_records)
        self.setVisible(has_records)

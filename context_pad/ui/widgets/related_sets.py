"""Compact related-sets list widget for set launcher context."""

from __future__ import annotations

from typing import Dict, List

from context_pad.maya_integration.qt_helpers import QtCore, QtWidgets


class RelatedSetsList(QtWidgets.QWidget):
    """Minimal vertical list for contextual related sets."""

    related_selected = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initialize related sets list."""

        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._label = QtWidgets.QLabel("Related")
        self._label.setObjectName("ContextPadLeftLabel")
        layout.addWidget(self._label)

        self._list = QtWidgets.QListWidget(self)
        self._list.setObjectName("ContextPadRelatedList")
        self._list.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._list, 1)

    def set_related_sets(self, records: List[Dict[str, str]]) -> None:
        """Populate related set list from id/name records."""

        self._list.clear()
        for record in records:
            item = QtWidgets.QListWidgetItem(record.get("name", "Set"))
            item.setData(QtCore.Qt.UserRole, record.get("id", ""))
            self._list.addItem(item)

        has_records = bool(records)
        self._label.setVisible(has_records)
        self._list.setVisible(has_records)
        self.setMaximumWidth(140 if has_records else 1)

        if has_records:
            self._list.setCurrentRow(0)

    def _on_selection_changed(self) -> None:
        """Emit selected related set id."""

        item = self._list.currentItem()
        if item is None:
            self.related_selected.emit("")
            return
        self.related_selected.emit(str(item.data(QtCore.Qt.UserRole) or ""))

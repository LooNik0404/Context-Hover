"""Reference-set picker dialog for importing sets into Set Hover library."""

from __future__ import annotations

from typing import List

from context_pad.core.set_registry import SetRegistry
from context_pad.maya_integration.qt_helpers import QtCore, QtWidgets


class ReferenceSetPickerDialog(QtWidgets.QDialog):
    """Lightweight picker for referenced sets with prepared/default filtering."""

    def __init__(self, registry: SetRegistry, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._sets = registry

        self.setWindowTitle("Add Sets from Reference")
        self.resize(520, 360)

        root = QtWidgets.QVBoxLayout(self)

        self._show_all_checkbox = QtWidgets.QCheckBox("Show all sets")
        self._show_all_checkbox.setChecked(False)
        self._show_all_checkbox.toggled.connect(self._reload_candidates)
        root.addWidget(self._show_all_checkbox)

        self._list = QtWidgets.QListWidget()
        self._list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        root.addWidget(self._list, 1)

        buttons = QtWidgets.QDialogButtonBox()
        self._add_button = buttons.addButton("Add Selected", QtWidgets.QDialogButtonBox.AcceptRole)
        self._cancel_button = buttons.addButton("Cancel", QtWidgets.QDialogButtonBox.RejectRole)
        self._add_button.clicked.connect(self.accept)
        self._cancel_button.clicked.connect(self.reject)
        root.addWidget(buttons)

        self._reload_candidates()

    def selected_sets(self) -> List[str]:
        """Return full Maya names for selected referenced sets."""

        names: List[str] = []
        for item in self._list.selectedItems():
            names.append(str(item.data(QtCore.Qt.UserRole) or ""))
        return [name for name in names if name]

    def _reload_candidates(self) -> None:
        prepared_only = not self._show_all_checkbox.isChecked()
        candidates = self._sets.list_reference_sets(prepared_only=prepared_only)

        self._list.clear()
        for set_name in candidates:
            item = QtWidgets.QListWidgetItem(self._display_label(set_name))
            item.setData(QtCore.Qt.UserRole, set_name)
            item.setToolTip(set_name)
            self._list.addItem(item)

        self._add_button.setEnabled(bool(candidates))

    def _display_label(self, full_set_name: str) -> str:
        short_name = str(full_set_name).split("|")[-1]
        return short_name.split(":")[-1]

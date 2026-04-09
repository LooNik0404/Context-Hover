"""Set Library manager dialog for Context Pad Set Hover entries."""

from __future__ import annotations

from typing import Any, Dict, List

from context_pad.core.set_registry import SetRegistry
from context_pad.maya_integration.qt_helpers import QtCore, QtWidgets


class _AddLocalSetsDialog(QtWidgets.QDialog):
    """Picker for importing existing local Maya sets into hover library."""

    def __init__(self, names: List[str], parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Existing Local Sets")
        self.resize(480, 320)

        root = QtWidgets.QVBoxLayout(self)
        self._list = QtWidgets.QListWidget()
        self._list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        root.addWidget(self._list, 1)

        for set_name in sorted(set(names)):
            item = QtWidgets.QListWidgetItem(self._display_label(set_name))
            item.setData(QtCore.Qt.UserRole, set_name)
            item.setToolTip(set_name)
            self._list.addItem(item)

        buttons = QtWidgets.QDialogButtonBox()
        self._add_button = buttons.addButton("Add Selected", QtWidgets.QDialogButtonBox.AcceptRole)
        self._cancel_button = buttons.addButton("Cancel", QtWidgets.QDialogButtonBox.RejectRole)
        self._add_button.clicked.connect(self.accept)
        self._cancel_button.clicked.connect(self.reject)
        self._add_button.setEnabled(bool(names))
        root.addWidget(buttons)

    def selected_set_names(self) -> List[str]:
        return [str(item.data(QtCore.Qt.UserRole) or "") for item in self._list.selectedItems() if item]

    def _display_label(self, full_set_name: str) -> str:
        short_name = str(full_set_name).split("|")[-1]
        return short_name.split(":")[-1]


class SetVisibilityDialog(QtWidgets.QDialog):
    """Set Library manager with bulk operations for hover entries."""

    def __init__(self, registry: SetRegistry, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._sets = registry
        self._entries: Dict[str, Dict[str, Any]] = {}

        self.setWindowTitle("Set Library Manager")
        self.resize(640, 420)

        root = QtWidgets.QVBoxLayout(self)

        self._list = QtWidgets.QTreeWidget()
        self._list.setHeaderLabels(["Label", "Set", "Visibility", "Source"])
        self._list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._list.setAlternatingRowColors(True)
        root.addWidget(self._list, 1)

        action_row = QtWidgets.QHBoxLayout()
        self._btn_add_existing = QtWidgets.QPushButton("Add Existing Local Sets...")
        self._btn_hide = QtWidgets.QPushButton("Hide Selected")
        self._btn_show = QtWidgets.QPushButton("Show Selected")
        self._btn_remove = QtWidgets.QPushButton("Remove Selected from Hover")
        self._btn_delete = QtWidgets.QPushButton("Delete Maya Set")
        for button in [self._btn_add_existing, self._btn_hide, self._btn_show, self._btn_remove, self._btn_delete]:
            action_row.addWidget(button)
        root.addLayout(action_row)

        close_row = QtWidgets.QHBoxLayout()
        close_row.addStretch(1)
        btn_close = QtWidgets.QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        close_row.addWidget(btn_close)
        root.addLayout(close_row)

        self._btn_add_existing.clicked.connect(self._add_existing_local_sets)
        self._btn_hide.clicked.connect(lambda: self._set_hidden_for_selected(True))
        self._btn_show.clicked.connect(lambda: self._set_hidden_for_selected(False))
        self._btn_remove.clicked.connect(self._remove_selected_entries)
        self._btn_delete.clicked.connect(self._delete_selected_maya_sets)

        self._rebuild_list()

    def _rebuild_list(self) -> None:
        self._entries = self._sets.load_scene_set_library()
        self._list.clear()

        for entry_id, entry in sorted(
            self._entries.items(),
            key=lambda item: (
                int(item[1].get("display_order", 1000)),
                str(item[1].get("display_label", "")).lower(),
                str(item[1].get("source_ref", "")).lower(),
            ),
        ):
            source_ref = str(entry.get("source_ref", ""))
            if not source_ref:
                continue
            hidden = bool(entry.get("hidden_in_launcher", False))
            item = QtWidgets.QTreeWidgetItem()
            item.setText(0, self._display_label(source_ref))
            item.setText(1, source_ref)
            item.setText(2, "Hidden" if hidden else "Visible")
            item.setText(3, "Referenced" if bool(entry.get("is_referenced", False)) else "Local")
            item.setToolTip(0, source_ref)
            item.setToolTip(1, source_ref)
            item.setData(0, QtCore.Qt.UserRole, entry_id)
            self._list.addTopLevelItem(item)

        for index in range(4):
            self._list.resizeColumnToContents(index)

    def _selected_entry_ids(self) -> List[str]:
        selected: List[str] = []
        for item in self._list.selectedItems():
            entry_id = str(item.data(0, QtCore.Qt.UserRole) or "")
            if entry_id:
                selected.append(entry_id)
        return selected

    def _set_hidden_for_selected(self, hidden: bool) -> None:
        selected_ids = self._selected_entry_ids()
        for entry_id in selected_ids:
            self._sets.update_set_library_entry(entry_id, {"hidden_in_launcher": bool(hidden)})
        self._rebuild_list()

    def _remove_selected_entries(self) -> None:
        selected_ids = self._selected_entry_ids()
        for entry_id in selected_ids:
            self._sets.delete_set_library_entry(entry_id)
        self._rebuild_list()

    def _delete_selected_maya_sets(self) -> None:
        selected_ids = self._selected_entry_ids()
        if not selected_ids:
            return

        confirm = QtWidgets.QMessageBox.question(
            self,
            "Delete Maya Set",
            "Delete selected local Maya sets from scene?",
        )
        if confirm != QtWidgets.QMessageBox.Yes:
            return

        for entry_id in selected_ids:
            entry = self._entries.get(entry_id, {})
            set_name = str(entry.get("source_ref", ""))
            if not set_name:
                continue
            if bool(entry.get("is_referenced", False)):
                continue
            if self._sets.delete_set(set_name):
                self._sets.delete_set_library_entry(entry_id)

        self._rebuild_list()

    def _add_existing_local_sets(self) -> None:
        entries = self._sets.load_scene_set_library()
        existing_refs = {str(entry.get("source_ref", "")) for entry in entries.values() if isinstance(entry, dict)}

        local_scene_sets = [
            name
            for name in self._sets.list_scene_sets()
            if name not in existing_refs and not self._sets.is_referenced_set(name)
        ]

        dialog = _AddLocalSetsDialog(names=local_scene_sets, parent=self)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        for set_name in dialog.selected_set_names():
            color = self._sets.choose_balanced_color(include_gray=False)
            self._sets.register_set_library_entry(
                source_ref=set_name,
                source_kind="local_maya_set",
                display_label=self._display_label(set_name),
                color=color,
                hidden_in_launcher=False,
                is_referenced=False,
            )

        self._rebuild_list()

    def _display_label(self, full_set_name: str) -> str:
        short_name = str(full_set_name).split("|")[-1]
        return short_name.split(":")[-1]

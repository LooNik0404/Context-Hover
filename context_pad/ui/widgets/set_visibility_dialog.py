"""Lightweight visibility manager dialog for Set Hover."""

from __future__ import annotations

from context_pad.core.set_registry import SetRegistry
from context_pad.maya_integration.qt_helpers import QtCore, QtWidgets


class SetVisibilityDialog(QtWidgets.QDialog):
    """Small utility dialog to show/hide sets from Set Hover."""

    def __init__(self, registry: SetRegistry, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._sets = registry
        self._state = self._sets.refresh_scene_set_ui_state()
        self._is_populating = False

        self.setWindowTitle("Set Visibility")
        self.resize(460, 360)

        root = QtWidgets.QVBoxLayout(self)
        filter_row = QtWidgets.QHBoxLayout()
        self._show_visible = QtWidgets.QCheckBox("Visible")
        self._show_hidden = QtWidgets.QCheckBox("Hidden")
        self._show_local = QtWidgets.QCheckBox("Local")
        self._show_referenced = QtWidgets.QCheckBox("Referenced")
        for checkbox in [self._show_visible, self._show_hidden, self._show_local, self._show_referenced]:
            checkbox.setChecked(True)
            checkbox.toggled.connect(self._rebuild_list)
            filter_row.addWidget(checkbox)
        filter_row.addStretch(1)
        root.addLayout(filter_row)

        self._list = QtWidgets.QTreeWidget()
        self._list.setHeaderLabels(["Set", "State", "Source"])
        self._list.itemChanged.connect(self._on_item_changed)
        root.addWidget(self._list, 1)

        close_row = QtWidgets.QHBoxLayout()
        close_row.addStretch(1)
        btn_close = QtWidgets.QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        close_row.addWidget(btn_close)
        root.addLayout(close_row)

        self._rebuild_list()

    def _rebuild_list(self) -> None:
        self._is_populating = True
        self._state = self._sets.refresh_scene_set_ui_state()
        self._list.clear()

        for set_name in self._sets.list_scene_sets():
            meta = self._state.get(set_name, {})
            hidden = bool(meta.get("hidden_in_launcher", False))
            referenced = self._sets.is_referenced_set(set_name)
            if not self._passes_filters(hidden=hidden, referenced=referenced):
                continue

            item = QtWidgets.QTreeWidgetItem()
            item.setText(0, self._display_label(set_name))
            item.setText(1, "Hidden" if hidden else "Visible")
            item.setText(2, "Referenced" if referenced else "Local")
            item.setToolTip(0, set_name)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(0, QtCore.Qt.Unchecked if hidden else QtCore.Qt.Checked)
            item.setData(0, QtCore.Qt.UserRole, set_name)
            self._list.addTopLevelItem(item)

        self._list.resizeColumnToContents(0)
        self._is_populating = False

    def _on_item_changed(self, item: QtWidgets.QTreeWidgetItem, column: int) -> None:
        if self._is_populating or column != 0:
            return

        set_name = str(item.data(0, QtCore.Qt.UserRole) or "")
        if not set_name:
            return

        is_visible = item.checkState(0) == QtCore.Qt.Checked
        self._state.setdefault(set_name, {})
        self._state[set_name]["hidden_in_launcher"] = not is_visible
        self._sets.save_scene_set_ui_state(self._state)
        item.setText(1, "Visible" if is_visible else "Hidden")

    def _passes_filters(self, hidden: bool, referenced: bool) -> bool:
        if hidden and not self._show_hidden.isChecked():
            return False
        if not hidden and not self._show_visible.isChecked():
            return False
        if referenced and not self._show_referenced.isChecked():
            return False
        if not referenced and not self._show_local.isChecked():
            return False
        return True

    def _display_label(self, set_name: str) -> str:
        short_name = str(set_name).split("|")[-1]
        return short_name.split(":")[-1]

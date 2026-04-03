"""Manager window for editing script library and scene set launcher metadata."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from context_pad.core.app_state import AppState
from context_pad.core.script_library_editor import ScriptLibraryEditor
from context_pad.core.set_registry import SetRegistry
from context_pad.maya_integration.qt_helpers import QtCore, QtWidgets
from context_pad.ui.widgets.color_picker import ColorPicker


class ManagerWindow(QtWidgets.QMainWindow):
    """Main manager window for Context Pad configuration."""

    def __init__(self, app_state: AppState, parent: QtWidgets.QWidget | None = None) -> None:
        """Initialize manager window and editor widgets."""

        super().__init__(parent)
        self._app_state = app_state
        self._editor = ScriptLibraryEditor()
        self._sets = SetRegistry()
        self._active_button_id: Optional[str] = None

        self.setWindowTitle("Context Pad Manager")
        self.resize(980, 680)

        container = QtWidgets.QWidget(self)
        self.setCentralWidget(container)
        root = QtWidgets.QVBoxLayout(container)

        self._status = QtWidgets.QLabel("Ready")

        root.addWidget(self._build_script_section(), 2)
        root.addWidget(self._build_set_section(), 1)
        root.addWidget(self._status)

        self._refresh_all()

    def _build_script_section(self) -> QtWidgets.QWidget:
        """Build script categories/buttons edit section."""

        box = QtWidgets.QGroupBox("Scripts")
        layout = QtWidgets.QHBoxLayout(box)

        # Categories panel
        cat_panel = QtWidgets.QVBoxLayout()
        self._category_list = QtWidgets.QListWidget()
        self._category_list.currentItemChanged.connect(self._on_category_changed)
        cat_panel.addWidget(QtWidgets.QLabel("Script Categories"))
        cat_panel.addWidget(self._category_list)

        cat_buttons = QtWidgets.QHBoxLayout()
        btn_cat_add = QtWidgets.QPushButton("Add")
        btn_cat_rename = QtWidgets.QPushButton("Rename")
        btn_cat_delete = QtWidgets.QPushButton("Delete")
        btn_cat_up = QtWidgets.QPushButton("↑")
        btn_cat_down = QtWidgets.QPushButton("↓")
        btn_cat_add.clicked.connect(self._add_category)
        btn_cat_rename.clicked.connect(self._rename_category)
        btn_cat_delete.clicked.connect(self._delete_category)
        btn_cat_up.clicked.connect(lambda: self._move_category(-1))
        btn_cat_down.clicked.connect(lambda: self._move_category(1))
        for widget in [btn_cat_add, btn_cat_rename, btn_cat_delete, btn_cat_up, btn_cat_down]:
            cat_buttons.addWidget(widget)
        cat_panel.addLayout(cat_buttons)

        # Buttons panel
        btn_panel = QtWidgets.QVBoxLayout()
        self._button_list = QtWidgets.QListWidget()
        self._button_list.currentItemChanged.connect(self._on_button_changed)
        btn_panel.addWidget(QtWidgets.QLabel("Script Buttons"))
        btn_panel.addWidget(self._button_list)

        btn_controls = QtWidgets.QHBoxLayout()
        btn_add = QtWidgets.QPushButton("Add")
        btn_delete = QtWidgets.QPushButton("Delete")
        btn_up = QtWidgets.QPushButton("↑")
        btn_down = QtWidgets.QPushButton("↓")
        btn_add.clicked.connect(self._add_button)
        btn_delete.clicked.connect(self._delete_button)
        btn_up.clicked.connect(lambda: self._move_button(-1))
        btn_down.clicked.connect(lambda: self._move_button(1))
        for widget in [btn_add, btn_delete, btn_up, btn_down]:
            btn_controls.addWidget(widget)
        btn_panel.addLayout(btn_controls)

        # Edit form
        form_panel = QtWidgets.QFormLayout()
        self._field_label = QtWidgets.QLineEdit()
        self._field_tooltip = QtWidgets.QLineEdit()
        self._field_source = QtWidgets.QLineEdit()
        self._field_lang = QtWidgets.QComboBox()
        self._field_lang.addItems(["python_inline", "python_file", "mel_inline", "mel_file"])
        self._field_color = ColorPicker()

        btn_apply = QtWidgets.QPushButton("Apply Button Changes")
        btn_save = QtWidgets.QPushButton("Save Manifest")
        btn_reload = QtWidgets.QPushButton("Reload Manifest")
        btn_apply.clicked.connect(self._apply_button_changes)
        btn_save.clicked.connect(self._save_manifest)
        btn_reload.clicked.connect(self._reload_manifest)

        form_panel.addRow("Label", self._field_label)
        form_panel.addRow("Tooltip", self._field_tooltip)
        form_panel.addRow("Action Type", self._field_lang)
        form_panel.addRow("Source (code/file)", self._field_source)
        form_panel.addRow("Color", self._field_color)
        form_panel.addRow(btn_apply)
        form_panel.addRow(btn_save, btn_reload)

        layout.addLayout(cat_panel, 1)
        layout.addLayout(btn_panel, 1)
        layout.addLayout(form_panel, 1)
        return box

    def _build_set_section(self) -> QtWidgets.QWidget:
        """Build scene set overview and metadata edit controls."""

        box = QtWidgets.QGroupBox("Scene Sets")
        layout = QtWidgets.QVBoxLayout(box)

        self._set_list = QtWidgets.QListWidget()
        self._set_list.currentItemChanged.connect(self._on_set_changed)
        layout.addWidget(self._set_list)

        form = QtWidgets.QFormLayout()
        self._set_order = QtWidgets.QSpinBox()
        self._set_order.setRange(0, 99999)
        self._set_group = QtWidgets.QLineEdit()
        self._set_hidden = QtWidgets.QCheckBox("Hidden in launcher")
        self._set_color = ColorPicker()

        form.addRow("Display order", self._set_order)
        form.addRow("Group", self._set_group)
        form.addRow("Color", self._set_color)
        form.addRow(self._set_hidden)

        btn_row = QtWidgets.QHBoxLayout()
        btn_refresh = QtWidgets.QPushButton("Refresh Sets")
        btn_apply = QtWidgets.QPushButton("Apply Set Metadata")
        btn_refresh.clicked.connect(self._refresh_sets)
        btn_apply.clicked.connect(self._apply_set_metadata)
        btn_row.addWidget(btn_refresh)
        btn_row.addWidget(btn_apply)

        layout.addLayout(form)
        layout.addLayout(btn_row)
        return box

    def _refresh_all(self) -> None:
        """Refresh categories, buttons, and sets from services."""

        self._editor.reload()
        self._refresh_categories()
        self._refresh_buttons()
        self._refresh_sets()

    def _refresh_categories(self) -> None:
        """Reload category list UI."""

        self._category_list.clear()
        for item in self._editor.categories():
            row = QtWidgets.QListWidgetItem(f"{item['label']} ({item['id']})")
            row.setData(QtCore.Qt.UserRole, item["id"])
            self._category_list.addItem(row)

    def _refresh_buttons(self) -> None:
        """Reload button list UI filtered by current category."""

        self._button_list.clear()
        category_id = self._current_category_id()
        for item in self._editor.buttons():
            if category_id and item.get("category_id") != category_id:
                continue
            row = QtWidgets.QListWidgetItem(f"{item['label']} ({item['action_type']})")
            row.setData(QtCore.Qt.UserRole, item["id"])
            self._button_list.addItem(row)

    def _refresh_sets(self) -> None:
        """Reload scene sets and metadata list."""

        self._set_list.clear()
        state = self._sets.refresh_scene_set_ui_state()
        for set_name in self._sets.list_scene_sets():
            meta = state.get(set_name, {})
            row = QtWidgets.QListWidgetItem(
                f"{set_name} | order:{meta.get('display_order', 1000)} | group:{meta.get('group', 'Default')}"
            )
            row.setData(QtCore.Qt.UserRole, set_name)
            self._set_list.addItem(row)

    def _current_category_id(self) -> str:
        """Return selected category id or empty string."""

        item = self._category_list.currentItem()
        return str(item.data(QtCore.Qt.UserRole)) if item else ""

    def _current_button_id(self) -> str:
        """Return selected button id or empty string."""

        item = self._button_list.currentItem()
        return str(item.data(QtCore.Qt.UserRole)) if item else ""

    def _on_category_changed(self, *_: Any) -> None:
        """Handle category selection changes."""

        self._refresh_buttons()

    def _on_button_changed(self, *_: Any) -> None:
        """Populate button form from selected button."""

        button_id = self._current_button_id()
        self._active_button_id = button_id or None
        item = next((b for b in self._editor.buttons() if b.get("id") == button_id), None)
        if not item:
            return

        self._field_label.setText(item.get("label", ""))
        self._field_tooltip.setText(item.get("tooltip", ""))
        self._field_source.setText(item.get("source", ""))
        self._field_lang.setCurrentText(item.get("action_type", "python_inline"))
        self._field_color.set_color(item.get("color", "#6B7280"))

    def _on_set_changed(self, *_: Any) -> None:
        """Populate set metadata form from selected set."""

        item = self._set_list.currentItem()
        if not item:
            return

        set_name = str(item.data(QtCore.Qt.UserRole))
        state = self._sets.refresh_scene_set_ui_state().get(set_name, {})
        self._set_order.setValue(int(state.get("display_order", 1000)))
        self._set_group.setText(str(state.get("group", "Default")))
        self._set_color.set_color(str(state.get("button_color", "#6B7280")))
        self._set_hidden.setChecked(bool(state.get("hidden_state", False)))

    def _add_category(self) -> None:
        """Add a new category from input dialog."""

        text, ok = QtWidgets.QInputDialog.getText(self, "Add Category", "Category name")
        if not ok or not text.strip():
            return
        self._editor.add_category(text.strip())
        self._refresh_categories()

    def _rename_category(self) -> None:
        """Rename selected category."""

        category_id = self._current_category_id()
        if not category_id:
            return
        text, ok = QtWidgets.QInputDialog.getText(self, "Rename Category", "New category name")
        if not ok or not text.strip():
            return
        self._editor.rename_category(category_id, text.strip())
        self._refresh_categories()

    def _delete_category(self) -> None:
        """Delete selected category and linked buttons."""

        category_id = self._current_category_id()
        if not category_id:
            return
        self._editor.delete_category(category_id)
        self._refresh_categories()
        self._refresh_buttons()

    def _move_category(self, direction: int) -> None:
        """Move selected category up or down."""

        category_id = self._current_category_id()
        if not category_id:
            return
        self._editor.move_category(category_id, direction)
        self._refresh_categories()

    def _add_button(self) -> None:
        """Add a button using current form values."""

        category_id = self._current_category_id()
        if not category_id:
            self._status.setText("Select a category first")
            return

        self._editor.add_button(
            {
                "label": self._field_label.text().strip() or "New Button",
                "tooltip": self._field_tooltip.text().strip(),
                "action_type": self._field_lang.currentText(),
                "source": self._field_source.text(),
                "color": self._field_color.color(),
                "category_id": category_id,
            }
        )
        self._refresh_buttons()

    def _apply_button_changes(self) -> None:
        """Apply edits to currently selected button."""

        if not self._active_button_id:
            self._status.setText("Select a button to edit")
            return

        ok = self._editor.update_button(
            self._active_button_id,
            {
                "label": self._field_label.text().strip(),
                "tooltip": self._field_tooltip.text().strip(),
                "action_type": self._field_lang.currentText(),
                "source": self._field_source.text(),
                "color": self._field_color.color(),
            },
        )
        if ok:
            self._status.setText("Button updated")
            self._refresh_buttons()

    def _delete_button(self) -> None:
        """Delete currently selected button."""

        button_id = self._current_button_id()
        if not button_id:
            return
        self._editor.delete_button(button_id)
        self._refresh_buttons()

    def _move_button(self, direction: int) -> None:
        """Move selected button up or down."""

        button_id = self._current_button_id()
        if not button_id:
            return
        self._editor.move_button(button_id, direction)
        self._refresh_buttons()

    def _save_manifest(self) -> None:
        """Validate and save manifest edits to disk."""

        try:
            self._editor.save()
            self._status.setText("Manifest saved")
        except Exception as exc:
            self._status.setText(f"Save failed: {exc}")

    def _reload_manifest(self) -> None:
        """Reload manifest from disk and refresh lists."""

        self._refresh_all()
        self._status.setText("Manifest reloaded")

    def _apply_set_metadata(self) -> None:
        """Apply metadata form values to selected scene set."""

        item = self._set_list.currentItem()
        if not item:
            self._status.setText("Select a scene set first")
            return

        set_name = str(item.data(QtCore.Qt.UserRole))
        state = self._sets.refresh_scene_set_ui_state()
        state.setdefault(set_name, {})
        state[set_name].update(
            {
                "display_order": self._set_order.value(),
                "button_color": self._set_color.color(),
                "group": self._set_group.text().strip() or "Default",
                "hidden_state": self._set_hidden.isChecked(),
            }
        )
        self._sets.save_scene_set_ui_state(state)
        self._refresh_sets()
        self._status.setText(f"Set metadata updated: {set_name}")

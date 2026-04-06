"""Manager window for editing script buttons in a Maya-friendly workflow."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from context_pad.core.app_state import AppState
from context_pad.core.script_library_editor import ScriptLibraryEditor
from context_pad.maya_integration.qt_helpers import QtCore, QtGui, QtWidgets
from context_pad.ui.styles import manager_stylesheet
from context_pad.ui.widgets.color_picker import ColorPicker


class ManagerWindow(QtWidgets.QMainWindow):
    """Two-tab manager focused on script button setup and code editing."""

    def __init__(self, app_state: AppState, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._app_state = app_state
        self._editor = ScriptLibraryEditor()
        self._active_button_id: Optional[str] = None
        self._is_syncing_properties = False

        self.setWindowTitle("Context Pad Library Manager")
        self.resize(1020, 720)
        self.setStyleSheet(manager_stylesheet())

        container = QtWidgets.QWidget(self)
        self.setCentralWidget(container)
        root = QtWidgets.QVBoxLayout(container)

        self._tabs = QtWidgets.QTabWidget()
        self._tabs.addTab(self._build_button_setup_tab(), "Button Setup")
        self._tabs.addTab(self._build_code_editor_tab(), "Code Editor")
        self._tabs.currentChanged.connect(self._update_shared_actions_state)

        self._status = QtWidgets.QLabel("Ready")
        shared_actions = self._build_shared_action_bar()

        root.addWidget(self._tabs)
        root.addWidget(shared_actions)
        root.addWidget(self._status)

        self._refresh_all()

    def _build_button_setup_tab(self) -> QtWidgets.QWidget:
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(tab)
        layout.setSpacing(12)

        layout.addWidget(self._build_categories_panel(), 1)
        layout.addWidget(self._build_buttons_panel(), 1)
        layout.addWidget(self._build_basic_properties_panel(), 1)
        return tab

    def _build_categories_panel(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QGroupBox("Categories")
        layout = QtWidgets.QVBoxLayout(panel)

        self._category_list = QtWidgets.QListWidget()
        self._category_list.currentItemChanged.connect(self._on_category_changed)
        layout.addWidget(self._category_list)

        toolbar = QtWidgets.QHBoxLayout()
        toolbar.setSpacing(6)
        btn_add = QtWidgets.QPushButton("Add")
        btn_rename = QtWidgets.QPushButton("Rename")
        btn_delete = QtWidgets.QPushButton("Delete")
        btn_up = QtWidgets.QPushButton("Move Up")
        btn_down = QtWidgets.QPushButton("Move Down")

        btn_add.clicked.connect(self._add_category)
        btn_rename.clicked.connect(self._rename_category)
        btn_delete.clicked.connect(self._delete_category)
        btn_up.clicked.connect(lambda: self._move_category(-1))
        btn_down.clicked.connect(lambda: self._move_category(1))

        for widget in [btn_add, btn_rename, btn_delete, btn_up, btn_down]:
            toolbar.addWidget(widget)
        layout.addLayout(toolbar)
        return panel

    def _build_buttons_panel(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QGroupBox("Buttons")
        layout = QtWidgets.QVBoxLayout(panel)

        self._button_list = QtWidgets.QListWidget()
        self._button_list.currentItemChanged.connect(self._on_button_changed)
        layout.addWidget(self._button_list)

        toolbar = QtWidgets.QHBoxLayout()
        toolbar.setSpacing(6)
        btn_add = QtWidgets.QPushButton("Add")
        btn_add_separator = QtWidgets.QPushButton("Add Separator")
        btn_rename = QtWidgets.QPushButton("Rename")
        btn_delete = QtWidgets.QPushButton("Delete")
        btn_up = QtWidgets.QPushButton("Move Up")
        btn_down = QtWidgets.QPushButton("Move Down")

        btn_add.clicked.connect(self._add_button)
        btn_add_separator.clicked.connect(self._add_separator)
        btn_rename.clicked.connect(self._rename_button)
        btn_delete.clicked.connect(self._delete_button)
        btn_up.clicked.connect(lambda: self._move_button(-1))
        btn_down.clicked.connect(lambda: self._move_button(1))

        for widget in [btn_add, btn_add_separator, btn_rename, btn_delete, btn_up, btn_down]:
            toolbar.addWidget(widget)
        layout.addLayout(toolbar)
        return panel

    def _build_basic_properties_panel(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QGroupBox("Basic Button Properties")
        form = QtWidgets.QFormLayout(panel)

        self._prop_name = QtWidgets.QLineEdit()
        self._prop_category = QtWidgets.QComboBox()
        self._prop_color = ColorPicker()
        self._prop_size = QtWidgets.QComboBox()
        self._prop_size.addItems(["Normal", "Small"])

        self._prop_name.editingFinished.connect(self._on_property_edited)
        self._prop_category.currentIndexChanged.connect(self._on_property_edited)
        self._prop_size.currentIndexChanged.connect(self._on_property_edited)
        self._prop_color.color_changed.connect(self._on_property_edited)

        form.addRow("Button Name", self._prop_name)
        form.addRow("Category", self._prop_category)
        form.addRow("Size", self._prop_size)
        form.addRow("Color", self._prop_color)
        return panel

    def _build_code_editor_tab(self) -> QtWidgets.QWidget:
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)

        header = QtWidgets.QHBoxLayout()
        self._selection_label = QtWidgets.QLabel("Select a button in Button Setup")
        self._selection_swatch = QtWidgets.QLabel()
        self._selection_swatch.setFixedSize(16, 16)
        self._selection_swatch.setStyleSheet("background:#6B7280; border:1px solid rgba(255,255,255,70); border-radius:3px;")
        header.addWidget(QtWidgets.QLabel("Current Selection:"))
        header.addWidget(self._selection_label, 1)
        header.addWidget(self._selection_swatch)
        layout.addLayout(header)

        language_row = QtWidgets.QHBoxLayout()
        self._code_language = QtWidgets.QComboBox()
        self._code_language.addItems(["Python", "MEL"])
        language_row.addWidget(QtWidgets.QLabel("Language"))
        language_row.addWidget(self._code_language)
        language_row.addStretch(1)
        layout.addLayout(language_row)

        self._code_editor = QtWidgets.QPlainTextEdit()
        self._code_editor.setPlaceholderText("Write script code here...")
        layout.addWidget(self._code_editor, 1)

        tooltip_row = QtWidgets.QFormLayout()
        self._code_tooltip = QtWidgets.QLineEdit()
        tooltip_row.addRow("Tooltip", self._code_tooltip)
        layout.addLayout(tooltip_row)

        hint = QtWidgets.QLabel(
            "Scene set creation and set maintenance stay in the Set Launcher hover UI."
        )
        hint.setStyleSheet("color: rgba(230,230,230,170);")
        layout.addWidget(hint)
        return tab

    def _build_shared_action_bar(self) -> QtWidgets.QWidget:
        """Shared manager action bar visible from both tabs."""

        bar = QtWidgets.QFrame()
        layout = QtWidgets.QHBoxLayout(bar)
        layout.setContentsMargins(0, 4, 0, 2)
        layout.setSpacing(6)

        self._btn_apply_code = QtWidgets.QPushButton("Apply Code")
        self._btn_save_library = QtWidgets.QPushButton("Save Library")
        self._btn_reload_library = QtWidgets.QPushButton("Reload Library")

        self._btn_apply_code.clicked.connect(self._apply_button_changes)
        self._btn_save_library.clicked.connect(self._save_library)
        self._btn_reload_library.clicked.connect(self._reload_library)

        layout.addWidget(self._btn_apply_code)
        layout.addStretch(1)
        layout.addWidget(self._btn_save_library)
        layout.addWidget(self._btn_reload_library)
        return bar


    def open_button_setup_tab(self) -> None:
        """Switch manager to Button Setup tab."""

        self._tabs.setCurrentIndex(0)

    def start_quick_add_button(self) -> None:
        """Start quick add button flow from external launcher actions."""

        self.open_button_setup_tab()
        if not self._current_category_id():
            if self._category_list.count() > 0:
                self._category_list.setCurrentRow(0)
        self._add_button()

    def _refresh_all(self) -> None:
        self._editor.reload()
        self._refresh_categories()
        self._refresh_category_dropdown()
        self._refresh_buttons()
        self._sync_selection_views()
        self._update_shared_actions_state()

    def _refresh_categories(self) -> None:
        selected = self._current_category_id()
        self._category_list.clear()
        for item in self._editor.categories():
            row = QtWidgets.QListWidgetItem(item["label"])
            row.setData(QtCore.Qt.UserRole, item["id"])
            self._category_list.addItem(row)
            if selected and item["id"] == selected:
                self._category_list.setCurrentItem(row)
        if self._category_list.count() and not self._category_list.currentItem():
            self._category_list.setCurrentRow(0)

    def _refresh_category_dropdown(self) -> None:
        selected_category_id = self._current_category_id()
        self._prop_category.blockSignals(True)
        self._prop_category.clear()
        for item in self._editor.categories():
            self._prop_category.addItem(item["label"], item["id"])
            if item["id"] == selected_category_id:
                self._prop_category.setCurrentIndex(self._prop_category.count() - 1)
        self._prop_category.blockSignals(False)

    def _refresh_buttons(self) -> None:
        selected_button = self._active_button_id
        self._button_list.clear()
        for item in self._buttons_for_current_category():
            item_type = str(item.get("item_type", "button"))
            label = str(item.get("label", "Unnamed"))
            if item_type == "separator":
                label = f"── {label or 'Separator'}"
            row = QtWidgets.QListWidgetItem(label)
            row.setData(QtCore.Qt.UserRole, item.get("id", ""))
            row.setIcon(self._make_color_icon(str(item.get("color", "#6B7280"))))
            self._button_list.addItem(row)
            if selected_button and item.get("id") == selected_button:
                self._button_list.setCurrentItem(row)

        if self._button_list.count() and not self._button_list.currentItem():
            self._button_list.setCurrentRow(0)
        elif self._button_list.count() == 0:
            self._active_button_id = None

    def _buttons_for_current_category(self) -> List[Dict[str, Any]]:
        category_id = self._current_category_id()
        return [item for item in self._editor.buttons() if item.get("category_id") == category_id]

    def _current_category_id(self) -> str:
        item = self._category_list.currentItem()
        return str(item.data(QtCore.Qt.UserRole)) if item else ""

    def _current_button_id(self) -> str:
        item = self._button_list.currentItem()
        return str(item.data(QtCore.Qt.UserRole)) if item else ""

    def _selected_button(self) -> Optional[Dict[str, Any]]:
        button_id = self._active_button_id or self._current_button_id()
        if not button_id:
            return None
        return next((item for item in self._editor.buttons() if item.get("id") == button_id), None)

    def _category_label(self, category_id: str) -> str:
        category = next((item for item in self._editor.categories() if item.get("id") == category_id), None)
        return category.get("label", "Unknown") if category else "Unknown"

    def _sync_selection_views(self) -> None:
        self._is_syncing_properties = True
        button = self._selected_button()
        has_selection = button is not None
        is_separator = bool(button and str(button.get("item_type", "button")) == "separator")

        self._prop_name.setEnabled(has_selection)
        self._prop_category.setEnabled(has_selection)
        self._prop_size.setEnabled(has_selection and not is_separator)
        self._prop_color.setEnabled(has_selection and not is_separator)
        self._code_language.setEnabled(has_selection and not is_separator)
        self._code_editor.setEnabled(has_selection and not is_separator)
        self._code_tooltip.setEnabled(has_selection and not is_separator)

        if not button:
            self._prop_name.clear()
            self._code_editor.clear()
            self._code_tooltip.clear()
            self._selection_label.setText("Select a button in Button Setup")
            self._selection_swatch.setStyleSheet(
                "background:#6B7280; border:1px solid rgba(255,255,255,70); border-radius:3px;"
            )
            self._is_syncing_properties = False
            self._update_shared_actions_state()
            return

        label = button.get("label", "Unnamed")
        category_id = button.get("category_id", "")
        category_label = self._category_label(category_id)
        color = button.get("color", "#6B7280")
        action_type = button.get("action_type", "python_inline")
        button_size = str(button.get("button_size", "normal")).lower()

        self._prop_name.setText(label)
        self._prop_color.set_color(color)
        self._prop_category.setCurrentIndex(max(0, self._prop_category.findData(category_id)))
        self._prop_size.setCurrentText("Small" if button_size == "small" else "Normal")

        self._selection_label.setText(f"{category_label} > {label}")
        self._selection_swatch.setStyleSheet(
            f"background:{color}; border:1px solid rgba(255,255,255,70); border-radius:3px;"
        )

        if is_separator:
            self._code_language.setCurrentText("Python")
            self._code_editor.setPlainText("")
            self._code_tooltip.setText("")
            self._is_syncing_properties = False
            self._update_shared_actions_state()
            return

        self._code_language.setCurrentText("Python" if action_type.startswith("python") else "MEL")
        source_value = button.get("source", "")
        if action_type.endswith("file"):
            from pathlib import Path

            file_path = Path(str(source_value)).expanduser()
            if file_path.exists() and file_path.is_file():
                try:
                    source_value = file_path.read_text(encoding="utf-8")
                    self._status.setText("Loaded file-based button source into editor. Apply converts it to inline mode.")
                except Exception:
                    source_value = f"# Could not read file: {file_path}"
            else:
                source_value = f"# Missing file path: {file_path}\n# Replace with inline script and click Apply."
                self._status.setText("File-based button path is missing. Apply to convert to inline mode.")

        self._code_editor.setPlainText(str(source_value))
        self._code_tooltip.setText(button.get("tooltip", ""))
        self._is_syncing_properties = False
        self._update_shared_actions_state()

    def _on_property_edited(self, *_: Any) -> None:
        """Auto-apply basic setup properties when changed by user."""

        if self._is_syncing_properties:
            return
        self._apply_properties()

    def _update_shared_actions_state(self) -> None:
        button = self._selected_button()
        is_code_tab = self._tabs.currentIndex() == 1
        is_button = bool(button and str(button.get("item_type", "button")) != "separator")
        self._btn_apply_code.setEnabled(bool(is_code_tab and is_button))

    def _on_category_changed(self, *_: Any) -> None:
        self._refresh_buttons()
        self._refresh_category_dropdown()
        self._sync_selection_views()

    def _on_button_changed(self, *_: Any) -> None:
        self._active_button_id = self._current_button_id() or None
        self._sync_selection_views()

    def _make_color_icon(self, color: str) -> QtGui.QIcon:
        """Build a compact color dot icon for button-list overview."""

        pixmap = QtGui.QPixmap(12, 12)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 110), 1))
        painter.setBrush(QtGui.QColor(color))
        painter.drawEllipse(1, 1, 10, 10)
        painter.end()
        return QtGui.QIcon(pixmap)

    def _add_category(self) -> None:
        text, ok = QtWidgets.QInputDialog.getText(self, "Add Category", "Category name")
        if not ok or not text.strip():
            return
        self._editor.add_category(text.strip())
        self._refresh_categories()
        self._refresh_category_dropdown()
        self._status.setText("Category added")

    def _rename_category(self) -> None:
        category_id = self._current_category_id()
        if not category_id:
            return
        text, ok = QtWidgets.QInputDialog.getText(self, "Rename Category", "New category name")
        if not ok or not text.strip():
            return
        self._editor.rename_category(category_id, text.strip())
        self._refresh_categories()
        self._refresh_category_dropdown()
        self._sync_selection_views()
        self._status.setText("Category renamed")

    def _delete_category(self) -> None:
        category_id = self._current_category_id()
        if not category_id:
            return
        self._editor.delete_category(category_id)
        self._refresh_categories()
        self._refresh_category_dropdown()
        self._refresh_buttons()
        self._sync_selection_views()
        self._status.setText("Category deleted")

    def _move_category(self, direction: int) -> None:
        category_id = self._current_category_id()
        if not category_id:
            return
        self._editor.move_category(category_id, direction)
        self._refresh_categories()
        self._refresh_category_dropdown()
        self._status.setText("Category moved")

    def _add_button(self) -> None:
        category_id = self._current_category_id()
        if not category_id:
            self._status.setText("Select a category first")
            return

        label, ok = QtWidgets.QInputDialog.getText(self, "Add Button", "Button name")
        if not ok:
            return
        self._editor.add_button(
            {
                "label": label.strip() or "New Button",
                "category_id": category_id,
                "color": "#6B7280",
                "action_type": "python_inline",
                "source": "",
                "tooltip": "",
                "item_type": "button",
                "button_size": "normal",
            }
        )
        self._refresh_buttons()
        self._active_button_id = self._current_button_id() or self._active_button_id
        self._sync_selection_views()
        self._status.setText("Button added")

    def _add_separator(self) -> None:
        """Create a non-executable visual separator item in current category."""

        category_id = self._current_category_id()
        if not category_id:
            self._status.setText("Select a category first")
            return

        label, ok = QtWidgets.QInputDialog.getText(self, "Add Separator", "Separator label")
        if not ok:
            return

        self._editor.add_button(
            {
                "label": label.strip() or "Separator",
                "category_id": category_id,
                "color": "#6B7280",
                "action_type": "separator",
                "source": "",
                "tooltip": "",
                "item_type": "separator",
                "button_size": "normal",
            }
        )
        self._refresh_buttons()
        self._active_button_id = self._current_button_id() or self._active_button_id
        self._sync_selection_views()
        self._status.setText("Separator added")

    def _rename_button(self) -> None:
        button = self._selected_button()
        if not button:
            return
        text, ok = QtWidgets.QInputDialog.getText(self, "Rename Button", "New button name", text=button.get("label", ""))
        if not ok or not text.strip():
            return
        self._editor.update_button(button["id"], {"label": text.strip()})
        self._refresh_buttons()
        self._sync_selection_views()
        self._status.setText("Button renamed")

    def _delete_button(self) -> None:
        button_id = self._current_button_id()
        if not button_id:
            return
        self._editor.delete_button(button_id)
        self._active_button_id = None
        self._refresh_buttons()
        self._sync_selection_views()
        self._status.setText("Button deleted")

    def _move_button(self, direction: int) -> None:
        button_id = self._current_button_id()
        category_id = self._current_category_id()
        if not button_id or not category_id:
            return
        self._editor.move_button(button_id, direction, category_id=category_id)
        self._refresh_buttons()
        self._status.setText("Button moved")

    def _apply_properties(self) -> None:
        button = self._selected_button()
        if not button:
            self._status.setText("Select a button first")
            return

        category_id = str(self._prop_category.currentData() or button.get("category_id", ""))
        item_type = str(button.get("item_type", "button"))
        payload = {"label": self._prop_name.text().strip() or button.get("label", "Button"), "category_id": category_id}
        if item_type == "separator":
            payload["item_type"] = "separator"
            payload["action_type"] = "separator"
            payload["button_size"] = "normal"
            payload["source"] = ""
            payload["tooltip"] = ""
        else:
            size_mode = "small" if self._prop_size.currentText() == "Small" else "normal"
            payload["item_type"] = "button"
            payload["color"] = self._prop_color.color()
            payload["button_size"] = size_mode
        self._editor.update_button(button["id"], payload)
        self._refresh_buttons()
        self._sync_selection_views()
        self._status.setText("Properties applied")

    def _apply_button_changes(self) -> None:
        button = self._selected_button()
        if not button:
            self._status.setText("Select a button in Button Setup")
            return

        if str(button.get("item_type", "button")) == "separator":
            payload = {
                "label": self._prop_name.text().strip() or button.get("label", "Separator"),
                "category_id": str(self._prop_category.currentData() or button.get("category_id", "")),
                "action_type": "separator",
                "source": "",
                "tooltip": "",
                "item_type": "separator",
                "button_size": "normal",
            }
            self._editor.update_button(button["id"], payload)
            self._refresh_buttons()
            self._sync_selection_views()
            self._status.setText("Separator updated")
            return

        language = self._code_language.currentText()
        action_type = "python_inline" if language == "Python" else "mel_inline"
        size_mode = "small" if self._prop_size.currentText() == "Small" else "normal"
        payload = {
            "label": self._prop_name.text().strip() or button.get("label", "Button"),
            "category_id": str(self._prop_category.currentData() or button.get("category_id", "")),
            "color": self._prop_color.color(),
            "tooltip": self._code_tooltip.text().strip(),
            "action_type": action_type,
            "source": self._code_editor.toPlainText(),
            "item_type": "button",
            "button_size": size_mode,
        }
        self._editor.update_button(button["id"], payload)
        self._refresh_buttons()
        self._sync_selection_views()
        self._status.setText("Button updated")

    def _save_library(self) -> None:
        try:
            self._editor.save()
            from context_pad.bootstrap import refresh_script_launcher

            refresh_script_launcher()
            self._status.setText("Library saved")
        except Exception as exc:
            self._status.setText(f"Save failed: {exc}")

    def _reload_library(self) -> None:
        self._refresh_all()
        try:
            from context_pad.bootstrap import refresh_script_launcher

            refresh_script_launcher()
        except Exception:
            pass
        self._status.setText("Library reloaded")

"""Selection set overlay launcher widget with contextual related sets."""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Tuple

from context_pad.core.set_registry import SetRegistry
from context_pad.maya_integration.qt_helpers import QtCore, QtWidgets

from .launcher_base import LauncherBase
from .widgets.related_sets import RelatedSetsList
from .widgets.set_visibility_dialog import SetVisibilityDialog


class SetLauncher(LauncherBase):
    """Overlay launcher for fast scene-set operations."""

    _RELATED_LIMIT = 7
    _SET_COLORS: List[Tuple[str, str]] = [
        ("Steel Blue", "#5D82A8"),
        ("Olive Green", "#6E8F66"),
        ("Muted Purple", "#7A70A3"),
        ("Sky Blue", "#4A90E2"),
        ("Moss Green", "#7EA178"),
        ("Lavender", "#887CB0"),
        ("Amber", "#D9822B"),
        ("Slate Gray", "#6B7280"),
    ]

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle("Context Pad - Sets")
        self.set_button_columns(2)

        self._sets = SetRegistry()
        self._related_widget = RelatedSetsList()
        self._related_widget.related_selected.connect(self._select_set_from_related)
        self.set_left_widget(self._related_widget)
        self.set_manager_button_visible(True)
        self.set_manager_button_text("◉")

        self._last_selection: List[str] = []
        self._watch_timer = QtCore.QTimer(self)
        self._watch_timer.setInterval(300)
        self._watch_timer.timeout.connect(self._refresh_related_if_selection_changed)
        self._context_menu_active = False

        self._command_grid.button_clicked.connect(self._on_set_clicked)
        self._command_grid.button_context_requested.connect(self._open_set_context_menu)

        self.refresh_from_scene()

    def refresh_from_scene(self) -> None:
        """Refresh all and related sets from scene data."""

        state = self._sets.refresh_scene_set_ui_state()
        all_sets = self._build_all_sets(state)
        related = self._build_related_sets(state)

        self.set_buttons(all_sets)
        self._related_widget.set_related_sets(related)
        self._last_selection = self._sets.get_current_selection()

    def on_add_requested(self) -> None:
        """Create a set quickly from current selection."""

        current = self._sets.get_current_selection()
        if not current:
            self._toast("Select objects first to create a set")
            return

        default_name = self._suggest_set_name()
        self._context_menu_active = True
        name, ok = QtWidgets.QInputDialog.getText(self, "Create Set", "Set name", text=default_name)
        self._context_menu_active = False
        if not ok or not name.strip():
            return

        raw_name = name.strip()
        new_name = self._sets.sanitize_set_name(raw_name)
        if new_name != raw_name:
            self._toast(f"Adjusted set name: {raw_name} → {new_name}")
            self._log_warning(f"Adjusted set name '{raw_name}' to '{new_name}' for Maya compatibility")
        if self._sets.create_set_from_selection(new_name):
            state = self._sets.refresh_scene_set_ui_state()
            state.setdefault(new_name, {})
            state[new_name]["button_color"] = self._choose_new_set_color(state)
            self._sets.save_scene_set_ui_state(state)
            self.refresh_from_scene()
            self._toast(f"Created set: {new_name}")
        else:
            self._toast("Could not create set")

    def on_manager_requested(self) -> None:
        """Open compact visibility manager dialog for set show/hide."""

        dialog = SetVisibilityDialog(registry=self._sets, parent=self)
        dialog.exec_()
        self.refresh_from_scene()

    def set_pinned(self, state: bool) -> None:
        """Toggle pin state and selection watch behavior."""

        super().set_pinned(state)
        if state and self.isVisible():
            self._start_selection_watch()
        else:
            self._stop_selection_watch()

    def show_at_cursor(self) -> None:
        """Show launcher and refresh scene data each time."""

        self.refresh_from_scene()
        super().show_at_cursor()
        if self._is_pinned:
            self._start_selection_watch()

    def closeEvent(self, event) -> None:  # noqa: N802
        """Ensure selection watch is fully stopped when closing."""

        self._stop_selection_watch()
        super().closeEvent(event)

    def focusOutEvent(self, event) -> None:  # noqa: N802
        """Keep launcher open while RMB menu/dialog interactions are active."""

        if self._context_menu_active:
            event.accept()
            return
        super().focusOutEvent(event)

    def _build_all_sets(self, state: Dict[str, dict]) -> List[Dict[str, str]]:
        """Build full set list respecting hidden/order/group metadata."""

        records: List[Dict[str, str]] = []
        for set_name in self._sets.list_scene_sets():
            meta = state.get(set_name, {})
            if bool(meta.get("hidden_in_launcher", False)):
                continue
            group = str(meta.get("group", "Main"))
            records.append(
                {
                    "id": set_name,
                    "name": set_name,
                    "category_id": group,
                    "color": str(meta.get("button_color", "#6B7280")),
                    "display_order": int(meta.get("display_order", 1000)),
                }
            )

        records.sort(
            key=lambda item: (
                str(item.get("category_id", "Main")).lower(),
                int(item.get("display_order", 1000)),
                str(item.get("name", "")).lower(),
            )
        )
        return records

    def _build_related_sets(self, state: Dict[str, dict]) -> List[Dict[str, str]]:
        """Build contextual related sets (top N) for current selection."""

        selection = self._sets.get_current_selection()
        require_all = len(selection) > 1
        related_names = self._sets.get_related_sets_for_selection(selection=selection, require_all=require_all)
        if not related_names:
            return []

        related_records: List[Dict[str, str]] = []
        for name in related_names[: self._RELATED_LIMIT]:
            meta = state.get(name, {})
            if bool(meta.get("hidden_in_launcher", False)):
                continue
            related_records.append(
                {
                    "id": name,
                    "name": name,
                    "color": str(meta.get("button_color", "#6B7280")),
                }
            )
        return related_records

    def _on_set_clicked(self, payload: Dict[str, str]) -> None:
        """LMB selects the set."""

        set_name = str(payload.get("id", ""))
        if not set_name:
            return

        if self._sets.select_set(set_name):
            if not self._is_pinned:
                self.close()
        else:
            self._toast(f"Could not select set: {set_name}")

    def _select_set_from_related(self, set_name: str) -> None:
        """Related quick shortcut uses the same select behavior."""

        self._on_set_clicked({"id": set_name})

    def _open_set_context_menu(self, payload: Dict[str, str], global_pos: object) -> None:
        """Open RMB context menu for set maintenance operations."""

        set_name = str(payload.get("id", ""))
        if not set_name:
            return

        self._context_menu_active = True
        menu = QtWidgets.QMenu(self)
        action_rename = menu.addAction("Rename")
        action_hide = menu.addAction("Hide from Launcher")
        action_delete = menu.addAction("Delete")
        action_color = menu.addAction("Change Color")
        action_update = menu.addAction("Update from Selection")

        selected = menu.exec_(global_pos)
        try:
            if selected is action_rename:
                self._rename_set(set_name)
            elif selected is action_hide:
                self._set_hidden_in_launcher(set_name, hidden=True)
            elif selected is action_delete:
                self._delete_set(set_name)
            elif selected is action_color:
                self._change_set_color(set_name)
            elif selected is action_update:
                self._update_from_selection(set_name)
        except Exception as exc:
            self._log_warning(f"Set action failed for '{set_name}': {exc}")

        self._context_menu_active = False

    def _rename_set(self, old_name: str) -> None:
        self._context_menu_active = True
        new_name, ok = QtWidgets.QInputDialog.getText(self, "Rename Set", "New set name", text=old_name)
        self._context_menu_active = False
        if not ok or not new_name.strip() or new_name.strip() == old_name:
            return

        raw_name = new_name.strip()
        clean_name = self._sets.sanitize_set_name(raw_name)
        if clean_name != raw_name:
            self._toast(f"Adjusted set name: {raw_name} → {clean_name}")
            self._log_warning(f"Adjusted set rename '{raw_name}' to '{clean_name}' for Maya compatibility")
        if clean_name == old_name:
            self._toast("Set name unchanged")
            return
        state_before = self._sets.load_scene_set_ui_state()
        cached_meta = dict(state_before.get(old_name, {}))

        if self._sets.rename_set(old_name, clean_name):
            state_after = self._sets.load_scene_set_ui_state()
            state_after.pop(old_name, None)
            if cached_meta:
                state_after[clean_name] = cached_meta
            self._sets.save_scene_set_ui_state(state_after)
            self._sets.refresh_scene_set_ui_state()
            self.refresh_from_scene()
            self._toast(f"Renamed: {clean_name}")
        else:
            self._toast("Could not rename set")

    def _delete_set(self, set_name: str) -> None:
        if self._sets.is_referenced_set(set_name):
            self._toast("Referenced sets cannot be deleted")
            return

        self._context_menu_active = True
        confirm = QtWidgets.QMessageBox.question(self, "Delete Set", f"Delete set '{set_name}'?")
        self._context_menu_active = False
        if confirm != QtWidgets.QMessageBox.Yes:
            return

        if self._sets.delete_set(set_name):
            self._sets.cleanup_missing_set_metadata()
            self.refresh_from_scene()
            self._toast(f"Deleted: {set_name}")
        else:
            self._toast("Could not delete set")

    def _set_hidden_in_launcher(self, set_name: str, hidden: bool) -> None:
        """Store reversible launcher visibility for full set name key."""

        state = self._sets.refresh_scene_set_ui_state()
        state.setdefault(set_name, {})
        state[set_name]["hidden_in_launcher"] = bool(hidden)
        self._sets.save_scene_set_ui_state(state)
        self.refresh_from_scene()
        self._toast(f"{'Hidden' if hidden else 'Shown'} in launcher: {set_name}")

    def _change_set_color(self, set_name: str) -> None:
        self._context_menu_active = True
        named_choices = [name for name, _ in self._SET_COLORS]
        selected_label, ok = QtWidgets.QInputDialog.getItem(
            self,
            "Set Color",
            "Choose color",
            named_choices,
            0,
            False,
        )
        self._context_menu_active = False
        if not ok or not selected_label:
            return

        color_value = next((hex_color for name, hex_color in self._SET_COLORS if selected_label == name), None)
        if not color_value:
            return

        state = self._sets.refresh_scene_set_ui_state()
        state.setdefault(set_name, {})
        state[set_name]["button_color"] = color_value
        self._sets.save_scene_set_ui_state(state)
        self.refresh_from_scene()
        self._toast(f"Color updated: {set_name}")

    def _update_from_selection(self, set_name: str) -> None:
        if self._sets.update_set_from_selection(set_name):
            self.refresh_from_scene()
            self._toast(f"Updated from selection: {set_name}")
        else:
            self._toast("Select objects first to update set")

    def _refresh_related_if_selection_changed(self) -> None:
        """Refresh related sets while pinned and visible only."""

        current = self._sets.get_current_selection()
        if current == self._last_selection:
            return
        self._last_selection = current
        state = self._sets.load_scene_set_ui_state()
        self._related_widget.set_related_sets(self._build_related_sets(state))

    def _start_selection_watch(self) -> None:
        if not self._watch_timer.isActive():
            self._watch_timer.start()

    def _stop_selection_watch(self) -> None:
        if self._watch_timer.isActive():
            self._watch_timer.stop()

    def _suggest_set_name(self) -> str:
        """Suggest a practical new set name."""

        existing = set(self._sets.list_scene_sets())
        base = "QuickSet"
        index = 1
        while True:
            candidate = f"{base}_{index:02d}"
            if candidate not in existing:
                return candidate
            index += 1

    def _choose_new_set_color(self, state: Dict[str, dict]) -> str:
        """Choose balanced color to reduce visible neighbor duplicates."""

        palette_values = [hex_color for _, hex_color in self._SET_COLORS]
        usage = Counter(str(meta.get("button_color", "")) for meta in state.values())

        all_sets = self._build_all_sets(state)
        recent_colors = [str(item.get("color", "")) for item in all_sets[-2:]]

        def score(color: str) -> Tuple[int, int]:
            repeat_penalty = 1 if color in recent_colors else 0
            return (usage.get(color, 0), repeat_penalty)

        return sorted(palette_values, key=score)[0]


    def _log_warning(self, message: str) -> None:
        """Emit readable warning without crashing launcher."""

        try:
            import maya.cmds as cmds  # type: ignore

            cmds.warning(f"[ContextPad:SetLauncher] {message}")
            return
        except Exception:
            pass

        print(f"[ContextPad:SetLauncher][WARN] {message}")

    def _toast(self, message: str) -> None:
        """Show lightweight user feedback near cursor."""

        QtWidgets.QToolTip.showText(self.mapToGlobal(self.rect().center()), message, self)

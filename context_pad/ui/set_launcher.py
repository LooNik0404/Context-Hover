"""Selection set overlay launcher widget with contextual related sets."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Tuple

from context_pad.core.set_registry import SetRegistry
from context_pad.maya_integration.qt_helpers import QtCore, QtGui, QtWidgets

from .launcher_base import LauncherBase
from .widgets.reference_set_picker import ReferenceSetPickerDialog
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
        self.set_button_columns(1)
        self.set_button_display_mode("list")

        self._sets = SetRegistry()
        self._related_widget = RelatedSetsList()
        self._related_widget.related_selected.connect(self._select_set_from_related)
        self.set_left_widget(self._related_widget)
        self.set_manager_button_visible(True)
        self.set_manager_button_text("◉")

        self._last_selection: List[str] = []
        self._launch_selection_snapshot: List[str] = []
        self._create_selection_snapshot: List[str] = []
        self._watch_timer = QtCore.QTimer(self)
        self._watch_timer.setInterval(300)
        self._watch_timer.timeout.connect(self._refresh_related_if_selection_changed)
        self._context_menu_active = False
        self._interaction_lock_count = 0
        self._layout_refresh_token = 0

        self._command_grid.button_clicked.connect(self._on_set_clicked)
        self._command_grid.button_aux_clicked.connect(self._on_set_aux_clicked)
        self._command_grid.button_context_requested.connect(self._open_set_context_menu)

        self.refresh_from_scene()

    def refresh_from_scene(self) -> None:
        """Refresh all and related sets from scene data."""

        state = self._sets.refresh_scene_set_ui_state()
        library = self._sets.load_scene_set_library()
        all_sets = self._build_all_sets(state, library)
        related = self._build_related_sets(state, library)

        self._related_widget.set_related_sets(related)
        self._last_selection = self._sets.get_ordered_selection()
        self._layout_refresh_token += 1
        token = self._layout_refresh_token

        def _apply_all_sets() -> None:
            if token != self._layout_refresh_token:
                return
            viewport_width = int(self._command_scroll.viewport().width()) if hasattr(self, "_command_scroll") else None
            self.set_button_available_width(viewport_width)
            self.set_buttons(all_sets)

        QtCore.QTimer.singleShot(0, _apply_all_sets)

    def on_add_requested(self) -> None:
        """LMB plus: create a local set from selection and register it."""

        self._create_selection_snapshot = self._sets.get_ordered_selection()
        selection_seed = self._valid_selection_seed()
        if not selection_seed:
            self._toast("Select objects first to create a set")
            return

        suggested_name = self._suggest_set_name(selection_seed)
        user_name, ok = self._prompt_text_input(
            title="Create Set from Selection",
            label="Set name",
            default_text=suggested_name,
            select_all=True,
        )
        if not ok:
            return

        raw_name = user_name.strip() or suggested_name
        sanitized_name = self._sets.sanitize_set_name(raw_name)
        unique_name = self._sets.ensure_unique_set_name(sanitized_name)
        if unique_name != raw_name:
            self._toast(f"Using unique set name: {unique_name}")

        created_name = self._sets.create_set_from_selection(unique_name, selection=selection_seed)
        if not created_name:
            self._toast("Could not create set from selection")
            return

        if not self._sets.set_exists(created_name):
            self._log_warning(f"Created set was not found after creation: '{created_name}'")
            self._toast("Set creation failed validation")
            return

        member_count = self._sets.get_set_size(created_name)
        if member_count <= 0:
            self._log_warning(f"Refusing to register empty set '{created_name}'")
            self._toast("Set creation produced no members")
            return

        color = self._sets.choose_balanced_color(include_gray=False)
        self._sets.register_set_library_entry(
            source_ref=created_name,
            source_kind="local_maya_set",
            display_label=self._display_label(created_name),
            color=color,
            hidden_in_launcher=False,
            is_referenced=False,
            selection_order=selection_seed,
        )
        self.refresh_from_scene()
        self._toast(f"Created set: {created_name}")

    def on_add_context_requested(self, global_pos: object) -> None:
        """RMB plus: show exactly two add actions."""

        self._enter_interaction()
        try:
            menu = QtWidgets.QMenu(self)
            action_create = menu.addAction("Create Set from Selection")
            action_add_existing_local = menu.addAction("Add Existing Local Sets...")
            action_add_ref = menu.addAction("Add Sets from Reference...")
            selected = menu.exec_(global_pos)
        finally:
            self._exit_interaction()

        if selected is action_create:
            self.on_add_requested()
        elif selected is action_add_existing_local:
            self._import_existing_local_sets()
        elif selected is action_add_ref:
            self._open_reference_add_dialog()

    def on_manager_requested(self) -> None:
        """Open compact visibility manager dialog for set show/hide."""

        self._enter_interaction()
        try:
            dialog = SetVisibilityDialog(registry=self._sets, parent=self)
            dialog.exec_()
        finally:
            self._exit_interaction()
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

        self._launch_selection_snapshot = self._sets.get_current_selection()
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

        if self.is_interaction_locked():
            event.accept()
            return
        super().focusOutEvent(event)

    def _build_all_sets(self, state: Dict[str, dict], library: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
        """Build full set list from explicit scene-local library entries."""

        records: List[Dict[str, str]] = []
        for entry in self._sorted_library_entries(library):
            set_name = str(entry.get("source_ref", ""))
            if not set_name:
                continue
            if bool(entry.get("hidden_in_launcher", False)):
                continue
            records.append(
                {
                    "id": set_name,
                    "name": self._elide_label(self._display_label(set_name)),
                    "category_id": "Main",
                    "color": self._calm_color(
                        str(entry.get("button_color", state.get(set_name, {}).get("button_color", "#6B7280")))
                    ),
                    "display_order": int(entry.get("display_order", 1000)),
                    "tooltip": set_name,
                    "show_set_algebra": True,
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

    def _build_related_sets(self, state: Dict[str, dict], library: Dict[str, Dict[str, Any]]) -> List[Dict[str, str]]:
        """Build contextual related sets (top N) for current selection."""

        allowed_names = {
            str(entry.get("source_ref", ""))
            for entry in library.values()
            if entry and not bool(entry.get("hidden_in_launcher", False))
        }
        selection = self._sets.get_ordered_selection()
        require_all = len(selection) > 1
        related_names = self._sets.get_related_sets_for_selection(selection=selection, require_all=require_all)
        if not related_names:
            return []

        related_records: List[Dict[str, str]] = []
        for name in related_names[: self._RELATED_LIMIT]:
            if name not in allowed_names:
                continue
            meta = state.get(name, {})
            if bool(meta.get("hidden_in_launcher", False)):
                continue
            related_records.append(
                {
                    "id": name,
                    "name": self._elide_label(self._display_label(name)),
                    "color": self._calm_color(str(meta.get("button_color", "#6B7280"))),
                    "tooltip": name,
                }
            )
        return related_records

    def _on_set_clicked(self, payload: Dict[str, str]) -> None:
        """LMB selects the set (replace mode)."""

        set_name = str(payload.get("id", ""))
        if not set_name:
            return

        ordered_members = self._selection_order_for_set(set_name)
        if self._sets.select_set_with_saved_order(set_name, ordered_members=ordered_members):
            if not self._is_pinned:
                self.close()
        else:
            self._toast(f"Could not select set: {set_name}")

    def _on_set_aux_clicked(self, payload: Dict[str, str], action: str) -> None:
        """Handle + / - set algebra actions without closing hover."""

        set_name = str(payload.get("id", ""))
        if not set_name:
            return
        ordered_members = self._selection_order_for_set(set_name)
        normalized = str(action or "").strip().lower()
        if normalized == "add":
            if not self._sets.add_set_with_saved_order(set_name, ordered_members=ordered_members):
                self._toast(f"Could not add set: {set_name}")
            return
        if normalized == "subtract":
            if not self._sets.remove_set_from_selection(set_name):
                self._toast(f"Could not subtract set: {set_name}")
            return

    def _select_set_from_related(self, set_name: str) -> None:
        """Related quick shortcut uses the same select behavior."""

        self._on_set_clicked({"id": set_name})

    def _open_set_context_menu(self, payload: Dict[str, str], global_pos: object) -> None:
        """Open RMB context menu for set maintenance operations."""

        set_name = str(payload.get("id", ""))
        if not set_name:
            return

        self._enter_interaction()
        try:
            menu = QtWidgets.QMenu(self)
            action_rename = menu.addAction("Rename")
            action_hide = menu.addAction("Hide from Launcher")
            action_remove_hover = menu.addAction("Remove from Hover")
            action_delete = menu.addAction("Delete Set")
            action_color = menu.addAction("Change Color")
            action_update = menu.addAction("Update from Selection")
            selected = menu.exec_(global_pos)
            if selected is action_rename:
                self._rename_set(set_name)
            elif selected is action_hide:
                self._set_hidden_in_launcher(set_name, hidden=True)
            elif selected is action_remove_hover:
                self._remove_from_hover(set_name)
            elif selected is action_delete:
                self._delete_set(set_name)
            elif selected is action_color:
                self._change_set_color(set_name)
            elif selected is action_update:
                self._update_from_selection(set_name)
        except Exception as exc:
            self._log_warning(f"Set action failed for '{set_name}': {exc}")
        finally:
            self._exit_interaction()

    def _rename_set(self, old_name: str) -> None:
        new_name, ok = self._prompt_text_input(
            title="Rename Set",
            label="New set name",
            default_text=old_name,
            select_all=True,
        )
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
        if self._sets.rename_set(old_name, clean_name):
            library = self._sets.load_scene_set_library()
            entry_id = self._entry_id_for_source_ref(library, old_name)
            final_name = self._resolve_current_name_from_old(old_name, clean_name)
            if entry_id:
                self._sets.update_set_library_entry(
                    entry_id,
                    {
                        "source_ref": final_name,
                        "display_label": self._display_label(final_name),
                        "is_referenced": False,
                    },
                )
            else:
                # Fallback safety: if entry missing, register renamed local set.
                self._sets.register_set_library_entry(
                    source_ref=final_name,
                    source_kind="local_maya_set",
                    display_label=self._display_label(final_name),
                    color=self._choose_new_set_color(state=self._sets.load_scene_set_ui_state()),
                    hidden_in_launcher=False,
                    is_referenced=False,
                )
            self.refresh_from_scene()
            self._toast(f"Renamed: {final_name}")
        else:
            self._toast("Could not rename set")

    def _delete_set(self, set_name: str) -> None:
        exists = self._sets.set_exists(set_name)
        if not exists:
            self._toast("Set no longer exists. Use Remove from Hover to clear stale entry.")
            return
        if self._sets.is_referenced_set(set_name):
            self._toast("Referenced sets cannot be deleted. Use Remove from Hover.")
            return
        library = self._sets.load_scene_set_library()
        entry = self._library_entry_for_set_name(library, set_name)
        if entry and str(entry.get("source_kind", "")) != "local_maya_set":
            self._toast("Only local scene sets can be deleted. Use Remove from Hover.")
            return

        self._enter_interaction()
        try:
            confirm = QtWidgets.QMessageBox.question(self, "Delete Set", f"Delete Maya set '{set_name}'?")
        finally:
            self._exit_interaction()
        if confirm != QtWidgets.QMessageBox.Yes:
            return

        if self._sets.delete_set(set_name):
            self._sets.cleanup_missing_set_metadata()
            entry_id = self._entry_id_for_source_ref(library, set_name)
            if entry_id:
                self._sets.delete_set_library_entry(entry_id)
            self.refresh_from_scene()
            self._toast(f"Deleted: {set_name}")
        else:
            self._toast("Could not delete set (local user-facing sets only)")

    def _remove_from_hover(self, set_name: str) -> None:
        """Remove launcher entry without deleting underlying Maya set."""

        library = self._sets.load_scene_set_library()
        entry_id = self._entry_id_for_source_ref(library, set_name)
        if not entry_id:
            self._toast("Set is not in hover library")
            return
        self._sets.delete_set_library_entry(entry_id)
        self.refresh_from_scene()
        self._toast(f"Removed from Hover: {set_name}")

    def _set_hidden_in_launcher(self, set_name: str, hidden: bool) -> None:
        """Store reversible launcher visibility for full set name key."""

        library = self._sets.load_scene_set_library()
        entry_id = self._entry_id_for_source_ref(library, set_name)
        if entry_id:
            self._sets.update_set_library_entry(entry_id, {"hidden_in_launcher": bool(hidden)})
        self.refresh_from_scene()
        self._toast(f"{'Hidden' if hidden else 'Shown'} in launcher: {set_name}")

    def _change_set_color(self, set_name: str) -> None:
        self._enter_interaction()
        try:
            named_choices = [name for name, _ in self._SET_COLORS]
            selected_label, ok = QtWidgets.QInputDialog.getItem(
                self,
                "Set Color",
                "Choose color",
                named_choices,
                0,
                False,
            )
        finally:
            self._exit_interaction()
        if not ok or not selected_label:
            return

        color_value = next((hex_color for name, hex_color in self._SET_COLORS if selected_label == name), None)
        if not color_value:
            return

        library = self._sets.load_scene_set_library()
        entry_id = self._entry_id_for_source_ref(library, set_name)
        if entry_id:
            self._sets.update_set_library_entry(entry_id, {"button_color": color_value})
        self.refresh_from_scene()
        self._toast(f"Color updated: {set_name}")

    def _update_from_selection(self, set_name: str) -> None:
        if self._sets.update_set_from_selection(set_name):
            library = self._sets.load_scene_set_library()
            entry_id = self._entry_id_for_source_ref(library, set_name)
            if entry_id:
                self._sets.update_set_library_entry(entry_id, {"selection_order": self._sets.get_ordered_selection()})
            self.refresh_from_scene()
            self._toast(f"Updated from selection: {set_name}")
        else:
            self._toast("Select objects first to update set")

    def _refresh_related_if_selection_changed(self) -> None:
        """Refresh related sets while pinned and visible only."""

        current = self._sets.get_ordered_selection()
        if current == self._last_selection:
            return
        self.refresh_from_scene()

    def _start_selection_watch(self) -> None:
        if not self._watch_timer.isActive():
            self._watch_timer.start()

    def _stop_selection_watch(self) -> None:
        if self._watch_timer.isActive():
            self._watch_timer.stop()

    def _suggest_set_name(self, selection: List[str] | None = None) -> str:
        """Suggest a practical new set name."""

        chosen = selection if selection is not None else self._valid_selection_seed()
        if chosen:
            first_name = self._display_label(chosen[0]).replace(" ", "_")
            base_seed = self._sets.sanitize_set_name(f"{first_name}_SET")
            if base_seed:
                return self._sets.ensure_unique_set_name(base_seed)

        existing = set(self._sets.list_scene_sets())
        base = "QuickSet"
        index = 1
        while True:
            candidate = f"{base}_{index:02d}"
            if candidate not in existing:
                return candidate
            index += 1

    def _choose_new_set_color(self, state: Dict[str, dict], library: Dict[str, Dict[str, Any]] | None = None) -> str:
        """Choose balanced color to reduce visible neighbor duplicates."""

        palette_values = [hex_color for _, hex_color in self._SET_COLORS]
        usage = Counter(str(meta.get("button_color", "")) for meta in state.values())

        active_library = library if library is not None else self._sets.load_scene_set_library()
        all_sets = self._build_all_sets(state, active_library)
        recent_colors = [str(item.get("color", "")) for item in all_sets[-2:]]

        def score(color: str) -> Tuple[int, int]:
            repeat_penalty = 1 if color in recent_colors else 0
            return (usage.get(color, 0), repeat_penalty)

        return sorted(palette_values, key=score)[0]

    def _valid_selection_seed(self) -> List[str]:
        """Prefer launch-time selection snapshot, fallback to current selection."""

        create_snapshot = [item for item in self._create_selection_snapshot if item]
        if create_snapshot:
            return create_snapshot
        snapshot = [item for item in self._launch_selection_snapshot if item]
        if snapshot:
            return snapshot
        return self._sets.get_ordered_selection()

    def _open_reference_add_dialog(self) -> None:
        """Open picker to import reference-approved (or all) reference sets."""

        self._enter_interaction()
        try:
            dialog = ReferenceSetPickerDialog(registry=self._sets, parent=self)
            accepted = dialog.exec_() == QtWidgets.QDialog.Accepted
        finally:
            self._exit_interaction()
        if not accepted:
            return

        selected_sets = dialog.selected_sets()
        if not selected_sets:
            self._toast("No reference sets selected")
            return

        state = self._sets.load_scene_set_ui_state()
        added_count = 0
        for set_name in selected_sets:
            existing = str(state.get(set_name, {}).get("button_color", ""))
            color = existing or self._sets.choose_balanced_color(include_gray=False)
            self._sets.register_set_library_entry(
                source_ref=set_name,
                source_kind="referenced_maya_set",
                display_label=self._display_label(set_name),
                color=color,
                hidden_in_launcher=False,
                is_referenced=True,
                selection_order=[],
            )
            added_count += 1
        self.refresh_from_scene()
        self._toast(f"Added {added_count} reference set(s)")

    def _sorted_library_entries(self, library: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(
            [entry for entry in library.values() if isinstance(entry, dict)],
            key=lambda entry: (
                int(entry.get("display_order", 1000)),
                str(entry.get("display_label", "")).lower(),
                str(entry.get("source_ref", "")).lower(),
            ),
        )

    def _entry_id_for_source_ref(self, library: Dict[str, Dict[str, Any]], source_ref: str) -> str | None:
        for entry_id, entry in library.items():
            if str(entry.get("source_ref", "")) == source_ref:
                return str(entry_id)
        return None

    def _library_entry_for_set_name(self, library: Dict[str, Dict[str, Any]], set_name: str) -> Dict[str, Any] | None:
        entry_id = self._entry_id_for_source_ref(library, set_name)
        return library.get(entry_id) if entry_id else None

    def _resolve_current_name_from_old(self, old_name: str, requested_new_name: str) -> str:
        """Resolve actual final set name after rename (handles auto-suffix collisions)."""

        if self._sets.set_exists(requested_new_name):
            return requested_new_name
        scene_sets = self._sets.list_scene_sets()
        candidates = [name for name in scene_sets if name.startswith(f"{requested_new_name}_")]
        if old_name in scene_sets:
            return old_name
        return sorted(candidates)[-1] if candidates else requested_new_name

    def _import_existing_local_sets(self) -> None:
        """Explicitly import local scene sets that are not yet in hover library."""

        scene_sets = self._sets.list_scene_sets()
        library = self._sets.load_scene_set_library()
        known = {str(entry.get("source_ref", "")) for entry in library.values() if isinstance(entry, dict)}
        missing = [name for name in scene_sets if name not in known and not self._sets.is_referenced_set(name)]
        if not missing:
            self._toast("No unregistered local sets found")
            return

        self._enter_interaction()
        try:
            prompt = QtWidgets.QMessageBox.question(
                self,
                "Add Existing Local Sets",
                f"Import {len(missing)} local set(s) into Hover library?",
            )
        finally:
            self._exit_interaction()
        if prompt != QtWidgets.QMessageBox.Yes:
            return

        added = 0
        for set_name in missing:
            self._sets.register_set_library_entry(
                source_ref=set_name,
                source_kind="local_maya_set",
                display_label=self._display_label(set_name),
                color=self._sets.choose_balanced_color(include_gray=False),
                hidden_in_launcher=False,
                is_referenced=False,
                selection_order=[],
            )
            added += 1
        self.refresh_from_scene()
        self._toast(f"Added {added} local set(s)")

    def is_interaction_locked(self) -> bool:
        """Return True while set UI menus/dialogs are active."""

        return self._interaction_lock_count > 0

    def _enter_interaction(self) -> None:
        self._context_menu_active = True
        self._interaction_lock_count += 1

    def _exit_interaction(self) -> None:
        self._interaction_lock_count = max(0, self._interaction_lock_count - 1)
        self._context_menu_active = self._interaction_lock_count > 0

    def _display_label(self, full_set_name: str) -> str:
        """Return namespace-free display label while keeping full name internal."""

        short_name = str(full_set_name).split("|")[-1]
        return short_name.split(":")[-1]

    def _calm_color(self, color_hex: str) -> str:
        base = QtGui.QColor(color_hex)
        neutral = QtGui.QColor("#55606B")
        mixed = QtGui.QColor(
            int((base.red() * 0.62) + (neutral.red() * 0.38)),
            int((base.green() * 0.62) + (neutral.green() * 0.38)),
            int((base.blue() * 0.62) + (neutral.blue() * 0.38)),
        )
        return mixed.name()

    def _elide_label(self, label: str, max_chars: int = 28) -> str:
        """Elide long labels to keep single-column set list compact and readable."""

        text = str(label)
        if len(text) <= max_chars:
            return text
        return f"{text[: max(1, max_chars - 1)]}…"


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

    def _selection_order_for_set(self, set_name: str) -> List[str]:
        library = self._sets.load_scene_set_library()
        entry = self._library_entry_for_set_name(library, set_name)
        order = entry.get("selection_order", []) if entry else []
        return [str(item) for item in order] if isinstance(order, list) else []

    def _prompt_text_input(self, title: str, label: str, default_text: str, select_all: bool = True) -> tuple[str, bool]:
        """Prompt text input under interaction lock with clean initial focus/selection."""

        class _HotkeyLeakBlocker(QtCore.QObject):
            """Temporarily suppress key-repeat leakage into newly focused line edits."""

            def __init__(self, grace_ms: int = 180) -> None:
                super().__init__()
                self._timer = QtCore.QElapsedTimer()
                self._timer.start()
                self._grace_ms = max(0, int(grace_ms))

            def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:  # noqa: N802
                if event.type() == QtCore.QEvent.KeyPress:
                    key_event = event
                    if key_event.isAutoRepeat():
                        return True
                    if self._timer.elapsed() <= self._grace_ms:
                        return True
                return False

        dialog = QtWidgets.QInputDialog(self)
        dialog.setWindowTitle(title)
        dialog.setLabelText(label)
        dialog.setTextEchoMode(QtWidgets.QLineEdit.Normal)
        dialog.setTextValue(default_text)
        dialog.setOkButtonText("OK")
        dialog.setCancelButtonText("Cancel")

        line_edit = dialog.findChild(QtWidgets.QLineEdit)
        leak_blocker = _HotkeyLeakBlocker()
        if line_edit is not None:
            line_edit.setText(default_text)
            line_edit.installEventFilter(leak_blocker)

            def _prepare_line_edit() -> None:
                line_edit.setFocus(QtCore.Qt.ActiveWindowFocusReason)
                if select_all:
                    line_edit.selectAll()
                else:
                    line_edit.setCursorPosition(len(line_edit.text()))

            QtCore.QTimer.singleShot(0, _prepare_line_edit)

        self._enter_interaction()
        try:
            QtWidgets.QApplication.processEvents(QtCore.QEventLoop.ExcludeUserInputEvents)
            accepted = dialog.exec_() == QtWidgets.QDialog.Accepted
        finally:
            self._exit_interaction()
            if line_edit is not None:
                line_edit.removeEventFilter(leak_blocker)
        return dialog.textValue(), accepted

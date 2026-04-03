"""Script overlay launcher widget."""

from __future__ import annotations

from context_pad.core.command_runner import run_button_action
from context_pad.core.script_registry import ManifestValidationError, ScriptRegistry

from .launcher_base import LauncherBase
from .widgets.category_bar import CategoryBar


class ScriptLauncher(LauncherBase):
    """Overlay launcher displaying script buttons from manifest."""

    def __init__(self, parent=None) -> None:
        """Initialize script launcher with category+grid layout."""

        super().__init__(parent=parent)
        self.setWindowTitle("Context Pad")
        self.set_button_columns(2)

        category_widget = CategoryBar()
        category_widget.set_title("Categories")
        category_widget.category_changed.connect(self._command_grid.filter_by_category)
        self.set_left_widget(category_widget)

        self._command_grid.button_clicked.connect(self._on_script_clicked)
        self.refresh_data()

    def refresh_data(self) -> None:
        """Load categories/buttons from manifest and populate launcher."""

        current_category_id = (
            self._left_widget.current_category() if isinstance(self._left_widget, CategoryBar) else ""
        )
        registry = ScriptRegistry()
        try:
            registry.load_manifest()
            manifest_dir = str(registry.manifest_path().parent) if registry.manifest_path() else ""
            categories = [
                {"id": item["id"], "name": item["label"], "color": item.get("color", "#6B7280")}
                for item in registry.get_categories()
            ]
            buttons = []
            for category in categories:
                for item in registry.get_buttons_for_category(category["id"]):
                    buttons.append(
                        {
                            "id": item["id"],
                            "name": item["label"],
                            "category_id": item["category_id"],
                            "color": item["color"],
                            "type": item["action_type"],
                            "source": item["source"],
                            "label": item["label"],
                            "tooltip": item.get("tooltip", ""),
                            "code": item["source"] if item["action_type"].endswith("inline") else "",
                            "file_path": item["source"] if item["action_type"].endswith("file") else "",
                            "manifest_dir": manifest_dir,
                        }
                    )

            self.set_categories(categories)
            if current_category_id and isinstance(self._left_widget, CategoryBar):
                self._left_widget.set_current_category(current_category_id)
            self.set_buttons(buttons)
            return
        except ManifestValidationError as exc:
            print(f"[ContextPad:ScriptLauncher][WARN] Manifest validation failed: {exc}")
        except Exception as exc:
            print(f"[ContextPad:ScriptLauncher][WARN] Failed loading library: {exc}")

        self.set_categories(
            [
                {"id": "anim", "name": "Animation", "color": "#9DB4D1"},
                {"id": "rig", "name": "Rig", "color": "#B1C7A2"},
                {"id": "util", "name": "Utilities", "color": "#B8AFD1"},
            ]
        )
        if current_category_id and isinstance(self._left_widget, CategoryBar):
            self._left_widget.set_current_category(current_category_id)
        self.set_buttons(
            [
                {
                    "id": "scr_1",
                    "name": "Bake Keys",
                    "label": "Bake Keys",
                    "category_id": "anim",
                    "color": "#5D82A8",
                    "type": "python_inline",
                    "source": "print('Bake Keys placeholder')",
                    "code": "print('Bake Keys placeholder')",
                    "file_path": "",
                },
                {
                    "id": "scr_2",
                    "name": "Mirror Pose",
                    "label": "Mirror Pose",
                    "category_id": "anim",
                    "color": "#6E95BC",
                    "type": "python_inline",
                    "source": "print('Mirror Pose placeholder')",
                    "code": "print('Mirror Pose placeholder')",
                    "file_path": "",
                },
            ]
        )

    def _on_script_clicked(self, payload: dict) -> None:
        """Run script action and close launcher on successful unpinned click."""

        success = run_button_action(payload)
        if success and not self.is_pinned():
            self.close()

    def on_add_requested(self) -> None:
        """Open manager and start quick script-button creation."""

        try:
            from context_pad.bootstrap import show_manager_window

            manager = show_manager_window()
            manager.open_button_setup_tab()
            manager.start_quick_add_button()
        except Exception as exc:
            print(f"[ContextPad:ScriptLauncher][WARN] Could not start quick add: {exc}")

    def on_manager_requested(self) -> None:
        """Open manager window from ellipsis icon."""

        try:
            from context_pad.bootstrap import show_manager_window

            manager = show_manager_window()
            manager.open_button_setup_tab()
        except Exception as exc:
            print(f"[ContextPad:ScriptLauncher][WARN] Could not open manager: {exc}")

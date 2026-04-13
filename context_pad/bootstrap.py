"""Bootstrapping helpers for launching Context Pad in Maya."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Optional

from .core.app_state import AppState
from .config import (
    ensure_user_data_layout,
    get_active_manifest_path,
    get_user_data_candidates,
    get_user_config_path,
    get_user_data_root,
    load_user_config,
    resolve_writable_user_data_root,
)
from .maya_integration.qt_helpers import QtCore, maya_main_window
from .ui.manager_window import ManagerWindow
from .ui.script_launcher import ScriptLauncher
from .ui.set_launcher import SetLauncher

try:
    import maya.cmds as cmds  # type: ignore
except Exception:  # pragma: no cover - outside Maya
    cmds = None


_MANAGER_WINDOW: Optional[ManagerWindow] = None
_SCRIPT_LAUNCHER: Optional[ScriptLauncher] = None
_SET_LAUNCHER: Optional[SetLauncher] = None
_SCRIPT_HOLD_ACTIVE: bool = False
_SET_HOLD_ACTIVE: bool = False
_SCRIPT_HIDE_TIMER: Optional[QtCore.QTimer] = None
_SET_HIDE_TIMER: Optional[QtCore.QTimer] = None
_USER_SETUP_MARKER_BEGIN = "# >>> ContextPad autostart >>>"
_USER_SETUP_MARKER_END = "# <<< ContextPad autostart <<<"
_HOTKEY_MARKER_BEGIN = "# >>> ContextPad hotkeys fallback >>>"
_HOTKEY_MARKER_END = "# <<< ContextPad hotkeys fallback <<<"


def launch_context_pad() -> ManagerWindow:
    """Launch or raise the manager window and prepare overlay launchers."""

    return show_manager_window()


def install_startup() -> dict:
    """One-time safe setup for user data + userSetup autostart block."""

    try:
        paths = ensure_user_data_layout()
        print(f"[ContextPad] install_startup user_root: {paths.get('user_root')}")
        print(f"[ContextPad] install_startup config_path: {paths.get('config_path')}")
        print(f"[ContextPad] install_startup manifest_path: {paths.get('manifest_path')}")
        _install_usersetup_block()
        print_paths()
        return paths
    except Exception as exc:
        _log_warning(f"install_startup failed: {exc}")
        raise


def autostart() -> bool:
    """Quiet startup initialization using user config + user manifest."""

    try:
        ensure_user_data_layout()
        _ = get_active_manifest_path()
        return True
    except Exception as exc:
        _log_warning(f"Autostart failed: {exc}")
        return False


def get_library_folder_path() -> str:
    """Return active user-editable Context Pad library folder path."""

    manifest_path = get_active_manifest_path()
    return str(manifest_path.parent)


def get_library_manifest_path() -> str:
    """Return active user-editable manifest path."""

    return str(get_active_manifest_path())


def print_paths() -> None:
    """Print active Context Pad user paths for debugging/support."""

    config = load_user_config()
    print(f"[ContextPad] user_root: {get_user_data_root()}")
    print(f"[ContextPad] user_data_candidates: {get_user_data_candidates()}")
    print(f"[ContextPad] config_path: {get_user_config_path()}")
    print(f"[ContextPad] active_manifest_path: {get_active_manifest_path()}")
    print(f"[ContextPad] config.active_manifest_path: {config.get('active_manifest_path', '')}")
    print(f"[ContextPad] user_root_writable: {_is_writable_path(resolve_writable_user_data_root())}")
    print(f"[ContextPad] startup_block_installed: {_has_usersetup_block(_USER_SETUP_MARKER_BEGIN, _USER_SETUP_MARKER_END)}")


def diagnose_install() -> None:
    """Print practical installation diagnostics for support/debug."""

    import context_pad

    print("[ContextPad] ---- install diagnostics ----")
    print(f"[ContextPad] import_location: {context_pad.__file__}")
    print(f"[ContextPad] maya_userScriptDir: {_maya_user_scripts_dir()}")
    print(f"[ContextPad] active_user_data_root: {get_user_data_root()}")
    print(f"[ContextPad] config_path: {get_user_config_path()}")
    print(f"[ContextPad] active_manifest_path: {get_active_manifest_path()}")
    print(f"[ContextPad] library_writable: {_is_writable_path(get_active_manifest_path().parent)}")
    print(f"[ContextPad] startup_block_installed: {_has_usersetup_block(_USER_SETUP_MARKER_BEGIN, _USER_SETUP_MARKER_END)}")
    print(f"[ContextPad] hotkey_fallback_block_installed: {_has_usersetup_block(_HOTKEY_MARKER_BEGIN, _HOTKEY_MARKER_END)}")


def install_hotkeys_startup() -> bool:
    """Install optional startup fallback block for restoring Context Pad hotkeys."""

    block = (
        f"{_HOTKEY_MARKER_BEGIN}\n"
        "try:\n"
        "    # Optional fallback for machines that lose hotkey prefs.\n"
        "    # Intentionally non-forced: edit this block to call your own hotkey restore command.\n"
        "    pass\n"
        "except Exception as _context_pad_hotkey_exc:\n"
        "    print(f\"[ContextPad][WARN] hotkey fallback failed: {_context_pad_hotkey_exc}\")\n"
        f"{_HOTKEY_MARKER_END}\n"
    )
    return _append_usersetup_block(_HOTKEY_MARKER_BEGIN, _HOTKEY_MARKER_END, block)


def open_library_folder() -> bool:
    """Open active user library folder in OS file browser."""

    folder = get_library_folder_path()
    manifest = get_library_manifest_path()
    print(f"[ContextPad] Opening library folder: {folder}")
    print(f"[ContextPad] Active manifest: {manifest}")
    try:
        if sys.platform.startswith("win"):
            os.startfile(folder)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])
        return True
    except Exception as exc:
        _log_warning(f"Could not open library folder: {exc}")
        return False


def show_manager_window() -> ManagerWindow:
    """Show singleton manager window."""

    global _MANAGER_WINDOW
    ensure_user_data_layout()
    if _MANAGER_WINDOW is None or not _is_alive(_MANAGER_WINDOW):
        _MANAGER_WINDOW = ManagerWindow(app_state=AppState(), parent=maya_main_window())
    _MANAGER_WINDOW.show()
    _MANAGER_WINDOW.raise_()
    _MANAGER_WINDOW.activateWindow()
    return _MANAGER_WINDOW


def show_script_launcher() -> ScriptLauncher:
    """Show the singleton script launcher near the cursor."""

    global _SCRIPT_LAUNCHER, _SCRIPT_HOLD_ACTIVE
    ensure_user_data_layout()
    _cancel_script_hide_timer()
    if _SCRIPT_HOLD_ACTIVE and _SCRIPT_LAUNCHER is not None and _is_alive(_SCRIPT_LAUNCHER) and _SCRIPT_LAUNCHER.isVisible():
        return _SCRIPT_LAUNCHER
    if _SCRIPT_HOLD_ACTIVE and (_SCRIPT_LAUNCHER is None or not _is_alive(_SCRIPT_LAUNCHER) or not _SCRIPT_LAUNCHER.isVisible()):
        _SCRIPT_HOLD_ACTIVE = False

    if _SCRIPT_LAUNCHER is None or not _is_alive(_SCRIPT_LAUNCHER):
        _SCRIPT_LAUNCHER = ScriptLauncher(parent=maya_main_window())
    _SCRIPT_HOLD_ACTIVE = True
    _SCRIPT_LAUNCHER.show_at_cursor()
    return _SCRIPT_LAUNCHER


def refresh_script_launcher() -> None:
    """Refresh existing script launcher content in place, when alive."""

    global _SCRIPT_LAUNCHER
    if _SCRIPT_LAUNCHER is None or not _is_alive(_SCRIPT_LAUNCHER):
        return
    _SCRIPT_LAUNCHER.refresh_data()


def show_set_launcher() -> SetLauncher:
    """Show the singleton set launcher near the cursor."""

    global _SET_LAUNCHER, _SET_HOLD_ACTIVE
    ensure_user_data_layout()
    _cancel_set_hide_timer()
    if _SET_HOLD_ACTIVE and _SET_LAUNCHER is not None and _is_alive(_SET_LAUNCHER) and _SET_LAUNCHER.isVisible():
        return _SET_LAUNCHER
    if _SET_HOLD_ACTIVE and (_SET_LAUNCHER is None or not _is_alive(_SET_LAUNCHER) or not _SET_LAUNCHER.isVisible()):
        _SET_HOLD_ACTIVE = False

    if _SET_LAUNCHER is None or not _is_alive(_SET_LAUNCHER):
        _SET_LAUNCHER = SetLauncher(parent=maya_main_window())
    _SET_HOLD_ACTIVE = True
    _SET_LAUNCHER.show_at_cursor()
    return _SET_LAUNCHER




def hide_script_launcher() -> None:
    """Hide/close script launcher unless pinned."""

    global _SCRIPT_LAUNCHER, _SCRIPT_HOLD_ACTIVE
    _SCRIPT_HOLD_ACTIVE = False
    if _SCRIPT_LAUNCHER is None or not _is_alive(_SCRIPT_LAUNCHER):
        return
    if _SCRIPT_LAUNCHER.is_pinned():
        return
    _schedule_script_hide()


def hide_set_launcher() -> None:
    """Hide/close set launcher unless pinned."""

    global _SET_LAUNCHER, _SET_HOLD_ACTIVE
    _SET_HOLD_ACTIVE = False
    if _SET_LAUNCHER is None or not _is_alive(_SET_LAUNCHER):
        return
    if _SET_LAUNCHER.is_pinned():
        return
    if hasattr(_SET_LAUNCHER, "is_interaction_locked") and _SET_LAUNCHER.is_interaction_locked():
        return
    _schedule_set_hide()

def launch_script_overlay() -> ScriptLauncher:
    """Compatibility alias for showing the script launcher."""

    return show_script_launcher()


def launch_set_overlay() -> SetLauncher:
    """Compatibility alias for showing the set launcher."""

    return show_set_launcher()


def is_maya_session() -> bool:
    """Return True when running inside a Maya session."""

    return cmds is not None


def _is_alive(widget: object) -> bool:
    """Return False when wrapped Qt widget has already been deleted."""

    try:
        _ = widget.objectName()  # type: ignore[attr-defined]
        return True
    except Exception:
        return False


def _schedule_script_hide() -> None:
    global _SCRIPT_HIDE_TIMER
    if _SCRIPT_HIDE_TIMER is None:
        _SCRIPT_HIDE_TIMER = QtCore.QTimer()
        _SCRIPT_HIDE_TIMER.setSingleShot(True)
        _SCRIPT_HIDE_TIMER.timeout.connect(_close_script_if_unpinned)
    _SCRIPT_HIDE_TIMER.start(50)


def _schedule_set_hide() -> None:
    global _SET_HIDE_TIMER
    if _SET_HIDE_TIMER is None:
        _SET_HIDE_TIMER = QtCore.QTimer()
        _SET_HIDE_TIMER.setSingleShot(True)
        _SET_HIDE_TIMER.timeout.connect(_close_set_if_unpinned)
    _SET_HIDE_TIMER.start(50)


def _cancel_script_hide_timer() -> None:
    if _SCRIPT_HIDE_TIMER is not None and _SCRIPT_HIDE_TIMER.isActive():
        _SCRIPT_HIDE_TIMER.stop()


def _cancel_set_hide_timer() -> None:
    if _SET_HIDE_TIMER is not None and _SET_HIDE_TIMER.isActive():
        _SET_HIDE_TIMER.stop()


def _close_script_if_unpinned() -> None:
    if _SCRIPT_LAUNCHER is None or not _is_alive(_SCRIPT_LAUNCHER):
        return
    if _SCRIPT_LAUNCHER.is_pinned():
        return
    _SCRIPT_LAUNCHER.close()


def _close_set_if_unpinned() -> None:
    if _SET_LAUNCHER is None or not _is_alive(_SET_LAUNCHER):
        return
    if _SET_LAUNCHER.is_pinned():
        return
    if hasattr(_SET_LAUNCHER, "is_interaction_locked") and _SET_LAUNCHER.is_interaction_locked():
        return
    _SET_LAUNCHER.close()


def _install_usersetup_block() -> None:
    """Install Context Pad autostart snippet into Maya userSetup.py once."""

    block = (
        f"{_USER_SETUP_MARKER_BEGIN}\n"
        "try:\n"
        "    from context_pad.bootstrap import autostart\n"
        "    autostart()\n"
        "except Exception as _context_pad_exc:\n"
        "    print(f\"[ContextPad][WARN] autostart failed: {_context_pad_exc}\")\n"
        f"{_USER_SETUP_MARKER_END}\n"
    )
    _append_usersetup_block(_USER_SETUP_MARKER_BEGIN, _USER_SETUP_MARKER_END, block)


def _maya_user_scripts_dir() -> "Path":
    from pathlib import Path

    if cmds is not None:
        try:
            value = str(cmds.internalVar(userScriptDir=True) or "").strip()
            if value:
                return Path(value)
        except Exception:
            pass
    return Path.home() / "maya" / "scripts"


def _log_warning(message: str) -> None:
    if cmds is not None:
        try:
            cmds.warning(f"[ContextPad] {message}")
            return
        except Exception:
            pass
    print(f"[ContextPad][WARN] {message}")


def _append_usersetup_block(marker_begin: str, marker_end: str, block: str) -> bool:
    """Append marker-based userSetup block once (idempotent)."""

    scripts_dir = _maya_user_scripts_dir()
    scripts_dir.mkdir(parents=True, exist_ok=True)
    user_setup = scripts_dir / "userSetup.py"
    existing = user_setup.read_text(encoding="utf-8") if user_setup.exists() else ""
    if marker_begin in existing and marker_end in existing:
        return False
    with user_setup.open("a", encoding="utf-8") as handle:
        if existing and not existing.endswith("\n"):
            handle.write("\n")
        handle.write(block)
    return True


def _has_usersetup_block(marker_begin: str, marker_end: str) -> bool:
    """Return True when marker block exists in userSetup.py."""

    user_setup = _maya_user_scripts_dir() / "userSetup.py"
    if not user_setup.exists():
        return False
    try:
        content = user_setup.read_text(encoding="utf-8")
    except Exception:
        return False
    return marker_begin in content and marker_end in content


def _is_writable_path(path: object) -> bool:
    """Best-effort writable check for diagnostics."""

    try:
        from pathlib import Path

        target = Path(path)  # type: ignore[arg-type]
        target.mkdir(parents=True, exist_ok=True)
        test_file = target / ".context_pad_write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        return True
    except Exception:
        return False

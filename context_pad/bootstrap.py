"""Bootstrapping helpers for launching Context Pad in Maya."""

from __future__ import annotations

from typing import Optional

from .core.app_state import AppState
from .maya_integration.qt_helpers import maya_main_window
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


def launch_context_pad() -> ManagerWindow:
    """Launch or raise the manager window and prepare overlay launchers."""

    return show_manager_window()


def show_manager_window() -> ManagerWindow:
    """Show singleton manager window."""

    global _MANAGER_WINDOW
    if _MANAGER_WINDOW is None or not _is_alive(_MANAGER_WINDOW):
        _MANAGER_WINDOW = ManagerWindow(app_state=AppState(), parent=maya_main_window())
    _MANAGER_WINDOW.show()
    _MANAGER_WINDOW.raise_()
    _MANAGER_WINDOW.activateWindow()
    return _MANAGER_WINDOW


def show_script_launcher() -> ScriptLauncher:
    """Show the singleton script launcher near the cursor."""

    global _SCRIPT_LAUNCHER
    if _SCRIPT_LAUNCHER is None or not _is_alive(_SCRIPT_LAUNCHER):
        _SCRIPT_LAUNCHER = ScriptLauncher(parent=maya_main_window())
    _SCRIPT_LAUNCHER.show_at_cursor()
    return _SCRIPT_LAUNCHER


def show_set_launcher() -> SetLauncher:
    """Show the singleton set launcher near the cursor."""

    global _SET_LAUNCHER
    if _SET_LAUNCHER is None or not _is_alive(_SET_LAUNCHER):
        _SET_LAUNCHER = SetLauncher(parent=maya_main_window())
    _SET_LAUNCHER.show_at_cursor()
    return _SET_LAUNCHER




def hide_script_launcher() -> None:
    """Hide/close script launcher unless pinned."""

    global _SCRIPT_LAUNCHER
    if _SCRIPT_LAUNCHER is None or not _is_alive(_SCRIPT_LAUNCHER):
        return
    if _SCRIPT_LAUNCHER.is_pinned():
        return
    _SCRIPT_LAUNCHER.close()


def hide_set_launcher() -> None:
    """Hide/close set launcher unless pinned."""

    global _SET_LAUNCHER
    if _SET_LAUNCHER is None or not _is_alive(_SET_LAUNCHER):
        return
    if _SET_LAUNCHER.is_pinned():
        return
    _SET_LAUNCHER.close()

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

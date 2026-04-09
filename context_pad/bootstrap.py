"""Bootstrapping helpers for launching Context Pad in Maya."""

from __future__ import annotations

from typing import Optional

from .core.app_state import AppState
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

    global _SCRIPT_LAUNCHER, _SCRIPT_HOLD_ACTIVE
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

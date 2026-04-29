"""Qt compatibility helpers for Maya and future Qt versions."""

from __future__ import annotations

from typing import Optional

try:
    from PySide2 import QtCore, QtGui, QtWidgets  # type: ignore
    from shiboken2 import wrapInstance  # type: ignore
    QT_API = "PySide2"
except ImportError:  # pragma: no cover - fallback path
    from PySide6 import QtCore, QtGui, QtWidgets  # type: ignore
    from shiboken6 import wrapInstance  # type: ignore
    QT_API = "PySide6"


def maya_main_window() -> Optional[QtWidgets.QWidget]:
    """Return Maya's main window widget when available."""

    try:
        from maya import OpenMayaUI as omui  # type: ignore
    except Exception:
        return None

    ptr = omui.MQtUtil.mainWindow()
    if ptr is None:
        return None
    return wrapInstance(int(ptr), QtWidgets.QWidget)

"""Shared UI styles for Context Pad widgets."""

from __future__ import annotations


def launcher_stylesheet() -> str:
    """Return stylesheet used by translucent launcher widgets."""

    return """
    QWidget#ContextPadBody {
        background-color: rgba(22, 22, 24, 210);
        border: 1px solid rgba(255, 255, 255, 28);
        border-radius: 12px;
    }
    QLabel#ContextPadTitle {
        color: rgb(230, 230, 235);
        font-size: 11px;
        font-weight: 600;
    }
    QListWidget#ContextPadCategoryList {
        background: rgba(0, 0, 0, 70);
        border: 1px solid rgba(255, 255, 255, 22);
        border-radius: 8px;
        color: rgb(220, 220, 225);
    }
    QListWidget#ContextPadCategoryList::item {
        height: 24px;
        padding-left: 6px;
        border-radius: 4px;
    }
    QListWidget#ContextPadCategoryList::item:selected {
        background: rgba(120, 170, 255, 130);
    }
    QPushButton#ContextPadCommandButton {
        border: 1px solid rgba(255, 255, 255, 30);
        border-radius: 8px;
        color: white;
        font-size: 10px;
        font-weight: 600;
        padding: 6px;
    }
    QFrame#ContextPadPinZone {
        background: rgba(255, 255, 255, 20);
        border: 1px solid rgba(255, 255, 255, 26);
        border-radius: 8px;
    }
    QPushButton#ContextPadPinButton {
        background: rgba(0, 0, 0, 55);
        border: 1px solid rgba(255, 255, 255, 35);
        border-radius: 6px;
        color: rgb(230, 230, 230);
        padding: 4px 8px;
    }
    """

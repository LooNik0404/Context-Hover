"""Shared UI styles for Context Pad widgets."""

from __future__ import annotations


def launcher_stylesheet() -> str:
    """Return stylesheet used by translucent launcher widgets."""

    return """
    QWidget#ContextPadBody {
        background-color: rgba(24, 25, 27, 208);
        border: 1px solid rgba(255, 255, 255, 22);
        border-radius: 12px;
    }
    QLabel#ContextPadLeftLabel {
        color: rgba(220, 223, 228, 180);
        font-size: 9px;
        font-weight: 600;
        letter-spacing: 0.5px;
        padding-left: 2px;
    }
    QListWidget#ContextPadCategoryList {
        background: transparent;
        border: none;
        color: rgb(220, 223, 228);
        outline: none;
    }
    QListWidget#ContextPadCategoryList::item {
        padding: 5px 6px;
        margin: 1px 0px;
        border-radius: 6px;
    }
    QListWidget#ContextPadCategoryList::item:selected {
        background: rgba(130, 160, 205, 75);
        color: rgb(240, 243, 248);
    }
    QPushButton#ContextPadRailButton {
        background: transparent;
        border: 1px solid rgba(255, 255, 255, 16);
        border-radius: 6px;
        color: rgb(220, 223, 228);
        padding: 5px 6px;
        text-align: center;
    }
    QPushButton#ContextPadRailButton:hover {
        background: rgba(130, 160, 205, 48);
        border: 1px solid rgba(160, 190, 235, 44);
    }
    QFrame#ContextPadDivider {
        background: rgba(255, 255, 255, 24);
        min-width: 1px;
        max-width: 1px;
    }
    QPushButton#ContextPadCommandButton,
    QPushButton#ContextPadRelatedButton {
        border: 1px solid rgba(255, 255, 255, 24);
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
        padding: 6px;
        text-align: center;
    }
    QScrollArea {
        background: transparent;
        border: none;
    }
    QScrollBar:vertical {
        background: rgba(255, 255, 255, 12);
        width: 8px;
        margin: 2px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical {
        background: rgba(210, 220, 235, 70);
        min-height: 20px;
        border-radius: 4px;
    }
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {
        background: transparent;
    }
    QFrame#ContextPadUtilityBar {
        background: transparent;
        border: none;
    }
    QToolButton#ContextPadIconButton {
        background: rgba(255, 255, 255, 16);
        border: 1px solid rgba(255, 255, 255, 24);
        border-radius: 7px;
        color: rgba(238, 241, 246, 210);
        min-width: 14px;
        min-height: 14px;
        padding: 1px;
    }
    QToolButton#ContextPadIconButton:hover {
        background: rgba(255, 255, 255, 24);
    }
    """

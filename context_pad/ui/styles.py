"""Shared UI styles for Context Pad widgets."""

from __future__ import annotations


def launcher_stylesheet() -> str:
    """Return stylesheet used by translucent launcher widgets."""

    return """
    QWidget#ContextPadBody {
        background-color: rgba(20, 22, 24, 214);
        border: 1px solid rgba(255, 255, 255, 20);
        border-radius: 12px;
    }
    QLabel#ContextPadLeftLabel {
        color: rgba(205, 210, 218, 170);
        font-size: 9px;
        font-weight: 600;
        letter-spacing: 0.3px;
        padding-left: 2px;
    }
    QListWidget#ContextPadCategoryList {
        background: transparent;
        border: none;
        color: rgb(214, 218, 224);
        outline: none;
    }
    QListWidget#ContextPadCategoryList::item {
        min-height: 24px;
        padding: 2px 6px;
        margin: 1px 0px;
        border-radius: 6px;
    }
    QListWidget#ContextPadCategoryList::item:selected {
        background: rgba(130, 155, 188, 58);
        color: rgb(238, 241, 246);
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
        background: rgba(255, 255, 255, 18);
        min-width: 1px;
        max-width: 1px;
    }
    QPushButton#ContextPadCommandButton,
    QPushButton#ContextPadRelatedButton {
        border: 1px solid rgba(255, 255, 255, 20);
        border-radius: 8px;
        font-size: 11px;
        font-weight: 600;
        padding: 4px 6px;
        text-align: center;
    }
    QPushButton#ContextPadRelatedButton {
        border-radius: 6px;
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
        min-height: 22px;
        max-height: 22px;
    }
    QToolButton#ContextPadIconButton {
        background: rgba(255, 255, 255, 12);
        border: 1px solid rgba(255, 255, 255, 20);
        border-radius: 6px;
        color: rgba(234, 238, 244, 205);
        min-width: 22px;
        min-height: 22px;
        max-width: 22px;
        max-height: 22px;
        padding: 0px;
    }
    QToolButton#ContextPadIconButton:hover {
        background: rgba(255, 255, 255, 20);
    }
    """


def manager_stylesheet() -> str:
    """Return stylesheet for calm, tool-like manager surface."""

    return """
    QMainWindow {
        background: rgb(34, 36, 40);
        color: rgb(220, 224, 230);
    }
    QGroupBox {
        border: 1px solid rgba(255, 255, 255, 16);
        border-radius: 8px;
        margin-top: 8px;
        padding-top: 8px;
        font-weight: 600;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 2px;
    }
    QListWidget, QTreeWidget, QPlainTextEdit, QLineEdit, QComboBox {
        border: 1px solid rgba(255, 255, 255, 18);
        border-radius: 6px;
        background: rgba(14, 16, 18, 145);
        padding: 3px;
    }
    QPushButton {
        border: 1px solid rgba(255, 255, 255, 20);
        border-radius: 8px;
        padding: 4px 8px;
        min-height: 24px;
        background: rgba(255, 255, 255, 9);
    }
    QPushButton:hover {
        background: rgba(255, 255, 255, 14);
    }
    """

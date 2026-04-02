"""Category list widget for launcher filtering."""

from __future__ import annotations

from typing import Dict, List

from context_pad.maya_integration.qt_helpers import QtCore, QtGui, QtWidgets


class CategoryBar(QtWidgets.QWidget):
    """Compact list widget for displaying selectable categories."""

    category_changed = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initialize the category bar."""

        super().__init__(parent)
        self._categories: List[Dict[str, str]] = []

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._list = QtWidgets.QListWidget()
        self._list.setObjectName("ContextPadCategoryList")
        self._list.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._list)

    def set_categories(self, categories: List[Dict[str, str]]) -> None:
        """Populate categories from data records with id/name/color keys."""

        self._categories = categories
        self._list.clear()
        for category in categories:
            label = category.get("name", category.get("id", "Category"))
            item = QtWidgets.QListWidgetItem(label)
            item.setData(QtCore.Qt.UserRole, category.get("id", ""))
            color = category.get("color")
            if color:
                item.setBackground(QtGui.QColor(color))
            self._list.addItem(item)

        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def current_category(self) -> str:
        """Return the currently selected category id."""

        item = self._list.currentItem()
        if item is None:
            return ""
        return str(item.data(QtCore.Qt.UserRole) or "")

    def _on_selection_changed(self) -> None:
        """Emit category changed when user changes selection."""

        self.category_changed.emit(self.current_category())

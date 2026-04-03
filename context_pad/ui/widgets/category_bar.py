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
        layout.setSpacing(4)

        self._label = QtWidgets.QLabel("Categories")
        self._label.setObjectName("ContextPadLeftLabel")
        layout.addWidget(self._label)

        self._list = QtWidgets.QListWidget()
        self._list.setObjectName("ContextPadCategoryList")
        self._list.itemSelectionChanged.connect(self._on_selection_changed)
        self._list.viewport().installEventFilter(self)
        self._list.installEventFilter(self)
        layout.addWidget(self._list, 1)

    def set_title(self, title: str) -> None:
        """Set optional compact title for the left column."""

        self._label.setText(title)
        self._label.setVisible(bool(title))

    def set_categories(self, categories: List[Dict[str, str]]) -> None:
        """Populate categories from data records with id/name/color keys."""

        previous_category_id = self.current_category()
        self._categories = categories
        self._list.blockSignals(True)
        self._list.clear()
        for category in categories:
            label = category.get("name", category.get("id", "Category"))
            item = QtWidgets.QListWidgetItem(label)
            item.setData(QtCore.Qt.UserRole, category.get("id", ""))
            color = category.get("color")
            if color:
                item.setForeground(QtGui.QColor(color))
            self._list.addItem(item)

        if self._list.count() > 0:
            restored = self.set_current_category(previous_category_id)
            if not restored:
                self._list.setCurrentRow(0)
        self._list.blockSignals(False)
        self.category_changed.emit(self.current_category())

    def set_current_category(self, category_id: str) -> bool:
        """Select category by id; return True when found."""

        if not category_id:
            return False
        for row in range(self._list.count()):
            item = self._list.item(row)
            if str(item.data(QtCore.Qt.UserRole) or "") == category_id:
                self._list.setCurrentRow(row)
                return True
        return False

    def current_category(self) -> str:
        """Return the currently selected category id."""

        item = self._list.currentItem()
        if item is None:
            return ""
        return str(item.data(QtCore.Qt.UserRole) or "")

    def _on_selection_changed(self) -> None:
        """Emit category changed when user changes selection."""

        self.category_changed.emit(self.current_category())

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """Switch categories via mouse wheel when hovering category rail."""

        if watched in {self._list, self._list.viewport()} and event.type() == QtCore.QEvent.Wheel:
            wheel_event = event
            if self._list.count() == 0:
                return True

            delta = wheel_event.angleDelta().y()
            if delta == 0:
                return True

            current_row = self._list.currentRow()
            if current_row < 0:
                current_row = 0
            step = -1 if delta > 0 else 1
            next_row = max(0, min(self._list.count() - 1, current_row + step))
            if next_row != current_row:
                self._list.setCurrentRow(next_row)
            return True

        return super().eventFilter(watched, event)

"""Grid widget for launcher command placeholders."""

from __future__ import annotations

from typing import Dict, List

from context_pad.maya_integration.qt_helpers import QtCore, QtGui, QtWidgets


class CommandGrid(QtWidgets.QWidget):
    """Grid widget rendering color-coded buttons."""

    button_clicked = QtCore.Signal(dict)
    button_context_requested = QtCore.Signal(dict, object)
    button_aux_clicked = QtCore.Signal(dict, str)

    def __init__(self, parent: QtWidgets.QWidget | None = None, columns: int = 2) -> None:
        """Initialize the command grid."""

        super().__init__(parent)
        self.setAutoFillBackground(False)
        self.setStyleSheet("background: transparent;")
        self._buttons: List[Dict[str, str]] = []
        self._visible_buttons: List[Dict[str, str]] = []
        self._visible_button_ids: List[str] = []
        self._columns = max(1, columns)
        self._display_mode = "grid"
        self._available_width_override: int | None = None
        self._last_layout_width = -1
        self._visual_profile = "default"

        self._layout = QtWidgets.QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setHorizontalSpacing(6)
        self._layout.setVerticalSpacing(4)
        self._layout.setAlignment(QtCore.Qt.AlignTop)
        self._button_height = 34

    def set_columns(self, columns: int) -> None:
        """Set number of columns used for button layout."""

        self._columns = max(1, columns)
        self._rebuild_grid(self._buttons)

    def set_display_mode(self, mode: str) -> None:
        """Set visual display mode: grid (default) or list (compact rows)."""

        normalized = str(mode or "grid").strip().lower()
        self._display_mode = "list" if normalized == "list" else "grid"
        self._rebuild_grid(self._visible_buttons or self._buttons)

    def set_available_width_override(self, width: int | None) -> None:
        """Optionally force layout width source from owner viewport geometry."""

        self._available_width_override = int(width) if width is not None else None
        self._rebuild_grid(self._visible_buttons or self._buttons)

    def set_visual_profile(self, profile: str) -> None:
        """Set visual profile for button rendering without changing layout behavior."""

        self._visual_profile = str(profile or "default").strip().lower()
        self._rebuild_grid(self._visible_buttons or self._buttons)

    def set_buttons(self, buttons: List[Dict[str, str]], rebuild: bool = True) -> None:
        """Populate grid from button records."""

        self._buttons = buttons
        if rebuild:
            self._set_visible_buttons(buttons)

    def filter_by_category(self, category_id: str) -> None:
        """Display buttons matching category id, or all when blank."""

        filtered = [b for b in self._buttons if not category_id or b.get("category_id") == category_id]
        self._set_visible_buttons(filtered)

    def _set_visible_buttons(self, buttons: List[Dict[str, str]]) -> None:
        """Rebuild only when visible ids actually changed."""

        visible_fingerprint = [
            "|".join(
                [
                    str(item.get("id", "")),
                    str(item.get("name", "")),
                    str(item.get("color", "")),
                    str(item.get("tooltip", "")),
                    str(item.get("item_type", "button")),
                    str(item.get("button_size", "normal")),
                ]
            )
            for item in buttons
        ]
        if visible_fingerprint == self._visible_button_ids:
            return
        self._visible_buttons = list(buttons)
        self._visible_button_ids = visible_fingerprint
        self._rebuild_grid(buttons)

    def _rebuild_grid(self, buttons: List[Dict[str, str]]) -> None:
        """Recreate the visible button grid."""

        self._last_layout_width = self._current_layout_width()
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        row = 0
        col = 0
        module_width = self._module_pixel_width()
        for item_data in buttons:
            item_type = str(item_data.get("item_type", "button"))
            if item_type == "separator":
                if col != 0:
                    row += 1
                    col = 0
                separator = self._make_separator_widget(item_data)
                self._layout.addWidget(separator, row, 0, 1, self._columns)
                row += 1
                continue

            if bool(item_data.get("show_set_algebra", False)) and self._display_mode == "list":
                if col != 0:
                    row += 1
                    col = 0
                row_widget = self._make_set_algebra_row(item_data, module_width)
                self._layout.addWidget(row_widget, row, 0, 1, self._columns)
                row += 1
                continue

            button_name = str(item_data.get("name", "Button"))
            button = QtWidgets.QPushButton()
            button.setObjectName("ContextPadCommandButton")
            tooltip = str(item_data.get("tooltip", "")).strip()
            button.setToolTip(tooltip or str(button_name))

            color_value = str(item_data.get("color", "#4A89DC"))
            size_mode = str(item_data.get("button_size", "normal")).lower()
            background = self._button_background(color_value, size_mode)
            foreground = self._contrast_color(background)
            button.setStyleSheet(self._button_stylesheet(background, foreground, size_mode))

            button.clicked.connect(lambda _=False, data=item_data: self.button_clicked.emit(data))
            button.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            button.customContextMenuRequested.connect(
                lambda pos, data=item_data, b=button: self.button_context_requested.emit(data, b.mapToGlobal(pos))
            )

            if size_mode == "large":
                col_span = self._columns
            elif size_mode == "small":
                col_span = 1
            else:
                col_span = min(2, self._columns)
            if col + col_span > self._columns:
                row += 1
                col = 0

            button_width = self._span_pixel_width(col_span, module_width)
            button.setMinimumWidth(button_width)
            button.setMaximumWidth(button_width)
            if size_mode == "large":
                row_height = 32 if self._display_mode == "list" else int(self._button_height + 10)
            elif size_mode == "small":
                row_height = 22 if self._display_mode == "list" else int(self._button_height - 6)
            else:
                row_height = 24 if self._display_mode == "list" else self._button_height
            button.setMinimumHeight(row_height)
            button.setMaximumHeight(row_height)
            button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            button.setText(self._elide_button_text(button_name, button.fontMetrics(), button_width - 14))

            self._layout.addWidget(button, row, col, 1, col_span)
            col += col_span
            if col >= self._columns:
                row += 1
                col = 0

        self._layout.setRowStretch(row + 1, 1)

    def _make_set_algebra_row(self, item_data: Dict[str, str], module_width: int) -> QtWidgets.QWidget:
        """Create set row with main replace zone plus compact + / - action zones."""

        container = QtWidgets.QFrame(self)
        container.setObjectName("ContextPadSetAlgebraRow")
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        button_name = str(item_data.get("name", "Set"))
        tooltip = str(item_data.get("tooltip", "")).strip() or button_name
        color_value = str(item_data.get("color", "#4A89DC"))
        background = self._button_background(color_value, "normal")
        foreground = self._contrast_color(background)

        row_width = self._span_pixel_width(self._columns, module_width)
        aux_width = 24
        main_width = max(64, row_width - (aux_width * 2) - 8)

        main_button = QtWidgets.QPushButton()
        main_button.setObjectName("ContextPadSetMainButton")
        main_button.setToolTip(f"{tooltip}\nLMB: Replace selection")
        main_button.setMinimumHeight(24)
        main_button.setMaximumHeight(24)
        main_button.setMinimumWidth(main_width)
        main_button.setMaximumWidth(main_width)
        main_button.setStyleSheet(self._button_stylesheet(background, foreground, "normal"))
        main_button.setText(self._elide_button_text(button_name, main_button.fontMetrics(), main_width - 14))
        main_button.clicked.connect(lambda _=False, data=item_data: self.button_clicked.emit(data))
        main_button.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        main_button.customContextMenuRequested.connect(
            lambda pos, data=item_data, b=main_button: self.button_context_requested.emit(data, b.mapToGlobal(pos))
        )

        plus_button = QtWidgets.QPushButton("+")
        plus_button.setObjectName("ContextPadSetPlusButton")
        plus_button.setToolTip(f"{tooltip}\nAdd set to current selection")
        plus_button.setMinimumSize(aux_width, 24)
        plus_button.setMaximumSize(aux_width, 24)
        plus_button.setStyleSheet(self._button_stylesheet(background.lighter(110), foreground, "small"))
        plus_button.clicked.connect(lambda _=False, data=item_data: self.button_aux_clicked.emit(data, "add"))

        minus_button = QtWidgets.QPushButton("–")
        minus_button.setObjectName("ContextPadSetMinusButton")
        minus_button.setToolTip(f"{tooltip}\nRemove set from current selection")
        minus_button.setMinimumSize(aux_width, 24)
        minus_button.setMaximumSize(aux_width, 24)
        minus_button.setStyleSheet(self._button_stylesheet(background.darker(106), foreground, "small"))
        minus_button.clicked.connect(lambda _=False, data=item_data: self.button_aux_clicked.emit(data, "subtract"))

        layout.addWidget(main_button, 1)
        layout.addWidget(plus_button, 0)
        layout.addWidget(minus_button, 0)
        return container

    def _make_separator_widget(self, item_data: Dict[str, str]) -> QtWidgets.QWidget:
        """Create subtle full-width separator widget with optional muted label."""

        container = QtWidgets.QWidget(self)
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(3)
        container.setMinimumHeight(11)
        container.setMaximumHeight(11)

        line_left = QtWidgets.QFrame(container)
        line_left.setFrameShape(QtWidgets.QFrame.HLine)
        line_left.setStyleSheet("color: rgba(220,220,220,28);")
        layout.addWidget(line_left, 1)

        label_text = str(item_data.get("name", "")).strip()
        if label_text:
            label = QtWidgets.QLabel(label_text, container)
            label.setStyleSheet("color: rgba(220,220,220,86); font-size: 8px; letter-spacing: 0.2px;")
            layout.addWidget(label, 0)

        line_right = QtWidgets.QFrame(container)
        line_right.setFrameShape(QtWidgets.QFrame.HLine)
        line_right.setStyleSheet("color: rgba(220,220,220,28);")
        layout.addWidget(line_right, 1)
        return container

    def _module_pixel_width(self) -> int:
        spacing = max(0, int(self._layout.horizontalSpacing()))
        margins = self._layout.contentsMargins()
        if self._available_width_override is not None:
            viewport_width = self._available_width_override
        else:
            viewport = self.parentWidget()
            viewport_width = viewport.width() if viewport is not None else self.width()
        available = max(1, int(viewport_width) - margins.left() - margins.right())
        total_spacing = spacing * max(0, self._columns - 1)
        module = (available - total_spacing) // max(1, self._columns)
        return max(28, int(module))

    def _span_pixel_width(self, span: int, module_width: int) -> int:
        spacing = self._layout.horizontalSpacing()
        return (module_width * span) + (spacing * max(0, span - 1))

    def _elide_button_text(self, text: str, metrics: QtGui.QFontMetrics, max_width: int) -> str:
        limit = max(12, int(max_width))
        if metrics.horizontalAdvance(text) <= limit:
            return text

        clipped = str(text)
        while clipped and metrics.horizontalAdvance(clipped) > limit:
            clipped = clipped[:-1]
        return clipped

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:  # noqa: N802
        """Reflow modular widths against real viewport/content width."""

        super().resizeEvent(event)
        if self._visible_buttons and self._current_layout_width() != self._last_layout_width:
            self._rebuild_grid(self._visible_buttons)

    def _current_layout_width(self) -> int:
        """Return current effective width driver for row/module calculations."""

        if self._available_width_override is not None:
            return int(self._available_width_override)
        viewport = self.parentWidget()
        if viewport is not None:
            return int(viewport.width())
        return int(self.width())

    def _contrast_color(self, color: QtGui.QColor) -> QtGui.QColor:
        """Return black/white text color based on luminance contrast."""

        luminance = (0.299 * color.red()) + (0.587 * color.green()) + (0.114 * color.blue())
        return QtGui.QColor("#111111") if luminance > 170 else QtGui.QColor("#F4F6FA")

    def _button_background(self, base_hex: str, size_mode: str) -> QtGui.QColor:
        """Return restrained background tone by size mode for stronger hierarchy."""

        base = QtGui.QColor(base_hex)
        if self._visual_profile != "script":
            return base

        neutral = QtGui.QColor("#4C5560")
        if size_mode == "small":
            mix = 0.58
        elif size_mode == "large":
            mix = 0.18
        else:
            mix = 0.34
        return QtGui.QColor(
            int((base.red() * (1.0 - mix)) + (neutral.red() * mix)),
            int((base.green() * (1.0 - mix)) + (neutral.green() * mix)),
            int((base.blue() * (1.0 - mix)) + (neutral.blue() * mix)),
        )

    def _button_stylesheet(self, background: QtGui.QColor, foreground: QtGui.QColor, size_mode: str) -> str:
        """Build stateful stylesheet for clearer normal/hover/pressed visual feedback."""

        hover = background.lighter(112)
        pressed = background.darker(114)
        border_alpha = "52" if size_mode == "large" else "38" if size_mode == "normal" else "28"
        radius = "9" if size_mode == "large" else "8" if size_mode == "normal" else "7"
        left_pad = "8" if self._display_mode == "list" else "6"
        align = "left" if self._display_mode == "list" else "center"
        return (
            "QPushButton {"
            f"background-color: {background.name()};"
            f"color: {foreground.name()};"
            f"border: 1px solid rgba(255,255,255,{border_alpha});"
            f"border-radius: {radius}px;"
            f"text-align: {align};"
            f"padding-left: {left_pad}px; padding-right: 4px;"
            "}"
            "QPushButton:hover {"
            f"background-color: {hover.name()};"
            "border: 1px solid rgba(255,255,255,64);"
            "}"
            "QPushButton:pressed {"
            f"background-color: {pressed.name()};"
            "border: 1px solid rgba(255,255,255,92);"
            "}"
        )

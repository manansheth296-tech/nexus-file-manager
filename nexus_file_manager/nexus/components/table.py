"""
Table Row states: Normal, Alternating, Hover, Selected, Multi-Selected.

NexusRowDelegate paints each row's background from tokens (so states re-theme
instantly); NexusTableView supplies hover tracking + selection count.
`delegate.force_state(row, state)` pins a state for the gallery / design QA.
"""
from __future__ import annotations

from PyQt6.QtCore import QModelIndex, QRectF, QSize, Qt
from PyQt6.QtGui import QPainter, QPalette
from PyQt6.QtWidgets import (QAbstractItemView, QHeaderView, QStyle, QStyledItemDelegate,
                             QStyleOptionViewItem, QTableView, QWidget)

from nexus.styles.theme_manager import theme_manager
from nexus.tokens.base import ICON_SIZE_MD, ROW_HEIGHT, TABLE_HEADER_HEIGHT
from nexus.tokens.color_utils import to_qcolor


class RowState:
    NORMAL = "normal"
    ALTERNATING = "alternating"
    HOVER = "hover"
    SELECTED = "selected"
    MULTI_SELECTED = "multi"


class NexusRowDelegate(QStyledItemDelegate):
    def __init__(self, view: "NexusTableView"):
        super().__init__(view)
        self._view = view
        self._forced: dict[int, str] = {}

    def force_state(self, row: int, state: str | None) -> None:
        if state is None:
            self._forced.pop(row, None)
        else:
            self._forced[row] = state
        self._view.viewport().update()

    def row_state(self, index: QModelIndex) -> str:
        row = index.row()
        if row in self._forced:
            return self._forced[row]
        sel = self._view.selectionModel()
        if sel and sel.isRowSelected(row, index.parent()):
            return RowState.MULTI_SELECTED if self._view.selected_row_count > 1 else RowState.SELECTED
        if row == self._view.hover_row:
            return RowState.HOVER
        return RowState.ALTERNATING if row % 2 else RowState.NORMAL

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        t = theme_manager().tokens
        state = self.row_state(index)
        bg = {
            RowState.ALTERNATING: t.COLOR_ROW_ALT,
            RowState.HOVER: t.COLOR_HOVER_OVERLAY,
            RowState.SELECTED: t.COLOR_SELECTED_BG,
            RowState.MULTI_SELECTED: t.COLOR_MULTI_SELECTED_BG,
        }.get(state)

        painter.save()
        if bg:
            painter.fillRect(option.rect, to_qcolor(bg))
        selected = state in (RowState.SELECTED, RowState.MULTI_SELECTED)
        if selected and index.column() == 0:                      # accent bar on the left edge
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(to_qcolor(t.COLOR_ACCENT_PRIMARY))
            r = option.rect
            painter.drawRoundedRect(QRectF(r.left(), r.top() + 6, 3, r.height() - 12), 1.5, 1.5)
        if self._view.hasFocus() and index.row() == self._view.currentIndex().row():
            painter.setPen(to_qcolor(t.COLOR_BORDER_FOCUS))       # keyboard-focus row: hairlines
            painter.drawLine(option.rect.topLeft(), option.rect.topRight())
            painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
        painter.restore()

        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        opt.state &= ~(QStyle.StateFlag.State_Selected | QStyle.StateFlag.State_MouseOver
                       | QStyle.StateFlag.State_HasFocus)
        primary = index.column() == 0 or selected or state == RowState.HOVER
        opt.palette.setColor(QPalette.ColorRole.Text,
                             to_qcolor(t.COLOR_TEXT_PRIMARY if primary else t.COLOR_TEXT_SECONDARY))
        self.paint_content(painter, opt, index, state)

    def paint_content(self, painter: QPainter, opt: QStyleOptionViewItem, index: QModelIndex, state: str) -> None:
        """Override in subclasses to custom-paint cells (badges, checkboxes, bars) on top of the row background."""
        super().paint(painter, opt, index)


class NexusTableView(QTableView):
    """Details-mode file table: sortable header, 36px rows, token-painted row states."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.hover_row = -1
        self.selected_row_count = 0
        self.row_delegate = NexusRowDelegate(self)
        self.setItemDelegate(self.row_delegate)
        self.setMouseTracking(True)
        self.setIconSize(QSize(ICON_SIZE_MD, ICON_SIZE_MD))
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setAlternatingRowColors(False)                       # delegate handles alternation
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.verticalHeader().hide()
        self.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        hh = self.horizontalHeader()
        hh.setFixedHeight(TABLE_HEADER_HEIGHT)
        hh.setHighlightSections(False)
        hh.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)   # QSS text-align is ignored by QHeaderView
        hh.setSectionsClickable(True)
        hh.setStretchLastSection(True)
        theme_manager().theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, _tokens) -> None:
        self.viewport().update()

    def set_column_spec(self, spec: list) -> None:
        """spec: per column either an int (fixed width px) or 'stretch'."""
        hh = self.horizontalHeader()
        for col, how in enumerate(spec):
            if how == "stretch":
                hh.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
            else:
                hh.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
                self.setColumnWidth(col, int(how))

    def setModel(self, model) -> None:
        super().setModel(model)
        self.selectionModel().selectionChanged.connect(self._on_selection_changed)
        hh = self.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col, w in zip(range(1, model.columnCount()), (110, 150, 170)):
            hh.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
            self.setColumnWidth(col, w)

    def _on_selection_changed(self, *_):
        self.selected_row_count = len(self.selectionModel().selectedRows())
        self.viewport().update()

    def mouseMoveEvent(self, e):
        row = self.indexAt(e.position().toPoint()).row()
        if row != self.hover_row:
            self.hover_row = row
            self.viewport().update()
        super().mouseMoveEvent(e)

    def leaveEvent(self, e):
        self.hover_row = -1
        self.viewport().update()
        super().leaveEvent(e)

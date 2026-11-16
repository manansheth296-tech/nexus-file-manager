"""
ExplorerView – the central file area: Details Table (Screen 1) or Icon Grid (Screen 2).

Both modes share one FileModel + proxy (sorting, live filter). Selection is carried across
mode switches. Double-click emits `itemActivated` (HOOK: open file / enter folder).
"""
from __future__ import annotations

from PyQt6.QtCore import QItemSelection, QItemSelectionModel, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QFontMetrics, QPainter
from PyQt6.QtWidgets import (QAbstractItemView, QLabel, QListView, QStackedWidget, QStyle,
                             QStyledItemDelegate, QVBoxLayout, QWidget)

from nexus.assets import icon_loader
from nexus.components import NexusTableView
from nexus.components._util import resolve_color
from nexus.core.mock_data import format_size
from nexus.styles.theme_manager import theme_manager
from nexus.tokens.base import (FONT_SIZE_XS, GRID_CELL_H, GRID_CELL_W, SPACE_MD, SPACE_SM, SPACE_XS)
from nexus.tokens.color_utils import to_qcolor
from nexus.tokens.file_types import kind_color, kind_icon
from nexus.views.file_model import ROLE_FILE, FileModel, FileSortProxy

GRID_ICON = 40


class GridCardDelegate(QStyledItemDelegate):
    """Rounded file card: centred icon, truncated name, size caption. Full name in tooltip."""

    def sizeHint(self, option, index) -> QSize:
        return QSize(GRID_CELL_W, GRID_CELL_H)

    def paint(self, p: QPainter, option, index) -> None:
        t = theme_manager().tokens
        f = index.data(ROLE_FILE)
        card = QRectF(option.rect).adjusted(SPACE_XS, SPACE_XS, -SPACE_XS, -SPACE_XS)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        fill = t.COLOR_SELECTED_BG if selected else (t.COLOR_HOVER_OVERLAY if hovered else t.COLOR_BG_CARD)
        border = t.COLOR_ACCENT_PRIMARY if selected else (t.COLOR_BORDER_STRONG if hovered else t.COLOR_BORDER)
        p.setPen(to_qcolor(border))
        p.setBrush(to_qcolor(fill))
        p.drawRoundedRect(card.adjusted(.5, .5, -.5, -.5), t.RADIUS_LG, t.RADIUS_LG)
        if option.state & QStyle.StateFlag.State_HasFocus and option.widget and option.widget.hasFocus():
            p.setPen(to_qcolor(t.COLOR_BORDER_FOCUS))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(card, t.RADIUS_LG, t.RADIUS_LG)

        color = resolve_color(kind_color(f["kind"]), t)
        pm = icon_loader.render_pixmap(kind_icon(f["kind"]), color, GRID_ICON)
        p.drawPixmap(int(card.center().x() - GRID_ICON / 2), int(card.top() + SPACE_MD + 4), pm)

        name_font = QFont(option.font)
        name_font.setWeight(QFont.Weight.Medium)
        p.setFont(name_font)
        p.setPen(to_qcolor(t.COLOR_TEXT_PRIMARY))
        w = int(card.width() - 2 * SPACE_SM)
        name = QFontMetrics(name_font).elidedText(f["name"], Qt.TextElideMode.ElideMiddle, w)
        y = card.top() + SPACE_MD + 4 + GRID_ICON + SPACE_SM
        p.drawText(QRectF(card.left() + SPACE_SM, y, w, 18), Qt.AlignmentFlag.AlignCenter, name)

        cap = QFont(option.font)
        cap.setPixelSize(FONT_SIZE_XS)
        p.setFont(cap)
        p.setPen(to_qcolor(t.COLOR_TEXT_MUTED))
        p.drawText(QRectF(card.left() + SPACE_SM, y + 18, w, 16), Qt.AlignmentFlag.AlignCenter,
                   "Folder" if f["size"] is None else format_size(f["size"]))
        p.restore()


class ExplorerView(QWidget):
    selectionChanged = pyqtSignal(list)     # list[dict] – selected file records
    itemActivated = pyqtSignal(dict)        # HOOK: open file / navigate into folder

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._mode = "table"
        self._syncing = False
        self.model = FileModel()
        self.proxy = FileSortProxy()
        self.proxy.setSourceModel(self.model)

        self.table = NexusTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.table.horizontalHeader().setSortIndicator(0, Qt.SortOrder.AscendingOrder)

        self.grid = QListView()
        self.grid.setModel(self.proxy)
        self.grid.setViewMode(QListView.ViewMode.IconMode)
        self.grid.setResizeMode(QListView.ResizeMode.Adjust)
        self.grid.setMovement(QListView.Movement.Static)
        self.grid.setWrapping(True)
        self.grid.setUniformItemSizes(True)
        self.grid.setGridSize(QSize(GRID_CELL_W, GRID_CELL_H))
        self.grid.setSpacing(0)
        self.grid.setMouseTracking(True)
        self.grid.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.grid.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.grid.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.grid.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.grid.setItemDelegate(GridCardDelegate(self.grid))
        self.grid.setContentsMargins(SPACE_SM, SPACE_SM, SPACE_SM, SPACE_SM)

        self.empty = QLabel("No files match your filter")
        self.empty.setProperty("role", "muted")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.stack = QStackedWidget()
        for w in (self.table, self.grid, self.empty):
            self.stack.addWidget(w)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.stack)

        self.table.selectionModel().selectionChanged.connect(lambda *_: self._on_sel("table"))
        self.grid.selectionModel().selectionChanged.connect(lambda *_: self._on_sel("grid"))
        self.table.doubleClicked.connect(self._on_double)
        self.grid.doubleClicked.connect(self._on_double)
        self.proxy.rowsInserted.connect(self._update_page)
        self.proxy.rowsRemoved.connect(self._update_page)
        self.proxy.modelReset.connect(self._update_page)
        self.proxy.layoutChanged.connect(self._update_page)

    # ── API ───────────────────────────────────────────────────────────────
    @property
    def mode(self) -> str:
        return self._mode

    def set_files(self, files: list[dict]) -> None:
        self.model.set_files(files)
        self._update_page()

    def set_filter(self, text: str) -> None:
        self.proxy.set_filter_text(text)
        self._update_page()

    def item_count(self) -> int:
        return self.proxy.rowCount()

    def selected_files(self) -> list[dict]:
        sm = (self.table if self._mode == "table" else self.grid).selectionModel()
        rows = sorted({i.row() for i in sm.selectedIndexes()})
        return [self.proxy.index(r, 0).data(ROLE_FILE) for r in rows]

    def select_names(self, names: list[str]) -> None:
        rows = [r for r in range(self.proxy.rowCount()) if self.proxy.index(r, 0).data(ROLE_FILE)["name"] in names]
        self._apply_selection(rows)
        self.selectionChanged.emit(self.selected_files())

    def set_mode(self, mode: str) -> None:
        if mode == self._mode:
            return
        rows = self._selected_rows()
        self._mode = mode
        self._apply_selection(rows)
        self._update_page()
        self.selectionChanged.emit(self.selected_files())

    # ── internals ─────────────────────────────────────────────────────────
    def _selected_rows(self) -> list[int]:
        sm = (self.table if self._mode == "table" else self.grid).selectionModel()
        return sorted({i.row() for i in sm.selectedIndexes()})

    def _apply_selection(self, rows: list[int]) -> None:
        self._syncing = True
        last = self.proxy.columnCount() - 1
        tsm, gsm = self.table.selectionModel(), self.grid.selectionModel()
        tsm.clearSelection()
        gsm.clearSelection()
        for r in rows:
            tsm.select(QItemSelection(self.proxy.index(r, 0), self.proxy.index(r, last)),
                       QItemSelectionModel.SelectionFlag.Select)
            gsm.select(self.proxy.index(r, 0), QItemSelectionModel.SelectionFlag.Select)
        self._syncing = False
        self.table._on_selection_changed()
        self.grid.viewport().update()

    def _on_sel(self, source: str) -> None:
        if not self._syncing and source == self._mode:
            self.selectionChanged.emit(self.selected_files())

    def _on_double(self, index) -> None:
        self.itemActivated.emit(index.sibling(index.row(), 0).data(ROLE_FILE))

    def _update_page(self, *_) -> None:
        if self.proxy.rowCount() == 0:
            self.stack.setCurrentWidget(self.empty)
        else:
            self.stack.setCurrentWidget(self.table if self._mode == "table" else self.grid)

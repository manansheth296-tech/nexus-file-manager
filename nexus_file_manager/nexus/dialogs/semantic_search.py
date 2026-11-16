"""
Semantic & Content Search (780 × 520) [spec Screen 8]: prominent search bar with a focus halo; results with file icon,
filename, "Relevance: NN%" badge and a context snippet whose matching terms are bold + underlined in the accent colour.

UI-only: `core/mock_search.search()` fakes meaning with a synonym table. HOOK: `searchRequested(query)` / `resultActivated(dict)`.
"""
from __future__ import annotations

import html
import re

from PyQt6.QtCore import QRectF, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QFontMetrics, QPainter, QStandardItem, QStandardItemModel, QTextDocument
from PyQt6.QtWidgets import (QAbstractItemView, QHBoxLayout, QLabel, QListView, QStackedWidget, QStyle,
                             QStyledItemDelegate, QVBoxLayout, QWidget)

from nexus.assets import icon_loader
from nexus.components import GlowInput, IconTile, NexusDialog, Divider
from nexus.components._util import resolve_color
from nexus.core import mock_search
from nexus.styles.theme_manager import theme_manager
from nexus.tokens.base import DIALOG_SEMANTIC_SEARCH, FONT_SIZE_XS, SPACE_LG, SPACE_MD, SPACE_SM, SPACE_XL
from nexus.tokens.color_utils import to_hex, to_qcolor, with_alpha
from nexus.tokens.file_types import kind_color, kind_icon

ROLE = Qt.ItemDataRole.UserRole
ITEM_H = 92


def highlight_html(text: str, terms: list[str], base: str, accent: str) -> str:
    """HTML for `text` with every occurrence of `terms` bold + underlined in `accent`."""
    safe = html.escape(text)
    if terms:
        pattern = re.compile("(" + "|".join(re.escape(html.escape(t)) for t in terms) + ")", re.I)
        safe = pattern.sub(lambda m: f'<span style="color:{accent}; font-weight:600; text-decoration:underline;">{m.group(1)}</span>', safe)
    return f'<span style="color:{base};">{safe}</span>'


class ResultDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index) -> QSize:
        return QSize(option.rect.width(), ITEM_H)

    def paint(self, p: QPainter, option, index) -> None:
        t = theme_manager().tokens
        r = index.data(ROLE)
        card = QRectF(option.rect).adjusted(0, 3, 0, -3)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        p.save()
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        fill = t.COLOR_SELECTED_BG if selected else (t.COLOR_HOVER_OVERLAY if hovered else t.COLOR_BG_CARD)
        border = t.COLOR_ACCENT_PRIMARY if selected else t.COLOR_BORDER
        p.setPen(to_qcolor(border))
        p.setBrush(to_qcolor(fill))
        p.drawRoundedRect(card.adjusted(.5, .5, -.5, -.5), t.RADIUS_LG, t.RADIUS_LG)

        accent = resolve_color(kind_color(r["kind"]), t)
        tile = QRectF(card.left() + SPACE_LG, card.top() + SPACE_MD, 36, 36)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(to_qcolor(with_alpha(accent, 0.16)))
        p.drawRoundedRect(tile, t.RADIUS_LG, t.RADIUS_LG)
        p.drawPixmap(int(tile.x() + 9), int(tile.y() + 9), icon_loader.render_pixmap(kind_icon(r["kind"]), accent, 18))

        x = tile.right() + SPACE_MD
        # relevance badge (right)
        rel = r["relevance"]
        badge_color = t.COLOR_SUCCESS if rel >= 85 else t.COLOR_ACCENT_PRIMARY
        font = QFont(option.font)
        font.setPixelSize(FONT_SIZE_XS)
        font.setWeight(QFont.Weight.DemiBold)
        label = f"Relevance: {rel}%"
        bw = QFontMetrics(font).horizontalAdvance(label) + 2 * SPACE_SM
        badge = QRectF(card.right() - SPACE_LG - bw, card.top() + SPACE_MD + 2, bw, 20)
        p.setBrush(to_qcolor(with_alpha(badge_color, 0.16)))
        p.drawRoundedRect(badge, t.RADIUS_SM, t.RADIUS_SM)
        p.setFont(font)
        p.setPen(to_qcolor(badge_color))
        p.drawText(badge, Qt.AlignmentFlag.AlignCenter, label)
        # name + path
        name_font = QFont(option.font)
        name_font.setWeight(QFont.Weight.DemiBold)
        p.setFont(name_font)
        p.setPen(to_qcolor(t.COLOR_TEXT_PRIMARY))
        avail = badge.left() - x - SPACE_MD
        p.drawText(QRectF(x, card.top() + SPACE_MD, avail, 18), Qt.AlignmentFlag.AlignVCenter,
                   QFontMetrics(name_font).elidedText(r["name"], Qt.TextElideMode.ElideRight, int(avail)))
        small = QFont(option.font)
        small.setPixelSize(FONT_SIZE_XS)
        p.setFont(small)
        p.setPen(to_qcolor(t.COLOR_TEXT_MUTED))
        p.drawText(QRectF(x, card.top() + SPACE_MD + 18, card.right() - x - SPACE_LG, 16), Qt.AlignmentFlag.AlignVCenter,
                   QFontMetrics(small).elidedText(r["path"], Qt.TextElideMode.ElideMiddle, int(card.right() - x - SPACE_LG)))
        # snippet with highlighted terms
        doc = QTextDocument()
        doc.setDefaultFont(option.font)
        doc.setDocumentMargin(0)
        doc.setTextWidth(card.right() - x - SPACE_LG)
        doc.setHtml(highlight_html(r["snippet"], r["terms"], to_hex(t.COLOR_TEXT_SECONDARY), to_hex(t.COLOR_ACCENT_PRIMARY)))
        p.translate(x, card.top() + SPACE_MD + 38)
        p.setClipRect(QRectF(0, 0, card.right() - x - SPACE_LG, 34))
        doc.drawContents(p)
        p.restore()


class SemanticSearchDialog(NexusDialog):
    searchRequested = pyqtSignal(str)      # HOOK: forward to the index backend
    resultActivated = pyqtSignal(dict)     # HOOK: open / reveal the file

    def __init__(self, parent: QWidget | None = None, query: str = "", search_fn=None):
        super().__init__("Semantic Search", "Search by meaning and file contents, not just filenames",
                         "search", "COLOR_ACCENT_PRIMARY", DIALOG_SEMANTIC_SEARCH, parent)
        self._search_fn = search_fn
        col = QVBoxLayout(self.body)
        col.setContentsMargins(SPACE_XL - 4, SPACE_LG - 2, SPACE_XL - 4, 0)
        col.setSpacing(SPACE_SM)
        self.search = GlowInput("Try “electricity bill”, “exam schedule” or “backup script”…")
        col.addWidget(self.search)

        self.pages = QStackedWidget()
        # 0 prompt, 1 results, 2 empty
        prompt = QWidget()
        pl = QVBoxLayout(prompt)
        pl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pl.setSpacing(SPACE_MD)
        pl.addWidget(IconTile("search", "COLOR_TEXT_MUTED", 48), 0, Qt.AlignmentFlag.AlignHCenter)
        for text, role in (("Search by meaning, not just filename", "subheading"),
                           ("“bill” also finds invoices · “exam” finds syllabus and lecture notes", "muted")):
            lab = QLabel(text)
            lab.setProperty("role", role)
            lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pl.addWidget(lab)
        self.model = QStandardItemModel()
        self.list = QListView()
        self.list.setModel(self.model)
        self.list.setItemDelegate(ResultDelegate(self.list))
        self.list.setMouseTracking(True)
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        empty = QWidget()
        el = QVBoxLayout(empty)
        el.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label = QLabel()
        self.empty_label.setProperty("role", "muted")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        el.addWidget(self.empty_label)
        for w in (prompt, self.list, empty):
            self.pages.addWidget(w)
        col.addWidget(self.pages, 1)

        col.addWidget(Divider())
        foot = QHBoxLayout()
        foot.setContentsMargins(SPACE_SM, 0, SPACE_SM, SPACE_SM + 2)
        hint = QLabel("↑ ↓ navigate  ·  Enter open  ·  Esc close")
        hint.setProperty("role", "muted")
        foot.addWidget(hint, 1)
        self.count = QLabel("")
        self.count.setProperty("role", "muted")
        foot.addWidget(self.count)
        col.addLayout(foot)

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(120)
        self._debounce.timeout.connect(lambda: self.run_query(self.search.field.text()))
        self.search.field.textChanged.connect(lambda _t: self._debounce.start())
        self.search.field.returnPressed.connect(self._activate_current)
        self.search.field.installEventFilter(self)
        self.list.doubleClicked.connect(lambda _i: self._activate_current())
        self.list.activated.connect(lambda _i: self._activate_current())
        self.search.field.setFocus()
        if query:
            self.search.field.setText(query)
            self.search.field.deselect()
            self.run_query(query)

    def run_query(self, query: str) -> None:
        self.model.clear()
        if not query.strip():
            self.pages.setCurrentIndex(0)
            self.count.setText("")
            return
        self.searchRequested.emit(query)
        if self._search_fn is not None:
            results = self._search_fn(query)
        else:
            results = mock_search.search(query)                       # HOOK
        for r in results:
            item = QStandardItem()
            item.setData(r, ROLE)
            self.model.appendRow(item)
        if results:
            self.pages.setCurrentIndex(1)
            self.list.setCurrentIndex(self.model.index(0, 0))
            self.count.setText(f"{len(results)} result{'s' if len(results) != 1 else ''}")
        else:
            self.empty_label.setText(f"No matches for “{query.strip()}”")
            self.pages.setCurrentIndex(2)
            self.count.setText("0 results")

    def result_names(self) -> list[str]:
        return [self.model.index(i, 0).data(ROLE)["name"] for i in range(self.model.rowCount())]

    def eventFilter(self, obj, ev):
        from PyQt6.QtCore import QEvent
        if obj is self.search.field and ev.type() == QEvent.Type.KeyPress and ev.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            if self.model.rowCount():
                row = self.list.currentIndex().row()
                row = max(0, min(self.model.rowCount() - 1, row + (1 if ev.key() == Qt.Key.Key_Down else -1)))
                self.list.setCurrentIndex(self.model.index(row, 0))
            return True
        return super().eventFilter(obj, ev)

    def _activate_current(self) -> None:
        idx = self.list.currentIndex()
        if idx.isValid():
            self.resultActivated.emit(idx.data(ROLE))
            self.accept()

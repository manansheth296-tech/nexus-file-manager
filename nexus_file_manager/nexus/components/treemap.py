"""
TreemapWidget – squarified treemap, box area = size [spec Screen 4].

Shows the children of the current folder; folders with room render their children nested inside
(one level). Click a folder to drill in; the owner mirrors `pathChanged` into a breadcrumb.
Hover paints a tooltip card (name, size, type, share). Category colours: tokens.file_types.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QFontMetricsF, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from nexus.components._util import resolve_color
from nexus.core.mock_data import format_size
from nexus.styles.theme_manager import theme_manager
from nexus.tokens.base import FONT_SIZE_XS, SPACE_MD, SPACE_SM, SPACE_XS
from nexus.tokens.color_utils import to_qcolor, with_alpha
from nexus.tokens.file_types import TREEMAP_CATEGORY_COLORS, TREEMAP_CATEGORY_LABELS

HEADER = 22          # folder header strip height
NEST_PAD = 4
MIN_NEST_W, MIN_NEST_H = 84, 60


def squarify(areas: list[float], rect: QRectF) -> list[QRectF]:
    """Squarified treemap layout. `areas` must be positive, sorted descending, summing to rect area."""
    rects: list[QRectF] = []
    x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()

    def worst(row: list[float], side: float) -> float:
        s = sum(row)
        return max(side * side * max(row) / (s * s), (s * s) / (side * side * min(row)))

    i, n = 0, len(areas)
    while i < n:
        side = min(w, h)
        row = [areas[i]]
        j = i + 1
        while j < n and side > 0 and worst(row + [areas[j]], side) <= worst(row, side):
            row.append(areas[j])
            j += 1
        s = sum(row)
        if w >= h:                                   # stack the row as a column on the left
            rw = s / h if h else 0.0
            cy = y
            for a in row:
                rh = a / rw if rw else 0.0
                rects.append(QRectF(x, cy, rw, rh))
                cy += rh
            x += rw
            w -= rw
        else:                                        # lay the row along the top
            rh = s / w if w else 0.0
            cx = x
            for a in row:
                rw = a / rh if rh else 0.0
                rects.append(QRectF(cx, y, rw, rh))
                cx += rw
            y += rh
            h -= rh
        i = j
    return rects


@dataclass
class _Tile:
    node: dict
    rect: QRectF
    size: int
    category: str
    is_folder: bool
    children: list["_Tile"] = field(default_factory=list)


class TreemapWidget(QWidget):
    pathChanged = pyqtSignal(list)       # [root_name, ..., current_name]

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.setMinimumSize(320, 220)
        self._path: list[dict] = []
        self._tiles: list[_Tile] = []
        self._hover: _Tile | None = None
        self._mouse = QPointF()
        self._size_cache: dict[int, int] = {}
        self._cat_cache: dict[int, str] = {}
        theme_manager().theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, _tokens) -> None:
        self.update()

    # ── data helpers ──────────────────────────────────────────────────────
    def _size(self, node: dict) -> int:
        k = id(node)
        if k not in self._size_cache:
            self._size_cache[k] = node["size"] if "children" not in node else sum(self._size(c) for c in node["children"])
        return self._size_cache[k]

    def _category(self, node: dict) -> str:
        """Leaf category, or the dominant category (by bytes) of a folder."""
        k = id(node)
        if k not in self._cat_cache:
            if "children" not in node:
                self._cat_cache[k] = node["category"]
            else:
                tally: dict[str, int] = {}
                for c in node["children"]:
                    cat = self._category(c)
                    tally[cat] = tally.get(cat, 0) + self._size(c)
                self._cat_cache[k] = max(tally, key=tally.get) if tally else "other"
        return self._cat_cache[k]

    # ── API ───────────────────────────────────────────────────────────────
    def set_root(self, root: dict) -> None:
        self._size_cache.clear()
        self._cat_cache.clear()
        self._path = [root]
        self._relayout()
        self.pathChanged.emit(self.path_names())

    def path_names(self) -> list[str]:
        return [n["name"] for n in self._path]

    def navigate_to(self, depth: int) -> None:
        """Pop back to breadcrumb index `depth` (0 = root)."""
        if 0 <= depth < len(self._path) - 1:
            self._path = self._path[:depth + 1]
            self._relayout()
            self.pathChanged.emit(self.path_names())

    def drill_into(self, node: dict) -> None:
        if "children" in node:
            self._path.append(node)
            self._hover = None
            self._relayout()
            self.pathChanged.emit(self.path_names())

    @property
    def current(self) -> dict | None:
        return self._path[-1] if self._path else None

    @property
    def tiles(self) -> list[_Tile]:
        return self._tiles

    # ── layout ────────────────────────────────────────────────────────────
    def _layout(self, node: dict, rect: QRectF, depth: int) -> list[_Tile]:
        kids = [c for c in node.get("children", []) if self._size(c) > 0]
        if not kids or rect.width() <= 1 or rect.height() <= 1:
            return []
        kids.sort(key=self._size, reverse=True)
        total = float(sum(self._size(c) for c in kids))
        scale = rect.width() * rect.height() / total
        rects = squarify([self._size(c) * scale for c in kids], rect)
        tiles = []
        for c, r in zip(kids, rects):
            tile = _Tile(c, r, self._size(c), self._category(c), "children" in c)
            if tile.is_folder and depth == 0 and r.width() >= MIN_NEST_W and r.height() >= MIN_NEST_H:
                tile.children = self._layout(c, r.adjusted(NEST_PAD, HEADER, -NEST_PAD, -NEST_PAD), 1)
            tiles.append(tile)
        return tiles

    def _relayout(self) -> None:
        if self._path:
            self._tiles = self._layout(self._path[-1], QRectF(self.rect()).adjusted(0, 0, 0, 0), 0)
        self.update()

    def resizeEvent(self, e):
        self._relayout()
        super().resizeEvent(e)

    # ── interaction ───────────────────────────────────────────────────────
    def _tile_at(self, pos: QPointF) -> _Tile | None:
        for tile in self._tiles:
            if tile.rect.contains(pos):
                for c in tile.children:
                    if c.rect.contains(pos):
                        return c
                return tile
        return None

    def mouseMoveEvent(self, e):
        self._mouse = e.position()
        hov = self._tile_at(self._mouse)
        self._hover = hov
        self.setCursor(Qt.CursorShape.PointingHandCursor if hov and hov.is_folder else Qt.CursorShape.ArrowCursor)
        self.update()

    def leaveEvent(self, e):
        self._hover = None
        self.update()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            tile = self._tile_at(e.position())
            if tile and tile.is_folder:
                self.drill_into(tile.node)

    # ── painting ──────────────────────────────────────────────────────────
    def paintEvent(self, event):
        t = theme_manager().tokens
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for tile in self._tiles:
            self._paint_tile(p, tile, t)
        if self._hover:
            self._paint_tooltip(p, self._hover, t)
        p.end()

    def _paint_tile(self, p: QPainter, tile: _Tile, t) -> None:
        color = resolve_color(TREEMAP_CATEGORY_COLORS.get(tile.category, "COLOR_TEXT_MUTED"), t)
        r = tile.rect.adjusted(1.5, 1.5, -1.5, -1.5)
        if r.width() < 2 or r.height() < 2:
            return
        hovered = tile is self._hover
        container = bool(tile.children)
        alpha = 0.34 if hovered else (0.10 if container else 0.22)
        radius = min(t.RADIUS_MD, r.width() / 3, r.height() / 3)
        p.setPen(QPen(to_qcolor(with_alpha(color, 0.95 if hovered else 0.5)), 1))
        p.setBrush(to_qcolor(with_alpha(color, alpha)))
        p.drawRoundedRect(r.adjusted(.5, .5, -.5, -.5), radius, radius)

        name_font = QFont(self.font())
        name_font.setWeight(QFont.Weight.DemiBold)
        small = QFont(self.font())
        small.setPixelSize(FONT_SIZE_XS)
        if container:
            avail = r.width() - 2 * SPACE_SM
            fm = QFontMetricsF(name_font)
            p.setFont(name_font)
            p.setPen(to_qcolor(t.COLOR_TEXT_PRIMARY))
            label = f"{tile.node['name']}  ·  {format_size(tile.size)}"
            p.drawText(QRectF(r.x() + SPACE_SM, r.y() + 3, avail, HEADER - 4), Qt.AlignmentFlag.AlignVCenter,
                       fm.elidedText(label, Qt.TextElideMode.ElideRight, avail))
            for c in tile.children:
                self._paint_tile(p, c, t)
        elif r.width() > 62 and r.height() > 30:
            avail = r.width() - 2 * SPACE_SM
            p.setFont(name_font)
            p.setPen(to_qcolor(t.COLOR_TEXT_PRIMARY))
            p.drawText(QRectF(r.x() + SPACE_SM, r.y() + SPACE_XS, avail, 18), Qt.AlignmentFlag.AlignVCenter,
                       QFontMetricsF(name_font).elidedText(tile.node["name"], Qt.TextElideMode.ElideMiddle, avail))
            if r.height() > 48:
                p.setFont(small)
                p.setPen(to_qcolor(t.COLOR_TEXT_SECONDARY))
                p.drawText(QRectF(r.x() + SPACE_SM, r.y() + SPACE_XS + 18, avail, 16), Qt.AlignmentFlag.AlignVCenter,
                           format_size(tile.size))

    def _paint_tooltip(self, p: QPainter, tile: _Tile, t) -> None:
        cur_total = max(1, self._size(self._path[-1]))
        kind = "Folder" if tile.is_folder else TREEMAP_CATEGORY_LABELS.get(tile.category, "File")
        lines = [(tile.node["name"], True),
                 (f"{format_size(tile.size)}  ·  {kind}", False),
                 (f"{tile.size / cur_total * 100:.1f}% of {self._path[-1]['name']}", False)]
        bold = QFont(self.font())
        bold.setWeight(QFont.Weight.DemiBold)
        w = max(QFontMetricsF(bold if b else self.font()).horizontalAdvance(s) for s, b in lines) + 2 * SPACE_MD
        h = SPACE_MD * 2 + 20 * len(lines) - 4
        x, y = self._mouse.x() + 16, self._mouse.y() + 16
        if x + w > self.width():
            x = self._mouse.x() - w - 12
        if y + h > self.height():
            y = self._mouse.y() - h - 12
        card = QRectF(max(0, x), max(0, y), w, h)
        p.setPen(to_qcolor(t.COLOR_BORDER_STRONG))
        p.setBrush(to_qcolor(t.COLOR_BG_SURFACE))
        p.drawRoundedRect(card, t.RADIUS_LG, t.RADIUS_LG)
        for i, (text, strong) in enumerate(lines):
            p.setFont(bold if strong else self.font())
            p.setPen(to_qcolor(t.COLOR_TEXT_PRIMARY if i == 0 else t.COLOR_TEXT_SECONDARY))
            p.drawText(QRectF(card.x() + SPACE_MD, card.y() + SPACE_MD + i * 20, w - 2 * SPACE_MD, 18),
                       Qt.AlignmentFlag.AlignVCenter, text)

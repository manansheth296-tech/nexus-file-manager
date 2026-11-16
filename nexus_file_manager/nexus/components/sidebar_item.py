"""
SidebarItem – states: Default, Hover, Active (current path).

Fully painted (icon tile + label + active indicator) for pixel-exact alignment.
`badge_color` gives Quick-Access folders their coloured icon tile (spec: "custom
folder badges"); accepts a hex or a token name like 'COLOR_ACCENT_SECONDARY'.
Subclasses override `_paint_content` (see DriveItem).
"""
from __future__ import annotations

from PyQt6.QtCore import QRectF, QSize, Qt
from PyQt6.QtGui import QFont, QFontMetrics, QPainter, QPainterPath
from PyQt6.QtWidgets import QAbstractButton, QSizePolicy, QWidget

from nexus.assets import icon_loader
from nexus.components._interactive import InteractiveMixin
from nexus.components._util import resolve_color
from nexus.styles.theme_manager import theme_manager
from nexus.tokens.base import (CONTROL_HEIGHT_MD, ICON_SIZE_MD, SIDEBAR_WIDTH, SPACE_MD, SPACE_SM)
from nexus.tokens.color_utils import lerp_qcolor, to_qcolor, with_alpha

TILE = 24  # icon tile edge (px)


def _hex(c) -> str:
    return f"#{c.red():02x}{c.green():02x}{c.blue():02x}"


class SidebarItem(InteractiveMixin, QAbstractButton):
    def __init__(self, text: str, icon: str, badge_color: str | None = None,
                 parent: QWidget | None = None, key: str = ""):
        super().__init__(parent)
        self.setText(text)
        self.key = key
        self._icon_name = icon
        self._badge_color = badge_color
        self._active = False
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._init_interactive("RADIUS_MD")

    # ── API ───────────────────────────────────────────────────────────────
    def set_active(self, active: bool) -> None:
        self._active = active
        self.update()

    @property
    def is_active(self) -> bool:
        return self._active

    def sizeHint(self) -> QSize:
        return QSize(SIDEBAR_WIDTH - 2 * SPACE_SM, CONTROL_HEIGHT_MD)

    # ── painting ──────────────────────────────────────────────────────────
    def paintEvent(self, event):
        t = theme_manager().tokens
        r = QRectF(self.rect())
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._paint_background(p, r, t)
        self._paint_interactive_overlay(p, r)
        self._paint_content(p, r, t)
        p.end()

    def _paint_background(self, p: QPainter, r: QRectF, t) -> None:
        if not self._active:
            return
        path = QPainterPath()
        path.addRoundedRect(r, t.RADIUS_MD, t.RADIUS_MD)
        p.fillPath(path, to_qcolor(t.COLOR_SELECTED_BG))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(to_qcolor(t.COLOR_ACCENT_PRIMARY))
        p.drawRoundedRect(QRectF(0, r.center().y() - 8, 3, 16), 1.5, 1.5)

    def _text_font(self) -> QFont:
        font = QFont(self.font())
        font.setWeight(QFont.Weight.DemiBold if self._active else QFont.Weight.Medium)
        return font

    def _text_color(self, t):
        return to_qcolor(t.COLOR_TEXT_PRIMARY) if self._active else \
            lerp_qcolor(to_qcolor(t.COLOR_TEXT_SECONDARY), to_qcolor(t.COLOR_TEXT_PRIMARY), self._hover_t)

    def _paint_tile(self, p: QPainter, tile: QRectF, t) -> None:
        if self._badge_color:
            accent = resolve_color(self._badge_color, t)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(to_qcolor(with_alpha(accent, 0.16)))
            p.drawRoundedRect(tile, t.RADIUS_SM + 2, t.RADIUS_SM + 2)
            icon_color = accent
        else:
            icon_color = t.COLOR_ACCENT_PRIMARY if self._active else _hex(
                lerp_qcolor(to_qcolor(t.COLOR_TEXT_SECONDARY), to_qcolor(t.COLOR_TEXT_PRIMARY), self._hover_t))
        pm = icon_loader.render_pixmap(self._icon_name, icon_color, ICON_SIZE_MD)
        p.drawPixmap(int(tile.x() + (TILE - ICON_SIZE_MD) / 2), int(tile.y() + (TILE - ICON_SIZE_MD) / 2), pm)

    def _paint_content(self, p: QPainter, r: QRectF, t) -> None:
        tile = QRectF(SPACE_MD, (r.height() - TILE) / 2, TILE, TILE)
        self._paint_tile(p, tile, t)
        font = self._text_font()
        p.setFont(font)
        p.setPen(self._text_color(t))
        x = tile.right() + SPACE_SM
        text = QFontMetrics(font).elidedText(self.text(), Qt.TextElideMode.ElideRight, int(r.width() - x - SPACE_MD))
        p.drawText(QRectF(x, 0, r.width() - x, r.height()),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)

"""DriveItem – sidebar entry for a drive: icon, name, usage bar (accent/warning/danger), free space."""
from __future__ import annotations

from PyQt6.QtCore import QRectF, QSize, Qt
from PyQt6.QtGui import QFont, QFontMetrics, QPainter
from PyQt6.QtWidgets import QWidget

from nexus.components.sidebar_item import TILE, SidebarItem
from nexus.core.mock_data import format_size
from nexus.tokens.base import (DRIVE_ITEM_HEIGHT, FONT_SIZE_XS, SIDEBAR_WIDTH, SPACE_MD, SPACE_SM, SPACE_XS)
from nexus.tokens.color_utils import to_qcolor

WARN_AT, DANGER_AT = 0.75, 0.90


class DriveItem(SidebarItem):
    def __init__(self, label: str, used: int, total: int, parent: QWidget | None = None, key: str = ""):
        super().__init__(label, "hard-drive", None, parent, key)
        self.used, self.total = used, total

    @property
    def fraction(self) -> float:
        return self.used / self.total if self.total else 0.0

    def sizeHint(self) -> QSize:
        return QSize(SIDEBAR_WIDTH - 2 * SPACE_SM, DRIVE_ITEM_HEIGHT)

    def _paint_content(self, p: QPainter, r: QRectF, t) -> None:
        tile = QRectF(SPACE_MD, SPACE_SM, TILE, TILE)
        self._paint_tile(p, tile, t)
        font = self._text_font()
        p.setFont(font)
        p.setPen(self._text_color(t))
        x = tile.right() + SPACE_SM
        name = QFontMetrics(font).elidedText(self.text(), Qt.TextElideMode.ElideRight, int(r.width() - x - SPACE_MD))
        p.drawText(QRectF(x, SPACE_SM, r.width() - x, TILE),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, name)

        # usage bar – colour escalates with fullness
        bar = QRectF(SPACE_MD, tile.bottom() + SPACE_SM, r.width() - 2 * SPACE_MD, 4)
        level = t.COLOR_DANGER if self.fraction >= DANGER_AT else \
            t.COLOR_WARNING if self.fraction >= WARN_AT else t.COLOR_ACCENT_PRIMARY
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(to_qcolor(t.COLOR_BORDER_STRONG))
        p.drawRoundedRect(bar, 2, 2)
        p.setBrush(to_qcolor(level))
        p.drawRoundedRect(QRectF(bar.x(), bar.y(), bar.width() * self.fraction, bar.height()), 2, 2)

        cap = QFont(self.font())
        cap.setPixelSize(FONT_SIZE_XS)
        p.setFont(cap)
        p.setPen(to_qcolor(t.COLOR_TEXT_MUTED))
        free = format_size(self.total - self.used)
        p.drawText(QRectF(SPACE_MD, bar.bottom() + SPACE_XS, r.width() - 2 * SPACE_MD, 16),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                   f"{free} free of {format_size(self.total)}")

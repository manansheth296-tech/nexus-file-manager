"""IconTile – rounded tinted square holding one tinted SVG (inspector header, empty states)."""
from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QWidget

from nexus.assets import icon_loader
from nexus.components._util import resolve_color
from nexus.styles.theme_manager import theme_manager
from nexus.tokens.color_utils import to_qcolor, with_alpha


class IconTile(QWidget):
    def __init__(self, icon: str, color: str, size: int = 36, parent: QWidget | None = None):
        super().__init__(parent)
        self._icon, self._color, self._size = icon, color, size
        self.setFixedSize(size, size)
        theme_manager().theme_changed.connect(self._on_theme_changed)

    def set_icon(self, icon: str, color: str) -> None:
        self._icon, self._color = icon, color
        self.update()

    def _on_theme_changed(self, _t) -> None:
        self.update()

    def paintEvent(self, event):
        t = theme_manager().tokens
        accent = resolve_color(self._color, t)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(to_qcolor(with_alpha(accent, 0.16)))
        radius = t.RADIUS_LG if self._size >= 32 else t.RADIUS_MD
        p.drawRoundedRect(QRectF(self.rect()), radius, radius)
        icon_px = round(self._size * 0.5)
        pm = icon_loader.render_pixmap(self._icon, accent, icon_px)
        off = (self._size - icon_px) // 2
        p.drawPixmap(off, off, pm)
        p.end()

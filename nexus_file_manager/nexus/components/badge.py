"""Badge – small tinted pill (file-type tags, category tags, resolution pills)."""
from __future__ import annotations

from PyQt6.QtCore import QRectF, QSize, Qt
from PyQt6.QtGui import QFont, QFontMetrics, QPainter
from PyQt6.QtWidgets import QWidget

from nexus.components._util import resolve_color
from nexus.styles.theme_manager import theme_manager
from nexus.tokens.base import FONT_SIZE_XS, SPACE_SM
from nexus.tokens.color_utils import to_qcolor, with_alpha


class Badge(QWidget):
    HEIGHT = 20

    def __init__(self, text: str, color: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._text, self._color = text, color
        self.setFixedHeight(self.HEIGHT)
        theme_manager().theme_changed.connect(self._on_theme_changed)

    def _font(self) -> QFont:
        f = QFont(self.font())
        f.setPixelSize(FONT_SIZE_XS)
        f.setWeight(QFont.Weight.DemiBold)
        return f

    def sizeHint(self) -> QSize:
        return QSize(QFontMetrics(self._font()).horizontalAdvance(self._text) + 2 * SPACE_SM, self.HEIGHT)

    def _on_theme_changed(self, _t) -> None:
        self.update()

    def paintEvent(self, event):
        t = theme_manager().tokens
        accent = resolve_color(self._color, t)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(to_qcolor(with_alpha(accent, 0.16)))
        p.drawRoundedRect(QRectF(self.rect()), t.RADIUS_SM, t.RADIUS_SM)
        p.setFont(self._font())
        p.setPen(to_qcolor(accent))
        p.drawText(QRectF(self.rect()), Qt.AlignmentFlag.AlignCenter, self._text)
        p.end()

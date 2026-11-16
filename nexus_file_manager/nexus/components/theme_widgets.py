"""ThemeThumbnail (mini app painted from ANY ThemeTokens), PaletteSwatch (circular palette), AccentChip."""
from __future__ import annotations

from PyQt6.QtCore import QRectF, QSize, Qt
from PyQt6.QtGui import QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QAbstractButton, QWidget

from nexus.styles.theme_manager import theme_manager
from nexus.tokens.color_utils import composite, to_qcolor, with_alpha
from nexus.tokens.themes import ThemeTokens


class ThemeThumbnail(QWidget):
    """A miniature explorer drawn with the *given* theme's tokens – so every theme previews itself faithfully."""
    DESIGN_W, DESIGN_H = 240, 132

    def __init__(self, tokens: ThemeTokens, size: tuple[int, int] = (240, 132), parent: QWidget | None = None):
        super().__init__(parent)
        self._t = tokens
        self.setFixedSize(*size)

    def paintEvent(self, event):
        t, active = self._t, theme_manager().tokens
        w, h = self.DESIGN_W, self.DESIGN_H                 # draw in design space, scale to the widget
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.scale(self.width() / w, self.height() / h)
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(0, 0, w, h), t.RADIUS_LG, t.RADIUS_LG)
        p.setClipPath(clip)
        p.fillRect(QRectF(0, 0, w, h), to_qcolor(t.COLOR_BG_BASE))
        surface = to_qcolor(t.COLOR_BG_SURFACE)
        top_h, side_w = 22, 58
        p.fillRect(QRectF(0, 0, w, top_h), surface)
        p.fillRect(QRectF(0, top_h, side_w, h - top_h), surface)
        p.setPen(to_qcolor(t.COLOR_BORDER))
        p.drawLine(0, top_h, w, top_h)
        p.drawLine(side_w, top_h, side_w, h)
        p.setPen(Qt.PenStyle.NoPen)
        # top bar: nav dots, breadcrumb pill, filter, primary button
        p.setBrush(to_qcolor(t.COLOR_TEXT_MUTED))
        for i in range(3):
            p.drawEllipse(QRectF(8 + i * 12, 9, 5, 5))
        p.setBrush(to_qcolor(t.COLOR_ACCENT_SOFT))
        p.drawRoundedRect(QRectF(58, 6, 70, 10), min(t.RADIUS_XL, 5), min(t.RADIUS_XL, 5))
        p.setBrush(to_qcolor(t.COLOR_BG_CARD))
        p.setPen(to_qcolor(t.COLOR_BORDER))
        p.drawRoundedRect(QRectF(w - 94, 6, 58, 10), min(t.RADIUS_MD, 4), min(t.RADIUS_MD, 4))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(to_qcolor(t.COLOR_ACCENT_PRIMARY))
        p.drawRoundedRect(QRectF(w - 28, 6, 20, 10), min(t.RADIUS_MD, 4), min(t.RADIUS_MD, 4))
        # sidebar items (first = active)
        for i in range(6):
            y = top_h + 10 + i * 15
            if i == 0:
                p.setBrush(to_qcolor(t.COLOR_SELECTED_BG))
                p.drawRoundedRect(QRectF(5, y - 3, side_w - 10, 13), min(t.RADIUS_MD, 4), min(t.RADIUS_MD, 4))
                p.setBrush(to_qcolor(t.COLOR_ACCENT_PRIMARY))
                p.drawRoundedRect(QRectF(5, y, 2, 7), 1, 1)
            p.setBrush(to_qcolor(t.COLOR_ACCENT_SECONDARY if i % 3 == 1 else t.COLOR_TEXT_SECONDARY))
            p.drawRoundedRect(QRectF(11, y + 1, 6, 6), min(t.RADIUS_SM, 2), min(t.RADIUS_SM, 2))
            p.setBrush(to_qcolor(with_alpha(t.COLOR_TEXT_SECONDARY, 0.75)))
            p.drawRoundedRect(QRectF(22, y + 2, 22 - (i % 3) * 4, 4), 2, 2)
        # file rows
        x0, y0, rh = side_w + 10, top_h + 10, 14
        p.setBrush(to_qcolor(with_alpha(t.COLOR_TEXT_MUTED, 0.8)))
        for cx, cw in ((x0, 34), (x0 + 74, 20), (x0 + 108, 30)):
            p.drawRoundedRect(QRectF(cx, y0, cw, 3), 1.5, 1.5)
        for i in range(6):
            y = y0 + 10 + i * rh
            if i == 2:
                p.setBrush(to_qcolor(t.COLOR_SELECTED_BG))
                p.drawRect(QRectF(side_w + 1, y - 2, w - side_w, rh))
                p.setBrush(to_qcolor(t.COLOR_ACCENT_PRIMARY))
                p.drawRoundedRect(QRectF(side_w + 1, y, 2, rh - 4), 1, 1)
            elif i % 2:
                p.setBrush(to_qcolor(t.COLOR_ROW_ALT))
                p.drawRect(QRectF(side_w + 1, y - 2, w - side_w, rh))
            p.setBrush(to_qcolor(with_alpha(t.COLOR_TEXT_PRIMARY, 0.85)))
            p.drawRoundedRect(QRectF(x0, y + 1, 32 + (i * 7) % 18, 4), 2, 2)
            p.setBrush(to_qcolor(with_alpha(t.COLOR_TEXT_SECONDARY, 0.7)))
            p.drawRoundedRect(QRectF(x0 + 74, y + 1, 14, 4), 2, 2)
            p.drawRoundedRect(QRectF(x0 + 108, y + 1, 26, 4), 2, 2)
        p.setClipping(False)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(to_qcolor(active.COLOR_BORDER_STRONG), 1))
        p.drawRoundedRect(QRectF(.5, .5, w - 1, h - 1), t.RADIUS_LG, t.RADIUS_LG)
        p.end()


class PaletteSwatch(QWidget):
    """Circular palette: four wedges = background, surface, primary accent, secondary accent."""

    def __init__(self, tokens: ThemeTokens, diameter: int = 30, parent: QWidget | None = None):
        super().__init__(parent)
        self._t = tokens
        self.setFixedSize(diameter + 4, diameter + 4)

    def paintEvent(self, event):
        t, active = self._t, theme_manager().tokens
        d = self.width() - 4
        r = QRectF(2, 2, d, d)
        colors = [t.COLOR_BG_BASE, composite(t.COLOR_BG_SURFACE, t.COLOR_BG_BASE), t.COLOR_ACCENT_PRIMARY, t.COLOR_ACCENT_SECONDARY]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        for i, c in enumerate(colors):
            p.setBrush(to_qcolor(c))
            p.drawPie(r, (90 - i * 90) * 16, -90 * 16)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(to_qcolor(active.COLOR_BORDER_STRONG), 1.5))
        p.drawEllipse(r)
        p.end()


class AccentChip(QAbstractButton):
    """Round accent-colour picker chip (checkable)."""

    def __init__(self, name: str, color: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.color_hex = color
        self.setToolTip(name)
        self.setCheckable(True)
        self.setFixedSize(30, 30)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        theme_manager().theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, _t) -> None:
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(30, 30)

    def paintEvent(self, event):
        t = theme_manager().tokens
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QRectF(self.rect()).center()
        hover = self.underMouse()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(to_qcolor(self.color_hex))
        rad = 9 + (1 if hover else 0)
        p.drawEllipse(c, rad, rad)
        if self.isChecked():
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(to_qcolor(t.COLOR_TEXT_PRIMARY), 2))
            p.drawEllipse(c, 13, 13)
        if self.hasFocus():
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(to_qcolor(t.COLOR_BORDER_FOCUS), 2))
            p.drawEllipse(c, 14.5, 14.5)
        p.end()

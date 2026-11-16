"""
SegmentedTabs – 2+ equal segments with a sliding highlight (Safe Locker's Lock/Unlock, Theme Store tabs).
States per segment: default, hover, active; keyboard: ←/→ when focused (ring painted).
"""
from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QRectF, QSize, Qt, QVariantAnimation, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QPen
from PyQt6.QtWidgets import QSizePolicy, QWidget

from nexus.assets import icon_loader
from nexus.styles.theme_manager import theme_manager
from nexus.tokens.base import ICON_SIZE_SM, MOTION_BASE, SPACE_LG, SPACE_SM, SPACE_XS
from nexus.tokens.color_utils import lerp_qcolor, to_qcolor


class SegmentedTabs(QWidget):
    currentChanged = pyqtSignal(int)
    HEIGHT = 36

    def __init__(self, labels: list[str], icons: list[str] | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self._labels = labels
        self._icons = icons or [None] * len(labels)
        self._index = 0
        self._hover = -1
        self._pos = 0.0                      # animated highlight position (segment units)
        self.setFixedHeight(self.HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(MOTION_BASE)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_anim)
        theme_manager().theme_changed.connect(self._on_theme_changed)

    @property
    def current(self) -> int:
        return self._index

    def set_current(self, i: int) -> None:
        if i == self._index or not 0 <= i < len(self._labels):
            return
        self._index = i
        if self.isVisible():
            self._anim.stop()
            self._anim.setStartValue(self._pos)
            self._anim.setEndValue(float(i))
            self._anim.start()
        else:
            self._pos = float(i)
        self.currentChanged.emit(i)
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(120 * len(self._labels), self.HEIGHT)

    def _on_anim(self, v) -> None:
        self._pos = float(v)
        self.update()

    def _on_theme_changed(self, _t) -> None:
        self.update()

    def _seg_width(self) -> float:
        return (self.width() - 2 * SPACE_XS) / len(self._labels)

    def _index_at(self, x: float) -> int:
        return max(0, min(len(self._labels) - 1, int((x - SPACE_XS) // self._seg_width())))

    def mouseMoveEvent(self, e):
        i = self._index_at(e.position().x())
        if i != self._hover:
            self._hover = i
            self.update()

    def leaveEvent(self, e):
        self._hover = -1
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.set_current(self._index_at(e.position().x()))

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right):
            self.set_current(self._index + (1 if e.key() == Qt.Key.Key_Right else -1))
        else:
            super().keyPressEvent(e)

    def paintEvent(self, event):
        t = theme_manager().tokens
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        track = QRectF(self.rect()).adjusted(.5, .5, -.5, -.5)
        p.setPen(to_qcolor(t.COLOR_BORDER))
        p.setBrush(to_qcolor(t.COLOR_BG_CARD))
        p.drawRoundedRect(track, t.RADIUS_LG, t.RADIUS_LG)
        sw = self._seg_width()
        thumb = QRectF(SPACE_XS + self._pos * sw, SPACE_XS, sw, self.height() - 2 * SPACE_XS)
        p.setPen(QPen(to_qcolor(t.COLOR_ACCENT_PRIMARY), 1))
        p.setBrush(to_qcolor(t.COLOR_ACCENT_SOFT))
        p.drawRoundedRect(thumb.adjusted(.5, .5, -.5, -.5), t.RADIUS_MD, t.RADIUS_MD)
        font = QFont(self.font())
        font.setWeight(QFont.Weight.DemiBold)
        p.setFont(font)
        for i, label in enumerate(self._labels):
            seg = QRectF(SPACE_XS + i * sw, SPACE_XS, sw, self.height() - 2 * SPACE_XS)
            if i == self._hover and i != self._index:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(to_qcolor(t.COLOR_HOVER_OVERLAY))
                p.drawRoundedRect(seg, t.RADIUS_MD, t.RADIUS_MD)
            active = max(0.0, 1 - abs(self._pos - i))           # 1 when the highlight sits on this segment
            color = lerp_qcolor(to_qcolor(t.COLOR_TEXT_SECONDARY), to_qcolor(t.COLOR_ACCENT_PRIMARY), active)
            p.setPen(color)
            fm = p.fontMetrics()
            icon = self._icons[i]
            text_w = fm.horizontalAdvance(label)
            total = text_w + ((ICON_SIZE_SM + SPACE_SM) if icon else 0)
            x = seg.center().x() - total / 2
            if icon:
                pm = icon_loader.render_pixmap(icon, f"#{color.red():02x}{color.green():02x}{color.blue():02x}", ICON_SIZE_SM)
                p.drawPixmap(int(x), int(seg.center().y() - ICON_SIZE_SM / 2), pm)
                x += ICON_SIZE_SM + SPACE_SM
            p.drawText(QRectF(x, seg.y(), text_w + 2, seg.height()), Qt.AlignmentFlag.AlignVCenter, label)
        if self.hasFocus():
            p.setPen(QPen(to_qcolor(t.COLOR_BORDER_FOCUS), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), t.RADIUS_LG, t.RADIUS_LG)
        p.end()



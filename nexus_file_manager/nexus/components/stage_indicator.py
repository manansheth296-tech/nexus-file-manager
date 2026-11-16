"""
StageIndicator – the Duplicate Hunter's multi-stage hashing indicator: Size → 4 KB Header → Full SHA-256.
Done stages: success tick; active stage: accent ring with a soft animated pulse + inline progress; pending: muted.
"""
from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QPointF, QRectF, QSize, Qt, QVariantAnimation
from PyQt6.QtGui import QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget

from nexus.styles.theme_manager import theme_manager
from nexus.tokens.base import FONT_SIZE_XS, SPACE_SM
from nexus.tokens.color_utils import to_qcolor, with_alpha

STAGES = ["Size", "4 KB header", "Full SHA-256"]


class StageIndicator(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(64)
        self._stage = 0          # active stage index (== len(STAGES) when finished)
        self._progress = 0.0     # progress within the active stage 0..1
        self._pulse = 0.0
        self._detail = ""
        self._anim = QVariantAnimation(self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setDuration(1100)
        self._anim.setLoopCount(-1)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._anim.valueChanged.connect(self._on_pulse)
        theme_manager().theme_changed.connect(self._on_theme_changed)

    def set_state(self, stage: int, progress: float = 0.0, detail: str = "") -> None:
        self._stage, self._progress, self._detail = stage, max(0.0, min(1.0, progress)), detail
        if self._stage < len(STAGES):
            if self._anim.state() != QVariantAnimation.State.Running and self.isVisible():
                self._anim.start()
        else:
            self._anim.stop()
            self._pulse = 0.0
        self.update()

    @property
    def finished(self) -> bool:
        return self._stage >= len(STAGES)

    def _on_pulse(self, v) -> None:
        self._pulse = float(v)
        self.update()

    def _on_theme_changed(self, _t) -> None:
        self.update()

    def showEvent(self, e):
        if self._stage < len(STAGES):
            self._anim.start()
        super().showEvent(e)

    def hideEvent(self, e):
        self._anim.stop()
        super().hideEvent(e)

    def sizeHint(self) -> QSize:
        return QSize(420, 64)

    def paintEvent(self, event):
        t = theme_manager().tokens
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        n = len(STAGES)
        r = 11
        margin = 62                      # half a label width, so the first/last labels never clip
        step = (self.width() - 2 * margin) / (n - 1)
        cy = 22.0
        centers = [QPointF(margin + i * step, cy) for i in range(n)]
        # connectors (filled portion = completed stages + current progress)
        for i in range(n - 1):
            a, b = centers[i].x() + r + 4, centers[i + 1].x() - r - 4
            p.setPen(QPen(to_qcolor(t.COLOR_BORDER_STRONG), 2, cap=Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(a, cy), QPointF(b, cy))
            fill = 1.0 if self._stage > i else (self._progress if self._stage == i else 0.0)
            if fill > 0:
                p.setPen(QPen(to_qcolor(t.COLOR_SUCCESS if self._stage > i else t.COLOR_ACCENT_PRIMARY), 2,
                              cap=Qt.PenCapStyle.RoundCap))
                p.drawLine(QPointF(a, cy), QPointF(a + (b - a) * fill, cy))
        small = QFont(self.font())
        small.setPixelSize(FONT_SIZE_XS)
        for i, c in enumerate(centers):
            done, active = i < self._stage, i == self._stage
            if active:                                           # soft pulse ring
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(to_qcolor(with_alpha(t.COLOR_ACCENT_PRIMARY, 0.22 * (1 - self._pulse))))
                p.drawEllipse(c, r + 2 + 7 * self._pulse, r + 2 + 7 * self._pulse)
            ring = t.COLOR_SUCCESS if done else (t.COLOR_ACCENT_PRIMARY if active else t.COLOR_BORDER_STRONG)
            p.setPen(QPen(to_qcolor(ring), 2))
            p.setBrush(to_qcolor(t.COLOR_SUCCESS if done else (t.COLOR_ACCENT_SOFT if active else t.COLOR_BG_CARD)))
            p.drawEllipse(c, r, r)
            if done:                                             # tick
                pen = QPen(to_qcolor(t.COLOR_BG_BASE), 2, cap=Qt.PenCapStyle.RoundCap, join=Qt.PenJoinStyle.RoundJoin)
                p.setPen(pen)
                path = QPainterPath(QPointF(c.x() - 4.5, c.y() + 0.5))
                path.lineTo(c.x() - 1.2, c.y() + 3.8)
                path.lineTo(c.x() + 4.8, c.y() - 3.2)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawPath(path)
            else:
                p.setFont(small)
                p.setPen(to_qcolor(t.COLOR_ACCENT_PRIMARY if active else t.COLOR_TEXT_MUTED))
                p.drawText(QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r), Qt.AlignmentFlag.AlignCenter, str(i + 1))
            label_font = QFont(self.font())
            label_font.setWeight(QFont.Weight.DemiBold if active else QFont.Weight.Medium)
            p.setFont(label_font)
            p.setPen(to_qcolor(t.COLOR_TEXT_PRIMARY if (done or active) else t.COLOR_TEXT_MUTED))
            p.drawText(QRectF(c.x() - step / 2, cy + r + 6, step, 18), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, STAGES[i])
        p.end()

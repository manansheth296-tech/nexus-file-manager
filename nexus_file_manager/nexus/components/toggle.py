"""
Checkbox + Switch – states: Unchecked, Checked, Indeterminate (checkbox), Off/On (switch),
plus Hover, Focused, Disabled. Both are painted from tokens (QSS can't tint indicators
per theme) and share the hover/focus behaviour of InteractiveMixin.
"""
from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QPointF, QRectF, QSize, Qt, QVariantAnimation
from PyQt6.QtGui import QFontMetrics, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QAbstractButton, QCheckBox, QSizePolicy, QWidget

from nexus.components._interactive import InteractiveMixin
from nexus.styles.theme_manager import theme_manager
from nexus.tokens.base import MOTION_BASE, SPACE_SM
from nexus.tokens.color_utils import lerp_qcolor, to_qcolor

_PAD = 3          # room for the focus ring around the control
_BOX = 18


def draw_check_box(p: QPainter, box: QRectF, state, t, hover_t: float = 0.0) -> None:
    """The 18px checkbox glyph (unchecked / checked / indeterminate). Shared with painted table cells."""
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    if state != Qt.CheckState.Unchecked:
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(to_qcolor(t.COLOR_ACCENT_PRIMARY))
        p.drawRoundedRect(box, t.RADIUS_SM, t.RADIUS_SM)
        pen = QPen(to_qcolor(t.COLOR_TEXT_ON_ACCENT), 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        if state == Qt.CheckState.PartiallyChecked:
            p.drawLine(QPointF(box.x() + 4.5, box.center().y()), QPointF(box.right() - 4.5, box.center().y()))
        else:
            path = QPainterPath(QPointF(box.x() + 4.5, box.y() + 9.5))
            path.lineTo(box.x() + 7.8, box.y() + 12.8)
            path.lineTo(box.x() + 13.5, box.y() + 5.5)
            p.drawPath(path)
        if hover_t > 0:                                       # hover wash on the filled state
            c = to_qcolor(t.COLOR_HOVER_OVERLAY)
            c.setAlphaF(c.alphaF() * hover_t)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(c)
            p.drawRoundedRect(box, t.RADIUS_SM, t.RADIUS_SM)
    else:                                                     # outlined box, border warms on hover
        border = lerp_qcolor(to_qcolor(t.COLOR_TEXT_MUTED), to_qcolor(t.COLOR_TEXT_SECONDARY), hover_t)
        p.setPen(QPen(border, 1.5))
        p.setBrush(to_qcolor(t.COLOR_BG_CARD))
        p.drawRoundedRect(box.adjusted(.75, .75, -.75, -.75), t.RADIUS_SM, t.RADIUS_SM)


class Checkbox(InteractiveMixin, QCheckBox):
    def __init__(self, text: str = "", tristate: bool = False, parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setTristate(tristate)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._init_interactive("RADIUS_SM")

    def nextCheckState(self) -> None:
        # Tri-state boxes behave like file managers: partial/unchecked -> checked -> unchecked (never back to partial by click)
        if self.isTristate():
            self.setCheckState(Qt.CheckState.Unchecked if self.checkState() == Qt.CheckState.Checked
                               else Qt.CheckState.Checked)
        else:
            super().nextCheckState()

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        text_w = fm.horizontalAdvance(self.text()) + SPACE_SM if self.text() else 0
        return QSize(2 * _PAD + _BOX + text_w, max(24, fm.height() + 4))

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def paintEvent(self, event):
        t = theme_manager().tokens
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        enabled = self.isEnabled()
        if not enabled:
            p.setOpacity(0.45)
        box = QRectF(_PAD, (self.height() - _BOX) / 2, _BOX, _BOX)
        state = self.checkState()
        on = state != Qt.CheckState.Unchecked

        draw_check_box(p, box, state, t, self._hover_t)

        if self.has_focus_ring:
            p.setPen(QPen(to_qcolor(t.COLOR_BORDER_FOCUS), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(box.adjusted(-2, -2, 2, 2), t.RADIUS_SM + 2, t.RADIUS_SM + 2)

        if self.text():
            p.setOpacity(1.0)
            p.setFont(self.font())
            p.setPen(to_qcolor(t.COLOR_TEXT_PRIMARY if enabled else t.COLOR_TEXT_MUTED))
            x = box.right() + SPACE_SM
            p.drawText(QRectF(x, 0, self.width() - x, self.height()),
                       Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())
        p.end()


class Switch(InteractiveMixin, QAbstractButton):
    TRACK_W, TRACK_H, KNOB = 36, 20, 14

    def __init__(self, text: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setText(text)
        self.setCheckable(True)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._init_interactive("RADIUS_LG")
        self._pos = 0.0
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(MOTION_BASE)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_pos)
        self.toggled.connect(self._on_toggled)

    def _on_toggled(self, on: bool) -> None:
        target = 1.0 if on else 0.0
        if not self.isVisible():
            self._pos = target
            return
        self._anim.stop()
        self._anim.setStartValue(self._pos)
        self._anim.setEndValue(target)
        self._anim.start()

    def _on_pos(self, v) -> None:
        self._pos = float(v)
        self.update()

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        text_w = fm.horizontalAdvance(self.text()) + SPACE_SM if self.text() else 0
        return QSize(2 * _PAD + self.TRACK_W + text_w, max(self.TRACK_H + 2 * _PAD, fm.height() + 4))

    def paintEvent(self, event):
        t = theme_manager().tokens
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self.isEnabled():
            p.setOpacity(0.45)
        track = QRectF(_PAD, (self.height() - self.TRACK_H) / 2, self.TRACK_W, self.TRACK_H)
        r = self.TRACK_H / 2

        color = lerp_qcolor(to_qcolor(t.COLOR_SWITCH_OFF), to_qcolor(t.COLOR_ACCENT_PRIMARY), self._pos)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)
        p.drawRoundedRect(track, r, r)
        if self._hover_t > 0:
            c = to_qcolor(t.COLOR_HOVER_OVERLAY)
            c.setAlphaF(c.alphaF() * self._hover_t)
            p.setBrush(c)
            p.drawRoundedRect(track, r, r)

        inset = (self.TRACK_H - self.KNOB) / 2
        travel = self.TRACK_W - self.KNOB - 2 * inset
        p.setBrush(to_qcolor(t.COLOR_KNOB))
        p.drawEllipse(QRectF(track.x() + inset + travel * self._pos, track.y() + inset, self.KNOB, self.KNOB))

        if self.has_focus_ring:
            p.setPen(QPen(to_qcolor(t.COLOR_BORDER_FOCUS), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(track.adjusted(-2, -2, 2, 2), r + 2, r + 2)

        if self.text():
            p.setOpacity(1.0)
            p.setFont(self.font())
            p.setPen(to_qcolor(t.COLOR_TEXT_PRIMARY if self.isEnabled() else t.COLOR_TEXT_MUTED))
            x = track.right() + SPACE_SM
            p.drawText(QRectF(x, 0, self.width() - x, self.height()),
                       Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())
        p.end()

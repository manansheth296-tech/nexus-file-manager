"""
InteractiveMixin – animated hover wash + keyboard focus ring for painted components.

QSS has no transitions, so hover is a translucent overlay whose alpha animates
0→1 over MOTION_FAST. Focus rings are painted too (QSS can't draw outside the
border box). Combine as: class Foo(InteractiveMixin, QPushButton).
"""
from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QRectF, Qt, QVariantAnimation
from PyQt6.QtGui import QPainter, QPainterPath, QPen

from nexus.components._util import force_state
from nexus.styles.theme_manager import theme_manager
from nexus.tokens.base import MOTION_FAST
from nexus.tokens.color_utils import to_qcolor


class InteractiveMixin:
    FOCUS_RING_WIDTH = 2

    def _init_interactive(self, radius_token: str = "RADIUS_MD") -> None:
        self._radius_token = radius_token
        self._hover_t = 0.0
        self._forced: str | None = None
        self._hover_anim = QVariantAnimation(self)
        self._hover_anim.setDuration(MOTION_FAST)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._hover_anim.valueChanged.connect(self._on_hover_value)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        theme_manager().theme_changed.connect(self._on_theme_changed)

    # ── events ────────────────────────────────────────────────────────────
    def enterEvent(self, event):
        self._animate_hover(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_hover(0.0)
        super().leaveEvent(event)

    def _animate_hover(self, target: float) -> None:
        if self._forced or not self.isEnabled():
            return
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_t)
        self._hover_anim.setEndValue(target)
        self._hover_anim.start()

    def _on_hover_value(self, value) -> None:
        self._hover_t = float(value)
        self.update()

    def _on_theme_changed(self, _tokens) -> None:
        self.update()

    # ── design-QA hook ────────────────────────────────────────────────────
    def set_forced_state(self, state: str | None) -> None:
        """Pin 'hover' | 'pressed' | 'focus' | None so a state can be rendered statically."""
        self._forced = state
        self._hover_anim.stop()
        self._hover_t = 1.0 if state == "hover" else 0.0
        force_state(self, state)

    # ── painting ──────────────────────────────────────────────────────────
    @property
    def has_focus_ring(self) -> bool:
        return self.isEnabled() and (self.hasFocus() or self._forced == "focus")

    def _paint_interactive_overlay(self, p: QPainter, rect: QRectF | None = None) -> None:
        """Hover wash + focus ring over `rect` (defaults to the whole widget)."""
        t = theme_manager().tokens
        r = rect if rect is not None else QRectF(self.rect())
        radius = getattr(t, self._radius_token)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._hover_t > 0 and self.isEnabled():
            c = to_qcolor(t.COLOR_HOVER_OVERLAY)
            c.setAlphaF(c.alphaF() * self._hover_t)
            path = QPainterPath()
            path.addRoundedRect(r, radius, radius)
            p.fillPath(path, c)
        if self.has_focus_ring:
            w = self.FOCUS_RING_WIDTH
            p.setPen(QPen(to_qcolor(t.COLOR_BORDER_FOCUS), w))
            p.setBrush(Qt.BrushStyle.NoBrush)
            inset = w / 2
            p.drawRoundedRect(r.adjusted(inset, inset, -inset, -inset), radius - inset, radius - inset)

"""
InputField – states: Default, Hover, Focused, Error (+ Disabled).

Pure QSS (`:hover`, `:focus`, `[error="true"]`) – QLineEdit already owns its border box,
so no painted overlay is needed. Optional leading SVG icon (e.g. magnifier for filter search).
"""
from __future__ import annotations

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QLineEdit, QWidget

from nexus.assets import icon_loader
from nexus.components._util import force_state, set_prop
from nexus.styles.theme_manager import theme_manager


class InputField(QLineEdit):
    def __init__(self, placeholder: str = "", icon: str | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self._icon_name = icon
        self._icon_action: QAction | None = None
        if icon:
            self._icon_action = self.addAction(self._make_icon(), QLineEdit.ActionPosition.LeadingPosition)
        theme_manager().theme_changed.connect(self._on_theme_changed)

    def set_error(self, error: bool) -> None:
        set_prop(self, "error", bool(error))

    def set_forced_state(self, state: str | None) -> None:     # design-QA hook
        force_state(self, state)

    def _make_icon(self):
        t = theme_manager().tokens
        return icon_loader.make_icon(self._icon_name, t.COLOR_TEXT_MUTED)

    def _on_theme_changed(self, _tokens) -> None:
        if self._icon_action:
            self._icon_action.setIcon(self._make_icon())


from PyQt6.QtCore import QEvent, QRectF, Qt  # noqa: E402
from PyQt6.QtGui import QPainter, QPen  # noqa: E402
from PyQt6.QtWidgets import QVBoxLayout  # noqa: E402

from nexus.tokens.color_utils import to_qcolor, with_alpha  # noqa: E402


class GlowInput(QWidget):
    """Prominent search field: a large InputField that wears a soft focus halo (Semantic Search, spec Screen 8)."""
    HALO = 4

    def __init__(self, placeholder: str = "", icon: str | None = "search", parent: QWidget | None = None):
        super().__init__(parent)
        self.field = InputField(placeholder, icon=icon)
        set_prop(self.field, "size", "lg")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(self.HALO, self.HALO, self.HALO, self.HALO)
        lay.addWidget(self.field)
        self.field.installEventFilter(self)
        theme_manager().theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, _t) -> None:
        self.update()

    def eventFilter(self, obj, ev):
        if obj is self.field and ev.type() in (QEvent.Type.FocusIn, QEvent.Type.FocusOut):
            self.update()
        return super().eventFilter(obj, ev)

    def paintEvent(self, event):
        if not self.field.hasFocus():
            return
        t = theme_manager().tokens
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for i, alpha in enumerate((0.30, 0.16, 0.07)):          # three fading rings = soft glow
            p.setPen(QPen(to_qcolor(with_alpha(t.COLOR_BORDER_FOCUS, alpha)), 1.5))
            off = 1.2 + i * 1.1
            p.drawRoundedRect(QRectF(self.field.geometry()).adjusted(-off, -off, off, off), t.RADIUS_LG + off, t.RADIUS_LG + off)
        p.end()

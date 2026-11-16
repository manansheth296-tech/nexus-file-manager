"""
BreadcrumbBar – clickable rounded pills with chevron separators [spec Screen 1].

Clicking blank space (or calling begin_edit(), bound to Ctrl+L) swaps to an editable path
field: Enter submits `pathSubmitted`, Esc cancels. With editable=False (Storage Doctor) it is
a plain drill-down trail.
"""
from __future__ import annotations

from PyQt6.QtCore import QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QFontMetrics, QPainter
from PyQt6.QtWidgets import QAbstractButton, QFrame, QHBoxLayout, QStackedWidget, QWidget

from nexus.assets import icon_loader
from nexus.components._interactive import InteractiveMixin
from nexus.components.input_field import InputField
from nexus.core.navigation import SEP
from nexus.styles.theme_manager import theme_manager
from nexus.tokens.base import CONTROL_HEIGHT_MD, SPACE_MD, SPACE_XS
from nexus.tokens.color_utils import to_qcolor

PILL_H = 24


class _Pill(InteractiveMixin, QAbstractButton):
    def __init__(self, text: str, current: bool):
        super().__init__()
        self.setText(text)
        self._current = current
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._init_interactive("RADIUS_XL")           # 12px on a 24px pill = full capsule

    def _font(self) -> QFont:
        f = QFont(self.font())
        f.setWeight(QFont.Weight.DemiBold if self._current else QFont.Weight.Medium)
        return f

    def sizeHint(self) -> QSize:
        return QSize(QFontMetrics(self._font()).horizontalAdvance(self.text()) + 2 * SPACE_MD, PILL_H)

    def paintEvent(self, event):
        t = theme_manager().tokens
        r = QRectF(self.rect())
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._current:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(to_qcolor(t.COLOR_ACCENT_SOFT))
            p.drawRoundedRect(r, t.RADIUS_XL, t.RADIUS_XL)
        self._paint_interactive_overlay(p, r)
        p.setFont(self._font())
        p.setPen(to_qcolor(t.COLOR_ACCENT_PRIMARY if self._current else t.COLOR_TEXT_SECONDARY))
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, self.text())
        p.end()


class _Chevron(QWidget):
    SIZE = 14

    def __init__(self):
        super().__init__()
        self.setFixedSize(self.SIZE, PILL_H)
        theme_manager().theme_changed.connect(self._on_theme)

    def _on_theme(self, _t) -> None:
        self.update()

    def paintEvent(self, event):
        pm = icon_loader.render_pixmap("chevron-right", theme_manager().tokens.COLOR_TEXT_MUTED, self.SIZE)
        p = QPainter(self)
        p.drawPixmap(0, (self.height() - self.SIZE) // 2, pm)
        p.end()


class _Crumbs(QFrame):
    blankClicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setProperty("surface", "card")
        self.setFixedHeight(CONTROL_HEIGHT_MD)
        self._row = QHBoxLayout(self)
        self._row.setContentsMargins(SPACE_XS, 3, SPACE_XS, 3)
        self._row.setSpacing(2)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.blankClicked.emit()
        super().mousePressEvent(e)


class _PathEdit(InputField):
    cancelled = pyqtSignal()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.cancelled.emit()
            e.accept()
            return
        super().keyPressEvent(e)


class BreadcrumbBar(QStackedWidget):
    segmentActivated = pyqtSignal(int)   # index into segments
    pathSubmitted = pyqtSignal(str)

    def __init__(self, editable: bool = True, parent: QWidget | None = None):
        super().__init__(parent)
        self._editable = editable
        self._segments: list[str] = []
        self.setFixedHeight(CONTROL_HEIGHT_MD)
        self._crumbs = _Crumbs()
        self._edit = _PathEdit("Enter a path…")
        self.addWidget(self._crumbs)
        self.addWidget(self._edit)
        if editable:
            self._crumbs.blankClicked.connect(self.begin_edit)
            self._edit.returnPressed.connect(lambda: self.pathSubmitted.emit(self._edit.text().strip()))
            self._edit.editingFinished.connect(self._end_edit)
            self._edit.cancelled.connect(self._end_edit)

    @property
    def segments(self) -> list[str]:
        return list(self._segments)

    def path_text(self) -> str:
        p = SEP.join(self._segments)
        return p + SEP if len(self._segments) == 1 and p.endswith(":") else p

    def set_segments(self, segments: list[str]) -> None:
        self._segments = list(segments)
        row = self._crumbs._row
        while row.count():
            w = row.takeAt(0).widget()
            if w:
                w.setParent(None)
                w.deleteLater()
        self._more = _Pill("…", current=False)
        self._more.setToolTip("Show hidden folders")
        self._more.clicked.connect(self._show_hidden_menu)
        self._more.hide()
        row.addWidget(self._more)
        self._items: list[tuple[_Pill, _Chevron | None]] = []
        for i, seg in enumerate(segments):
            chev = None
            if i:
                chev = _Chevron()
                row.addWidget(chev)
            pill = _Pill(seg, current=(i == len(segments) - 1))
            pill.clicked.connect(lambda _=False, idx=i: self.segmentActivated.emit(idx))
            row.addWidget(pill)
            self._items.append((pill, chev))
        row.addStretch(1)
        self._hidden = 0
        self._end_edit()
        self._fit()

    def _fit(self) -> None:
        """Collapse leading segments into a '…' menu when the trail doesn't fit; the current folder always stays."""
        items = getattr(self, "_items", [])
        if not items:
            return
        avail = self.width() - 2 * SPACE_XS - 10
        gap = 2 + _Chevron.SIZE + 2
        widths = [p.sizeHint().width() + 2 + (gap if c is not None else 0) for p, c in items]
        more_w = self._more.sizeHint().width() + 2
        total, first = 0, len(items) - 1
        for i in range(len(items) - 1, -1, -1):
            need = widths[i] + (more_w if i > 0 else 0)
            if i == len(items) - 1 or total + need <= avail:
                total += widths[i]
                first = i
            else:
                break
        for i, (pill, chev) in enumerate(items):
            pill.setVisible(i >= first)
            if chev is not None:
                chev.setVisible(i >= first)
        self._hidden = first
        self._more.setVisible(first > 0)

    @property
    def hidden_count(self) -> int:
        return getattr(self, "_hidden", 0)

    def _show_hidden_menu(self) -> None:
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        for i in range(self._hidden):
            act = menu.addAction(self._segments[i])
            act.triggered.connect(lambda _=False, idx=i: self.segmentActivated.emit(idx))
        menu.exec(self._more.mapToGlobal(self._more.rect().bottomLeft()))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._fit()

    def begin_edit(self) -> None:        # Ctrl+L
        if not self._editable:
            return
        self._edit.setText(self.path_text())
        self.setCurrentIndex(1)
        self._edit.setFocus()
        self._edit.selectAll()

    def _end_edit(self) -> None:
        self.setCurrentIndex(0)

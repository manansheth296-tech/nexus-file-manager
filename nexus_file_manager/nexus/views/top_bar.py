"""
TopBar – navigation row [spec Screen 1]: Back/Forward/Up/Refresh, breadcrumb (Ctrl+L), live filter
(Ctrl+F), Deep Search, New Folder, New File, Theme Picker, Toggle Preview (+ a list/grid view toggle,
[assumed] – the spec defines both modes but no control to switch between them).
Below COMPACT_TOOLBAR_BREAKPOINT the labelled buttons collapse to icon-only.
"""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QWidget

from nexus.components import Button, Divider, InputField
from nexus.components.breadcrumb import BreadcrumbBar
from nexus.tokens.base import COMPACT_TOOLBAR_BREAKPOINT, SPACE_LG, SPACE_SM, SPACE_XS, TOPBAR_HEIGHT


class TopBar(QFrame):
    backRequested = pyqtSignal()
    forwardRequested = pyqtSignal()
    upRequested = pyqtSignal()
    refreshRequested = pyqtSignal()
    pathSubmitted = pyqtSignal(str)
    segmentActivated = pyqtSignal(int)
    filterChanged = pyqtSignal(str)
    deepSearchRequested = pyqtSignal()
    newFolderRequested = pyqtSignal()
    newFileRequested = pyqtSignal()
    themePickerRequested = pyqtSignal()
    previewToggled = pyqtSignal(bool)
    viewModeChanged = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("surface", "surface")
        self.setFixedHeight(TOPBAR_HEIGHT)
        row = QHBoxLayout(self)
        row.setContentsMargins(SPACE_LG, 0, SPACE_LG, 0)
        row.setSpacing(SPACE_SM)

        self.btn_back = Button(icon="arrow-left", variant="ghost")
        self.btn_forward = Button(icon="arrow-right", variant="ghost")
        self.btn_up = Button(icon="arrow-up", variant="ghost")
        self.btn_refresh = Button(icon="refresh", variant="ghost")
        for b, tip, sig in ((self.btn_back, "Back (Alt+Left)", self.backRequested),
                            (self.btn_forward, "Forward (Alt+Right)", self.forwardRequested),
                            (self.btn_up, "Up one level (Alt+Up)", self.upRequested),
                            (self.btn_refresh, "Refresh (F5)", self.refreshRequested)):
            b.setToolTip(tip)
            b.clicked.connect(lambda _=False, s=sig: s.emit())
            row.addWidget(b)
        row.addSpacing(SPACE_XS)

        self.breadcrumb = BreadcrumbBar()
        self.breadcrumb.segmentActivated.connect(self.segmentActivated)
        self.breadcrumb.pathSubmitted.connect(self.pathSubmitted)
        row.addWidget(self.breadcrumb, 1)

        self.filter = InputField("Filter files…  Ctrl+F", icon="search")
        self.filter.setMinimumWidth(170)
        self.filter.setMaximumWidth(240)
        self.filter.textChanged.connect(self.filterChanged)
        row.addWidget(self.filter, 1)

        self._labelled = [
            Button("Deep Search", icon="search"),
            Button("New Folder", icon="folder-plus"),
            Button("New File", icon="file-plus"),
        ]
        self._labelled[0].clicked.connect(lambda: self.deepSearchRequested.emit())
        self._labelled[1].clicked.connect(lambda: self.newFolderRequested.emit())
        self._labelled[2].clicked.connect(lambda: self.newFileRequested.emit())
        for b in self._labelled:
            row.addWidget(b)

        self.btn_theme = Button(icon="droplet", variant="ghost")
        self.btn_theme.setToolTip("Theme Picker")
        self.btn_theme.clicked.connect(lambda: self.themePickerRequested.emit())
        row.addWidget(self.btn_theme)

        self.btn_preview = Button(icon="sidebar", variant="ghost")
        self.btn_preview.setCheckable(True)
        self.btn_preview.setChecked(True)
        self.btn_preview.setToolTip("Toggle Preview")
        self.btn_preview.toggled.connect(self.previewToggled)
        row.addWidget(self.btn_preview)

        row.addWidget(Divider(vertical=True))
        self.btn_list = Button(icon="list", variant="ghost")
        self.btn_grid = Button(icon="grid", variant="ghost")
        group = QButtonGroup(self)
        for b, mode, tip in ((self.btn_list, "table", "Details view"), (self.btn_grid, "grid", "Icon grid")):
            b.setCheckable(True)
            b.setToolTip(tip)
            group.addButton(b)
            b.clicked.connect(lambda _=False, m=mode: self.viewModeChanged.emit(m))
            row.addWidget(b)
        self.btn_list.setChecked(True)

    # ── API ───────────────────────────────────────────────────────────────
    def set_segments(self, segs: list[str]) -> None:
        self.breadcrumb.set_segments(segs)

    @property
    def segments(self) -> list[str]:
        return self.breadcrumb.segments

    def set_nav_state(self, back: bool, forward: bool, up: bool) -> None:
        self.btn_back.setEnabled(back)
        self.btn_forward.setEnabled(forward)
        self.btn_up.setEnabled(up)

    def set_view_mode(self, mode: str) -> None:
        (self.btn_grid if mode == "grid" else self.btn_list).setChecked(True)

    def begin_path_edit(self) -> None:    # Ctrl+L
        self.breadcrumb.begin_edit()

    def focus_filter(self) -> None:       # Ctrl+F
        self.filter.setFocus()
        self.filter.selectAll()

    def resizeEvent(self, e):
        compact = self.width() < COMPACT_TOOLBAR_BREAKPOINT
        for b in self._labelled:
            b.set_compact(compact)
        super().resizeEvent(e)

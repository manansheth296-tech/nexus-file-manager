"""
Component Gallery (Phase 1 preview) – every token and every component state on one
scrollable page, with a live theme toggle. Doubles as the design-QA reference sheet.
"""
from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QPainter, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (QGridLayout, QHBoxLayout, QLabel, QMainWindow, QProgressBar,
                             QScrollArea, QVBoxLayout, QWidget)

from nexus.assets import icon_loader
from nexus.components import (Badge, Button, Card, Checkbox, Divider, InputField, NexusTableView, PasswordField,
                              RowState, SegmentedTabs, SidebarItem, StageIndicator, StrengthMeter, Switch)
from nexus.components._util import set_prop
from nexus.core.mock_data import MOCK_FILES, format_size
from nexus.styles.theme_manager import theme_manager
from nexus.tokens import DAYLIGHT_SLATE, MIDNIGHT_CYBER
from nexus.tokens.base import (SIDEBAR_WIDTH, SPACE_LG, SPACE_MD, SPACE_SM, SPACE_XL, ROW_HEIGHT,
                               TABLE_HEADER_HEIGHT, WINDOW_MIN_H, WINDOW_MIN_W)
from nexus.tokens.color_utils import to_hex, to_qcolor
from nexus.tokens.file_types import FILE_TYPE_COLORS, FILE_TYPE_ICONS

SPEC_TOKENS = [
    "COLOR_BG_BASE", "COLOR_BG_SURFACE", "COLOR_BG_CARD", "COLOR_BORDER", "COLOR_BORDER_FOCUS",
    "COLOR_ACCENT_PRIMARY", "COLOR_ACCENT_SECONDARY", "COLOR_TEXT_PRIMARY", "COLOR_TEXT_SECONDARY",
    "COLOR_TEXT_MUTED", "COLOR_DANGER", "COLOR_WARNING", "COLOR_SUCCESS",
]
STATES = ["Default", "Hover", "Pressed", "Disabled", "Focused"]


def _label(text: str, role: str | None = None) -> QLabel:
    lab = QLabel(text)
    if role:
        lab.setProperty("role", role)
    return lab


class _Chip(QWidget):
    """Colour chip painted over the base background so alpha tokens read correctly."""

    def __init__(self, token: str):
        super().__init__()
        self._token = token
        self.setFixedSize(84, 44)

    def paintEvent(self, _):
        t = theme_manager().tokens
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(.5, .5, -.5, -.5)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(to_qcolor(t.COLOR_BG_BASE if self._token != "COLOR_BG_BASE" else t.COLOR_BG_SURFACE))
        p.drawRoundedRect(r, t.RADIUS_MD, t.RADIUS_MD)
        p.setBrush(to_qcolor(getattr(t, self._token)))
        p.setPen(to_qcolor(t.COLOR_BORDER_STRONG))
        p.drawRoundedRect(r, t.RADIUS_MD, t.RADIUS_MD)
        p.end()


class _Swatch(QWidget):
    def __init__(self, token: str):
        super().__init__()
        self._token = token
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        lay.addWidget(_Chip(token))
        name = _label(token.replace("COLOR_", "color-").lower().replace("_", "-"), "caption")
        self._hex = _label("", "mono")
        lay.addWidget(name)
        lay.addWidget(self._hex)
        theme_manager().theme_changed.connect(self._refresh)
        self._refresh()

    def _refresh(self, *_):
        value = getattr(theme_manager().tokens, self._token)
        self._hex.setText(value.upper() if value.startswith("#") else value)


class ComponentGallery(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nexus File Manager — Component Gallery (Phase 1)")
        self.resize(WINDOW_MIN_W, WINDOW_MIN_H + 100)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.setCentralWidget(scroll)
        body = QWidget()
        scroll.setWidget(body)
        self._col = QVBoxLayout(body)
        self._col.setContentsMargins(SPACE_XL * 2, SPACE_XL, SPACE_XL * 2, SPACE_XL * 2)
        self._col.setSpacing(SPACE_XL)

        self._build_header()
        self._build_tokens()
        self._build_buttons()
        self._build_sidebar()
        self._build_inputs()
        self._build_toggles()
        self._build_dialog_parts()
        self._build_table()
        self._build_misc()
        self._col.addStretch(1)

    # ── layout helpers ────────────────────────────────────────────────────
    def _section(self, title: str, note: str = "") -> QGridLayout:
        self._col.addWidget(_label(title, "subheading"))
        if note:
            self._col.addWidget(_label(note, "muted"))
        card = Card()
        grid = QGridLayout(card)
        grid.setContentsMargins(SPACE_XL, SPACE_LG, SPACE_XL, SPACE_LG)
        grid.setHorizontalSpacing(SPACE_XL)
        grid.setVerticalSpacing(SPACE_MD)
        self._col.addWidget(card)
        return grid

    @staticmethod
    def _matrix(grid: QGridLayout, rows: list[str], cols: list[str], factory) -> None:
        for c, name in enumerate(cols):
            grid.addWidget(_label(name.upper(), "caption"), 0, c + 1)
        for r, rname in enumerate(rows):
            grid.addWidget(_label(rname, "secondary"), r + 1, 0)
            for c, cname in enumerate(cols):
                w = factory(rname, cname)
                grid.addWidget(w, r + 1, c + 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        grid.setColumnStretch(len(cols) + 1, 1)

    # ── sections ──────────────────────────────────────────────────────────
    def _build_header(self):
        row = QHBoxLayout()
        titles = QVBoxLayout()
        titles.addWidget(_label("Nexus File Manager", "title"))
        titles.addWidget(_label("Phase 1 · tokens → QSS → base components. Every state below is rendered live from tokens.", "secondary"))
        row.addLayout(titles, 1)
        sw = Switch("Daylight demo theme")
        sw.toggled.connect(lambda on: theme_manager().apply(DAYLIGHT_SLATE if on else MIDNIGHT_CYBER))
        row.addWidget(sw)
        self._col.addLayout(row)
        self._col.addWidget(Divider())

    def _build_tokens(self):
        grid = self._section("Colour tokens", "Midnight Cyber – hex codes verbatim from the spec. Swatches repaint on theme change.")
        for i, tok in enumerate(SPEC_TOKENS):
            grid.addWidget(_Swatch(tok), i // 7, i % 7)

    def _build_buttons(self):
        grid = self._section("Button", "Default · Hover · Pressed · Disabled · Focused — four variants")

        def make(variant, state):
            b = Button("Deep Search" if variant != "danger" else "Move to Recycle Bin",
                       icon="search" if variant != "danger" else None, variant=variant.lower())
            if state == "Disabled":
                b.setEnabled(False)
            elif state != "Default":
                b.set_forced_state(state.lower() if state != "Focused" else "focus")
            return b
        self._matrix(grid, ["primary", "secondary", "ghost", "danger"], STATES, make)
        # icon-only nav buttons
        nav = QHBoxLayout()
        nav.setSpacing(4)
        for ic in ("arrow-left", "arrow-right", "arrow-up", "refresh", "folder-plus"):
            nav.addWidget(Button(icon=ic, variant="ghost"))
        nav.addStretch(1)
        grid.addWidget(_label("icon-only (nav)", "secondary"), 6, 0)
        grid.addLayout(nav, 6, 1, 1, 5)

    def _build_sidebar(self):
        grid = self._section("Sidebar item", f"Default · Hover · Active — {SIDEBAR_WIDTH}px sidebar, with and without folder badge")

        def make(row, state):
            holder = QWidget()
            holder.setFixedWidth(SIDEBAR_WIDTH - 16)
            lay = QVBoxLayout(holder)
            lay.setContentsMargins(0, 0, 0, 0)
            badge = {"plain": None, "badge": "COLOR_ACCENT_SECONDARY"}[row]
            it = SidebarItem("Downloads", "download", badge)
            if state == "Hover":
                it.set_forced_state("hover")
            elif state == "Active":
                it.set_active(True)
            elif state == "Focused":
                it.set_forced_state("focus")
            lay.addWidget(it)
            return holder
        self._matrix(grid, ["plain", "badge"], ["Default", "Hover", "Active", "Focused"], make)

    def _build_inputs(self):
        grid = self._section("Input field", "Default · Hover · Focused · Error · Disabled")

        def make(row, state):
            f = InputField("Filter files…" if row == "search" else "Path", icon="search" if row == "search" else None)
            f.setFixedWidth(200)
            if state == "Hover":
                f.set_forced_state("hover")
            elif state == "Focused":
                f.set_forced_state("focus")
            elif state == "Error":
                f.setText("C:\\no\\such\\path")
                f.set_error(True)
            elif state == "Disabled":
                f.setEnabled(False)
            return f
        self._matrix(grid, ["search", "path"], ["Default", "Hover", "Focused", "Error", "Disabled"], make)

    def _build_toggles(self):
        grid = self._section("Checkbox / Switch", "Unchecked · Checked · Indeterminate · Hover · Focused · Disabled")
        cols = ["Unchecked", "Checked", "Indeterminate", "Hover", "Focused", "Disabled"]

        def make(row, state):
            if row == "checkbox":
                cb = Checkbox("Keep newest", tristate=True)
                if state == "Checked":
                    cb.setCheckState(Qt.CheckState.Checked)
                elif state == "Indeterminate":
                    cb.setCheckState(Qt.CheckState.PartiallyChecked)
                elif state == "Hover":
                    cb.set_forced_state("hover")
                elif state == "Focused":
                    cb.set_forced_state("focus")
                elif state == "Disabled":
                    cb.setCheckState(Qt.CheckState.Checked)
                    cb.setEnabled(False)
                return cb
            if state == "Indeterminate":
                return _label("—", "muted")
            sw = Switch("Enabled")
            if state == "Checked":
                sw.setChecked(True)
            elif state == "Hover":
                sw.set_forced_state("hover")
            elif state == "Focused":
                sw.set_forced_state("focus")
            elif state == "Disabled":
                sw.setChecked(True)
                sw.setEnabled(False)
            return sw
        self._matrix(grid, ["checkbox", "switch"], cols, make)

    def _build_dialog_parts(self):
        grid = self._section("Dialog components", "Segmented tabs · password field + strength meter · hashing stage indicator")
        tabs = SegmentedTabs(["Lock (Encrypt)", "Unlock (Decrypt)"], ["lock", "shield"])
        tabs.setFixedWidth(360)
        grid.addWidget(_label("segmented tabs", "secondary"), 0, 0)
        grid.addWidget(tabs, 0, 1, 1, 3)
        grid.addWidget(_label("password + strength", "secondary"), 1, 0)
        for i, (pw, level) in enumerate((("", 0), ("hunter2", 1), ("Tr0ub4dor&3", 3), ("correct-Horse-battery-9!", 4))):
            box = QVBoxLayout()
            field = PasswordField("Password")
            field.setText(pw)
            field.setFixedWidth(210)
            meter = StrengthMeter()
            meter.setFixedWidth(210)
            meter.set_level(level, empty=not pw)
            box.addWidget(field)
            box.addWidget(meter)
            grid.addLayout(box, 1, 1 + i)
        grid.addWidget(_label("stage indicator", "secondary"), 2, 0)
        for i, (stage, prog) in enumerate(((0, 0.4), (1, 0.6), (3, 0.0))):
            si = StageIndicator()
            si.setFixedWidth(330)
            si.set_state(stage, prog)
            grid.addWidget(si, 2, 1 + i)

    def _build_table(self):
        self._col.addWidget(_label("Table row", "subheading"))
        self._col.addWidget(_label("Top to bottom: Normal · Alternating · Hover · Selected · Multi-Selected (pinned for review; the live view also reacts to mouse + Ctrl/Shift)", "muted"))
        card = Card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(SPACE_SM, SPACE_SM, SPACE_SM, SPACE_SM)
        model = QStandardItemModel(0, 4)
        model.setHorizontalHeaderLabels(["NAME", "SIZE", "TYPE", "DATE MODIFIED"])
        states = [RowState.NORMAL, RowState.ALTERNATING, RowState.HOVER, RowState.SELECTED, RowState.MULTI_SELECTED]
        for row, st in zip(MOCK_FILES[1:6], states):
            kind = row["kind"]
            name = QStandardItem(row["name"])
            name.setIcon(icon_loader.make_icon(FILE_TYPE_ICONS.get(kind, "file"), FILE_TYPE_COLORS.get(kind, theme_manager().tokens.COLOR_TEXT_SECONDARY)))
            model.appendRow([name, QStandardItem(format_size(row["size"])), QStandardItem(row["type"]),
                             QStandardItem(row["modified"])])
        view = NexusTableView()
        view.setModel(model)
        for i, st in enumerate(states):
            view.row_delegate.force_state(i, st)
        view.setFixedHeight(TABLE_HEADER_HEIGHT + ROW_HEIGHT * len(states) + 4)
        lay.addWidget(view)
        self._col.addWidget(card)

    def _build_misc(self):
        grid = self._section("File-type accents · badges · progress", "Accent hexes from the spec's file-type table")
        for i, (key, color) in enumerate(FILE_TYPE_COLORS.items()):
            cell = QHBoxLayout()
            cell.addWidget(Badge(key.upper(), color))
            cell.addWidget(_label(color, "mono"))
            cell.addStretch(1)
            grid.addLayout(cell, i // 3, i % 3)
        for j, (level, val) in enumerate((("", 38), ("warn", 76), ("danger", 93))):
            bar = QProgressBar()
            bar.setTextVisible(False)
            bar.setValue(val)
            if level:
                set_prop(bar, "level", level)
            grid.addWidget(_label(f"Drive usage {val}%", "secondary"), 3 + j, 0)
            grid.addWidget(bar, 3 + j, 1, 1, 2)
        bd = QHBoxLayout()
        for text, color in (("#finance", "COLOR_SUCCESS"), ("#academic", "COLOR_ACCENT_SECONDARY"),
                            ("#media", "COLOR_WARNING"), ("#code", "COLOR_ACCENT_PRIMARY"), ("DUPLICATE", "COLOR_DANGER")):
            bd.addWidget(Badge(text, color))
        bd.addStretch(1)
        grid.addWidget(_label("semantic badges", "secondary"), 6, 0)
        grid.addLayout(bd, 6, 1, 1, 3)

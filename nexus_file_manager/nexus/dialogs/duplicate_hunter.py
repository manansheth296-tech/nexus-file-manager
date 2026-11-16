"""
Duplicate Hunter (850 × 560) [spec Screen 5]: multi-stage hashing indicator (Size → 4 KB Header → Full SHA-256),
grouped tree (group header = name + wasted space, child rows with checkboxes), quick selection
(Keep Newest / Keep Oldest / Deselect All) and a danger "Move Selected to Recycle Bin".

UI-only: the scan is a timer-driven simulation; results come from mock_data.MOCK_DUPLICATES.
HOOKS: `scanRequested(root)` out, `trashRequested(paths)` out (nothing is moved here).
Safety rule enforced in the UI: a group may never have *every* copy selected.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from nexus.components import (Badge, Button, Card, Checkbox, ElidedLabel, IconTile, NexusDialog, StageIndicator)
from nexus.components._interactive import InteractiveMixin
from nexus.core.mock_data import MOCK_DUPLICATES, format_size
from nexus.tokens.base import DIALOG_DUPLICATE_HUNTER, SPACE_LG, SPACE_MD, SPACE_SM, SPACE_XL, SPACE_XS
from nexus.tokens.file_types import file_type_for, kind_color, kind_icon

ROW_H = 36


class _CopyRow(InteractiveMixin, QWidget):
    changed = pyqtSignal()

    def __init__(self, copy: dict, size: int, tag: str | None):
        super().__init__()
        self.copy = copy
        self.size = size
        self.setFixedHeight(ROW_H)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(SPACE_XL + SPACE_2 + 28, 0, SPACE_LG, 0)
        lay.setSpacing(SPACE_MD)
        self.check = Checkbox()
        self.check.stateChanged.connect(lambda _s: self.changed.emit())
        lay.addWidget(self.check)
        path = ElidedLabel(copy["path"])
        path.setProperty("role", "secondary")
        lay.addWidget(path, 1)
        tag_box = QWidget()
        tag_box.setFixedWidth(64)
        tl = QHBoxLayout(tag_box)
        tl.setContentsMargins(0, 0, 0, 0)
        if tag:
            tl.addWidget(Badge(tag.upper(), "COLOR_SUCCESS" if tag == "newest" else "COLOR_WARNING"))
        tl.addStretch(1)
        lay.addWidget(tag_box)
        mod = QLabel(copy["modified"])
        mod.setProperty("role", "muted")
        mod.setFixedWidth(116)
        lay.addWidget(mod)
        size_l = QLabel(format_size(size))
        size_l.setProperty("role", "muted")
        size_l.setFixedWidth(64)
        size_l.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(size_l)
        self._init_interactive("RADIUS_MD")

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.check.toggle()
        super().mouseReleaseEvent(e)

    def paintEvent(self, event):
        p = QPainter(self)
        self._paint_interactive_overlay(p)
        p.end()


SPACE_2 = 8  # small inset used to align child rows under the group's name


class _GroupCard(Card):
    changed = pyqtSignal()

    def __init__(self, group: dict):
        super().__init__("card")
        self.group = group
        copies = sorted(group["copies"], key=lambda c: c["modified"])
        newest, oldest = copies[-1]["path"], copies[0]["path"]
        col = QVBoxLayout(self)
        col.setContentsMargins(0, SPACE_XS, 0, SPACE_XS)
        col.setSpacing(0)

        head = QWidget()
        head.setFixedHeight(44)
        hl = QHBoxLayout(head)
        hl.setContentsMargins(SPACE_SM, 0, SPACE_LG, 0)
        hl.setSpacing(SPACE_MD)
        self.btn_toggle = Button(icon="chevron-down", variant="ghost")
        self.btn_toggle.setFixedSize(28, 28)
        self.btn_toggle.setToolTip("Collapse / expand")
        self.btn_toggle.clicked.connect(self._toggle_collapsed)
        hl.addWidget(self.btn_toggle)
        self.check = Checkbox(tristate=True)
        self.check.clicked.connect(self._on_group_clicked)
        hl.addWidget(self.check)
        kind = file_type_for(group["name"]) or "file"
        hl.addWidget(IconTile(kind_icon(kind), kind_color(kind), 28))
        name = ElidedLabel(group["name"])
        name.setStyleSheet("font-weight: 600;")
        hl.addWidget(name, 1)
        hl.addWidget(Badge(f"{len(copies)} copies", "COLOR_ACCENT_SECONDARY"))
        self.badge_unsafe = Badge("KEEPS NO COPY", "COLOR_DANGER")
        self.badge_unsafe.hide()
        hl.addWidget(self.badge_unsafe)
        self.wasted = group["size"] * (len(copies) - 1)
        hl.addWidget(Badge(f"{format_size(self.wasted)} wasted", "COLOR_WARNING"))
        col.addWidget(head)

        self.rows_box = QWidget()
        rl = QVBoxLayout(self.rows_box)
        rl.setContentsMargins(SPACE_SM, 0, SPACE_SM, SPACE_XS)
        rl.setSpacing(0)
        self.rows: list[_CopyRow] = []
        for c in copies:
            tag = "newest" if c["path"] == newest else ("oldest" if c["path"] == oldest else None)
            row = _CopyRow(c, group["size"], tag)
            row.changed.connect(self._on_row_changed)
            self.rows.append(row)
            rl.addWidget(row)
        col.addWidget(self.rows_box)

    # selection helpers
    def checked_rows(self) -> list[_CopyRow]:
        return [r for r in self.rows if r.check.isChecked()]

    @property
    def unsafe(self) -> bool:
        return len(self.checked_rows()) == len(self.rows)

    def set_checked(self, predicate) -> None:
        for r in self.rows:
            r.check.blockSignals(True)
            r.check.setChecked(bool(predicate(r)))
            r.check.blockSignals(False)
        self._refresh_group_state()

    def _refresh_group_state(self) -> None:
        n = len(self.checked_rows())
        self.check.blockSignals(True)
        self.check.setCheckState(Qt.CheckState.Unchecked if n == 0 else
                                 Qt.CheckState.Checked if n == len(self.rows) else Qt.CheckState.PartiallyChecked)
        self.check.blockSignals(False)
        self.badge_unsafe.setVisible(self.unsafe)

    def _on_row_changed(self) -> None:
        self._refresh_group_state()
        self.changed.emit()

    def _on_group_clicked(self) -> None:
        on = self.check.checkState() == Qt.CheckState.Checked
        self.set_checked(lambda _r: on)
        self.changed.emit()

    def _toggle_collapsed(self) -> None:
        show = not self.rows_box.isVisible()
        self.rows_box.setVisible(show)
        self.btn_toggle._icon_name = "chevron-down" if show else "chevron-right"
        self.btn_toggle._refresh_icon()


class DuplicateList(QScrollArea):
    selectionChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._body = QWidget()
        self._col = QVBoxLayout(self._body)
        self._col.setContentsMargins(0, 0, SPACE_SM, 0)
        self._col.setSpacing(SPACE_SM)
        self._col.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWidget(self._body)
        self.groups: list[_GroupCard] = []

    def set_groups(self, groups: list[dict]) -> None:
        while self._col.count():
            w = self._col.takeAt(0).widget()
            if w:
                w.setParent(None)
                w.deleteLater()
        self.groups = []
        for g in groups:
            card = _GroupCard(g)
            card.changed.connect(self.selectionChanged)
            self.groups.append(card)
            self._col.addWidget(card)

    def keep_newest(self) -> None:
        for g in self.groups:
            newest = max(g.rows, key=lambda r: r.copy["modified"])
            g.set_checked(lambda r, n=newest: r is not n)
        self.selectionChanged.emit()

    def keep_oldest(self) -> None:
        for g in self.groups:
            oldest = min(g.rows, key=lambda r: r.copy["modified"])
            g.set_checked(lambda r, o=oldest: r is not o)
        self.selectionChanged.emit()

    def deselect_all(self) -> None:
        for g in self.groups:
            g.set_checked(lambda _r: False)
        self.selectionChanged.emit()

    def selected_paths(self) -> list[str]:
        return [r.copy["path"] for g in self.groups for r in g.checked_rows()]

    def selected_bytes(self) -> int:
        return sum(r.size for g in self.groups for r in g.checked_rows())

    def has_unsafe_group(self) -> bool:
        return any(g.unsafe for g in self.groups)


class DuplicateHunterDialog(NexusDialog):
    scanRequested = pyqtSignal(str)        # HOOK: start the real scan
    trashRequested = pyqtSignal(list)      # HOOK: move these paths to the Recycle Bin

    def __init__(self, parent: QWidget | None = None, root: str = "C:\\Users\\User", animate: bool = True):
        super().__init__("Duplicate Hunter", f"Scanning {root}", "copy", "COLOR_WARNING",
                         DIALOG_DUPLICATE_HUNTER, parent)
        self.root = root
        col = QVBoxLayout(self.body)
        col.setContentsMargins(SPACE_XL, SPACE_LG, SPACE_XL, 0)
        col.setSpacing(SPACE_MD)

        scan = Card("card")
        sl = QHBoxLayout(scan)
        sl.setContentsMargins(SPACE_LG, SPACE_SM, SPACE_XL, SPACE_SM)
        sl.setSpacing(SPACE_XL)
        self.stages = StageIndicator()
        sl.addWidget(self.stages, 1)
        metrics = QVBoxLayout()
        metrics.setSpacing(0)
        self.metric_main = QLabel("Scanning…")
        self.metric_main.setProperty("role", "subheading")
        self.metric_sub = QLabel("")
        self.metric_sub.setProperty("role", "muted")
        metrics.addStretch(1)
        metrics.addWidget(self.metric_main)
        metrics.addWidget(self.metric_sub)
        metrics.addStretch(1)
        sl.addLayout(metrics)
        col.addWidget(scan)

        bar = QHBoxLayout()
        bar.setSpacing(SPACE_SM)
        self.btn_newest = Button("Keep Newest")
        self.btn_oldest = Button("Keep Oldest")
        self.btn_none = Button("Deselect All", variant="ghost")
        for b in (self.btn_newest, self.btn_oldest, self.btn_none):
            bar.addWidget(b)
        bar.addStretch(1)
        self.summary = QLabel("")
        self.summary.setProperty("role", "secondary")
        bar.addWidget(self.summary)
        col.addLayout(bar)

        self.list = DuplicateList()
        col.addWidget(self.list, 1)

        self.btn_newest.clicked.connect(self.list.keep_newest)
        self.btn_oldest.clicked.connect(self.list.keep_oldest)
        self.btn_none.clicked.connect(self.list.deselect_all)
        self.list.selectionChanged.connect(self._update_actions)

        from nexus.components import Divider
        col.addWidget(Divider())
        foot = QHBoxLayout()
        foot.setContentsMargins(0, 0, 0, SPACE_MD)
        foot.setSpacing(SPACE_SM)
        note = QLabel("Files go to the Recycle Bin — nothing is deleted permanently.")
        note.setProperty("role", "muted")
        foot.addWidget(note, 1)
        self.btn_cancel = Button("Cancel", variant="ghost")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_trash = Button("Move Selected to Recycle Bin", icon="trash", variant="danger")
        self.btn_trash.clicked.connect(self._on_trash)
        foot.addWidget(self.btn_cancel)
        foot.addWidget(self.btn_trash)
        col.addLayout(foot)

        self._set_toolbar_enabled(False)
        self._update_actions()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._step = 0.0
        self._stage = 0
        self.scanRequested.emit(root)
        if animate:
            self._timer.start(55)
        else:
            self.finish_scan()

    # ── simulated scan (HOOK: drive from real progress events) ──────────────
    _DETAILS = ["Comparing file sizes · 3,480 files", "Hashing first 4 KB · 412 candidates",
                "Computing SHA-256 · 96 candidates"]

    def _tick(self) -> None:
        self._step += 0.045
        if self._step >= 1.0:
            self._step = 0.0
            self._stage += 1
            if self._stage >= 3:
                self.finish_scan()
                return
        self.stages.set_state(self._stage, self._step)
        self.metric_sub.setText(self._DETAILS[self._stage])

    def finish_scan(self) -> None:
        self._timer.stop()
        self.stages.set_state(3)
        groups = MOCK_DUPLICATES
        wasted = sum(g["size"] * (len(g["copies"]) - 1) for g in groups)
        self.list.set_groups(groups)
        self.metric_main.setText(f"{len(groups)} duplicate groups")
        self.metric_sub.setText(f"{format_size(wasted)} reclaimable")
        self.set_subtitle(f"Scan complete · {self.root}")
        self._set_toolbar_enabled(True)
        self._update_actions()

    def _set_toolbar_enabled(self, on: bool) -> None:
        for b in (self.btn_newest, self.btn_oldest, self.btn_none):
            b.setEnabled(on)

    def _update_actions(self) -> None:
        paths, size = self.list.selected_paths(), self.list.selected_bytes()
        unsafe = self.list.has_unsafe_group()
        self.summary.setText(f"{len(paths)} selected · {format_size(size)}" if paths else "Nothing selected")
        self.btn_trash.setEnabled(bool(paths) and not unsafe)
        self.btn_trash.setToolTip("Every group must keep at least one copy" if unsafe else "")

    def _on_trash(self) -> None:
        self.trashRequested.emit(self.list.selected_paths())
        self.accept()

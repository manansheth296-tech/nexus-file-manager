"""
AI Smart Organizer (920 × 580) [spec Screen 6]: dry-run table
[Checkbox] | Original Name | Proposed Clean Name | Target Category badge | Confidence %,
with category pills (#finance #academic #media #code) and an "Execute Reorganization" action.

UI-only: proposals come from mock_data.MOCK_ORGANIZER. HOOK: `executeRequested(rows)`; nothing is renamed here.
"""
from __future__ import annotations

from PyQt6.QtCore import QAbstractTableModel, QEvent, QModelIndex, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QFontMetrics, QPainter
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from nexus.assets import icon_loader
from nexus.components import Badge, Button, Divider, NexusDialog, NexusTableView, Switch
from nexus.components._util import resolve_color
from nexus.components.table import NexusRowDelegate
from nexus.components.toggle import draw_check_box
from nexus.core.mock_data import MOCK_ORGANIZER
from nexus.styles.theme_manager import theme_manager
from nexus.tokens.base import DIALOG_AI_ORGANIZER, FONT_SIZE_XS, ICON_SIZE_MD, SPACE_LG, SPACE_MD, SPACE_SM, SPACE_XL
from nexus.tokens.color_utils import to_qcolor, with_alpha
from nexus.tokens.file_types import CATEGORY_TAG_COLORS, kind_color, kind_icon

HEADERS = ["", "ORIGINAL NAME", "PROPOSED CLEAN NAME", "TARGET CATEGORY", "CONFIDENCE"]
HIGH, GOOD = 0.90, 0.75


class OrganizerModel(QAbstractTableModel):
    checkedChanged = pyqtSignal()

    def __init__(self, rows):
        super().__init__()
        self.rows = [{"original": o, "proposed": p, "tag": tag, "confidence": c, "kind": k,
                      "checked": c >= GOOD} for o, p, tag, c, k in rows]

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return HEADERS[section]
        return None

    def flags(self, index):
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        r, c = self.rows[index.row()], index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            return (None, r["original"], r["proposed"], r["tag"], f"{round(r['confidence'] * 100)}%")[c]
        if role == Qt.ItemDataRole.CheckStateRole and c == 0:
            return Qt.CheckState.Checked if r["checked"] else Qt.CheckState.Unchecked
        if role == Qt.ItemDataRole.DecorationRole and c == 1:
            t = theme_manager().tokens
            return icon_loader.make_icon(kind_icon(r["kind"]), resolve_color(kind_color(r["kind"]), t))
        if role == Qt.ItemDataRole.ToolTipRole:
            return f"{r['original']}  →  {r['proposed']}"
        if role == Qt.ItemDataRole.UserRole:
            return r
        return None

    def set_checked(self, row: int, on: bool) -> None:
        if self.rows[row]["checked"] != on:
            self.rows[row]["checked"] = on
            self.dataChanged.emit(self.index(row, 0), self.index(row, 0))
            self.checkedChanged.emit()

    def set_all(self, predicate) -> None:
        for i, r in enumerate(self.rows):
            r["checked"] = bool(predicate(r))
        self.dataChanged.emit(self.index(0, 0), self.index(len(self.rows) - 1, 0))
        self.checkedChanged.emit()

    def checked_rows(self) -> list[dict]:
        return [r for r in self.rows if r["checked"]]


class OrganizerDelegate(NexusRowDelegate):
    def paint_content(self, painter, opt, index, state):
        t = theme_manager().tokens
        col, r = index.column(), index.data(Qt.ItemDataRole.UserRole)
        rect = QRectF(opt.rect)
        if col == 0:
            state_ = index.data(Qt.ItemDataRole.CheckStateRole)
            painter.save()
            draw_check_box(painter, QRectF(rect.center().x() - 9, rect.center().y() - 9, 18, 18), state_, t)
            painter.restore()
        elif col == 2:                                           # the proposal is the point: primary + semibold
            opt.font.setWeight(QFont.Weight.DemiBold)
            opt.palette.setColor(opt.palette.ColorRole.Text, to_qcolor(t.COLOR_TEXT_PRIMARY))
            super().paint_content(painter, opt, index, state)
        elif col == 3:
            accent = resolve_color(CATEGORY_TAG_COLORS.get(r["tag"], "COLOR_TEXT_MUTED"), t)
            font = QFont(opt.font)
            font.setPixelSize(FONT_SIZE_XS)
            font.setWeight(QFont.Weight.DemiBold)
            w = QFontMetrics(font).horizontalAdvance(r["tag"]) + 2 * SPACE_SM
            pill = QRectF(rect.left() + SPACE_MD, rect.center().y() - 10, w, 20)
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(to_qcolor(with_alpha(accent, 0.16)))
            painter.drawRoundedRect(pill, t.RADIUS_SM, t.RADIUS_SM)
            painter.setFont(font)
            painter.setPen(to_qcolor(accent))
            painter.drawText(pill, Qt.AlignmentFlag.AlignCenter, r["tag"])
            painter.restore()
        elif col == 4:
            c = r["confidence"]
            color = t.COLOR_SUCCESS if c >= HIGH else (t.COLOR_ACCENT_PRIMARY if c >= GOOD else t.COLOR_WARNING)
            bar = QRectF(rect.left() + SPACE_MD, rect.center().y() - 2, 64, 4)
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(to_qcolor(t.COLOR_BORDER_STRONG))
            painter.drawRoundedRect(bar, 2, 2)
            painter.setBrush(to_qcolor(color))
            painter.drawRoundedRect(QRectF(bar.x(), bar.y(), bar.width() * c, 4), 2, 2)
            painter.setFont(opt.font)
            painter.setPen(to_qcolor(t.COLOR_TEXT_PRIMARY))
            painter.drawText(QRectF(bar.right() + SPACE_SM, rect.top(), 48, rect.height()),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, f"{round(c * 100)}%")
            painter.restore()
        else:
            super().paint_content(painter, opt, index, state)

    def editorEvent(self, event, model, option, index):
        if index.column() == 0 and event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
            model.set_checked(index.row(), not model.rows[index.row()]["checked"])
            return True
        return False


class _OrganizerTable(NexusTableView):
    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Space:                          # space toggles the selected rows
            rows = sorted({i.row() for i in self.selectionModel().selectedRows()})
            model = self.model()
            if rows:
                target = not all(model.rows[r]["checked"] for r in rows)
                for r in rows:
                    model.set_checked(r, target)
            return
        super().keyPressEvent(e)


class AIOrganizerDialog(NexusDialog):
    executeRequested = pyqtSignal(list)    # HOOK: apply these renames/moves

    def __init__(self, parent: QWidget | None = None, root: str = "C:\\Users\\User\\Downloads", rows: list | None = None):
        super().__init__("AI Smart Organizer", "Dry run — review the proposals; nothing changes until you execute",
                         "wand", "COLOR_ACCENT_SECONDARY", DIALOG_AI_ORGANIZER, parent)
        col = QVBoxLayout(self.body)
        col.setContentsMargins(SPACE_XL, SPACE_LG, SPACE_XL, 0)
        col.setSpacing(SPACE_MD)

        top = QHBoxLayout()
        top.setSpacing(SPACE_SM)
        items = rows if rows is not None else MOCK_ORGANIZER
        self.model = OrganizerModel(items)
        top.addWidget(Badge(f"{len(self.model.rows)} files analysed", "COLOR_ACCENT_PRIMARY"))
        top.addWidget(Badge(f"{sum(r['confidence'] >= HIGH for r in self.model.rows)} high confidence", "COLOR_SUCCESS"))
        top.addWidget(Badge(f"{sum(r['confidence'] < GOOD for r in self.model.rows)} need a look", "COLOR_WARNING"))
        loc = QLabel(root)
        loc.setProperty("role", "mono")
        top.addWidget(loc)
        top.addStretch(1)
        self.sw_high = Switch("High confidence only (≥ 90%)")
        self.sw_high.toggled.connect(self._on_high_only)
        top.addWidget(self.sw_high)
        col.addLayout(top)

        self.table = _OrganizerTable()
        self.table.setItemDelegate(OrganizerDelegate(self.table))
        self.table.row_delegate = self.table.itemDelegate()
        self.table.setModel(self.model)
        self.table.set_column_spec([48, "stretch", "stretch", 150, 170])
        self.table.setSelectionMode(self.table.SelectionMode.ExtendedSelection)
        col.addWidget(self.table, 1)
        self.table.horizontalHeader().sectionClicked.connect(lambda c: self._toggle_all() if c == 0 else None)

        col.addWidget(Divider())
        foot = QHBoxLayout()
        foot.setContentsMargins(0, 0, 0, SPACE_MD)
        foot.setSpacing(SPACE_SM)
        self.btn_all = Button("Select all", variant="ghost")
        self.btn_none = Button("Deselect all", variant="ghost")
        self.btn_all.clicked.connect(lambda: self.model.set_all(lambda r: True))
        self.btn_none.clicked.connect(lambda: self.model.set_all(lambda r: False))
        foot.addWidget(self.btn_all)
        foot.addWidget(self.btn_none)
        self.summary = QLabel()
        self.summary.setProperty("role", "secondary")
        foot.addWidget(self.summary, 1, Qt.AlignmentFlag.AlignVCenter)
        self.btn_cancel = Button("Cancel", variant="ghost")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_execute = Button("Execute Reorganization", icon="check", variant="primary")
        self.btn_execute.clicked.connect(self._on_execute)
        foot.addWidget(self.btn_cancel)
        foot.addWidget(self.btn_execute)
        col.addLayout(foot)

        self.model.checkedChanged.connect(self._update)
        self._update()

    def _toggle_all(self) -> None:
        on = not all(r["checked"] for r in self.model.rows)
        self.model.set_all(lambda r: on)

    def _on_high_only(self, on: bool) -> None:
        self.model.set_all(lambda r: r["confidence"] >= (HIGH if on else GOOD))

    def _update(self) -> None:
        n = len(self.model.checked_rows())
        self.summary.setText(f"{n} of {len(self.model.rows)} selected")
        self.btn_execute.setEnabled(n > 0)

    def _on_execute(self) -> None:
        self.executeRequested.emit([dict(r) for r in self.model.checked_rows()])
        self.accept()

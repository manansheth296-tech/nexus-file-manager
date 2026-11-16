"""Mock-backed file model + sort/filter proxy (folders always sort first)."""
from __future__ import annotations

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt

from nexus.assets import icon_loader
from nexus.components._util import resolve_color
from nexus.core.mock_data import format_size
from nexus.styles.theme_manager import theme_manager
from nexus.tokens.file_types import kind_color, kind_icon

COLUMNS = ["NAME", "SIZE", "TYPE", "DATE MODIFIED"]
ROLE_SORT = Qt.ItemDataRole.UserRole
ROLE_FILE = Qt.ItemDataRole.UserRole + 1


class FileModel(QAbstractTableModel):
    def __init__(self, files: list[dict] | None = None):
        super().__init__()
        self._files: list[dict] = list(files or [])

    def set_files(self, files: list[dict]) -> None:
        self.beginResetModel()
        self._files = list(files)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._files)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(COLUMNS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                return COLUMNS[section]
            if role == Qt.ItemDataRole.TextAlignmentRole and section == 1:
                return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        f, col = self._files[index.row()], index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            return (f["name"], format_size(f["size"]) if f["size"] is not None else "—", f["type"], f["modified"])[col]
        if role == Qt.ItemDataRole.DecorationRole and col == 0:
            t = theme_manager().tokens
            return icon_loader.make_icon(kind_icon(f["kind"]), resolve_color(kind_color(f["kind"]), t))
        if role == Qt.ItemDataRole.TextAlignmentRole and col == 1:
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if role == Qt.ItemDataRole.ToolTipRole:
            return f["name"]
        if role == ROLE_SORT:
            return (f["name"].lower(), -1 if f["size"] is None else f["size"], f["type"].lower(), f["modified"])[col]
        if role == ROLE_FILE:
            return f
        return None


class FileSortProxy(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.setSortRole(ROLE_SORT)
        self.setDynamicSortFilter(True)
        self._text = ""

    def set_filter_text(self, text: str) -> None:
        self._text = text.strip().lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, row, parent) -> bool:
        if not self._text:
            return True
        return self._text in self.sourceModel().index(row, 0, parent).data().lower()

    def lessThan(self, left, right) -> bool:
        lf, rf = left.data(ROLE_FILE), right.data(ROLE_FILE)
        l_dir, r_dir = lf["kind"] == "folder", rf["kind"] == "folder"
        if l_dir != r_dir:   # folders stay on top in both sort directions
            return l_dir if self.sortOrder() == Qt.SortOrder.AscendingOrder else r_dir
        return left.data(ROLE_SORT) < right.data(ROLE_SORT)

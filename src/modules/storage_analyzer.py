"""Storage Treemap Analyzer: recursively measures disk space and generates a squarified treemap."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from src.config import format_size, FILE_CATEGORIES


class TreemapNode:
    """Represents a file or folder node in the treemap hierarchy."""

    def __init__(self, name: str, path: Path, is_dir: bool, size: int = 0):
        self.name = name
        self.path = path
        self.is_dir = is_dir
        self.size = size
        self.children: List["TreemapNode"] = []
        # Layout coordinates (normalized 0.0 to 1.0 or pixel coordinates)
        self.rect: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)  # x, y, w, h
        self.color: str = "#4A90E2"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": str(self.path),
            "is_dir": self.is_dir,
            "size": self.size,
            "size_str": format_size(self.size),
            "rect": self.rect,
            "children": [c.to_dict() for c in self.children],
        }


class StorageScanWorker(QThread):
    """Asynchronous background worker to scan directory sizes."""

    progress_updated = pyqtSignal(int, str)  # (scanned_count, current_path)
    scan_completed = pyqtSignal(object, dict)  # (root_node, category_breakdown)

    def __init__(self, target_dir: Path, max_depth: int = 4, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.target_dir = target_dir
        self.max_depth = max_depth
        self._is_cancelled = False
        self.scanned_items = 0

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            category_stats: Dict[str, int] = {
                cat: 0 for cat in FILE_CATEGORIES.keys()
            }
            category_stats["other"] = 0
            root_node = self._scan_node(self.target_dir, current_depth=0, cat_stats=category_stats)
            self.scan_completed.emit(root_node, category_stats)
        except Exception as e:
            print(f"Error in storage scan: {e}")
            empty_root = TreemapNode(self.target_dir.name, self.target_dir, True, 0)
            self.scan_completed.emit(empty_root, {})

    def _scan_node(self, path: Path, current_depth: int, cat_stats: Dict[str, int]) -> TreemapNode:
        if self._is_cancelled:
            return TreemapNode(path.name, path, path.is_dir(), 0)

        self.scanned_items += 1
        if self.scanned_items % 50 == 0:
            self.progress_updated.emit(self.scanned_items, path.name)

        if not path.is_dir():
            try:
                size = path.stat().st_size
            except OSError:
                size = 0
            # Track category stats
            ext = path.suffix.lower()
            categorized = False
            for cat, extensions in FILE_CATEGORIES.items():
                if ext in extensions:
                    cat_stats[cat] = cat_stats.get(cat, 0) + size
                    categorized = True
                    break
            if not categorized:
                cat_stats["other"] = cat_stats.get("other", 0) + size
            return TreemapNode(path.name, path, False, size)

        node = TreemapNode(path.name, path, True, 0)
        total_size = 0

        try:
            with os.scandir(path) as it:
                entries = list(it)
        except (PermissionError, OSError):
            entries = []

        for entry in entries:
            if self._is_cancelled:
                break
            entry_path = Path(entry.path)
            if entry.is_dir(follow_symlinks=False):
                if current_depth < self.max_depth:
                    child = self._scan_node(entry_path, current_depth + 1, cat_stats)
                else:
                    # Quick fast size sum without deep recursion
                    fast_size = self._fast_folder_size(entry_path)
                    child = TreemapNode(entry.name, entry_path, True, fast_size)
                node.children.append(child)
                total_size += child.size
            else:
                try:
                    file_size = entry.stat().st_size
                except OSError:
                    file_size = 0
                child = TreemapNode(entry.name, entry_path, False, file_size)
                node.children.append(child)
                total_size += file_size

                ext = entry_path.suffix.lower()
                categorized = False
                for cat, extensions in FILE_CATEGORIES.items():
                    if ext in extensions:
                        cat_stats[cat] = cat_stats.get(cat, 0) + file_size
                        categorized = True
                        break
                if not categorized:
                    cat_stats["other"] = cat_stats.get("other", 0) + file_size

        node.size = total_size
        # Sort children largest first for treemap calculation
        node.children.sort(key=lambda c: c.size, reverse=True)
        return node

    def _fast_folder_size(self, path: Path) -> int:
        """Fast folder size sum for depths exceeding max_depth."""
        total = 0
        try:
            for root, _, files in os.walk(path):
                if self._is_cancelled:
                    break
                for f in files:
                    try:
                        total += (Path(root) / f).stat().st_size
                    except OSError:
                        pass
        except OSError:
            pass
        return total


def calculate_squarified_treemap(
    nodes: List[TreemapNode], x: float, y: float, w: float, h: float
) -> None:
    """
    Squarified Treemap layout algorithm (Bruls, Huizing, van Wijk).
    Divides a bounding box into rectangles whose aspect ratios are as close to 1:1 as possible.
    """
    if not nodes or w <= 0 or h <= 0:
        return

    total_size = sum(n.size for n in nodes)
    if total_size <= 0:
        return

    # Normalized sizes summing to area (w * h)
    total_area = w * h
    node_areas = [(n, (n.size / total_size) * total_area) for n in nodes if n.size > 0]
    if not node_areas:
        return

    def layout_row(row_items: List[tuple[TreemapNode, float]], cur_x: float, cur_y: float, side_len: float, is_horizontal: bool):
        row_area = sum(a for _, a in row_items)
        if row_area <= 0 or side_len <= 0:
            return
        other_dim = row_area / side_len

        offset = 0.0
        for node, area in row_items:
            item_len = area / other_dim
            if is_horizontal:
                # row runs along width, stacking along height
                node.rect = (cur_x + offset, cur_y, item_len, other_dim)
            else:
                # row runs along height, stacking along width
                node.rect = (cur_x, cur_y + offset, other_dim, item_len)
            offset += item_len

    # Standard squarify procedure
    cur_x, cur_y, cur_w, cur_h = x, y, w, h
    remaining = list(node_areas)
    current_row: List[tuple[TreemapNode, float]] = []

    while remaining:
        shortest_side = min(cur_w, cur_h)
        is_horiz = (cur_w >= cur_h)
        candidate = remaining[0]

        test_row = current_row + [candidate]
        # Calculate worst aspect ratio of test_row
        row_sum = sum(a for _, a in test_row)
        max_ratio_test = max((max((a * shortest_side) / (row_sum ** 2), (row_sum ** 2) / (a * shortest_side)) if a > 0 else 1.0) for _, a in test_row)

        if current_row:
            cur_sum = sum(a for _, a in current_row)
            max_ratio_cur = max((max((a * shortest_side) / (cur_sum ** 2), (cur_sum ** 2) / (a * shortest_side)) if a > 0 else 1.0) for _, a in current_row)
        else:
            max_ratio_cur = float("inf")

        if max_ratio_test <= max_ratio_cur:
            current_row.append(remaining.pop(0))
        else:
            # Layout current_row
            row_area = sum(a for _, a in current_row)
            layout_row(current_row, cur_x, cur_y, cur_w if is_horiz else cur_h, is_horiz)
            if is_horiz:
                other_dim = row_area / cur_w
                cur_y += other_dim
                cur_h = max(0.0, cur_h - other_dim)
            else:
                other_dim = row_area / cur_h
                cur_x += other_dim
                cur_w = max(0.0, cur_w - other_dim)
            current_row = []

    if current_row:
        is_horiz = (cur_w >= cur_h)
        layout_row(current_row, cur_x, cur_y, cur_w if is_horiz else cur_h, is_horiz)

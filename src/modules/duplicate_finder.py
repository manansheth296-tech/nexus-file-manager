"""Smart Multi-Tier Duplicate File Finder: detects duplicate files with different names."""

import os
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from PyQt6.QtCore import QThread, pyqtSignal, QObject

from src.config import format_size


def get_partial_hash(path: Path, num_bytes: int = 4096) -> str:
    """Read first 4KB of a file and return its hex digest."""
    hasher = hashlib.md5()
    try:
        with open(path, "rb") as f:
            chunk = f.read(num_bytes)
            hasher.update(chunk)
        return hasher.hexdigest()
    except (PermissionError, OSError):
        return ""


def get_full_hash(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Calculate full SHA-256 digest of a file in chunks."""
    hasher = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    except (PermissionError, OSError):
        return ""


class DuplicateFinderWorker(QThread):
    """
    Background worker that runs a 3-tier deduplication pipeline:
    1. Size-based grouping (O(1))
    2. 4KB header hashing (Fast I/O)
    3. Full SHA-256 verification
    """

    progress_updated = pyqtSignal(int, str)  # (percent 0-100, status_message)
    duplicates_found = pyqtSignal(dict)      # {sha256_hash: [Path, Path, ...]}

    def __init__(self, search_dir: Path, min_file_size: int = 1, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.search_dir = search_dir
        self.min_file_size = min_file_size
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            # Step 1: Scan and group by file size
            self.progress_updated.emit(10, "Stage 1/3: Scanning directory and grouping files by size...")
            size_map: Dict[int, List[Path]] = defaultdict(list)
            total_scanned = 0

            for root, _, files in os.walk(self.search_dir):
                if self._is_cancelled:
                    return
                for f in files:
                    fp = Path(root) / f
                    try:
                        sz = fp.stat().st_size
                        if sz >= self.min_file_size:
                            size_map[sz].append(fp)
                            total_scanned += 1
                    except (PermissionError, OSError):
                        pass

            # Filter candidates where size appears at least twice
            size_candidates: List[List[Path]] = [paths for paths in size_map.values() if len(paths) > 1]
            if not size_candidates:
                self.progress_updated.emit(100, "Scan complete: No potential duplicates found.")
                self.duplicates_found.emit({})
                return

            # Step 2: Partial 4KB hash grouping
            self.progress_updated.emit(40, f"Stage 2/3: Checking 4KB headers on {len(size_candidates)} candidate groups...")
            partial_map: Dict[Tuple[int, str], List[Path]] = defaultdict(list)

            for group in size_candidates:
                if self._is_cancelled:
                    return
                for fp in group:
                    phash = get_partial_hash(fp)
                    if phash:
                        try:
                            sz = fp.stat().st_size
                            partial_map[(sz, phash)].append(fp)
                        except OSError:
                            pass

            full_candidates: List[List[Path]] = [paths for paths in partial_map.values() if len(paths) > 1]
            if not full_candidates:
                self.progress_updated.emit(100, "Scan complete: No duplicates found after header verification.")
                self.duplicates_found.emit({})
                return

            # Step 3: Full SHA-256 hashing
            total_items_to_hash = sum(len(grp) for grp in full_candidates)
            hashed_count = 0
            self.progress_updated.emit(70, f"Stage 3/3: Full SHA-256 verification on {total_items_to_hash} files...")

            final_duplicates: Dict[str, List[Path]] = defaultdict(list)
            for group in full_candidates:
                if self._is_cancelled:
                    return
                for fp in group:
                    if self._is_cancelled:
                        return
                    fhash = get_full_hash(fp)
                    if fhash:
                        final_duplicates[fhash].append(fp)
                    hashed_count += 1
                    pct = 70 + int((hashed_count / max(1, total_items_to_hash)) * 28)
                    self.progress_updated.emit(pct, f"Hashed {hashed_count}/{total_items_to_hash}: {fp.name}")

            # Keep only entries with >= 2 paths
            results = {h: paths for h, paths in final_duplicates.items() if len(paths) > 1}
            self.progress_updated.emit(100, f"Complete: Found {len(results)} duplicate groups.")
            self.duplicates_found.emit(results)
        except Exception as e:
            print(f"Error during duplicate search: {e}")
            self.duplicates_found.emit({})

"""Filesystem operations: async copy, move, trash, delete, rename, and directory creation."""

import os
import shutil
import time
from pathlib import Path
from typing import List, Optional, Callable
from PyQt6.QtCore import QThread, pyqtSignal, QObject
import send2trash

from src.config import format_size

CHUNK_SIZE = 1024 * 1024  # 1 MB buffer for smooth streaming copy


class FileOperationWorker(QThread):
    """Background worker thread to perform heavy copy/move/delete operations without UI lag."""

    progress_updated = pyqtSignal(int, str, str)  # (percent 0-100, current_file_name, speed_str)
    operation_completed = pyqtSignal(bool, str)   # (success, summary_message)
    file_conflict = pyqtSignal(str, str)          # (source_path, target_path)

    def __init__(
        self,
        operation: str,  # 'copy', 'move', 'delete_trash', 'delete_permanent'
        sources: List[Path],
        destination: Optional[Path] = None,
        overwrite: bool = True,
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self.operation = operation
        self.sources = sources
        self.destination = destination
        self.overwrite = overwrite
        self._is_cancelled = False

    def cancel(self):
        """Request thread cancellation."""
        self._is_cancelled = True

    def run(self):
        try:
            if self.operation in ("copy", "move"):
                self._execute_transfer()
            elif self.operation == "delete_trash":
                self._execute_trash()
            elif self.operation == "delete_permanent":
                self._execute_permanent_delete()
            else:
                self.operation_completed.emit(False, f"Unknown operation: {self.operation}")
        except Exception as e:
            self.operation_completed.emit(False, f"Operation failed: {str(e)}")

    def _execute_transfer(self):
        if not self.destination or not self.destination.exists():
            self.operation_completed.emit(False, "Destination directory does not exist.")
            return

        # 1. Calculate total bytes
        total_bytes = 0
        items_to_copy: List[tuple[Path, Path]] = []

        for src in self.sources:
            if not src.exists():
                continue
            if src.is_file():
                total_bytes += src.stat().st_size
                dest_file = self._resolve_conflict(self.destination / src.name)
                items_to_copy.append((src, dest_file))
            elif src.is_dir():
                dest_dir = self._resolve_conflict(self.destination / src.name)
                for root, _, files in os.walk(src):
                    rel = Path(root).relative_to(src)
                    for f in files:
                        file_path = Path(root) / f
                        try:
                            total_bytes += file_path.stat().st_size
                        except OSError:
                            pass
                        items_to_copy.append((file_path, dest_dir / rel / f))

        transferred_bytes = 0
        start_time = time.time()
        last_update_time = start_time

        for src_path, dst_path in items_to_copy:
            if self._is_cancelled:
                self.operation_completed.emit(False, "Operation was cancelled.")
                return

            dst_path.parent.mkdir(parents=True, exist_ok=True)
            self.progress_updated.emit(
                int((transferred_bytes / max(1, total_bytes)) * 100),
                src_path.name,
                "Starting...",
            )

            # Copy file content in chunks
            with open(src_path, "rb") as fsrc, open(dst_path, "wb") as fdst:
                while True:
                    if self._is_cancelled:
                        self.operation_completed.emit(False, "Operation was cancelled.")
                        return
                    chunk = fsrc.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    fdst.write(chunk)
                    transferred_bytes += len(chunk)

                    curr_time = time.time()
                    if curr_time - last_update_time >= 0.15:  # Update UI every 150ms
                        elapsed = max(0.001, curr_time - start_time)
                        speed = transferred_bytes / elapsed
                        percent = int((transferred_bytes / max(1, total_bytes)) * 100)
                        self.progress_updated.emit(
                            min(100, percent),
                            src_path.name,
                            f"{format_size(int(speed))}/s",
                        )
                        last_update_time = curr_time

            # Copy permissions and metadata
            try:
                shutil.copystat(src_path, dst_path)
            except OSError:
                pass

        # If move operation, remove source files/directories
        if self.operation == "move":
            for src in self.sources:
                if src.exists():
                    if src.is_file():
                        src.unlink(missing_ok=True)
                    elif src.is_dir():
                        shutil.rmtree(src, ignore_errors=True)

        self.progress_updated.emit(100, "Finished", "")
        action = "Moved" if self.operation == "move" else "Copied"
        self.operation_completed.emit(True, f"Successfully {action.lower()} {len(self.sources)} items.")

    def _resolve_conflict(self, target: Path) -> Path:
        """Resolve filename collisions if overwrite is False."""
        if not target.exists() or self.overwrite:
            return target
        base = target.stem
        ext = target.suffix
        counter = 1
        new_target = target.parent / f"{base} ({counter}){ext}"
        while new_target.exists():
            counter += 1
            new_target = target.parent / f"{base} ({counter}){ext}"
        return new_target

    def _execute_trash(self):
        success_count = 0
        for src in self.sources:
            if self._is_cancelled:
                break
            try:
                send2trash.send2trash(str(src))
                success_count += 1
            except Exception as e:
                print(f"Error trashing {src}: {e}")
        self.operation_completed.emit(
            True, f"Sent {success_count} item{'s' if success_count != 1 else ''} to Recycle Bin."
        )

    def _execute_permanent_delete(self):
        success_count = 0
        for src in self.sources:
            if self._is_cancelled:
                break
            try:
                if src.is_file() or src.is_symlink():
                    src.unlink(missing_ok=True)
                elif src.is_dir():
                    shutil.rmtree(src)
                success_count += 1
            except Exception as e:
                print(f"Error deleting {src}: {e}")
        self.operation_completed.emit(
            True, f"Permanently deleted {success_count} item{'s' if success_count != 1 else ''}."
        )


def create_new_folder(parent_dir: Path, name: str = "New Folder") -> Path:
    """Create a new directory, appending an incrementing index if name already exists."""
    candidate = parent_dir / name
    if not candidate.exists():
        candidate.mkdir(parents=True, exist_ok=True)
        return candidate
    counter = 1
    while (parent_dir / f"{name} ({counter})").exists():
        counter += 1
    target = parent_dir / f"{name} ({counter})"
    target.mkdir(parents=True, exist_ok=True)
    return target


def create_new_file(parent_dir: Path, name: str = "New Text Document.txt") -> Path:
    """Create a new empty file, appending an index if name already exists."""
    candidate = parent_dir / name
    if not candidate.exists():
        candidate.touch()
        return candidate
    base = candidate.stem
    ext = candidate.suffix
    counter = 1
    while (parent_dir / f"{base} ({counter}){ext}").exists():
        counter += 1
    target = parent_dir / f"{base} ({counter}){ext}"
    target.touch()
    return target


def rename_item(target: Path, new_name: str) -> Path:
    """Rename a file or folder safely."""
    dest = target.parent / new_name
    if dest.exists() and dest != target:
        raise FileExistsError(f"An item named '{new_name}' already exists.")
    return target.rename(dest)

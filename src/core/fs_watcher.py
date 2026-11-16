"""Filesystem watcher to detect external changes and auto-refresh the UI safely without blocking."""

import sys
import threading
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent


class DirectoryChangeHandler(FileSystemEventHandler):
    """Bridge between watchdog events and Qt signal emitter."""

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def on_any_event(self, event: FileSystemEvent):
        # Ignore directory changes themselves to avoid feedback loops
        if not event.is_directory:
            self.callback(event.src_path)


class FilesystemWatcher(QObject):
    """Watches the active folder for file creation, deletion, or renaming without GUI thread blocking."""

    directory_changed = pyqtSignal(str)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.observer: Optional[Observer] = None
        self.current_watched_path: Optional[str] = None
        self._lock = threading.Lock()

    def watch_directory(self, path: Path):
        """Watch the new directory non-blockingly."""
        if not path.exists() or not path.is_dir():
            self.stop()
            return

        str_path = str(path.resolve())
        with self._lock:
            if self.current_watched_path == str_path and self.observer and self.observer.is_alive():
                return

            self._stop_internal()
            self.current_watched_path = str_path
            self.observer = Observer()
            handler = DirectoryChangeHandler(lambda p: self.directory_changed.emit(p))
            try:
                self.observer.schedule(handler, str_path, recursive=False)
                self.observer.daemon = True
                self.observer.start()
            except Exception as e:
                print(f"Error starting filesystem watcher on {str_path}: {e}", file=sys.stderr)

    def _stop_internal(self):
        """Stop active observer without blocking the caller."""
        old_obs = self.observer
        self.observer = None
        self.current_watched_path = None
        if old_obs:
            try:
                old_obs.stop()
            except Exception:
                pass

    def stop(self):
        """Safely stop active watcher."""
        with self._lock:
            self._stop_internal()

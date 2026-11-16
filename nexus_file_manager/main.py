"""
Nexus File Manager – entry point.

    python main.py                          # main window (remembers theme, accent, installed themes, window geometry)
    python main.py --gallery                # component gallery (all tokens + states)
    python main.py --theme "Converge Dark"  # force a theme for this run (no persistence)
    python main.py --dialog duplicates      # duplicates | organizer | vault | vault-unlock | search | themes | themes-market
    python main.py --mock                   # use mock data instead of real filesystem
    python main.py --grab out.png [...flags] # render one frame (dialogs over the dimmed app) to PNG and exit
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtWidgets import QApplication

from nexus.core.real_backend import RealBackend
from nexus.dev.gallery import ComponentGallery
from nexus.styles.theme_manager import theme_manager
from nexus.tokens import MIDNIGHT_CYBER, THEMES
from nexus.tokens.color_utils import to_qcolor
from nexus.views.main_window import MainWindow

DIALOGS = ("duplicates", "organizer", "vault", "vault-unlock", "search", "themes", "themes-market")


def _open_dialog(win: MainWindow, name: str, query: str, grabbing: bool):
    return {
        "duplicates": lambda: win.open_duplicate_hunter(animate=not grabbing),
        "organizer": win.open_ai_organizer,
        "vault": lambda: win.open_safe_locker("lock"),
        "vault-unlock": lambda: win.open_safe_locker("unlock"),
        "search": lambda: win.open_semantic_search(query),
        "themes": lambda: win.open_theme_store(0),
        "themes-market": lambda: win.open_theme_store(1),
    }[name]()


def _install_crash_logger():
    import sys, traceback
    from datetime import datetime
    from pathlib import Path
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        log_dir = Path.home() / ".nexus_file_manager"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "crash.log"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Unhandled Exception:\n")
                traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
        except Exception:
            pass
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    sys.excepthook = handle_exception


def main(argv: list[str] | None = None) -> int:
    _install_crash_logger()
    ap = argparse.ArgumentParser(description="Nexus File Manager")
    ap.add_argument("--theme", help="theme name or alias (midnight, converge, daylight, or any catalogue name)")
    ap.add_argument("--gallery", action="store_true", help="open the component gallery instead")
    ap.add_argument("--mode", choices=("table", "grid"), default="table")
    ap.add_argument("--page", choices=("explorer", "storage"), default="explorer")
    ap.add_argument("--select", nargs="*", default=[], metavar="NAME", help="pre-select files by name")
    ap.add_argument("--size", metavar="WxH", help="window size, e.g. 1920x1080")
    ap.add_argument("--dialog", choices=DIALOGS, help="open a dialog on start")
    ap.add_argument("--query", default="", help="initial query for --dialog search")
    ap.add_argument("--mock", action="store_true", help="use mock data instead of real filesystem")
    ap.add_argument("--path", default=None, help="initial folder path to open")
    ap.add_argument("--grab", metavar="PNG", help="save a screenshot and exit")
    ap.add_argument("--no-splash", action="store_true", help="skip the launcher splash screen")
    args = ap.parse_args(argv)

    app = QApplication(sys.argv[:1])
    app.setApplicationName("Nexus File Manager")

    # Set Window, Alt-Tab, and Taskbar Application Icon
    for c in (
        Path(__file__).resolve().parent / "nexus" / "assets" / "icon.png",
        Path(__file__).resolve().parent.parent / "assets" / "icon.png",
        Path(sys.executable).parent / "assets" / "icon.png",
        Path(getattr(sys, "_MEIPASS", "")) / "assets" / "icon.png",
    ):
        if c and c.exists():
            from PyQt6.QtGui import QIcon
            app.setWindowIcon(QIcon(str(c)))
            break

    splash = None
    if not (args.grab or args.gallery or args.no_splash):
        from nexus.components.splash_screen import NexusSplashScreen
        splash = NexusSplashScreen()
        splash.show()
        splash.set_progress(25, "Loading theme engines & appearance...")

    tm = theme_manager()
    aliases = {
        "midnight": "Midnight Cyber",
        "converge": "Converge Dark",
        "daylight": "Daylight Slate (demo)",
    }
    forced = args.theme and (aliases.get(args.theme.lower()) or next((n for n in THEMES if n.lower() == args.theme.lower()), None))
    if forced:
        tm.apply(THEMES[forced], app)
    elif args.theme:
        ap.error(f"unknown theme {args.theme!r}; choose from: {', '.join(THEMES)}")
    elif not (args.grab or args.gallery):
        tm.enable_persistence()
        if not tm.restore(app):
            tm.apply(MIDNIGHT_CYBER, app)
    else:
        tm.apply(MIDNIGHT_CYBER, app)

    if args.gallery:
        win = ComponentGallery()
    else:
        if splash:
            splash.set_progress(55, "Mounting system partitions & drives...")
        backend = None if args.mock else RealBackend()
        if splash:
            splash.set_progress(80, "Initializing workspace...")
        win = MainWindow(backend=backend, persist=not (args.grab or forced))
        if args.size:
            w, h = (int(v) for v in args.size.lower().split("x"))
            win.resize(w, h)
        if args.path:
            win.navigate(args.path)
        win.top.set_view_mode(args.mode)
        win.explorer.set_mode(args.mode)
        if args.select:
            win.explorer.select_names(args.select)
        if args.page == "storage":
            win._on_tool("storage_doctor")

    if splash:
        splash.finish_and_show(win)
    else:
        win.show()
    dlg = None
    if args.dialog and not args.gallery:
        dlg = _open_dialog(win, args.dialog, args.query, bool(args.grab))

    if args.grab:
        def snap():
            target = win.centralWidget().widget() if args.gallery else win
            shot = target.grab()
            canvas = QPixmap(shot.size())
            canvas.fill(to_qcolor(tm.tokens.COLOR_BG_BASE))                  # grab() keeps transparency
            painter = QPainter(canvas)
            painter.drawPixmap(0, 0, shot)
            if dlg is not None:                                              # composite the dialog over the dimmed window
                offset = dlg.geometry().topLeft() - win.geometry().topLeft()
                painter.drawPixmap(offset, dlg.grab())
            painter.end()
            canvas.save(args.grab)
            app.quit()
        QTimer.singleShot(700, snap)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

"""Entry point for the Nexus File Manager desktop application."""

import sys
import signal
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from src.config import APP_NAME, APP_VERSION
from src.ui.main_window import MainWindow

ICON_PATH = Path(__file__).resolve().parent.parent / "assets" / "icon.png"


def main():
    # Allow clean exit with Ctrl+C in terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("Nexus")

    if ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(ICON_PATH)))

    window = MainWindow()
    if ICON_PATH.exists():
        window.setWindowIcon(QIcon(str(ICON_PATH)))
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

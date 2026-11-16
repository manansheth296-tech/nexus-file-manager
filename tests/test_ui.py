"""Headless/Offscreen GUI tests for Nexus File Manager."""

import sys
import os
import unittest
from pathlib import Path
from PyQt6.QtWidgets import QApplication

# Set offscreen platform plugin for automated testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from src.ui.main_window import MainWindow
from src.ui.treemap_widget import StorageAnalyzerWidget
from src.ui.duplicates_dialog import DuplicatesDialog
from src.ui.ai_organizer_dialog import AIOrganizerDialog
from src.ui.vault_dialog import VaultDialog


class TestNexusGUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)

    def test_main_window_instantiation(self):
        window = MainWindow()
        self.assertIsNotNone(window)
        self.assertTrue(window.windowTitle().startswith("Nexus File Manager"))

        # Check navigation
        test_path = Path(__file__).parent.resolve()
        window.navigate_to(test_path)
        self.assertEqual(window.current_path, test_path)

        # Check status bar
        self.assertTrue(window.lbl_status_items.text().endswith("item") or "items" in window.lbl_status_items.text())
        window.close()

    def test_treemap_widget_instantiation(self):
        test_path = Path(__file__).parent.resolve()
        treemap = StorageAnalyzerWidget(test_path)
        self.assertIsNotNone(treemap)
        if treemap.scan_worker and treemap.scan_worker.isRunning():
            treemap.scan_worker.cancel()
            treemap.scan_worker.wait(1000)
        treemap.close()

    def test_dialogs_instantiation(self):
        test_path = Path(__file__).parent.resolve()
        dup_dlg = DuplicatesDialog(test_path)
        self.assertIsNotNone(dup_dlg)
        if dup_dlg.worker and dup_dlg.worker.isRunning():
            dup_dlg.worker.cancel()
            dup_dlg.worker.wait(1000)
        dup_dlg.close()

        org_dlg = AIOrganizerDialog(test_path)
        self.assertIsNotNone(org_dlg)
        if org_dlg.worker and org_dlg.worker.isRunning():
            org_dlg.worker.cancel()
            org_dlg.worker.wait(1000)
        org_dlg.close()

        vault_dlg = VaultDialog(current_dir=test_path)
        self.assertIsNotNone(vault_dlg)
        vault_dlg.close()


if __name__ == "__main__":
    unittest.main()

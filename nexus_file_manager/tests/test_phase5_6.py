"""Phase 5–6 tests (dialogs, theme store, persistence, contrast, polish).
Run:  QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyQt6.QtCore import Qt  # noqa: E402
from PyQt6.QtTest import QTest  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from nexus.components.breadcrumb import BreadcrumbBar  # noqa: E402
from nexus.core.mock_data import MOCK_DUPLICATES, MOCK_ORGANIZER  # noqa: E402
from nexus.dialogs import (AIOrganizerDialog, DuplicateHunterDialog, SafeLockerDialog, SemanticSearchDialog,  # noqa: E402
                           ThemeStoreDialog)
from nexus.dialogs.ai_organizer import GOOD, HIGH  # noqa: E402
from nexus.dialogs.semantic_search import highlight_html  # noqa: E402
from nexus.core.strength import password_strength  # noqa: E402
from nexus.styles.theme_manager import ThemeManager, theme_manager  # noqa: E402
from nexus.tokens import MARKETPLACE_THEMES, MIDNIGHT_CYBER, THEMES, base  # noqa: E402
from nexus.tokens.color_utils import composite, contrast_ratio  # noqa: E402
from nexus.views.main_window import MainWindow  # noqa: E402

app = QApplication.instance() or QApplication([])
theme_manager().apply(MIDNIGHT_CYBER, app)


class DialogSizes(unittest.TestCase):
    def test_sizes_match_spec(self):
        cases = ((DuplicateHunterDialog, {"animate": False}, (850, 560)), (AIOrganizerDialog, {}, (920, 580)),
                 (SafeLockerDialog, {}, (520, 380)), (SemanticSearchDialog, {}, (780, 520)))
        m = base.DIALOG_SHADOW_MARGIN
        for cls, kw, size in cases:
            d = cls(**kw)
            d.show()
            app.processEvents()
            self.assertEqual(d.content_size, size, cls.__name__)
            self.assertEqual((d.width(), d.height()), (size[0] + 2 * m, size[1] + 2 * m), cls.__name__)
            d.close()


class DuplicateHunter(unittest.TestCase):
    def setUp(self):
        self.d = DuplicateHunterDialog(animate=False)
        self.d.show()
        app.processEvents()

    def tearDown(self):
        self.d.close()

    def test_scan_finishes_with_all_groups(self):
        self.assertTrue(self.d.stages.finished)
        self.assertEqual(len(self.d.list.groups), len(MOCK_DUPLICATES))

    def test_keep_newest_leaves_the_newest_copy_and_is_safe(self):
        self.d.btn_newest.click()
        expected = sum(len(g["copies"]) - 1 for g in MOCK_DUPLICATES)
        self.assertEqual(len(self.d.list.selected_paths()), expected)
        for g in self.d.list.groups:
            newest = max(g.rows, key=lambda r: r.copy["modified"])
            self.assertFalse(newest.check.isChecked())
        self.assertFalse(self.d.list.has_unsafe_group())
        self.assertTrue(self.d.btn_trash.isEnabled())

    def test_keep_oldest_and_deselect(self):
        self.d.btn_oldest.click()
        for g in self.d.list.groups:
            self.assertFalse(min(g.rows, key=lambda r: r.copy["modified"]).check.isChecked())
        self.d.btn_none.click()
        self.assertEqual(self.d.list.selected_paths(), [])
        self.assertFalse(self.d.btn_trash.isEnabled())

    def test_selecting_every_copy_of_a_group_blocks_the_action(self):
        g = self.d.list.groups[0]
        g.check.click()                                             # tri-state header: checks all copies
        self.assertTrue(g.unsafe)
        self.assertTrue(g.badge_unsafe.isVisibleTo(self.d))
        self.assertFalse(self.d.btn_trash.isEnabled())
        g.rows[0].check.setChecked(False)                           # keep one copy -> safe again
        self.assertEqual(g.check.checkState(), Qt.CheckState.PartiallyChecked)
        self.assertTrue(self.d.btn_trash.isEnabled())

    def test_trash_emits_selected_paths_only(self):
        got = []
        self.d.trashRequested.connect(got.append)
        self.d.btn_newest.click()
        self.d.btn_trash.click()
        self.assertEqual(len(got[0]), sum(len(g["copies"]) - 1 for g in MOCK_DUPLICATES))

    def test_animated_scan_progresses_through_stages(self):
        d = DuplicateHunterDialog(animate=True)
        d.show()
        QTest.qWait(400)
        self.assertFalse(d.stages.finished)
        self.assertFalse(d.btn_newest.isEnabled())                   # toolbar locked while scanning
        d._timer.stop()
        d.close()


class AIOrganizer(unittest.TestCase):
    def test_defaults_toggle_and_execute(self):
        d = AIOrganizerDialog()
        d.show()
        app.processEvents()
        rows = d.model.rows
        self.assertEqual(len(d.model.checked_rows()), sum(r["confidence"] >= GOOD for r in rows))
        d.sw_high.setChecked(True)
        self.assertEqual(len(d.model.checked_rows()), sum(r["confidence"] >= HIGH for r in rows))
        d.btn_none.click()
        self.assertFalse(d.btn_execute.isEnabled())
        d.btn_all.click()
        got = []
        d.executeRequested.connect(got.append)
        d.btn_execute.click()
        self.assertEqual(len(got[0]), len(MOCK_ORGANIZER))
        d.close()

    def test_space_toggles_selected_rows(self):
        d = AIOrganizerDialog()
        d.show()
        d.table.selectRow(6)                                         # a row that starts unchecked (66%)
        before = d.model.rows[6]["checked"]
        QTest.keyClick(d.table, Qt.Key.Key_Space)
        self.assertNotEqual(d.model.rows[6]["checked"], before)
        d.close()


class SafeLocker(unittest.TestCase):
    def test_validation_modes_and_hook(self):
        d = SafeLockerDialog()
        d.show()
        app.processEvents()
        self.assertFalse(d.btn_go.isEnabled())
        d.password.setText("Tr0ub4dor&3")
        d.confirm.setText("nope")
        self.assertTrue(d.confirm.property("error"))                 # error state on mismatch
        self.assertFalse(d.btn_go.isEnabled())
        d.confirm.setText("Tr0ub4dor&3")
        self.assertFalse(d.confirm.property("error"))
        self.assertTrue(d.btn_go.isEnabled())
        self.assertGreaterEqual(d.meter.level, 3)
        got = []
        d.vaultActionRequested.connect(lambda *a: got.append(a))
        d.btn_go.click()
        self.assertEqual(got[0][0], "lock")
        self.assertTrue(got[0][3])                                   # safety checkbox defaults to ON
        self.assertEqual(d.password.text(), "")                      # cleared after use
        d.close()

    def test_unlock_tab(self):
        d = SafeLockerDialog(mode="unlock")
        d.show()
        app.processEvents()
        self.assertEqual(d.mode, "unlock")
        self.assertFalse(d.confirm.isVisibleTo(d))
        self.assertFalse(d.safety.isVisibleTo(d))
        self.assertEqual(d.btn_go.text(), "Unlock File")
        self.assertTrue(d.target_name.text().endswith(".nxv"))
        d.password.setText("x")
        self.assertTrue(d.btn_go.isEnabled())
        d.close()

    def test_reveal_toggle(self):
        d = SafeLockerDialog()
        self.assertFalse(d.password.revealed)
        d.password.toggle_reveal()
        self.assertTrue(d.password.revealed)
        d.close()

    def test_strength_heuristic_is_monotonic_for_typical_cases(self):
        levels = [password_strength(p) for p in ("abc", "abcdefg", "Abcdefg1", "Abcdefg1!xyz", "Tr0ub4dor&3-Horse")]
        self.assertEqual(levels, sorted(levels))
        self.assertEqual(levels[0], 0)
        self.assertEqual(levels[-1], 4)


class SemanticSearch(unittest.TestCase):
    def test_meaning_not_just_names(self):
        d = SemanticSearchDialog()
        d.show()
        d.run_query("bill")                                          # 'bill' ≈ invoice / electricity / payment
        names = d.result_names()
        self.assertEqual(names[0], "Electricity Bill – Oct 2026.pdf")
        self.assertIn("Meeting Notes.docx", names)                   # found via 'invoice' in the text
        rels = [d.model.index(i, 0).data(Qt.ItemDataRole.UserRole)["relevance"] for i in range(len(names))]
        self.assertEqual(rels, sorted(rels, reverse=True))
        d.run_query("zzzzqqq")
        self.assertEqual(d.pages.currentIndex(), 2)
        d.run_query("")
        self.assertEqual(d.pages.currentIndex(), 0)
        d.close()

    def test_highlight_markup_and_escaping(self):
        out = highlight_html("Pay the <b>bill</b> now", ["bill"], base="BASE", accent="ACCENT")
        self.assertIn("underline", out)
        self.assertIn("&lt;b&gt;", out)                              # content is escaped, never interpreted
        self.assertNotIn("<b>bill", out)

    def test_enter_activates_top_result(self):
        d = SemanticSearchDialog(query="exam")
        d.show()
        got = []
        d.resultActivated.connect(got.append)
        QTest.keyClick(d.search.field, Qt.Key.Key_Return)
        self.assertEqual(len(got), 1)


class ThemeStore(unittest.TestCase):
    def setUp(self):
        self._installed = theme_manager().installed

    def tearDown(self):
        tm = theme_manager()
        tm._installed = list(self._installed)
        tm.apply(MIDNIGHT_CYBER, app)

    def test_apply_theme_from_card_reskins_app(self):
        s = ThemeStoreDialog()
        s.show()
        s._cards["Nord Frost"].button.click()
        app.processEvents()
        self.assertEqual(theme_manager().tokens.name, "Nord Frost")
        self.assertIn("#2e3440", app.styleSheet().lower())           # the generated QSS now carries Nord's base colour
        s.close()

    def test_marketplace_install_flow(self):
        tm = theme_manager()
        s = ThemeStoreDialog(tab=1)
        s.show()
        self.assertFalse(tm.is_installed("Cyberpunk Neon"))
        got = []
        s.installRequested.connect(got.append)
        s._cards["Cyberpunk Neon"].button.click()
        self.assertEqual(got, ["Cyberpunk Neon"])
        self.assertEqual(s._cards["Cyberpunk Neon"].state, "installing")
        QTest.qWait(1200)
        self.assertTrue(tm.is_installed("Cyberpunk Neon"))
        app.processEvents()
        self.assertEqual(s._cards["Cyberpunk Neon"].state, "installed")   # card flips to Apply after install
        s.close()

    def test_accent_override_and_reset(self):
        tm = theme_manager()
        tm.apply_accent("#FB7185")
        self.assertEqual(tm.tokens.COLOR_ACCENT_PRIMARY, "#FB7185")
        self.assertEqual(tm.tokens.COLOR_BORDER_FOCUS, "#FB7185")
        self.assertEqual(tm.tokens.name, "Midnight Cyber")
        tm.reset_accent()
        self.assertEqual(tm.tokens.COLOR_ACCENT_PRIMARY, MIDNIGHT_CYBER.COLOR_ACCENT_PRIMARY)

    def test_square_corner_theme_changes_radius_everywhere(self):
        theme_manager().apply(THEMES["Windows 95 Retro"], app)
        self.assertIn("border-radius: 0px", app.styleSheet())
        self.assertNotIn("border-radius: 6px", app.styleSheet())


class Persistence(unittest.TestCase):
    """Uses an explicit temp INI file, so the developer's real settings are never read or written."""

    def _manager(self, tmp: str) -> ThemeManager:
        m = ThemeManager()
        m.set_settings_file(str(Path(tmp) / "nexus-test.ini"))
        return m

    def test_theme_accent_and_installed_survive_a_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = self._manager(tmp)
            first.enable_persistence()
            first.install(MARKETPLACE_THEMES[0])
            first.apply(THEMES["Nord Frost"], app)
            first.apply_accent("#A78BFA")
            second = self._manager(tmp)                              # a fresh process, in effect
            self.assertTrue(second.restore(app))
            self.assertEqual(second.tokens.name, "Nord Frost")
            self.assertEqual(second.tokens.COLOR_ACCENT_PRIMARY, "#A78BFA")
            self.assertTrue(second.is_installed("Cyberpunk Neon"))
        theme_manager().apply(MIDNIGHT_CYBER, app)

    def test_restore_with_nothing_saved_is_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(self._manager(tmp).restore(app))

    def test_nothing_is_written_unless_persistence_is_enabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            m = self._manager(tmp)
            m.apply(THEMES["Forest Night"], app)
            self.assertFalse((Path(tmp) / "nexus-test.ini").exists())
        theme_manager().apply(MIDNIGHT_CYBER, app)

    def test_window_geometry_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            tm = theme_manager()
            tm.set_settings_file(str(Path(tmp) / "win.ini"))
            try:
                w = MainWindow(persist=True)
                w.resize(1500, 930)
                w.show()
                app.processEvents()
                w.close()
                self.assertTrue(tm.settings().contains("window/geometry"))        # saved on close
                w2 = MainWindow(persist=True)                                      # restored on start
                # (a headless virtual screen clamps the restored size, so assert the contract, not exact pixels)
                self.assertGreaterEqual(w2.width(), base.WINDOW_MIN_W)
                self.assertGreaterEqual(w2.height(), base.WINDOW_MIN_H)
                w2.close()
            finally:
                tm.set_settings_file(None)


class Accessibility(unittest.TestCase):
    def test_contrast_ratios_in_every_theme(self):
        for name, t in THEMES.items():
            surface = composite(t.COLOR_BG_SURFACE, t.COLOR_BG_BASE)
            for bg_name, bg in (("base", t.COLOR_BG_BASE), ("surface", surface)):
                self.assertGreaterEqual(contrast_ratio(t.COLOR_TEXT_PRIMARY, bg), 7.0, f"{name} primary/{bg_name}")
                self.assertGreaterEqual(contrast_ratio(t.COLOR_TEXT_SECONDARY, bg), 4.5, f"{name} secondary/{bg_name}")
                self.assertGreaterEqual(contrast_ratio(t.COLOR_TEXT_MUTED, bg), 3.0, f"{name} muted/{bg_name}")
            self.assertGreaterEqual(contrast_ratio(t.COLOR_TEXT_ON_ACCENT, t.COLOR_ACCENT_PRIMARY), 4.5, f"{name} on-accent")
            # Danger buttons: the spec fixes #EF4444 + #F8FAFC (3.6:1 – fine for bold UI text, below 4.5 for body text)
            self.assertGreaterEqual(contrast_ratio(t.COLOR_TEXT_ON_DANGER, t.COLOR_DANGER), 3.5, f"{name} on-danger")


class Polish(unittest.TestCase):
    def test_breadcrumb_collapses_leading_segments_but_keeps_current(self):
        bc = BreadcrumbBar()
        bc.resize(260, 32)
        bc.show()
        bc.set_segments(["C:", "Users", "User", "Documents", "Semester 5", "Thermodynamics", "Lab Reports"])
        app.processEvents()
        self.assertGreater(bc.hidden_count, 0)
        self.assertTrue(bc._items[-1][0].isVisibleTo(bc))            # current folder always visible
        self.assertTrue(bc._more.isVisibleTo(bc))
        bc.resize(1400, 32)
        app.processEvents()
        self.assertEqual(bc.hidden_count, 0)
        bc.close()

    def test_main_window_dialog_lifecycle_and_scrim(self):
        w = MainWindow()
        w.show()
        app.processEvents()
        dlg = w.open_semantic_search()
        self.assertIs(w._dialog, dlg)
        self.assertTrue(w.scrim.isVisible())
        dlg.reject()
        app.processEvents()
        self.assertIsNone(w._dialog)
        self.assertFalse(w.scrim.isVisible())
        w.close()

    def test_sidebar_tools_and_toolbar_open_the_right_dialogs(self):
        w = MainWindow()
        w.show()
        for key, cls in (("duplicate_hunter", DuplicateHunterDialog), ("ai_organizer", AIOrganizerDialog),
                         ("encrypted_vault", SafeLockerDialog)):
            w._on_tool(key)
            self.assertIsInstance(w._dialog, cls)
        w.top.btn_theme.click()
        self.assertIsInstance(w._dialog, ThemeStoreDialog)
        w.top.deepSearchRequested.emit()
        self.assertIsInstance(w._dialog, SemanticSearchDialog)
        w._dialog.reject()
        app.processEvents()
        w.close()

    def test_safe_locker_uses_the_selected_file(self):
        w = MainWindow()
        w.show()
        w.explorer.select_names(["Budget 2026.xlsx"])
        d = w.open_safe_locker()
        self.assertEqual(d.file["name"], "Budget 2026.xlsx")
        d.reject()
        app.processEvents()
        w.close()


if __name__ == "__main__":
    unittest.main()

"""Phase 2–4 tests. Run:  QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v"""
import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PyQt6.QtCore import QRectF, Qt  # noqa: E402
from PyQt6.QtTest import QTest  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from nexus.components.treemap import squarify  # noqa: E402
from nexus.core import mock_data  # noqa: E402
from nexus.core.navigation import NavigationHistory, join_path, parent_path, split_path  # noqa: E402
from nexus.styles.theme_manager import theme_manager  # noqa: E402
from nexus.tokens import MIDNIGHT_CYBER  # noqa: E402
from nexus.views import previews  # noqa: E402
from nexus.views.file_model import ROLE_FILE  # noqa: E402
from nexus.views.main_window import MainWindow  # noqa: E402

app = QApplication.instance() or QApplication([])
theme_manager().apply(MIDNIGHT_CYBER, app)


class Navigation(unittest.TestCase):
    def test_paths(self):
        self.assertEqual(split_path("C:\\Users\\User"), ["C:", "Users", "User"])
        self.assertEqual(join_path(["C:"]), "C:\\")
        self.assertEqual(parent_path("C:\\Users\\User"), "C:\\Users")
        self.assertEqual(parent_path("C:\\"), "C:\\")

    def test_history(self):
        h = NavigationHistory("a")
        h.push("b"); h.push("c")
        self.assertEqual(h.back(), "b")
        h.push("d")                       # pushing truncates the forward stack
        self.assertFalse(h.can_forward)
        self.assertEqual((h.back(), h.back()), ("b", "a"))


class Treemap(unittest.TestCase):
    def test_squarify_fills_rect_and_preserves_areas(self):
        rect = QRectF(0, 0, 800, 500)
        sizes = sorted([40, 25, 15, 10, 6, 4], reverse=True)
        scale = rect.width() * rect.height() / sum(sizes)
        areas = [s * scale for s in sizes]
        rects = squarify(areas, rect)
        self.assertEqual(len(rects), len(sizes))
        for r, a in zip(rects, areas):
            self.assertAlmostEqual(r.width() * r.height(), a, delta=1.0)        # box area = size
            self.assertTrue(rect.adjusted(-.01, -.01, .01, .01).contains(r))    # stays inside


class Explorer(unittest.TestCase):
    def setUp(self):
        self.w = MainWindow()
        self.w.show()
        app.processEvents()

    def tearDown(self):
        self.w.close()

    def test_folders_sort_first_in_both_directions(self):
        ex = self.w.explorer
        for order in (Qt.SortOrder.AscendingOrder, Qt.SortOrder.DescendingOrder):
            ex.table.sortByColumn(1, order)
            kinds = [ex.proxy.index(r, 0).data(ROLE_FILE)["kind"] for r in range(ex.proxy.rowCount())]
            n = kinds.count("folder")
            self.assertTrue(all(k == "folder" for k in kinds[:n]), order)

    def test_filter_and_empty_state(self):
        ex = self.w.explorer
        self.w.top.filter.setText("pdf")
        self.assertEqual(ex.item_count(), 2)
        self.w.top.filter.setText("zzzz-no-match")
        self.assertIs(ex.stack.currentWidget(), ex.empty)
        self.w.top.filter.setText("")
        self.assertEqual(ex.item_count(), len(mock_data.MOCK_FILES))

    def test_selection_survives_mode_switch(self):
        ex = self.w.explorer
        ex.select_names(["main.py", "app.js"])
        self.assertEqual(len(ex.selected_files()), 2)
        ex.set_mode("grid")
        self.assertEqual({f["name"] for f in ex.selected_files()}, {"main.py", "app.js"})
        ex.set_mode("table")
        self.assertEqual(len(ex.selected_files()), 2)

    def test_navigation_buttons_and_history(self):
        w = self.w
        w.navigate("C:\\Users\\User\\Documents")
        self.assertEqual(w.top.segments[-1], "Documents")
        self.assertTrue(w.top.btn_back.isEnabled())
        w.go_up()
        self.assertEqual(w.top.segments[-1], "User")
        w.go_back()
        self.assertEqual(w.top.segments[-1], "Documents")
        self.assertTrue(w.top.btn_forward.isEnabled())

    def test_shortcuts_ctrl_l_and_ctrl_f(self):
        QTest.keyClick(self.w, Qt.Key.Key_L, Qt.KeyboardModifier.ControlModifier)
        app.processEvents()
        self.assertEqual(self.w.top.breadcrumb.currentIndex(), 1)       # edit mode
        QTest.keyClick(self.w.top.breadcrumb._edit, Qt.Key.Key_Escape)
        self.assertEqual(self.w.top.breadcrumb.currentIndex(), 0)
        QTest.keyClick(self.w, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier)
        self.assertTrue(self.w.top.filter.hasFocus())

    def test_breadcrumb_edit_submit_navigates(self):
        bc = self.w.top.breadcrumb
        bc.begin_edit()
        bc._edit.setText("C:\\Users\\User\\Music")
        QTest.keyClick(bc._edit, Qt.Key.Key_Return)
        self.assertEqual(self.w.history.current, "C:\\Users\\User\\Music")

    def test_sidebar_active_follows_location_and_tools(self):
        w = self.w
        w.navigate("C:\\Users\\User\\Downloads")
        self.assertTrue(w.sidebar._items["path:C:\\Users\\User\\Downloads"].is_active)
        w._on_tool("storage_doctor")
        self.assertTrue(w.sidebar._items["tool:storage_doctor"].is_active)
        self.assertIs(w.pages.currentWidget(), w.storage)
        self.assertFalse(w.inspector.isVisible())                        # inspector is explorer-only

    def test_preview_toggle(self):
        self.w.top.btn_preview.setChecked(False)
        self.assertFalse(self.w.inspector.isVisible())
        self.w.top.btn_preview.setChecked(True)
        self.assertTrue(self.w.inspector.isVisible())

    def test_compact_toolbar_at_narrow_width(self):
        self.w.resize(1280, 720)
        app.processEvents()
        self.assertEqual(self.w.top._labelled[0].text(), "")
        self.w.resize(1600, 900)
        app.processEvents()
        self.assertEqual(self.w.top._labelled[0].text(), "Deep Search")


class Inspector(unittest.TestCase):
    def test_every_file_kind_gets_the_right_preview(self):
        expected = {
            "word": previews.DocPreview, "excel": previews.SheetPreview, "image": previews.ImagePreview,
            "pdf": previews.PdfPreview, "archive": previews.ArchivePreview, "audio": previews.MediaPreview,
            "video": previews.MediaPreview, "binary": previews.HexPreview,
            "powerpoint": previews.GenericPreview, "folder": previews.GenericPreview, "code": previews.GenericPreview,
        }
        by_kind = {}
        for f in mock_data.MOCK_FILES:
            by_kind.setdefault(f["kind"], f)
        for kind, cls in expected.items():
            self.assertIsInstance(previews.make_preview(by_kind[kind]), cls, kind)

    def test_inspector_states(self):
        w = MainWindow()
        w.show()
        w.explorer.select_names([])
        self.assertEqual(w.inspector.stack.currentIndex(), 0)
        w.explorer.select_names(["main.py"])
        self.assertEqual(w.inspector.stack.currentIndex(), 1)
        w.explorer.select_names(["main.py", "app.js"])
        self.assertEqual(w.inspector.stack.currentIndex(), 2)
        w.close()


class StorageDoctor(unittest.TestCase):
    def test_drill_and_breadcrumb(self):
        w = MainWindow()
        w.show()
        w._on_tool("storage_doctor")
        tm = w.storage.treemap
        self.assertEqual(tm.path_names(), ["User"])
        videos = next(t for t in tm.tiles if t.node["name"] == "Videos")
        tm.drill_into(videos.node)
        self.assertEqual(tm.path_names(), ["User", "Videos"])
        self.assertEqual(w.storage.breadcrumb.segments, ["C:", "Users", "User", "Videos"])
        w.storage._on_crumb(2)                                           # click 'User'
        self.assertEqual(tm.path_names(), ["User"])
        w.close()

    def test_tile_areas_proportional_to_size(self):
        w = MainWindow()
        w.resize(1440, 900)
        w.show()
        w._on_tool("storage_doctor")
        app.processEvents()
        tiles = w.storage.treemap.tiles
        total_area = sum(t.rect.width() * t.rect.height() for t in tiles)
        total_size = sum(t.size for t in tiles)
        for t in tiles:
            self.assertAlmostEqual(t.rect.width() * t.rect.height() / total_area, t.size / total_size, delta=0.002)
        w.close()


class Responsive(unittest.TestCase):
    def test_render_at_spec_sizes_both_themes(self):
        from nexus.tokens import DAYLIGHT_SLATE
        for theme in (MIDNIGHT_CYBER, DAYLIGHT_SLATE):
            theme_manager().apply(theme, app)
            for size in ((1280, 720), (1440, 900), (1920, 1080)):
                for mode in ("table", "grid"):
                    w = MainWindow()
                    w.resize(*size)
                    w.top.set_view_mode(mode)
                    w.explorer.set_mode(mode)
                    w.show()
                    app.processEvents()
                    self.assertFalse(w.grab().isNull())
                    w.close()
        theme_manager().apply(MIDNIGHT_CYBER, app)


if __name__ == "__main__":
    unittest.main()

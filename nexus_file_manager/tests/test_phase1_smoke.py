"""Phase 1 smoke tests. Run:  QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v"""
import os
import re
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PyQt6.QtWidgets import QApplication  # noqa: E402

from nexus.styles.qss_generator import generate_qss  # noqa: E402
from nexus.styles.theme_manager import theme_manager  # noqa: E402
from nexus.tokens import DAYLIGHT_SLATE, MIDNIGHT_CYBER  # noqa: E402
from nexus.tokens.color_utils import to_qss  # noqa: E402

app = QApplication.instance() or QApplication([])


class SpecFidelity(unittest.TestCase):
    def test_midnight_cyber_hex_codes_match_spec(self):
        t = MIDNIGHT_CYBER
        self.assertEqual(
            (t.COLOR_BG_BASE, t.COLOR_BG_SURFACE, t.COLOR_BORDER_FOCUS, t.COLOR_ACCENT_PRIMARY,
             t.COLOR_ACCENT_SECONDARY, t.COLOR_TEXT_PRIMARY, t.COLOR_TEXT_SECONDARY,
             t.COLOR_TEXT_MUTED, t.COLOR_DANGER, t.COLOR_WARNING, t.COLOR_SUCCESS),
            ("#0B0F19", "#111827", "#38BDF8", "#38BDF8", "#818CF8", "#F8FAFC", "#94A3B8",
             "#64748B", "#EF4444", "#F59E0B", "#10B981"))

    def test_alpha_converted_for_qss(self):
        self.assertEqual(to_qss("rgba(255, 255, 255, 0.04)"), "rgba(255, 255, 255, 10)")


class QssGeneration(unittest.TestCase):
    def test_no_unresolved_placeholders(self):
        for theme in (MIDNIGHT_CYBER, DAYLIGHT_SLATE):
            qss = generate_qss(theme)
            self.assertNotIn("${", qss)
            self.assertNotIn("$COLOR", qss)

    def test_themes_produce_different_qss(self):
        self.assertNotEqual(generate_qss(MIDNIGHT_CYBER), generate_qss(DAYLIGHT_SLATE))


class Components(unittest.TestCase):
    def test_gallery_builds_and_rethemes(self):
        from nexus.dev.gallery import ComponentGallery
        theme_manager().apply(MIDNIGHT_CYBER, app)
        win = ComponentGallery()
        win.show()
        app.processEvents()
        theme_manager().apply(DAYLIGHT_SLATE, app)
        app.processEvents()
        win.grab()
        theme_manager().apply(MIDNIGHT_CYBER, app)
        win.close()


class NoHardCodedColours(unittest.TestCase):
    """Colours may only be written in nexus/tokens/ (spec: nothing scattered in widgets)."""

    def test_no_hex_literals_outside_tokens(self):
        hex_re = re.compile(r"#[0-9A-Fa-f]{6}\b|rgba?\(")
        offenders = []
        for sub in ("components", "styles", "dev", "views", "dialogs", "core"):
            for path in (ROOT / "nexus" / sub).rglob("*.py"):
                for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    code = line.split("#", 1)[0] if "#" in line and "'#" not in line and '"#' not in line else line
                    if hex_re.search(code) and not line.strip().startswith(("#", '"""')):
                        offenders.append(f"{path.relative_to(ROOT)}:{n}: {line.strip()}")
        self.assertEqual(offenders, [], "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()

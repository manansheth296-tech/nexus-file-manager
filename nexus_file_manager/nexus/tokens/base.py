"""
Theme-independent design tokens.

Names mirror the designer spec (`space-md` -> SPACE_MD, `radius-lg` -> RADIUS_LG).
Values marked [spec] come straight from the handoff document; values marked
[assumed] are sensible defaults for things the spec leaves undefined.
Only int/float constants are exposed to the QSS generator (see styles/qss_generator.py).
"""

# ── Spacing scale [spec §3] ────────────────────────────────────────────────
SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 12
SPACE_LG = 16
SPACE_XL = 24
SPACE_2XL = 32

# ── Border radius [spec §3] (ThemeTokens re-exposes these as overridable) ──
RADIUS_SM = 4    # small badges, pills
RADIUS_MD = 6    # buttons, input fields
RADIUS_LG = 8    # cards, table containers, preview frame
RADIUS_XL = 12   # modals, dialog windows

# ── Layout [spec §1–2] ─────────────────────────────────────────────────────
WINDOW_DEFAULT_W, WINDOW_DEFAULT_H = 1440, 900
WINDOW_MIN_W, WINDOW_MIN_H = 840, 520
WINDOW_LARGE_W, WINDOW_LARGE_H = 1920, 1080
SIDEBAR_WIDTH = 220
INSPECTOR_WIDTH = 300

# Dialog sizes [spec §2] – (width, height) tuples, not exported to QSS
DIALOG_DUPLICATE_HUNTER = (850, 560)
DIALOG_AI_ORGANIZER = (920, 580)
DIALOG_SAFE_LOCKER = (520, 380)
DIALOG_SEMANTIC_SEARCH = (780, 520)

# ── Control metrics [assumed] ──────────────────────────────────────────────
CONTROL_HEIGHT_SM = 28
CONTROL_HEIGHT_MD = 32
CONTROL_HEIGHT_LG = 40
CONTROL_INNER_HEIGHT = CONTROL_HEIGHT_MD - 2   # content height inside a 1px border
CONTROL_LG_INNER = CONTROL_HEIGHT_LG + 4 - 2   # prominent search field (44px)
ROW_HEIGHT = 36
TABLE_HEADER_HEIGHT = 32

# ── Icons [spec: 24x24 viewBox] / rendered sizes [assumed] ─────────────────
ICON_VIEWBOX = 24
ICON_SIZE_SM = 16
ICON_SIZE_MD = 18
ICON_SIZE_LG = 24

# ── Typography [assumed – spec silent] ─────────────────────────────────────
# First installed family wins; the app falls back to the platform default.
FONT_STACK_UI = ("Inter", "SF Pro Text", "Segoe UI Variable Text", "Segoe UI", "Roboto", "Ubuntu")
FONT_STACK_MONO = ("JetBrains Mono", "Cascadia Code", "SF Mono", "Menlo", "Consolas", "DejaVu Sans Mono")
FONT_SIZE_XS = 11
FONT_SIZE_SM = 12
FONT_SIZE_MD = 13
FONT_SIZE_LG = 15
FONT_SIZE_XL = 18
FONT_SIZE_2XL = 22

# ── Motion [assumed] (milliseconds) ────────────────────────────────────────
MOTION_FAST = 120
MOTION_BASE = 180
MOTION_SLOW = 280

# ── Keyboard shortcuts [spec §2, Screen 1] ─────────────────────────────────
SHORTCUT_EDIT_PATH = "Ctrl+L"
SHORTCUT_FOCUS_SEARCH = "Ctrl+F"

# ── Phase 2–4 layout metrics [assumed] ─────────────────────────────────────
TOPBAR_HEIGHT = 56
STATUSBAR_HEIGHT = 30
GRID_CELL_W, GRID_CELL_H = 116, 124
COMPACT_TOOLBAR_BREAKPOINT = 1360      # below this width, toolbar buttons drop their labels
PREVIEW_CARD_WIDTH = INSPECTOR_WIDTH - 1 - 2 * SPACE_LG   # minus the 1px divider
DRIVE_ITEM_HEIGHT = 66

# ── Phase 5–6 dialog metrics ────────────────────────────────────────────────
DIALOG_SHADOW_MARGIN = 24                # transparent margin around a dialog so its drop shadow isn't clipped
DIALOG_HEADER_HEIGHT = 64
DIALOG_THEME_STORE = (960, 620)          # [assumed] the spec gives no size for Screen 9

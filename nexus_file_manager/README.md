# Nexus File Manager — UI build

**Status: Phases 1–4 of 6** — tokens · QSS generator · base components · main explorer · preview inspector · Storage Doctor.
Remaining: Phase 5 (Duplicate Hunter, AI Organizer, Safe Locker, Semantic Search dialogs) · Phase 6 (Theme Store + polish).

## Run
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py                                  # main window
python main.py --gallery                        # every token + component state on one page
python main.py --mode grid --select main.py     # start in icon-grid mode with a file selected
python main.py --page storage                   # open Storage Doctor
python main.py --size 1280x720 --theme daylight # check responsiveness / the demo light theme
python main.py --grab out.png [...flags]        # render one frame and exit (use QT_QPA_PLATFORM=offscreen on CI)
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
```

## Try it
`Ctrl+L` edit the path · `Ctrl+F` filter · `F5` refresh · `Alt+←/→/↑` history/up · click a column header to sort ·
list/grid toggle (top-right) · sidebar → *Storage Doctor* (click a folder tile to drill in, breadcrumb to go back) ·
droplet button cycles the demo themes · double-click a folder to enter it.

## Structure
```
main.py
nexus/
  tokens/      base · themes (ThemeTokens, MIDNIGHT_CYBER) · file_types (accents, treemap categories) · color_utils
  styles/      qss_generator (tokens -> QSS) · theme_manager
  components/  Button · SidebarItem · DriveItem · InputField · Checkbox/Switch · NexusTableView · BreadcrumbBar
               TreemapWidget · Badge · IconTile · Card/Divider · _interactive (animated hover + focus ring)
  views/       main_window · top_bar · sidebar · explorer (table + grid) · inspector · previews (7 states)
               storage_doctor · status_bar · file_model
  core/        backend (HOOK POINTS) · mock_data · navigation
  assets/      icon_loader + 37 SVG icons
  dev/         gallery
  dialogs/     (Phase 5)
tests/         23 tests incl. a guard that no colour literals exist outside tokens/
```

## Backend hook points
`core/backend.py` holds signals (UI→backend) and `# HOOK:` stubs (backend→UI). Unwired actions in the UI flash a
`HOOK: …` message in the status bar so you can see exactly where logic will plug in. `MOCK_TRANSFER` in
`views/main_window.py` animates the status-bar transfer for demo purposes only.

# 🌌 Nexus File Manager

A modern, high-performance desktop file manager built with **Python 3**, **PyQt6**, and native systems/AI utilities. Nexus features an ultra-fast asynchronous file preview engine, customizable theme system, squarified storage visualizer, multi-tier deduplication, zero-knowledge encryption, and content-aware document intelligence.

---

## 🌟 Key Features & Enhancements

### 1. ⚡ Ultra-Fast Asynchronous File Previews (with LRU Cache)
* **Zero UI Lag:** Preview generation runs entirely on background worker threads (`AsyncPreviewWorker`). Metadata (size, type, modified time) is displayed instantly ($< 1\text{ms}$), while heavy document and media rendering is calculated asynchronously.
* **In-Memory LRU Cache:** Processed image thumbnails, document text, and archive catalogs are retained in an in-memory cache, making revisits instant ($0\text{ms}$).
* **Supported File Types:**
  * 📄 **Microsoft Word (`.docx`, `.doc`, `.rtf`):** Extracts headings, paragraphs, and word counts without external office suites.
  * 📊 **Spreadsheets (`.xlsx`, `.xls`, `.csv`, `.tsv`):** Interactive mini-table view rendering the first 20 rows and columns.
  * 🖼️ **Images & Paint (`.png`, `.jpg`, `.bmp`, `.gif`, `.webp`, `.ico`, `.tiff`, `.svg`, `.psd`):** High-DPI aspect-ratio scaled image rendering with dimensions and megapixels.
  * 📑 **PDF Documents (`.pdf`):** Renders page 1 at 110 DPI with total page counts.
  * 📦 **Compressed Archives (`.zip`, `.tar`, `.gz`):** Inspects the contents of zip archives (file list, compression ratio) without extracting them.
  * 🎵 **Audio (`.mp3`, `.wav`, `.flac`, `.ogg`, `.m4a`):** Audio metadata card with format and size.
  * 🎬 **Video (`.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`):** Video metadata inspector.
  * 💻 **Code & Text (`.py`, `.js`, `.ts`, `.html`, `.css`, `.json`, `.md`, `.txt`, `.sql`):** Syntax snippet viewer with line and character counts.
  * 🔬 **Binaries & Unknown Files (`.exe`, `.dll`, `.bin`, `.iso`, `.dat`):** Formatted hexadecimal dump viewer showing raw offsets, hex bytes, and ASCII representation.

### 2. 🎨 Modern Design & Dynamic Theme Engine
* Built-in dynamic theme switcher accessible via the **Palette Icon** in the top navigation bar:
  1. **Midnight Cyber (Default)** - Dark slate with electric cyan and indigo glowing accents.
  2. **Dracula Velvet** - Deep purple-black with vampire pink & green accents.
  3. **Catppuccin Mocha** - Warm pastel dark theme.
  4. **Nord Frost** - Arctic dark blue with cool frost cyan.
  5. **OLED Pure Black** - High-contrast pure black for OLED displays.
  6. **Modern Light** - Clean light mode with subtle gray borders and blue accents.
* **Theme & Icon Store (Marketplace):** Pre-built tab showcasing downloadable community theme packs and custom folder badge bundles.
* **Vibrant Categorized Icons:** Color-coded FontAwesome vector glyphs for every file type (Blue for Word, Green for Excel, Orange for PPT, Red for PDF, Emerald for Images, Cyan for Code, Amber for Archives).

### 3. 📊 Storage Doctor (Squarified Treemap)
* Implements the **Squarified Treemap Layout Algorithm** (*Bruls, Huizing, van Wijk*) to visualize folder space usage where box area corresponds to file size.
* Double-click any folder box on the canvas to drill down into that directory.

### 4. 🧬 Smart 3-Tier Duplicate Hunter
$$\text{Filter by size } (O(1)) \longrightarrow \text{Hash 4KB header } (\text{Fast I/O}) \longrightarrow \text{Full SHA-256 Digest}$$
* Groups duplicate files with different names.
* One-click cleanup options: *"Keep Newest"*, *"Keep Oldest"*, and safe Recycle Bin moving.

### 5. 🤖 Autonomous "Downloads Zero" AI Organizer
* Scans messy directories (e.g. `Downloads` or `Desktop`).
* Classifies files into categorized folders (`Documents/Finance`, `Documents/Academic`, `Media/Images`, `Development/Code`, etc.).
* **Smart Renaming & Dry-Run Verification:** Proposes clean, readable titles with an interactive review table before making changes.

### 6. 🔍 Semantic & Content Search (TF-IDF)
* Searches inside document contents across PDFs, Markdown, Python, JSON, and text using an in-memory Inverted Index.
* Calculates relevance scores ($0\%\dots100\%$) and extracts context excerpts with matched keywords highlighted.

### 7. 🔒 Encrypted Safe Locker (AES-256-GCM)
* Password-derived keys using **PBKDF2-HMAC-SHA256** (100,000 iterations).
* Zero-knowledge authenticated encryption in Galois/Counter Mode (GCM). Tampered files or wrong passwords fail authentication automatically.

---

## 📁 Project Structure

```
FileManager/
├── assets/                         # Application Icon assets (icon.ico, icon.png)
├── dist/
│   └── NexusFileManager/
│       └── NexusFileManager.exe   # Standalone Compiled Windows Executable
├── src/
│   ├── main.py                     # Primary Application Entry Point
│   ├── config.py                   # Settings, bookmarks, MIME categories, sizing utils
│   ├── themes.py                   # Dynamic Theme Engine & 6 QSS Presets
│   ├── core/                       # Filesystem & Kernel Integrations
│   │   ├── fs_operations.py        # Async chunked copy/move/trash/rename worker
│   │   ├── fs_watcher.py           # Watchdog directory watcher with Qt signals
│   │   └── drive_detector.py       # Drive & storage partition detection
│   ├── modules/                    # Advanced Feature Engines
│   │   ├── preview_loader.py       # Asynchronous multi-format previewer + LRU Cache
│   │   ├── storage_analyzer.py     # Squarified Treemap algorithm & recursive size engine
│   │   ├── duplicate_finder.py     # 3-tier hash deduplication pipeline
│   │   ├── ai_organizer.py         # Content/Rule-based classifier & smart renamer
│   │   ├── semantic_search.py      # Inverted Index & TF-IDF content search engine
│   │   └── crypto_vault.py         # AES-256-GCM secure vault locker
│   └── ui/                         # Modern PyQt6 GUI Components
│       ├── main_window.py          # Unified MainWindow coordinator
│       ├── breadcrumb_bar.py       # Breadcrumb navigation & path switcher
│       ├── file_view.py            # Sortable Table & Grid views with context menus
│       ├── preview_panel.py        # Fast asynchronous media & document inspector
│       ├── treemap_widget.py       # Interactive QPainter Treemap canvas
│       ├── duplicates_dialog.py    # Side-by-side duplicate file cleaner modal
│       ├── ai_organizer_dialog.py  # Dry-run AI organization modal
│       ├── semantic_search_dialog.py # Document search modal
│       ├── vault_dialog.py         # Encrypted safe locker modal
│       └── theme_dialog.py         # Theme picker & Customization Store modal
├── tests/                          # Automated Unit & GUI Test Suites
│   ├── test_all_modules.py         # Tests for core hashing, encryption, treemap, ops
│   ├── test_preview_loader.py      # Tests for fast async previewer
│   └── test_ui.py                  # Headless offscreen GUI instantiation tests
├── build_app.py                    # PyInstaller packaging automation script
├── build.bat                       # 1-Click Windows build script
├── run.py                          # Root quick launcher
├── requirements.txt                # Python dependencies
└── README.md                       # Comprehensive documentation
```

---

## 🚀 Running the Application

### Option A: Run the Standalone Desktop App (.exe)
You can launch the compiled desktop application directly without installing Python dependencies:
```powershell
.\dist\NexusFileManager\NexusFileManager.exe
```

### Option B: Run via Python Source
```powershell
python run.py
```

### Option C: Recompile the Standalone App
To recompile the `.exe` at any time:
```powershell
python build_app.py
```
*(or double-click `build.bat`)*

---

## 🧪 Automated Test Suite

Run all 13 automated unit and GUI tests:
```powershell
python -m unittest discover tests
```
*(Runs in ~1.2 seconds)*

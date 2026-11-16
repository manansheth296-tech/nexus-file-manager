# Nexus File Manager: UI/UX Designer Handoff Package & Specification Brief

> **Target Platform:** Desktop Application (Windows 11, macOS, Linux)  
> **Framework:** Python 3 + PyQt6 (Qt Style Sheets / QSS + SVG Icons)  
> **Figma Canvas Target:** Desktop 1440 × 900 (Responsive: 1920 × 1080 and 1280 × 720)

---

## 1. Executive Summary & Design Vision

**Nexus File Manager** is a next-generation desktop file explorer that unifies fast file navigation with built-in storage visualization (WinDirStat-style treemaps), deduplication, zero-knowledge encryption, and AI-assisted file organization.

### Aesthetic Tone
* **Keywords:** *Hyper-clean, Local-First, Developer-Grade, Fluid, Glassmorphic / Modern Slate.*
* **Inspirations:** Raycast, Linear.app, Arc Browser, macOS Finder, Windows 11 Fluent Design.
* **Core Philosophy:** Avoid cluttered, clunky legacy enterprise UI (like Windows 7 Explorer or Total Commander). Everything should feel responsive, modular, with smooth hover transitions, clear typography, and spacious information density.

---

## 2. Complete Screen & Modal Inventory

The designer must provide Figma mockups and component variants for the following **9 core views**:

### Screen 1: Main Explorer Window (Details Table Mode)
* **Top Navigation Bar:**
  * Back, Forward, Up, and Refresh icon buttons.
  * Interactive Breadcrumb bar: Each folder segment is a clickable rounded pill button with chevron separators (`>`); clicking blank space switches into a direct text editable path input (`Ctrl+L`).
  * Live filter search input (`Ctrl+F`) with an integrated magnifying glass icon.
  * Action Buttons: "Deep Search", "New Folder", "New File", "Theme Picker", and "Toggle Preview".
* **Left Navigation Sidebar (Width: ~220px):**
  * Section 1: `QUICK ACCESS` (Home, Desktop, Downloads, Documents, Pictures, Music, Videos) with custom folder badges.
  * Section 2: `DRIVES` (Shows `C:\`, `D:\`, etc., accompanied by a subtle storage usage progress bar and free space indicator).
  * Section 3: `SPECIALIZED TOOLS` (Storage Doctor, Duplicate Hunter, AI Organizer, Encrypted Vault).
* **Central File Area:**
  * Sortable Table Columns: `NAME`, `SIZE`, `TYPE`, `DATE MODIFIED`.
  * Distinct row states: Default, Alternating tint, Hover, Selected, and Multi-Selected.
* **Bottom Status Bar:**
  * Left: Total item count / selected item count with combined byte size.
  * Right: Async background transfer progress bar showing real-time throughput (e.g. `Copying: data.iso (18.4 MB/s)`).

### Screen 2: Main Explorer Window (Icon Grid Mode)
* Identical layout to Screen 1, but the central file area switches into a responsive icon grid.
* File cards have rounded bounding boxes, centered high-res icons or thumbnails, and truncated filenames with full name tooltips.

### Screen 3: File Preview Inspector (Right Sidebar, Width: ~300px)
Must display state-specific previews for:
1. **Word Document (`.docx`, `.doc`):** Card with document icon, word count badge, and formatted typography excerpt.
2. **Spreadsheet (`.xlsx`, `.csv`):** Mini 2D table grid with styled alternating cells.
3. **Images & Paint (`.png`, `.jpg`, `.psd`, `.svg`):** High-DPI preview card with resolution pill (e.g., `1920 × 1080 px`) and megapixel badge.
4. **PDF Document (`.pdf`):** Crisp Page 1 preview thumbnail with a total page badge.
5. **Compressed Archive (`.zip`, `.tar`):** Nested file list showing files inside the zip without extracting.
6. **Audio & Video (`.mp3`, `.mp4`):** Media card with waveform graphic and file metadata.
7. **Hex Dump (`.exe`, `.bin`):** Monospace code view showing memory offsets, hex bytes, and ASCII character columns.

### Screen 4: Storage Doctor (Treemap Visualizer)
* Visual nested rectangles layout representing disk storage where box area = file size.
* Color-coded category tags (e.g. Video = Purple, Images = Green, Code = Blue, Archives = Amber, Documents = Yellow).
* Hover state showing a tooltip card with file name, size, and type.
* Breadcrumb navigation at the top to drill down into subfolders.

### Screen 5: Duplicate Hunter Dialog
* Modal dialog (850 × 560).
* Search progress header with animated multi-stage hashing indicator (Size → 4KB Header → Full SHA-256).
* Grouped tree list: Group header showing duplicate file name, total wasted space, and child rows with checkboxes.
* Quick selection toolbar: *"Keep Newest"*, *"Keep Oldest"*, *"Deselect All"*.
* Action button: *"Move Selected to Recycle Bin"* in warning/danger color.

### Screen 6: AI Smart Organizer Dialog
* Modal dialog (920 × 580).
* Header with AI magic wand icon.
* Dry-Run Table with 5 columns:
  `[Checkbox] | Original Name | Proposed Clean Name | Target Category Badge | Confidence Score %`
* Category badges with distinct color pills (`#finance`, `#academic`, `#media`, `#code`).
* Action button: *"Execute Reorganization"*.

### Screen 7: Encrypted Safe Locker Dialog
* Modal dialog (520 × 380).
* 2 Segmented Tabs: `Lock (Encrypt)` and `Unlock (Decrypt)`.
* Password input field with password strength meter or reveal toggle.
* Safety checkbox: *"Move original unencrypted file to Recycle Bin after locking"*.
* Shield visual branding.

### Screen 8: Semantic & Content Search Dialog
* Modal dialog (780 × 520).
* Search bar with prominent focus state.
* Results list showing document icon, filename, relevance percentage badge (e.g., `Relevance: 94%`), and a highlighted contextual text snippet with matching search terms underlined or bolded.

### Screen 9: Theme & Customization Store
* Tab 1: `Installed Themes` (Grid/list of preset themes with circular palette swatches).
* Tab 2: `Marketplace / Store` (Card shelf displaying downloadable community themes like *Cyberpunk Neon*, *macOS Glass*, *Windows 95 Retro*).

---

## 3. Design Tokens & Specifications

The designer should define the following tokens as Figma Variables:

### Color Palette (Midnight Cyber - Primary)
| Token Name | Hex Code | Usage |
| :--- | :--- | :--- |
| `color-bg-base` | `#0B0F19` | Application background |
| `color-bg-surface` | `#111827` | Sidebar, cards, headers, panels |
| `color-bg-card` | `rgba(255, 255, 255, 0.04)` | Subtle containers, preview frame |
| `color-border` | `rgba(255, 255, 255, 0.08)` | Dividers, card borders |
| `color-border-focus` | `#38BDF8` | Active input borders, focused items |
| `color-accent-primary` | `#38BDF8` | Primary cyan buttons, active pills |
| `color-accent-secondary` | `#818CF8` | Secondary indigo accents |
| `color-text-primary` | `#F8FAFC` | Primary headings, file names |
| `color-text-secondary` | `#94A3B8` | Column headers, dates, sizes |
| `color-text-muted` | `#64748B` | Disabled states, subtle labels |
| `color-danger` | `#EF4444` | Delete actions, error alerts |
| `color-warning` | `#F59E0B` | Vault notices, duplicate indicators |
| `color-success` | `#10B981` | Completed tasks, organized indicators |

### File Type Accent Colors
* **Word Documents:** `#2563EB` (Blue)
* **Excel Spreadsheets:** `#16A34A` (Green)
* **PowerPoint Presentations:** `#EA580C` (Orange)
* **PDF Documents:** `#EF4444` (Red)
* **Images & Paint:** `#10B981` (Emerald)
* **Code & Scripts:** `#38BDF8` (Sky Blue)
* **Archives & Packages:** `#F59E0B` (Amber)
* **Audio & Music:** `#8B5CF6` (Violet)
* **Video & Movies:** `#A855F7` (Purple)

### Spacing Scale
* `space-xs`: 4px
* `space-sm`: 8px
* `space-md`: 12px
* `space-lg`: 16px
* `space-xl`: 24px
* `space-2xl`: 32px

### Border Radius
* `radius-sm`: 4px (small badges, pills)
* `radius-md`: 6px (buttons, input fields)
* `radius-lg`: 8px (cards, table containers, preview frame)
* `radius-xl`: 12px (modals, dialog windows)

---

## 4. Component Variant Requirements

Every component created in Figma must include these interactive states:

1. **Button:** `Default`, `Hover`, `Pressed`, `Disabled`, `Focused`.
2. **Table Row:** `Normal`, `Alternating`, `Hover`, `Selected`, `Multi-Selected`.
3. **Sidebar Item:** `Default`, `Hover`, `Active (Current Path)`.
4. **Input Field:** `Default`, `Hover`, `Focused`, `Error (Red border)`.
5. **Checkbox / Switch:** `Unchecked`, `Checked`, `Indeterminate`.

---

## 5. What the Designer Must Deliver

Request the following assets from the designer:
1. **Figma File (`.fig` or Figma Team Link):**
   * Auto-Layout enabled across all components and frames.
   * Defined Figma Local Variables (Color Tokens, Typography Styles).
   * Prototype flow demonstrating navigation between Views, Modals, and Inspector panels.
2. **Icon & Graphic Assets:**
   * Exported vector SVGs (24 × 24 dp standard viewbox).
   * High-res application logo (PNG @1x, @2x, @3x and SVG).
3. **Handoff Style Guide / Spec Sheet:**
   * CSS / QSS snippet annotations or Figma inspect specs with exact paddings, margins, and hex codes.

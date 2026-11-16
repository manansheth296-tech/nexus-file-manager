"""
Nexus File Manager – Modern Windows Setup & Installer Wizard.
Provides a modern, multi-step graphical installation experience:
1. Welcome & Feature Overview
2. Destination Directory Picker (with free disk space calculation)
3. Feature & Windows Integration Checklist
4. Installation Progress & File Copying
5. Installation Complete with Instant Launch
"""
from __future__ import annotations

import os
import shutil
import sys
import subprocess
import winreg
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QRectF, QSize
from PyQt6.QtGui import QFont, QIcon, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import (QApplication, QCheckBox, QFileDialog, QFrame,
                             QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                             QProgressBar, QPushButton, QStackedWidget,
                             QVBoxLayout, QWidget, QStyle)

# Colors matching Windows 11 Fluent aesthetic
BG_BASE = "#1F1F1F"
BG_SURFACE = "#282828"
BG_CARD = "#323232"
BORDER = "#3D3D3D"
BORDER_STRONG = "#505050"
TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#D1D5DB"
TEXT_MUTED = "#8A8A8A"
ACCENT_PRIMARY = "#60CDFF"
ACCENT_HOVER = "#78D5FF"
SUCCESS = "#6CCB5F"


def get_default_install_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "Programs" / "NexusFileManager"
    return Path.home() / "AppData" / "Local" / "Programs" / "NexusFileManager"


def format_bytes(num_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


class InstallWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, source_dir: Path, target_dir: Path, options: dict):
        super().__init__()
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.options = options

    def run(self):
        try:
            self.progress.emit(5, "Preparing target directory...")
            self.target_dir.mkdir(parents=True, exist_ok=True)

            # Discover all files to copy
            all_files = []
            for root, _, files in os.walk(self.source_dir):
                for f in files:
                    src_file = Path(root) / f
                    rel_path = src_file.relative_to(self.source_dir)
                    all_files.append((src_file, self.target_dir / rel_path))

            total = len(all_files)
            if total == 0:
                raise RuntimeError(f"No files found to install in {self.source_dir}")

            # Copy files
            for idx, (src, dest) in enumerate(all_files):
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                pct = int(10 + (idx / total) * 70)
                self.progress.emit(pct, f"Installing: {dest.name}")

            exe_path = self.target_dir / "NexusFileManager.exe"
            icon_path = self.target_dir / "assets" / "icon.ico"
            if not icon_path.exists():
                icon_path = exe_path

            # Create Desktop Shortcut
            if self.options.get("desktop_shortcut", True):
                self.progress.emit(83, "Creating Desktop shortcut...")
                self._create_desktop_shortcut(exe_path, icon_path)

            # Create Start Menu Shortcut
            if self.options.get("start_menu_shortcut", True):
                self.progress.emit(88, "Creating Start Menu shortcut...")
                self._create_start_menu_shortcut(exe_path, icon_path)

            # Register Windows Context Menu
            if self.options.get("context_menu", True):
                self.progress.emit(92, "Configuring Windows Explorer context menu...")
                self._register_context_menu(exe_path)

            # Register .nxv file association
            if self.options.get("file_assoc", True):
                self.progress.emit(95, "Registering .nxv Safe Locker file association...")
                self._register_file_association(exe_path, icon_path)

            # Register in Windows Add/Remove Programs
            self.progress.emit(98, "Registering uninstaller with Windows...")
            self._register_uninstaller(exe_path, icon_path)

            self.progress.emit(100, "Installation completed successfully!")
            self.finished.emit(True, "")
        except Exception as e:
            self.finished.emit(False, str(e))

    def _create_desktop_shortcut(self, exe: Path, icon: Path):
        try:
            import win32com.client
            wshell = win32com.client.Dispatch("WScript.Shell")
            desktop = wshell.SpecialFolders("Desktop")
            shortcut = wshell.CreateShortcut(os.path.join(desktop, "Nexus File Manager.lnk"))
            shortcut.TargetPath = str(exe)
            shortcut.WorkingDirectory = str(exe.parent)
            shortcut.IconLocation = str(icon)
            shortcut.Description = "Nexus File Manager"
            shortcut.Save()
        except Exception:
            # Fallback to PowerShell
            ps_cmd = f"""
            $wshell = New-Object -ComObject WScript.Shell;
            $desk = [Environment]::GetFolderPath('Desktop');
            $s = $wshell.CreateShortcut("$desk\\Nexus File Manager.lnk");
            $s.TargetPath = '{exe}';
            $s.WorkingDirectory = '{exe.parent}';
            $s.IconLocation = '{icon}';
            $s.Save();
            """
            subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps_cmd], capture_output=True)

    def _create_start_menu_shortcut(self, exe: Path, icon: Path):
        try:
            app_data = os.environ.get("APPDATA")
            if app_data:
                sm_programs = Path(app_data) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Nexus File Manager"
                sm_programs.mkdir(parents=True, exist_ok=True)
                ps_cmd = f"""
                $wshell = New-Object -ComObject WScript.Shell;
                $s = $wshell.CreateShortcut('{sm_programs / "Nexus File Manager.lnk"}');
                $s.TargetPath = '{exe}';
                $s.WorkingDirectory = '{exe.parent}';
                $s.IconLocation = '{icon}';
                $s.Save();
                """
                subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps_cmd], capture_output=True)
        except Exception:
            pass

    def _register_context_menu(self, exe: Path):
        try:
            key_path = r"Software\Classes\Directory\shell\NexusFileManager"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, "Open in Nexus File Manager")
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, str(exe))
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path + r"\command") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f'"{exe}" "%V"')
        except Exception as e:
            print("Context menu reg error:", e)

    def _register_file_association(self, exe: Path, icon: Path):
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.nxv") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, "NexusVaultFile")
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\NexusVaultFile") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, "Nexus Encrypted Safe Locker Vault")
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\NexusVaultFile\DefaultIcon") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, str(icon))
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\NexusVaultFile\shell\open\command") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f'"{exe}" "%1"')
        except Exception as e:
            print("File assoc reg error:", e)

    def _register_uninstaller(self, exe: Path, icon: Path):
        # Create uninstaller batch script
        uninstaller_script = self.target_dir / "uninstall.bat"
        uninstaller_content = f"""@echo off
echo ========================================================
echo Uninstalling Nexus File Manager...
echo ========================================================
timeout /t 1 /nobreak >nul
taskkill /f /im NexusFileManager.exe >nul 2>&1

:: Remove shortcuts
del /q "%USERPROFILE%\\Desktop\\Nexus File Manager.lnk" >nul 2>&1
del /q "%USERPROFILE%\\OneDrive\\Desktop\\Nexus File Manager.lnk" >nul 2>&1
rmdir /s /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Nexus File Manager" >nul 2>&1

:: Remove registry keys
reg delete "HKCU\\Software\\Classes\\Directory\\shell\\NexusFileManager" /f >nul 2>&1
reg delete "HKCU\\Software\\Classes\\.nxv" /f >nul 2>&1
reg delete "HKCU\\Software\\Classes\\NexusVaultFile" /f >nul 2>&1
reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\NexusFileManager" /f >nul 2>&1

echo Nexus File Manager uninstalled. Removing files...
cd ..
timeout /t 2 /nobreak >nul
rmdir /s /q "{self.target_dir}" >nul 2>&1
echo Done.
"""
        try:
            uninstaller_script.write_text(uninstaller_content, encoding="utf-8")
        except Exception:
            pass

        # Windows Add / Remove Programs
        try:
            uninst_key = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\NexusFileManager"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, uninst_key) as key:
                winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "Nexus File Manager")
                winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0 Pro")
                winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "Nexus Team")
                winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(icon))
                winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(self.target_dir))
                winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'cmd.exe /c "{uninstaller_script}"')
                winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
        except Exception:
            pass


class SetupWizard(QMainWindow):
    def __init__(self, source_dir: Path):
        super().__init__()
        self.source_dir = source_dir
        self.setWindowTitle("Nexus File Manager – Setup Wizard")
        self.setFixedSize(680, 500)

        self.install_dir = get_default_install_dir()

        self._init_ui()
        self._apply_styles()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header Bar
        head = QWidget()
        head.setFixedHeight(72)
        head.setObjectName("head")
        hl = QHBoxLayout(head)
        hl.setContentsMargins(28, 0, 28, 0)
        hl.setSpacing(16)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        t_label = QLabel("NEXUS FILE MANAGER")
        t_label.setObjectName("headTitle")
        s_label = QLabel("Setup & Installation Wizard")
        s_label.setObjectName("headSubtitle")
        title_col.addWidget(t_label)
        title_col.addWidget(s_label)
        hl.addLayout(title_col, 1)

        v_badge = QLabel("v1.0.0 PRO")
        v_badge.setObjectName("versionBadge")
        hl.addWidget(v_badge)
        main_layout.addWidget(head)

        # Stacked Pages
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, 1)

        self._build_page1_welcome()
        self._build_page2_location()
        self._build_page3_components()
        self._build_page4_progress()
        self._build_page5_finish()

        # Bottom Navigation Bar
        self.nav_bar = QWidget()
        self.nav_bar.setFixedHeight(64)
        self.nav_bar.setObjectName("navBar")
        nl = QHBoxLayout(self.nav_bar)
        nl.setContentsMargins(28, 0, 28, 0)
        nl.setSpacing(12)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.close)
        nl.addWidget(self.btn_cancel)

        nl.addStretch(1)

        self.btn_back = QPushButton("← Back")
        self.btn_back.clicked.connect(self._go_back)
        self.btn_back.setEnabled(False)
        nl.addWidget(self.btn_back)

        self.btn_next = QPushButton("Next →")
        self.btn_next.setObjectName("btnPrimary")
        self.btn_next.clicked.connect(self._go_next)
        nl.addWidget(self.btn_next)

        main_layout.addWidget(self.nav_bar)

    # ── Page 1: Welcome ───────────────────────────────────────────────────
    def _build_page1_welcome(self):
        page = QWidget()
        pl = QVBoxLayout(page)
        pl.setContentsMargins(36, 28, 36, 20)
        pl.setSpacing(16)

        h1 = QLabel("Welcome to Nexus File Manager")
        h1.setObjectName("pageTitle")
        pl.addWidget(h1)

        desc = QLabel(
            "Nexus is an intelligent, high-performance desktop file manager featuring:\n\n"
            "  • Fluid, modern design with customizable themes & split-screen snapping\n"
            "  • Safe Locker: Zero-knowledge AES-256-GCM encrypted vaults\n"
            "  • Storage Doctor: Interactive squarified treemaps for disk analysis\n"
            "  • Duplicate Hunter: 3-tier deep hash deduplication engine\n"
            "  • AI Smart Organizer: Local categorization heuristics & clean renames\n"
            "  • Semantic & Content Search: Multi-document TF-IDF keyword indexing\n"
            "  • Deep Previews: Live Word, PDF, Hex, Zip, and CSV/Excel inspectors\n\n"
            "Click Next to choose your installation directory and options."
        )
        desc.setObjectName("pageText")
        desc.setWordWrap(True)
        pl.addWidget(desc)
        pl.addStretch(1)
        self.stack.addWidget(page)

    # ── Page 2: Location ──────────────────────────────────────────────────
    def _build_page2_location(self):
        page = QWidget()
        pl = QVBoxLayout(page)
        pl.setContentsMargins(36, 28, 36, 20)
        pl.setSpacing(16)

        h1 = QLabel("Choose Installation Location")
        h1.setObjectName("pageTitle")
        pl.addWidget(h1)

        desc = QLabel("Setup will install Nexus File Manager into the following folder. To install into a different folder, click Browse and select another location.")
        desc.setObjectName("pageText")
        desc.setWordWrap(True)
        pl.addWidget(desc)

        box = QFrame()
        box.setObjectName("cardFrame")
        bl = QHBoxLayout(box)
        bl.setContentsMargins(16, 12, 16, 12)
        bl.setSpacing(12)

        self.path_input = QLineEdit(str(self.install_dir))
        self.path_input.textChanged.connect(self._on_path_changed)
        bl.addWidget(self.path_input, 1)

        btn_browse = QPushButton("Browse…")
        btn_browse.clicked.connect(self._browse_location)
        bl.addWidget(btn_browse)
        pl.addWidget(box)

        # Space metrics
        self.space_label = QLabel()
        self.space_label.setObjectName("pageMuted")
        pl.addWidget(self.space_label)
        self._update_space_metric()

        pl.addStretch(1)
        self.stack.addWidget(page)

    def _browse_location(self):
        chosen = QFileDialog.getExistingDirectory(self, "Select Installation Folder", str(self.install_dir))
        if chosen:
            p = Path(chosen)
            if p.name.lower() != "nexusfilemanager":
                p = p / "NexusFileManager"
            self.install_dir = p
            self.path_input.setText(str(p))

    def _on_path_changed(self, text: str):
        if text.strip():
            self.install_dir = Path(text.strip())
            self._update_space_metric()

    def _update_space_metric(self):
        try:
            drive = self.install_dir.drive or "C:"
            usage = shutil.disk_usage(drive + "\\")
            free_str = format_bytes(usage.free)
            self.space_label.setText(f"Space required: ~85.0 MB   ·   Space available on drive {drive}: {free_str}")
        except Exception:
            self.space_label.setText("Space required: ~85.0 MB")

    # ── Page 3: Components ────────────────────────────────────────────────
    def _build_page3_components(self):
        page = QWidget()
        pl = QVBoxLayout(page)
        pl.setContentsMargins(36, 28, 36, 20)
        pl.setSpacing(14)

        h1 = QLabel("Select Features & Windows Integration")
        h1.setObjectName("pageTitle")
        pl.addWidget(h1)

        desc = QLabel("Choose which features and shortcuts you want to install on your computer:")
        desc.setObjectName("pageText")
        pl.addWidget(desc)

        card = QFrame()
        card.setObjectName("cardFrame")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(12)

        self.cb_core = QCheckBox("Core File Explorer & Deep Previews Engine (Required)")
        self.cb_core.setChecked(True)
        self.cb_core.setEnabled(False)
        cl.addWidget(self.cb_core)

        self.cb_desktop = QCheckBox("Create Desktop Shortcut")
        self.cb_desktop.setChecked(True)
        cl.addWidget(self.cb_desktop)

        self.cb_startmenu = QCheckBox("Create Start Menu Programs Shortcut")
        self.cb_startmenu.setChecked(True)
        cl.addWidget(self.cb_startmenu)

        self.cb_context = QCheckBox("Add 'Open in Nexus File Manager' to Windows Right-Click Folder Menu")
        self.cb_context.setChecked(True)
        cl.addWidget(self.cb_context)

        self.cb_assoc = QCheckBox("Associate .nxv files with Nexus Safe Locker (Encrypted Vaults)")
        self.cb_assoc.setChecked(True)
        cl.addWidget(self.cb_assoc)

        pl.addWidget(card)
        pl.addStretch(1)
        self.stack.addWidget(page)

    # ── Page 4: Progress ──────────────────────────────────────────────────
    def _build_page4_progress(self):
        page = QWidget()
        pl = QVBoxLayout(page)
        pl.setContentsMargins(36, 40, 36, 20)
        pl.setSpacing(18)

        h1 = QLabel("Installing Nexus File Manager…")
        h1.setObjectName("pageTitle")
        pl.addWidget(h1)

        self.status_msg = QLabel("Copying files to destination…")
        self.status_msg.setObjectName("pageText")
        pl.addWidget(self.status_msg)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(0)
        pl.addWidget(self.progress_bar)

        pl.addStretch(1)
        self.stack.addWidget(page)

    # ── Page 5: Finish ────────────────────────────────────────────────────
    def _build_page5_finish(self):
        page = QWidget()
        pl = QVBoxLayout(page)
        pl.setContentsMargins(36, 36, 36, 20)
        pl.setSpacing(16)

        h1 = QLabel("Nexus File Manager Installed Successfully!")
        h1.setObjectName("pageTitle")
        pl.addWidget(h1)

        desc = QLabel(
            "Nexus File Manager has been installed on your computer.\n\n"
            "You can launch it anytime from your Desktop, Start Menu, or by right-clicking any folder.\n"
            "Your settings, custom themes, and encrypted vaults will be preserved across updates."
        )
        desc.setObjectName("pageText")
        desc.setWordWrap(True)
        pl.addWidget(desc)

        pl.addSpacing(10)
        self.cb_launch_now = QCheckBox("Launch Nexus File Manager now")
        self.cb_launch_now.setChecked(True)
        pl.addWidget(self.cb_launch_now)

        self.cb_open_folder = QCheckBox("Open installation folder in Windows Explorer")
        self.cb_open_folder.setChecked(False)
        pl.addWidget(self.cb_open_folder)

        pl.addStretch(1)
        self.stack.addWidget(page)

    # ── Navigation Logic ──────────────────────────────────────────────────
    def _go_next(self):
        idx = self.stack.currentIndex()
        if idx == 0:
            self.stack.setCurrentIndex(1)
            self.btn_back.setEnabled(True)
        elif idx == 1:
            self.stack.setCurrentIndex(2)
            self.btn_next.setText("Install Now →")
        elif idx == 2:
            self._start_installation()
        elif idx == 4:
            self._on_finish()

    def _go_back(self):
        idx = self.stack.currentIndex()
        if idx == 1:
            self.stack.setCurrentIndex(0)
            self.btn_back.setEnabled(False)
        elif idx == 2:
            self.stack.setCurrentIndex(1)
            self.btn_next.setText("Next →")

    def _start_installation(self):
        self.stack.setCurrentIndex(3)
        self.btn_back.setEnabled(False)
        self.btn_next.setEnabled(False)
        self.btn_cancel.setEnabled(False)

        options = {
            "desktop_shortcut": self.cb_desktop.isChecked(),
            "start_menu_shortcut": self.cb_startmenu.isChecked(),
            "context_menu": self.cb_context.isChecked(),
            "file_assoc": self.cb_assoc.isChecked(),
        }

        self.worker = InstallWorker(self.source_dir, self.install_dir, options)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_installed)
        self.worker.start()

    def _on_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.status_msg.setText(msg)

    def _on_installed(self, success: bool, err_msg: str):
        if success:
            self.stack.setCurrentIndex(4)
            self.btn_next.setEnabled(True)
            self.btn_next.setText("Finish")
            self.btn_cancel.setVisible(False)
        else:
            self.status_msg.setText(f"Installation failed: {err_msg}")
            self.btn_cancel.setEnabled(True)

    def _on_finish(self):
        exe_path = self.install_dir / "NexusFileManager.exe"
        if self.cb_launch_now.isChecked() and exe_path.exists():
            subprocess.Popen([str(exe_path)], cwd=str(self.install_dir))
        if self.cb_open_folder.isChecked() and self.install_dir.exists():
            subprocess.Popen(["explorer.exe", str(self.install_dir)])
        self.close()

    # ── Styling ───────────────────────────────────────────────────────────
    def _apply_styles(self):
        qss = f"""
        QMainWindow {{
            background-color: {BG_BASE};
            color: {TEXT_PRIMARY};
        }}
        #head {{
            background-color: {BG_SURFACE};
            border-bottom: 1px solid {BORDER};
        }}
        #headTitle {{
            color: {TEXT_PRIMARY};
            font-size: 16px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}
        #headSubtitle {{
            color: {TEXT_SECONDARY};
            font-size: 12px;
        }}
        #versionBadge {{
            background-color: rgba(56, 189, 248, 0.15);
            color: {ACCENT_PRIMARY};
            font-weight: 600;
            font-size: 11px;
            padding: 4px 10px;
            border-radius: 6px;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }}
        #navBar {{
            background-color: {BG_SURFACE};
            border-top: 1px solid {BORDER};
        }}
        #pageTitle {{
            color: {TEXT_PRIMARY};
            font-size: 18px;
            font-weight: 600;
        }}
        #pageText {{
            color: {TEXT_SECONDARY};
            font-size: 13px;
            line-height: 1.5;
        }}
        #pageMuted {{
            color: {TEXT_MUTED};
            font-size: 12px;
        }}
        #cardFrame {{
            background-color: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: 8px;
        }}
        QPushButton {{
            background-color: {BG_CARD};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER};
            border-radius: 6px;
            padding: 8px 18px;
            font-size: 13px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: #334155;
            border-color: {BORDER_STRONG};
        }}
        QPushButton#btnPrimary {{
            background-color: {ACCENT_PRIMARY};
            color: #0F172A;
            border: 1px solid {ACCENT_PRIMARY};
            font-weight: 600;
        }}
        QPushButton#btnPrimary:hover {{
            background-color: {ACCENT_HOVER};
            border-color: {ACCENT_HOVER};
        }}
        QLineEdit {{
            background-color: {BG_BASE};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER};
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
        }}
        QLineEdit:focus {{
            border-color: {ACCENT_PRIMARY};
        }}
        QCheckBox {{
            color: {TEXT_PRIMARY};
            font-size: 13px;
            spacing: 10px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 1px solid {BORDER};
            background-color: {BG_BASE};
        }}
        QCheckBox::indicator:checked {{
            background-color: {ACCENT_PRIMARY};
            border-color: {ACCENT_PRIMARY};
            image: none;
        }}
        QProgressBar {{
            background-color: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: 6px;
        }}
        QProgressBar::chunk {{
            background-color: {ACCENT_PRIMARY};
            border-radius: 5px;
        }}
        """
        self.setStyleSheet(qss)


def main():
    app = QApplication(sys.argv[:1])
    app.setApplicationName("Nexus File Manager Setup")

    # Locate the application distribution to install
    # When packaged with PyInstaller, sys._MEIPASS holds bundled data
    base_dir = getattr(sys, "_MEIPASS", None)
    if base_dir:
        dist_dir = Path(base_dir) / "app"
    else:
        root_dir = Path(__file__).resolve().parent.parent
        dist_dir = root_dir / "dist" / "NexusFileManager"

    if not dist_dir.exists():
        print(f"Error: Application distribution directory not found at {dist_dir}")
        sys.exit(1)

    wizard = SetupWizard(dist_dir)
    wizard.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

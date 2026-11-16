"""Encrypted Safe Locker Dialog: AES-256-GCM vault management."""

from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QFileDialog, QMessageBox, QTabWidget, QWidget, QCheckBox
)
from PyQt6.QtCore import Qt
import qtawesome as qta
import send2trash

from src.modules.crypto_vault import encrypt_file, decrypt_file, is_vault_file


class VaultDialog(QDialog):
    """Encrypted Vault management modal: encrypt or decrypt files with AES-256-GCM."""

    def __init__(self, preselected_files: Optional[List[Path]] = None, current_dir: Optional[Path] = None, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.preselected_files = preselected_files or []
        self.current_dir = current_dir or Path.home()

        self.setWindowTitle("Nexus Encrypted Vault (AES-256-GCM)")
        self.resize(520, 360)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        icon = QLabel(self)
        icon.setPixmap(qta.icon("fa5s.shield-alt", color="#eab308").pixmap(32, 32))
        header.addWidget(icon)

        title_box = QVBoxLayout()
        title = QLabel("Encrypted Safe Locker", self)
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #FFFFFF;")
        subtitle = QLabel("Zero-knowledge AES-256-GCM authenticated encryption", self)
        subtitle.setStyleSheet("color: #94A3B8; font-size: 12px;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()

        layout.addLayout(header)

        # Tabs: Lock (Encrypt) vs Unlock (Decrypt)
        self.tabs = QTabWidget(self)

        # Tab 1: Encrypt
        tab_encrypt = QWidget()
        enc_layout = QVBoxLayout(tab_encrypt)
        enc_layout.setSpacing(10)

        enc_layout.addWidget(QLabel("Files to Encrypt:"))
        self.lbl_enc_files = QLabel(
            f"{len(self.preselected_files)} files selected" if self.preselected_files else "No files selected",
            self,
        )
        self.lbl_enc_files.setStyleSheet("color: #38bdf8; font-weight: 500;")
        enc_layout.addWidget(self.lbl_enc_files)

        self.btn_choose_files = QPushButton("Choose File...", self)
        self.btn_choose_files.clicked.connect(self._choose_files_to_encrypt)
        enc_layout.addWidget(self.btn_choose_files)

        enc_layout.addWidget(QLabel("Master Password:"))
        self.pwd_enc = QLineEdit(self)
        self.pwd_enc.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_enc.setPlaceholderText("Enter a strong passphrase")
        enc_layout.addWidget(self.pwd_enc)

        self.chk_trash_orig = QCheckBox("Move original unencrypted file(s) to Recycle Bin after locking", self)
        self.chk_trash_orig.setChecked(True)
        enc_layout.addWidget(self.chk_trash_orig)

        self.btn_do_encrypt = QPushButton("Lock & Encrypt", self)
        self.btn_do_encrypt.setIcon(qta.icon("fa5s.lock", color="#22c55e"))
        self.btn_do_encrypt.clicked.connect(self._run_encrypt)
        enc_layout.addWidget(self.btn_do_encrypt)
        enc_layout.addStretch()

        self.tabs.addTab(tab_encrypt, "Lock (Encrypt)")

        # Tab 2: Decrypt
        tab_decrypt = QWidget()
        dec_layout = QVBoxLayout(tab_decrypt)
        dec_layout.setSpacing(10)

        dec_layout.addWidget(QLabel("Select .vault File:"))
        self.vault_file_edit = QLineEdit(self)
        self.vault_file_edit.setPlaceholderText("Path to .vault file")
        dec_layout.addWidget(self.vault_file_edit)

        self.btn_choose_vault = QPushButton("Browse .vault...", self)
        self.btn_choose_vault.clicked.connect(self._choose_vault_file)
        dec_layout.addWidget(self.btn_choose_vault)

        dec_layout.addWidget(QLabel("Master Password:"))
        self.pwd_dec = QLineEdit(self)
        self.pwd_dec.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_dec.setPlaceholderText("Enter the decryption password")
        dec_layout.addWidget(self.pwd_dec)

        self.btn_do_decrypt = QPushButton("Unlock & Decrypt", self)
        self.btn_do_decrypt.setIcon(qta.icon("fa5s.unlock", color="#38bdf8"))
        self.btn_do_decrypt.clicked.connect(self._run_decrypt)
        dec_layout.addWidget(self.btn_do_decrypt)
        dec_layout.addStretch()

        self.tabs.addTab(tab_decrypt, "Unlock (Decrypt)")

        layout.addWidget(self.tabs)

        # If user opened dialog on a .vault file, switch directly to Unlock tab
        if self.preselected_files and is_vault_file(self.preselected_files[0]):
            self.vault_file_edit.setText(str(self.preselected_files[0]))
            self.tabs.setCurrentIndex(1)

    def _choose_files_to_encrypt(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files to Lock", str(self.current_dir))
        if files:
            self.preselected_files = [Path(f) for f in files]
            self.lbl_enc_files.setText(f"{len(self.preselected_files)} files selected")

    def _choose_vault_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select Vault File", str(self.current_dir), "Nexus Vault Files (*.vault)"
        )
        if file:
            self.vault_file_edit.setText(file)

    def _run_encrypt(self):
        if not self.preselected_files:
            QMessageBox.warning(self, "Error", "Please select at least one file to encrypt.")
            return

        password = self.pwd_enc.text()
        if len(password) < 4:
            QMessageBox.warning(self, "Password Too Short", "Please enter a passphrase of at least 4 characters.")
            return

        success = 0
        for src in self.preselected_files:
            if not src.is_file():
                continue
            dest_vault = src.parent / f"{src.name}.vault"
            try:
                encrypt_file(src, dest_vault, password)
                if self.chk_trash_orig.isChecked():
                    send2trash.send2trash(str(src))
                success += 1
            except Exception as e:
                QMessageBox.critical(self, "Encryption Failed", f"Failed to encrypt {src.name}: {e}")
                return

        QMessageBox.information(
            self, "Success", f"Successfully encrypted {success} file(s) into AES-256 vault container(s)!"
        )
        self.accept()

    def _run_decrypt(self):
        vault_str = self.vault_file_edit.text().strip()
        if not vault_str:
            QMessageBox.warning(self, "Error", "Please specify a .vault file.")
            return

        vault_path = Path(vault_str)
        if not vault_path.exists():
            QMessageBox.warning(self, "Error", f"File '{vault_path}' does not exist.")
            return

        password = self.pwd_dec.text()
        if not password:
            QMessageBox.warning(self, "Password Required", "Please enter the vault password.")
            return

        out_dir = vault_path.parent
        try:
            decrypted = decrypt_file(vault_path, out_dir, password)
            QMessageBox.information(
                self, "Vault Unlocked", f"Decryption successful!\nFile restored to: {decrypted.name}"
            )
            self.accept()
        except ValueError as ve:
            QMessageBox.critical(
                self,
                "Authentication Failed",
                "Decryption failed: Incorrect password or the vault file has been corrupted/tampered with.",
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {e}")

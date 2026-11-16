"""Comprehensive unit test suite for all Nexus File Manager core & specialized modules."""

import unittest
import tempfile
import shutil
from pathlib import Path

from src.core.fs_operations import (
    create_new_folder,
    create_new_file,
    rename_item,
)
from src.modules.storage_analyzer import (
    TreemapNode,
    calculate_squarified_treemap,
)
from src.modules.duplicate_finder import (
    get_partial_hash,
    get_full_hash,
)
from src.modules.crypto_vault import (
    encrypt_file,
    decrypt_file,
    is_vault_file,
)
from src.modules.ai_organizer import AIOrganizerWorker
from src.modules.semantic_search import tokenize


class TestFileManagerCore(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="nexus_test_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_create_and_rename_file(self):
        # 1. Create file
        f = create_new_file(self.test_dir, "notes.txt")
        self.assertTrue(f.exists())
        self.assertEqual(f.name, "notes.txt")

        # 2. Collision avoidance
        f2 = create_new_file(self.test_dir, "notes.txt")
        self.assertTrue(f2.exists())
        self.assertEqual(f2.name, "notes (1).txt")

        # 3. Rename
        renamed = rename_item(f, "renamed_notes.txt")
        self.assertTrue(renamed.exists())
        self.assertFalse(f.exists())

    def test_create_folder(self):
        folder = create_new_folder(self.test_dir, "Projects")
        self.assertTrue(folder.is_dir())
        folder2 = create_new_folder(self.test_dir, "Projects")
        self.assertEqual(folder2.name, "Projects (1)")

    def test_duplicate_hashing(self):
        # Create two identical files and one different file
        content_a = b"Nexus File Manager Hashing Test Data" * 500
        content_b = b"Different Content Completely"

        f1 = self.test_dir / "file1.bin"
        f2 = self.test_dir / "file2.bin"
        f3 = self.test_dir / "file3.bin"

        f1.write_bytes(content_a)
        f2.write_bytes(content_a)
        f3.write_bytes(content_b)

        # Partial hash matches for f1 and f2
        self.assertEqual(get_partial_hash(f1), get_partial_hash(f2))
        # Full hash matches for f1 and f2
        self.assertEqual(get_full_hash(f1), get_full_hash(f2))
        # Differs from f3
        self.assertNotEqual(get_full_hash(f1), get_full_hash(f3))

    def test_crypto_vault_aes_gcm(self):
        secret_file = self.test_dir / "sensitive_passwords.txt"
        secret_file.write_text("Secret: MyCryptoKey123!", encoding="utf-8")

        vault_file = self.test_dir / "safe.vault"
        password = "MasterPasswordSecure!42"

        # Encrypt
        encrypt_file(secret_file, vault_file, password)
        self.assertTrue(vault_file.exists())
        self.assertTrue(is_vault_file(vault_file))

        # Ensure ciphertext is not readable as plaintext
        cipher_bytes = vault_file.read_bytes()
        self.assertNotIn(b"Secret: MyCryptoKey123!", cipher_bytes)

        # Decrypt with correct password
        decrypted_dir = self.test_dir / "decrypted"
        decrypted_dir.mkdir()
        decrypted_file = decrypt_file(vault_file, decrypted_dir, password)
        self.assertTrue(decrypted_file.exists())
        self.assertEqual(decrypted_file.read_text(encoding="utf-8"), "Secret: MyCryptoKey123!")

        # Decrypt with wrong password must fail
        with self.assertRaises(ValueError):
            decrypt_file(vault_file, decrypted_dir, "WrongPassword!")

    def test_squarified_treemap_algorithm(self):
        nodes = [
            TreemapNode("BigFile.iso", Path("/dummy/1"), False, size=5000),
            TreemapNode("Medium.zip", Path("/dummy/2"), False, size=3000),
            TreemapNode("Small.txt", Path("/dummy/3"), False, size=2000),
        ]
        calculate_squarified_treemap(nodes, x=0, y=0, w=800, h=600)

        # Check that all nodes received non-zero bounding rects
        for node in nodes:
            x, y, w, h = node.rect
            self.assertGreater(w, 0)
            self.assertGreater(h, 0)
            self.assertLessEqual(x + w, 800.01)
            self.assertLessEqual(y + h, 600.01)

    def test_text_tokenization(self):
        text = "Nexus File Manager with AI-powered TF-IDF search!"
        tokens = tokenize(text)
        self.assertIn("nexus", tokens)
        self.assertIn("file", tokens)
        self.assertIn("manager", tokens)
        self.assertIn("search", tokens)


if __name__ == "__main__":
    unittest.main()

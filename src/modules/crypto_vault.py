"""Secure Encrypted Vault: AES-256-GCM authenticated encryption for sensitive files."""

import os
from pathlib import Path
from typing import Tuple
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

VAULT_MAGIC = b"NEXV"  # Nexus Vault Header Magic Bytes
SALT_SIZE = 16
NONCE_SIZE = 12
PBKDF2_ITERATIONS = 100_000


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit AES key from a passphrase using PBKDF2-HMAC-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 256 bits
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_file(source_file: Path, destination_vault: Path, password: str) -> None:
    """
    Encrypt a source file into a secure .vault file using AES-256-GCM.
    Binary layout: [MAGIC: 4B][SALT: 16B][NONCE: 12B][CIPHERTEXT + TAG]
    """
    if not source_file.is_file():
        raise FileNotFoundError(f"Source file {source_file} not found.")

    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(password, salt)

    with open(source_file, "rb") as f:
        plaintext = f.read()

    aesgcm = AESGCM(key)
    # Store original filename as Associated Data (AAD) for integrity checking
    aad = source_file.name.encode("utf-8")
    ciphertext = aesgcm.encrypt(nonce, plaintext, aad)

    with open(destination_vault, "wb") as f:
        f.write(VAULT_MAGIC)
        f.write(salt)
        f.write(nonce)
        # Write AAD length and AAD
        f.write(len(aad).to_bytes(2, byteorder="big"))
        f.write(aad)
        f.write(ciphertext)


def decrypt_file(vault_file: Path, output_directory: Path, password: str) -> Path:
    """
    Decrypt a .vault file back to its original file.
    Validates integrity tag; fails if password is incorrect or file is tampered with.
    """
    if not vault_file.is_file():
        raise FileNotFoundError(f"Vault file {vault_file} not found.")

    with open(vault_file, "rb") as f:
        magic = f.read(4)
        if magic != VAULT_MAGIC:
            raise ValueError("Invalid vault file: Missing NEXV magic header.")

        salt = f.read(SALT_SIZE)
        nonce = f.read(NONCE_SIZE)
        aad_len = int.from_bytes(f.read(2), byteorder="big")
        aad = f.read(aad_len)
        ciphertext = f.read()

    key = derive_key(password, salt)
    aesgcm = AESGCM(key)

    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, aad)
    except Exception as e:
        raise ValueError("Decryption failed: Incorrect password or corrupted/tampered file.") from e

    original_filename = aad.decode("utf-8", errors="replace")
    output_path = output_directory / original_filename

    # Avoid overwriting existing file
    counter = 1
    base_stem = output_path.stem
    ext = output_path.suffix
    while output_path.exists():
        output_path = output_directory / f"{base_stem}_decrypted_{counter}{ext}"
        counter += 1

    with open(output_path, "wb") as f:
        f.write(plaintext)

    return output_path


def is_vault_file(path: Path) -> bool:
    """Check if file starts with NEXV header."""
    if not path.is_file() or path.stat().st_size < 34:
        return False
    try:
        with open(path, "rb") as f:
            return f.read(4) == VAULT_MAGIC
    except Exception:
        return False

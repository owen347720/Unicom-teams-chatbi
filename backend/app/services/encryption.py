# backend/app/services/encryption.py

import base64
import hashlib

from cryptography.fernet import Fernet

from app.config import settings


def _get_fernet() -> Fernet:
    """
    Derive Fernet key from configured encryption_key.
    Uses SHA256 to produce 32 bytes, then base64-encodes for Fernet.
    """
    key = base64.urlsafe_b64encode(
        hashlib.sha256(settings.encryption_key.encode("utf-8")).digest()
    )
    return Fernet(key)


def encrypt(password: str) -> str:
    """
    Encrypt a password.

    Args:
        password: plaintext password

    Returns:
        encrypted string
    """
    return _get_fernet().encrypt(password.encode("utf-8")).decode("utf-8")


def decrypt(encrypted: str) -> str:
    """
    Decrypt a password.

    Args:
        encrypted: encrypted string

    Returns:
        plaintext password
    """
    return _get_fernet().decrypt(encrypted.encode("utf-8")).decode("utf-8")

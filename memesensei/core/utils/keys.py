from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


WARNING_BANNER = (
    "BASE58_SECRET loaded from env. DEVELOPMENT ONLY. Do not use in production."
)


@dataclass
class KeyLoaderResult:
    secret: str
    warning: Optional[str] = None


def _load_encrypted_key(path: str, passphrase: str) -> str:
    key_bytes = base64.urlsafe_b64encode(passphrase.encode().ljust(32)[:32])
    cipher = Fernet(key_bytes)
    encrypted = Path(path).read_bytes()
    try:
        decrypted = cipher.decrypt(encrypted)
    except InvalidToken as exc:
        raise ValueError("Invalid key passphrase") from exc
    payload = json.loads(decrypted.decode())
    if "secret" not in payload:
        raise ValueError("Missing secret in encrypted key file")
    return payload["secret"]


def load_private_key(encrypted_path: Optional[str], passphrase_env: Optional[str], base58_fallback: Optional[str]) -> KeyLoaderResult:
    if encrypted_path and passphrase_env:
        passphrase = os.getenv(passphrase_env)
        if not passphrase:
            raise ValueError("Passphrase env var not set")
        return KeyLoaderResult(secret=_load_encrypted_key(encrypted_path, passphrase))
    if base58_fallback:
        return KeyLoaderResult(secret=base58_fallback, warning=WARNING_BANNER)
    raise ValueError("No key configuration provided")

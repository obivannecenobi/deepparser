"""API key storage with Windows DPAPI encryption."""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "SETTINGS.json"

if sys.platform == "win32":
    import win32crypt


def _encrypt(text: str) -> str:
    if sys.platform == "win32":
        blob = win32crypt.CryptProtectData(text.encode("utf-8"), None, None, None, None, 0)[1]
        return base64.b64encode(blob).decode("utf-8")
    return text


def _decrypt(text: str) -> str:
    if sys.platform == "win32" and text:
        data = base64.b64decode(text)
        blob = win32crypt.CryptUnprotectData(data, None, None, None, 0)[1]
        return blob.decode("utf-8")
    return text


def store_api_key(provider: str, key: str) -> None:
    """Encrypt and store API key for provider."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}
    data.setdefault("api", {})[f"{provider}_API_KEY"] = _encrypt(key)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_api_key(provider: str) -> str:
    """Retrieve decrypted API key for provider."""
    if not CONFIG_PATH.exists():
        return ""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    enc = data.get("api", {}).get(f"{provider}_API_KEY", "")
    return _decrypt(enc) if enc else ""

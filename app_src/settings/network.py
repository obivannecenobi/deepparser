"""Proxy configuration utilities."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import requests

CONFIG_PATH = Path(__file__).resolve().parent.parent / "SETTINGS.json"


@dataclass
class ProxySettings:
    """Container for proxy addresses."""

    http: str = ""
    https: str = ""

    def as_dict(self) -> Dict[str, str]:
        proxies: Dict[str, str] = {}
        if self.http:
            proxies["http"] = self.http
        if self.https:
            proxies["https"] = self.https
        return proxies

    def apply(self) -> None:
        """Apply the proxy settings to environment variables."""
        if self.http:
            os.environ["HTTP_PROXY"] = self.http
            os.environ["http_proxy"] = self.http
        if self.https:
            os.environ["HTTPS_PROXY"] = self.https
            os.environ["https_proxy"] = self.https


def load_proxy_settings() -> ProxySettings:
    """Load proxy settings from configuration file."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        net = data.get("network", {})
        return ProxySettings(net.get("http_proxy", ""), net.get("https_proxy", ""))
    return ProxySettings()


def save_proxy_settings(settings: ProxySettings) -> None:
    """Persist proxy settings into configuration file."""
    data = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    data.setdefault("network", {})
    data["network"]["http_proxy"] = settings.http
    data["network"]["https_proxy"] = settings.https
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def test_proxy_connection(settings: ProxySettings, url: str = "https://www.google.com", timeout: int = 5) -> bool:
    """Check whether the provided proxy settings can reach a URL."""
    proxies = settings.as_dict()
    if not proxies:
        return True
    try:
        requests.get(url, proxies=proxies, timeout=timeout)
        return True
    except Exception:
        return False

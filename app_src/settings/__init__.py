"""Settings utilities for DeepParser."""

from .network import (
    ProxySettings,
    load_proxy_settings,
    save_proxy_settings,
    test_proxy_connection,
)
from .credentials import load_api_key, store_api_key

__all__ = [
    'ProxySettings',
    'load_proxy_settings',
    'save_proxy_settings',
    'test_proxy_connection',
    'load_api_key',
    'store_api_key',
]

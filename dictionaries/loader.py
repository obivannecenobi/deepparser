from __future__ import annotations
import json
from pathlib import Path
from time import sleep
from typing import Callable, List
import requests

DICT_FILE = Path(__file__).with_name("synonyms.json")

# A small built-in dictionary to demonstrate loading
BUILTIN = {
    "быстрый": ["скорый", "проворный", "оперативный"],
    "красивый": ["прекрасный", "симпатичный", "привлекательный"],
    "дом": ["жилище", "строение", "хата"],
}

def load_dictionary(progress: Callable[[int], None] | None = None) -> Path:
    """Load dictionary data to DICT_FILE with progress callback."""
    total = len(BUILTIN)
    data = {}
    for i, (w, syns) in enumerate(BUILTIN.items(), start=1):
        data[w] = syns
        sleep(0.1)
        if progress:
            progress(int(i / total * 100))
    with open(DICT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    if progress:
        progress(100)
    return DICT_FILE

def get_synonyms(word: str) -> List[str]:
    """Return synonyms for a word using local dictionary or Datamuse API."""
    word = word.lower()
    if DICT_FILE.exists():
        try:
            with open(DICT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if word in data:
                return data[word]
        except Exception:
            pass
    try:
        resp = requests.get(f"https://api.datamuse.com/words?ml={word}", timeout=5)
        if resp.ok:
            return [item["word"] for item in resp.json()[:5]]
    except Exception:
        pass
    return []

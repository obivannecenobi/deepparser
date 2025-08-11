from .base import Translator
from .gemini import GeminiTranslator
from .gpt5 import GPT5Translator
from .claude import ClaudeTranslator
from .grok import GrokTranslator

TRANSLATORS = {
    "gemini": GeminiTranslator,
    "gpt5": GPT5Translator,
    "claude": ClaudeTranslator,
    "grok": GrokTranslator,
}

def create_translator(name: str, api_key: str | None = None, **kwargs) -> Translator:
    cls = TRANSLATORS.get(name.lower())
    if not cls:
        raise ValueError(f"Unknown translator: {name}")
    return cls(api_key=api_key, **kwargs)

__all__ = [
    "Translator",
    "GeminiTranslator",
    "GPT5Translator",
    "ClaudeTranslator",
    "GrokTranslator",
    "create_translator",
]

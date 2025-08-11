class ContextBuilder:
    def build(self, original: str, miniprompt: str) -> str:
        """Build translation text from original and mini prompt.

        This is a simple placeholder implementation that concatenates the
        original text with the mini prompt. In real application it would
        prepare rich context for an MT model.
        """
        original = original.strip()
        prompt = miniprompt.strip()
        if prompt:
            return f"{original}\n\n[{prompt}]"
        return original

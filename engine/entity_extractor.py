"""Entity extraction for interest radar.

Goal: pull out meaningful tokens for recall queries.
Avoid super common noise words.
"""

import re
from typing import List, Set


class EntityExtractor:
    """Extract salient tokens from content."""

    # Stop words that are too generic
    STOP_WORDS = {
        "release", "released", "update", "support", "supports", "fixed", "changed",
        "github", "agent", "model", "models", "local", "system", "memory",
        "context", "the", "and", "with", "from", "this", "that", "version",
        "what", "full", "changelog", "new", "open", "use", "using", "launch",
        "install", "build", "run", "cli", "api", "doc", "docs", "readme",
        "code", "commit", "branch", "master", "main", "pull", "push",
    }

    # Preserve specific technical phrases that regex tokenization would break
    PHRASES = [
        "ollama", "llama.cpp", "reasoning_content", "deepseek", "hermes",
        "openxr", "android xr", "vision pro", "mlx", "gguf", "opencode",
        "rtk", "hindsight", "mem0", "honcho", "supermemory",
    ]

    def extract(self, title: str, summary: str, url: str) -> List[str]:
        text = f"{title} {summary} {url}".lower()
        tokens: Set[str] = set()

        # Preserve known phrases first
        for ph in self.PHRASES:
            if ph in text:
                tokens.add(ph)

        # Tokenize: alphanumeric with len >= 3, skip stop words
        for tok in re.findall(r"[a-zA-Z][a-zA-Z0-9_.+-]{3,}", text):
            if tok not in self.STOP_WORDS and not tok.startswith("http"):
                tokens.add(tok)

        return sorted(tokens)[:25]  # cap to keep query small

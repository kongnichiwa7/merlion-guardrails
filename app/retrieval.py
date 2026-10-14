"""BM25 keyword retrieval over the document store. No API calls."""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List

from rank_bm25 import BM25Okapi

DOCS_DIR = Path(__file__).resolve().parent.parent / "data" / "docs"
TOP_K = 3


@dataclass(frozen=True)
class Chunk:
    source: str  # file name, e.g. "atm.md"
    title: str   # page title + section heading
    text: str


def _tokens(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def load_chunks(docs_dir: Path = DOCS_DIR) -> List[Chunk]:
    """One chunk per `##` section; the page title is prefixed to each."""
    chunks = []
    for path in sorted(docs_dir.glob("*.md")):
        raw = path.read_text()
        title_match = re.match(r"#\s+(.+)", raw)
        page_title = title_match.group(1).strip() if title_match else path.stem
        sections = re.split(r"\n(?=## )", raw)
        for section in sections[1:] if len(sections) > 1 else sections:
            heading = section.splitlines()[0].lstrip("# ").strip()
            chunks.append(Chunk(path.name, f"{page_title} - {heading}", section.strip()))
    return chunks


class Retriever:
    def __init__(self, chunks: List[Chunk]):
        self.chunks = chunks
        self._bm25 = BM25Okapi([_tokens(c.title + " " + c.text) for c in chunks])

    def search(self, query: str, k: int = TOP_K) -> List[Chunk]:
        scores = self._bm25.get_scores(_tokens(query))
        ranked = sorted(range(len(self.chunks)), key=lambda i: scores[i], reverse=True)
        return [self.chunks[i] for i in ranked[:k] if scores[i] > 0]


@lru_cache(maxsize=1)
def default_retriever() -> Retriever:
    return Retriever(load_chunks())

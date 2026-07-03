"""Stage 2: Text chunking (DDD 6 Stage 2).

Uses LangChain RecursiveCharacterTextSplitter: 500-char chunks, 100-char overlap.
Each chunk is tagged with a heuristically-detected resume section. Fragments
below 50 chars are merged into the previous chunk.
"""
from __future__ import annotations

import logging
import re
from typing import Dict, List

from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
MIN_CHUNK_SIZE = 50
SEPARATORS = ["\n\n", "\n", ". ", " "]

# Section header heuristics -> normalized section label.
SECTION_PATTERNS = [
    ("experience", re.compile(r"(?i)\b(work\s+experience|professional\s+experience|experience|employment)\b")),
    ("education", re.compile(r"(?i)\b(education|academic|qualifications)\b")),
    ("skills", re.compile(r"(?i)\b(technical\s+skills|skills|competenc(?:y|ies)|technologies)\b")),
    ("projects", re.compile(r"(?i)\b(projects|portfolio|key\s+projects)\b")),
]


def _detect_section(text: str, carry: str) -> str:
    """Return the section for a chunk, carrying forward the previous section."""
    head = text[:120]
    for label, pattern in SECTION_PATTERNS:
        if pattern.search(head):
            return label
    return carry


def chunk_text(raw_text: str) -> List[Dict]:
    """Split raw resume text into tagged chunks.

    Returns a list of { text, index, section }.
    """
    if not raw_text or not raw_text.strip():
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=SEPARATORS,
        length_function=len,
    )
    raw_chunks = splitter.split_text(raw_text)

    # Merge undersized fragments into the previous chunk.
    merged: List[str] = []
    for piece in raw_chunks:
        piece = piece.strip()
        if not piece:
            continue
        if merged and len(piece) < MIN_CHUNK_SIZE:
            merged[-1] = (merged[-1] + " " + piece).strip()
        else:
            merged.append(piece)

    chunks: List[Dict] = []
    carry_section = "other"
    for idx, text in enumerate(merged):
        carry_section = _detect_section(text, carry_section)
        chunks.append({"text": text, "index": idx, "section": carry_section})

    logger.info("Chunked resume into %d chunks", len(chunks))
    return chunks

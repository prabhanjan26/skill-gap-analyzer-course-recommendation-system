"""Stage 6: RAG context assembly (DDD 6 Stage 6).

Builds the numbered-chunk context and role-requirements JSON that feed the
skill-extraction LLM prompt. Truncates to a rough token budget (~3000 tokens).
"""
from __future__ import annotations

import json
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

# ~4 chars per token heuristic; 3000 tokens => ~12000 chars context budget.
MAX_CONTEXT_CHARS = 12000


def build_skill_extraction_context(
    retrieved_chunks: List[Dict], role_skills: List[Dict]
) -> Dict[str, str]:
    """Assemble context for the extraction prompt.

    Returns { context_text, role_requirements }.
    - context_text: numbered chunks "[1] ...\n[2] ...".
    - role_requirements: JSON string of the role's skills (name, level, category).
    """
    numbered: List[str] = []
    running = 0
    for i, chunk in enumerate(retrieved_chunks, start=1):
        text = (chunk.get("text") or "").strip()
        if not text:
            continue
        entry = f"[{i}] {text}"
        if running + len(entry) > MAX_CONTEXT_CHARS:
            # Truncate this chunk to fit remaining budget, then stop.
            remaining = max(0, MAX_CONTEXT_CHARS - running)
            if remaining > 40:
                numbered.append(entry[:remaining])
            logger.info("RAG context truncated at chunk %d (budget reached)", i)
            break
        numbered.append(entry)
        running += len(entry) + 1

    context_text = "\n".join(numbered) if numbered else "(no relevant resume content retrieved)"

    role_requirements = json.dumps(
        [
            {
                "skill_name": s["skill_name"],
                "required_level": s["required_level"],
                "category": s["category"],
            }
            for s in role_skills
        ],
        indent=2,
    )

    return {"context_text": context_text, "role_requirements": role_requirements}

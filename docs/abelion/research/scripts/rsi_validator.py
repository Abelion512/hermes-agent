"""Validate lesson candidates before RSI injection.

Applies criteria:
1. Minimum length >= 20 chars
2. Either: cause-effect statement mentioning a tool, OR heuristic format (trigger: action)
3. Not a duplicate of existing lessons
4. No contradiction with existing lessons
"""

import json
import re
from typing import Any, Callable

# ── Criteria patterns ─────────────────────────────────────────────────

CAUSE_EFFECT_PATTERNS = [
    r"\bcauses?\b", r"\bleads?\s+to\b", r"\bresults?\s+in\b",
    r"\bbecause\b", r"\btherefore\b", r"\bif\b.*\bthen\b",
    r"\bwhen\b.*\bthen\b", r"\bprevents?\b", r"\bavoids?\b", r"\bfixes?\b",
]

HERMES_TOOLS = [
    "read_file", "write_file", "edit", "patch",
    "search_files", "grep", "glob",
    "terminal", "bash", "shell",
    "web_search", "web_extract", "web_fetch",
    "browser_navigate", "browser_click", "browser_type",
    "delegate_task", "clarify",
    "vision_analyze",
]

CONTRADICTION_PAIRS = [
    (r"avoid\s+using\b", r"use\b.*\binstead\b"),
    (r"do\s+not\s+use\b", r"recommend\s+using\b"),
    (r"never\s+use\b", r"always\s+use\b"),
    (r"should\s+not\b", r"should\s+always\b"),
]


def _has_cause_effect(text: str) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in CAUSE_EFFECT_PATTERNS)


def _mentions_tool(text: str) -> bool:
    pat = r"\b(" + "|".join(re.escape(t) for t in HERMES_TOOLS) + r")\b"
    return bool(re.search(pat, text, re.IGNORECASE))


# ── Duplicate check ───────────────────────────────────────────────────

def _jaccard_similarity(a: str, b: str) -> float:
    wa = set(a.lower().split())
    wb = set(b.lower().split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def _is_duplicate(content: str, existing: str, threshold: float = 0.6) -> bool:
    return _jaccard_similarity(content, existing) > threshold


# ── Conflict detection ────────────────────────────────────────────────

def _is_contradictory(a: str, b: str) -> tuple[bool, str]:
    """Check if two lessons contradict each other."""
    a_low = a.lower()
    b_low = b.lower()
    for neg_pat, pos_pat in CONTRADICTION_PAIRS:
        has_neg_a = bool(re.search(neg_pat, a_low))
        has_pos_a = bool(re.search(pos_pat, a_low))
        has_neg_b = bool(re.search(neg_pat, b_low))
        has_pos_b = bool(re.search(pos_pat, b_low))
        if (has_neg_a and has_pos_b) or (has_pos_a and has_neg_b):
            return True, f"Contradiction: '{neg_pat}' vs '{pos_pat}'"
    neg_tools = re.findall(r"(?:avoid|don't|never)\s+(?:use\s+)?(\w+)", a_low)
    pos_tools = re.findall(r"(?:use|recommend|prefer)\s+(?:using\s+)?(\w+)", b_low)
    for t in neg_tools:
        if t in b_low and re.search(r"use\b.*" + re.escape(t), b_low):
            return True, f"Contradiction: avoid {t} vs use {t}"
    return False, ""


# ── Main validation ───────────────────────────────────────────────────

def meets_criteria(
    content: str,
    existing: list[str],
    min_length: int = 20,
) -> tuple[bool, str | None]:
    """Check lesson against criteria. Returns (valid, reason)."""
    if len(content) < min_length:
        return False, f"Too short ({len(content)}<{min_length})"

    # Heuristic format (trigger: action) — always valid
    if ":" in content and len(content) > 40:
        trigger, action = content.split(":", 1)
        if len(trigger.strip()) > 3 and len(action.strip()) > 20:
            pass  # heuristic format passes
        else:
            if not _has_cause_effect(content) and not _mentions_tool(content):
                return False, "Not a valid heuristic or cause-effect lesson"
    else:
        # Cause-effect + tool mention
        if not _has_cause_effect(content):
            return False, "Missing cause-effect statement"
        if not _mentions_tool(content):
            return False, "No tool mentioned"

    for existing_content in existing:
        if _is_duplicate(content, existing_content):
            return False, f"Duplicate (Jaccard>{0.6})"
        conflict, reason = _is_contradictory(content, existing_content)
        if conflict:
            return False, reason

    return True, None


def validate_lesson(
    lesson: dict[str, Any],
    existing_lessons: list[dict[str, Any]],
) -> dict[str, Any]:
    """Validate a single lesson candidate against all criteria.

    Args:
        lesson: dict with 'content' key (and optionally source_tool, confidence)
        existing_lessons: list of previously validated lesson dicts

    Returns:
        dict with 'is_valid' (bool), 'reason' (str or None),
        and 'adjusted_confidence' (float)
    """
    content = lesson.get("content", "")
    existing_contents = [l.get("content", "") for l in existing_lessons]

    is_valid, reason = meets_criteria(content, existing_contents)

    # Auto-confidence adjust
    base_conf = lesson.get("confidence", 0.6)
    if not is_valid:
        base_conf *= 0.5
    elif len(content) > 200:
        base_conf = min(1.0, base_conf + 0.1)

    return {
        "is_valid": is_valid,
        "reason": reason,
        "adjusted_confidence": round(base_conf, 3),
    }


def validate_and_store(
    candidate: dict,
    store: Any = None,
    store_callback: Callable[[dict], str] | None = None,
) -> dict:
    """Validate a candidate and store it via callback if valid.

    Args:
        candidate: Lesson dict with 'content', 'source_tool', 'confidence'
        store: Object with get_all_active() and store_lesson() methods (optional)
        store_callback: Function that takes lesson dict and returns lesson_id

    Returns:
        dict with 'stored' (bool), 'reason', 'lesson_id', 'confidence'
    """
    active = store.get_all_active() if store and hasattr(store, 'get_all_active') else []
    existing = [l.get("action_body", l.get("content", "")) for l in active]

    verdict = validate_lesson(candidate, [{"content": e} for e in existing])
    if not verdict["is_valid"]:
        return {"stored": False, "reason": verdict["reason"], "lesson_id": None}

    lesson_data = {
        "action_body": candidate.get("content", ""),
        "confidence": verdict["adjusted_confidence"],
        "source_trace_id": candidate.get("source_tool", ""),
        "trigger_type": "error",
        "trigger_value": candidate.get("source_tool", "unknown"),
        "tags": json.dumps(["rsi_exp", candidate.get("source_tool", "")]),
        "status": "active",
    }

    if store_callback:
        lesson_id = store_callback(lesson_data)
    elif store and hasattr(store, 'store_lesson'):
        lesson_id = store.store_lesson(lesson_data)
    else:
        lesson_id = None

    return {
        "stored": True,
        "reason": None,
        "lesson_id": lesson_id,
        "confidence": verdict["adjusted_confidence"],
    }

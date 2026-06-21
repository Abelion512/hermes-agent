"""Validate lesson candidates before RSI injection.

Applies criteria:
1. Contains cause-effect statement
2. Mentions specific Hermes tool
3. Minimum length >= 20 chars
4. Not a duplicate of existing lessons
"""

from typing import Any


def meets_criteria(
    content: str,
    existing: list[str],
    min_length: int = 20,
) -> tuple[bool, str | None]:
    """Check if a lesson candidate meets all validation criteria.

    Returns (is_valid, reason_if_invalid_or_none).
    """
    # Criterion 3: minimum length
    if len(content) < min_length:
        return False, f"Too short ({len(content)} chars, minimum {min_length})"

    # Criterion 1: cause-effect statement
    if not _has_cause_effect(content):
        return False, "Missing cause-effect statement"

    # Criterion 2: mentions a tool
    if not _mentions_tool(content):
        return False, "Does not mention a specific tool"

    # Criterion 4: not a duplicate
    for existing_content in existing:
        if _is_duplicate(content, existing_content):
            return False, "Duplicate of existing lesson"

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
        dict with 'is_valid' (bool) and 'reason' (str or None)
    """
    content = lesson.get("content", "")
    existing_contents = [l.get("content", "") for l in existing_lessons]

    is_valid, reason = meets_criteria(content, existing_contents)

    return {
        "is_valid": is_valid,
        "reason": reason,
    }


def _has_cause_effect(text: str) -> bool:
    """Check if text contains a cause-effect statement."""
    import re
    patterns = [
        r"\bcauses?\b",
        r"\bleads?\s+to\b",
        r"\bresults?\s+in\b",
        r"\bbecause\b",
        r"\btherefore\b",
        r"\bif\b.*\bthen\b",
        r"\bwhen\b.*\bthen\b",
        r"\bprevents?\b",
        r"\bavoids?\b",
        r"\bfixes?\b",
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def _mentions_tool(text: str) -> bool:
    """Check if text mentions a known Hermes tool by name."""
    import re
    hermes_tools = [
        "read_file", "write_file", "edit", "patch",
        "search_files", "grep", "glob",
        "terminal", "bash", "shell",
        "web_search", "web_extract", "web_fetch",
        "browser_navigate",
        "delegate_task", "clarify",
    ]
    pattern = r"\b(" + "|".join(re.escape(t) for t in hermes_tools) + r")\b"
    return bool(re.search(pattern, text, re.IGNORECASE))


def _is_duplicate(content_a: str, content_b: str) -> bool:
    """Check if two lesson contents are semantically similar enough to be duplicates."""
    words_a = set(content_a.lower().split())
    words_b = set(content_b.lower().split())
    if not words_a or not words_b:
        return False
    overlap = len(words_a & words_b) / min(len(words_a), len(words_b))
    return overlap > 0.7

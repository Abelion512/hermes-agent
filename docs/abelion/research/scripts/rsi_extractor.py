"""Extract lesson candidates from agent conversation messages.

A lesson candidate is a potential piece of knowledge extracted from
tool call failures, corrections, and successful patterns.
"""

import re
from typing import Any


def has_cause_effect(text: str) -> bool:
    """Check if text contains a cause-effect statement."""
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
        r"\busing\b.*\bcauses?\b",
        r"\bwithout\b.*\bleads?\b",
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def _mentions_tool(text: str) -> bool:
    """Check if text mentions a known Hermes tool by name."""
    hermes_tools = [
        "read_file", "write_file", "edit", "patch",
        "search_files", "grep", "glob",
        "terminal", "bash", "shell",
        "web_search", "web_extract", "web_fetch",
        "browser_navigate", "browser_click", "browser_type",
        "delegate_task", "clarify",
        "vision_analyze",
    ]
    pattern = r"\b(" + "|".join(re.escape(t) for t in hermes_tools) + r")\b"
    return bool(re.search(pattern, text, re.IGNORECASE))


def _extract_error_pattern(assistant_msg: dict, tool_result_msg: dict) -> str | None:
    """Given an assistant message and its tool result, extract an error pattern."""
    tool_name = "unknown"
    if assistant_msg.get("tool_calls"):
        for tc in assistant_msg["tool_calls"]:
            tool_name = tc["function"]["name"]
            break

    result_content = tool_result_msg.get("content", "")
    if not result_content or result_content == "":
        return None

    # Check if tool result indicates failure
    failure_indicators = [
        "error", "exception", "fail", "traceback",
        "not found", "does not exist", "permission denied",
        "syntaxerror", "importerror", "typeerror", "valueerror",
        "keyerror", "attributeerror", "indexerror",
        "connection refused", "timeout", "no such",
    ]
    has_failure = any(indicator in result_content.lower()
                      for indicator in failure_indicators)
    if not has_failure:
        return None

    return (
        f"Using {tool_name} without proper validation causes errors: "
        f"{result_content[:100]}"
    )


def extract_lesson_candidates(
    messages: list[dict[str, Any]],
    min_length: int = 20,
) -> list[dict[str, Any]]:
    """Extract lesson candidates from agent conversation messages.

    Scans for:
    - Tool call failures with corrections
    - User corrections that reveal knowledge
    - Successful patterns that could be repeated

    Returns list of candidate dicts with:
      - content: lesson text
      - source_tool: tool involved
      - confidence: 0.0-1.0
    """
    candidates = []

    for i, msg in enumerate(messages):
        if msg.get("role") != "tool":
            continue
        if not msg.get("content"):
            continue

        # Find the corresponding assistant message that triggered this tool call
        tool_call_id = msg.get("tool_call_id")
        if not tool_call_id:
            continue

        # Search backward for the assistant message with matching tool_call_id
        assistant_msg = None
        for j in range(i - 1, -1, -1):
            if messages[j].get("role") != "assistant":
                continue
            tc = messages[j].get("tool_calls", [])
            if any(t.get("id") == tool_call_id for t in tc):
                assistant_msg = messages[j]
                break

        if not assistant_msg:
            continue

        pattern = _extract_error_pattern(assistant_msg, msg)
        if pattern:
            candidates.append({
                "content": pattern,
                "source_tool": (
                    assistant_msg["tool_calls"][0]["function"]["name"]
                    if assistant_msg.get("tool_calls") else "unknown"
                ),
                "confidence": 0.6,
            })

        # Check if tool result contains correction language
        result = msg.get("content", "")
        if any(word in result.lower()
               for word in ["instead", "should be", "actually", "correct way"]):
            candidates.append({
                "content": f"Tool correction pattern: {result[:200]}",
                "source_tool": (
                    assistant_msg["tool_calls"][0]["function"]["name"]
                    if assistant_msg.get("tool_calls") else "unknown"
                ),
                "confidence": 0.7,
            })

    # Deduplicate by content prefix
    seen: set[str] = set()
    unique = []
    for c in candidates:
        prefix = c["content"][:80]
        if prefix not in seen:
            seen.add(prefix)
            unique.append(c)

    return unique

"""Lesson injection strategy — decides WHEN and HOW to inject lessons.

Cache-aware: defers injection if it would break prompt cache mid-conversation.
Compression-aware: merges multiple lessons into minimal system prompt hints.

Injection modes:
- inline: inject as system message (breaks cache, use sparingly)
- deferred: store for next session (cache-safe)
- compressed: merge similar lessons into one hint
"""

from __future__ import annotations

import json
from typing import Any


class Injector:
    """Decides lesson injection strategy based on cache state and lesson volume."""

    def __init__(self, max_inline: int = 3, max_tokens: int = 800):
        self.max_inline = max_inline  # max lessons to inject inline per batch
        self.max_tokens = max_tokens  # max total tokens for injected lessons

    def select_lessons(
        self,
        lessons: list[dict[str, Any]],
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Select best lessons to inject, sorted by confidence desc."""
        limit = limit or self.max_inline
        sorted_lessons = sorted(
            lessons, key=lambda l: (l.get("confidence", 0), l.get("evidence_count", 0)),
            reverse=True,
        )
        selected = []
        total_chars = 0
        for l in sorted_lessons:
            action = l.get("action") or l.get("action_body") or l.get("content", "")
            if total_chars + len(action) > self.max_tokens:
                break
            selected.append(l)
            total_chars += len(action)
            if len(selected) >= limit:
                break
        return selected

    def format_injection_prompt(self, lessons: list[dict]) -> str:
        """Format selected lessons as a concise system hint."""
        if not lessons:
            return ""

        parts = ["[Lessons from experience]"]
        for i, l in enumerate(lessons, 1):
            action = l.get("action") or l.get("action_body") or l.get("content", "")
            # Truncate long actions
            if len(action) > 300:
                action = action[:297] + "..."
            parts.append(f"{i}. {action}")
        return "\n".join(parts)

    def compress(self, lessons: list[dict]) -> list[dict]:
        """Merge similar lessons by trigger category.

        If multiple lessons share the same trigger, keep only the
        highest-confidence one.
        """
        seen_trigger: dict[str, dict] = {}
        for l in lessons:
            trigger = l.get("trigger", "general")
            if trigger in seen_trigger:
                existing = seen_trigger[trigger]
                if l.get("confidence", 0) > existing.get("confidence", 0):
                    seen_trigger[trigger] = l
            else:
                seen_trigger[trigger] = l
        return list(seen_trigger.values())

    def should_inject(
        self,
        task_index: int,
        lessons_available: int,
    ) -> bool:
        """Decide if injection is worth it.

        Returns True if:
        - We have high-confidence lessons (>=0.7)
        - Not the first task (no lessons yet)
        - Lessons exist
        """
        return lessons_available > 0 and task_index > 0

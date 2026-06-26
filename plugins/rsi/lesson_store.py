"""Persistent lesson store for RSI.

Uses Hermes built-in MEMORY.md for storage (``[rsi]``-tagged entries).
No own database. No additional infrastructure.

Why:
- Lessons persist across sessions via existing MEMORY.md
- Zero infrastructure — no SQLite, no DB, no schema migration
- Users can see their lessons by reading MEMORY.md directly
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from hermes_constants import get_hermes_home

from .compressor import Lesson

logger = logging.getLogger(__name__)

RSI_TAG = "[rsi]"


class LessonStore:
    """Lesson store backed by Hermes MEMORY.md.

    Reads/writes lessons as tagged entries in the existing memory file.
    No own storage layer — fully leverages Hermes infrastructure.
    """

    def __init__(self):
        self._mem_path: Path | None = None
        self._in_memory_lessons: dict[str, Lesson] = {}  # fallback cache

    @property
    def mem_path(self) -> Path:
        if self._mem_path is None:
            self._mem_path = get_hermes_home() / "memories" / "MEMORY.md"
            self._mem_path.parent.mkdir(parents=True, exist_ok=True)
        return self._mem_path

    async def get_relevant_lessons(
        self,
        task_description: str = "",
        tags: list[str] | None = None,
        limit: int = 20,
        min_confidence: float = 0.0,
    ) -> list[Lesson]:
        """Get all RSI lessons from MEMORY.md.

        Currently returns all lessons; future can add relevance filtering
        by matching task_description keywords.
        """
        lessons = self._read_all()
        filtered = [l for l in lessons if l.confidence >= min_confidence]
        # Sort by confidence desc, limit
        filtered.sort(key=lambda l: -l.confidence)
        return filtered[:limit]

    async def upsert_lesson(self, lesson: Lesson) -> None:
        """Store a lesson in MEMORY.md.

        If lesson with same tag+pattern exists, update its frequency.
        Otherwise append new entry.
        """
        existing = self._read_all()

        # Check if similar lesson exists (same pattern)
        for i, ex in enumerate(existing):
            if ex.pattern == lesson.pattern or ex.action == lesson.action:
                # Update: increase frequency, merge confidence
                ex.frequency += 1
                ex.confidence = max(ex.confidence, lesson.confidence)
                self._write_all(existing)
                logger.debug(
                    "[RSI] Updated lesson: %s (freq=%d, conf=%.2f)",
                    lesson.pattern[:40], ex.frequency, ex.confidence,
                )
                return

        # New lesson: append
        existing.append(lesson)
        self._write_all(existing)
        logger.info("[RSI] New lesson: %s → %s (conf=%.2f)",
                     lesson.pattern[:40], lesson.action[:40], lesson.confidence)

    async def save_session_metrics(self, metrics: dict) -> None:
        """Save session metrics for FASR/entropy analysis.

        Appends to a JSONL file next to MEMORY.md.
        """
        metrics_path = self.mem_path.parent / "rsi_session_metrics.jsonl"
        serializable = {
            k: list(v) if isinstance(v, set) else v
            for k, v in metrics.items()
        }
        with open(metrics_path, "a") as f:
            f.write(json.dumps(serializable) + "\n")

    # ── Internal helpers ──────────────────────────────────────────────

    def _read_all(self) -> list[Lesson]:
        """Parse all [rsi]-tagged entries from MEMORY.md."""
        if not self.mem_path.exists():
            return list(self._in_memory_lessons.values())

        lessons: list[Lesson] = []
        try:
            text = self.mem_path.read_text(encoding="utf-8")
            # MEMORY.md uses § as section delimiter
            entries = text.split("§")
            for entry in entries:
                entry = entry.strip()
                if not entry.startswith(RSI_TAG):
                    continue
                # Parse: [rsi] <pattern> → <action> (or various formats)
                body = entry[len(RSI_TAG):].strip()
                lesson = self._parse_entry(body)
                if lesson:
                    lessons.append(lesson)
        except (OSError, IOError) as e:
            logger.warning("[RSI] Failed to read MEMORY.md: %s", e)
            return list(self._in_memory_lessons.values())

        # Merge with in-memory cache
        seen_ids = {l.id for l in lessons}
        for ml in self._in_memory_lessons.values():
            if ml.id not in seen_ids:
                lessons.append(ml)

        return lessons

    def _write_all(self, lessons: list[Lesson]) -> None:
        """Write lessons to MEMORY.md with [rsi] tags."""
        try:
            # Read existing content, strip old RSI entries
            existing = ""
            if self.mem_path.exists():
                existing = self.mem_path.read_text(encoding="utf-8")
                # Remove all [rsi] sections
                lines = existing.split("\n")
                cleaned = [l for l in lines if RSI_TAG not in l]
                existing = "\n".join(cleaned).strip()

            # Build new RSI entries
            rsi_entries = []
            for l in lessons:
                rsi_entries.append(f"§\n{RSI_TAG} IF {l.pattern} → {l.action}")

            # Write back
            rsi_section = "\n".join(rsi_entries)
            final = existing + "\n\n" + rsi_section if existing else rsi_section
            self.mem_path.write_text(final.strip() + "\n", encoding="utf-8")

            # Update in-memory cache
            self._in_memory_lessons = {l.id: l for l in lessons}

        except (OSError, IOError) as e:
            logger.error("[RSI] Failed to write MEMORY.md: %s", e)
            # Fallback: keep in-memory
            for l in lessons:
                self._in_memory_lessons[l.id] = l

    @staticmethod
    def _parse_entry(body: str) -> Lesson | None:
        """Parse a single [rsi] entry body into a Lesson."""
        # Format: IF <pattern> → <action>
        if "→" in body:
            parts = body.split("→", 1)
            pattern = parts[0].replace("IF", "", 1).strip()
            action = parts[1].strip()
            return Lesson(
                id=f"rsi_{hash(pattern) & 0xFFFFFFFF}",
                pattern=pattern,
                action=action,
                confidence=0.65,
                frequency=1,
            )
        return None

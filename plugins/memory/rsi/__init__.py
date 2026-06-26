"""RSI Memory Provider — learns from tool errors across sessions.

Integrates with Hermes via the MemoryProvider ABC.

How it works:
1. on_session_end(messages) → extract lesson candidates from tool errors
2. validate → store in SQLite+FTS5 per-persona
3. system_prompt_block() → inject top lessons as experience hints
4. prefetch() → inject task-relevant lessons before each turn

No external dependencies. Uses stdlib sqlite3 + FTS5.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.memory_provider import MemoryProvider
from tools.registry import tool_error

logger = logging.getLogger(__name__)

# ── Heuristic patterns ────────────────────────────────────────────────

HEURISTICS: list[tuple[str, str, str, float]] = [
    ("awk.*(?:No such file|not found|cannot access)",
     "Shell pipeline output parsing",
     "When processing find/xargs output with awk, use explicit paths or pipe through cat first.",
     0.75),
    ("sort.*(?:-t|invalid option)",
     "Shell sort with delimiters",
     "When sorting CSV: sort -t',' -k3 -rn. Single quotes around comma delimiter.",
     0.7),
    ("find.*(?:-delete|No such file).*empty",
     "Find and delete operations",
     "Before deleting with find, test with -print first. Use -exec rm {} + for portability.",
     0.7),
    ("grep.*(?:-r|binary|not found)",
     "Recursive grep",
     "Use grep -rl 'pattern' --include='*.py'. Add -l for file paths only.",
     0.7),
    ("tar.*(?:Error|cannot open|not found)",
     "Creating tar archives",
     "Use tar -czf archive.tar.gz -C /path/to/source . to avoid full paths.",
     0.7),
    ("(?:md5|sha)[0-9]*sum.*(?:not found)",
     "Checksum operations",
     "Use find -exec md5sum {} + | sort | uniq -w32 -d for duplicate detection.",
     0.65),
    ("(?:race|thread.*(?:safe|lock|concurrent))",
     "Thread safety",
     "When multiple threads access shared data, use threading.Lock. Acquire before ALL reads and writes. Use 'with lock:' pattern.",
     0.8),
    ("(?:recursi|RecursionError|maximum recursion)",
     "Recursion depth",
     "If function can receive large input, provide iterative fallback. Add guard 'if n > 1000: use loop' before recursive call.",
     0.75),
    ("(?:encoding|UnicodeDecode|UnicodeEncode|latin|utf)",
     "Encoding/decoding",
     "Always use UTF-8 for encoding/decoding. If encoded with encode('utf-8'), decode with decode('utf-8'), not latin-1.",
     0.75),
    ("(?:GIL|multiprocess|thread.*CPU)",
     "CPU-bound parallelism",
     "For CPU-bound work: use multiprocessing.Pool, not threading.Thread. GIL limits threading to one core.",
     0.75),
    ("(?:SQL.*(?:inject|parameter|placeholder|\\?))",
     "SQL injection prevention",
     "Never use f-strings for SQL queries. Use parameterized queries with ? placeholders: cursor.execute('SELECT * FROM t WHERE x = ?', (value,)).",
     0.85),
    ("(?:timezone|naive.*aware|pytz)",
     "Timezone-aware datetime",
     "Never compare naive and aware datetimes. Make aware: naive.replace(tzinfo=pytz.UTC). Or make both naive.",
     0.7),
    ("(?:mutable.*default|default.*argument|list.*accumulat)",
     "Mutable default arguments",
     "Never use mutable default args ([] or {}). Use None as default: 'def f(x=None):' and create new list inside.",
     0.8),
    ("(?:Permission denied|EACCES)",
     "File permission issues",
     "Check file ownership with ls -la, use chmod +x for scripts, or prefix with sudo.",
     0.6),
    ("(?:No such file|FileNotFound|does not exist)",
     "Missing file/directory",
     "Before operating on a file, verify it exists with 'test -f path'. Use ls to discover correct path.",
     0.7),
]


def _match_heuristic(error_text: str) -> dict | None:
    """Match error text against known heuristic patterns."""
    import re
    for pattern_str, trigger, action, conf in HEURISTICS:
        if re.search(pattern_str, error_text, re.IGNORECASE):
            return {"trigger": trigger, "action": action, "confidence": conf}
    return None


def _extract_error_content(result_content: str) -> str | None:
    """Extract relevant error from tool result."""
    if not result_content:
        return None
    indicators = [
        "error", "exception", "traceback", "fail",
        "not found", "permission denied", "no such",
        "syntaxerror", "importerror", "typeerror",
    ]
    lines = result_content.split("\n")
    relevant = [l.strip()[:120] for l in lines[:20]
                if any(ind in l.lower() for ind in indicators)]
    return " | ".join(relevant[:3]) if relevant else None


def _synthesize_lesson(tool_name: str, error_text: str) -> dict | None:
    """Synthesize a lesson from tool name + error text."""
    # Pattern-based
    matched = _match_heuristic(error_text)
    if matched:
        content = f"{matched['trigger']}: {matched['action']}"
        return {"content": content, "trigger": matched["trigger"],
                "action": matched["action"], "confidence": matched["confidence"]}

    # Fallback: tool-specific heuristics
    tool_lessons = {
        "terminal": ("Terminal error handling",
                     f"When running terminal commands, verify preconditions before execution. Handle exit codes properly.",
                     0.5),
        "read_file": ("File reading",
                      "Always verify file exists with os.path.exists() before reading. Handle missing files gracefully.",
                      0.5),
        "write_file": ("File writing",
                       "When writing files, ensure parent directory exists (os.makedirs). Use temp files for atomic writes.",
                       0.5),
        "patch": ("Patch application",
                  "When applying patches, verify target file context matches expected content before applying.",
                  0.5),
        "delegate_task": ("Task delegation",
                          "When delegating tasks, provide clear context and expected output format. Use specific tool sets.",
                          0.4),
    }
    base = tool_lessons.get(tool_name, (
        f"{tool_name} usage",
        f"When using {tool_name}, verify preconditions and handle errors gracefully.",
        0.3,
    ))
    content = f"{base[0]}: {base[1]}"
    return {"content": content, "trigger": base[0], "action": base[1], "confidence": base[2]}


# ── Store ─────────────────────────────────────────────────────────────

_HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))


class _Store:
    """Thread-safe lesson store (simplified MemoryStore for plugin use)."""

    def __init__(self, persona_id: str):
        self.persona_id = persona_id
        self._db_path = _HERMES_HOME / "memory" / persona_id / "rsi_lessons.db"
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS lessons (
                    id TEXT PRIMARY KEY,
                    persona_id TEXT NOT NULL DEFAULT 'default',
                    trigger_type TEXT NOT NULL DEFAULT 'unknown',
                    trigger_value TEXT NOT NULL DEFAULT '',
                    action_body TEXT NOT NULL,
                    confidence REAL NOT NULL DEFAULT 0.5,
                    evidence_count INTEGER NOT NULL DEFAULT 1,
                    success_count INTEGER NOT NULL DEFAULT 0,
                    fail_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                    status TEXT NOT NULL DEFAULT 'active'
                )
            """)
            self._conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_rsi_persona
                ON lessons(persona_id, status, confidence DESC)
            """)
            self._conn.commit()
        return self._conn

    def store_lesson(self, lesson: dict) -> str:
        with self._lock:
            conn = self._get_conn()
            lesson_id = lesson.get("id", str(uuid.uuid4()))
            raw_action = lesson.get("action_body", lesson.get("action", lesson.get("content", "")))
            trigger = lesson.get("trigger", lesson.get("trigger_type", "general"))
            # Include trigger in stored action for better context
            action = f"[{trigger}] {raw_action}" if trigger != "general" else raw_action
            confidence = lesson.get("confidence", 0.5)

            # Check if similar lesson exists
            existing = conn.execute(
                "SELECT id, confidence, evidence_count FROM lessons "
                "WHERE persona_id=? AND action_body=?",
                (self.persona_id, action[:200]),
            ).fetchone()

            if existing:
                if confidence > existing["confidence"]:
                    conn.execute(
                        "UPDATE lessons SET confidence=?, evidence_count=evidence_count+1, "
                        "updated_at=datetime('now') WHERE id=?",
                        (confidence, existing["id"]),
                    )
                else:
                    conn.execute(
                        "UPDATE lessons SET evidence_count=evidence_count+1, "
                        "updated_at=datetime('now') WHERE id=?",
                        (existing["id"],),
                    )
                lesson_id = existing["id"]
            else:
                conn.execute(
                    "INSERT INTO lessons (id, persona_id, trigger_type, trigger_value, "
                    "action_body, confidence) VALUES (?,?,?,?,?,?)",
                    (lesson_id, self.persona_id, "tool_error", trigger, action[:500], confidence),
                )
            conn.commit()
            return lesson_id

    def get_active_lessons(self, limit: int = 5, min_confidence: float = 0.4) -> list[dict]:
        with self._lock:
            conn = self._get_conn()
            rows = conn.execute(
                "SELECT * FROM lessons WHERE persona_id=? AND status='active' "
                "AND confidence>=? ORDER BY confidence DESC LIMIT ?",
                (self.persona_id, min_confidence, limit),
            ).fetchall()
            return [dict(r) for r in rows]

    def update_feedback(self, lesson_id: str, helped: bool) -> None:
        with self._lock:
            conn = self._get_conn()
            if helped:
                conn.execute(
                    "UPDATE lessons SET success_count=success_count+1, "
                    "confidence=MIN(1.0, confidence+0.05), updated_at=datetime('now') WHERE id=?",
                    (lesson_id,),
                )
            else:
                conn.execute(
                    "UPDATE lessons SET fail_count=fail_count+1, "
                    "confidence=MAX(0.0, confidence-0.1), updated_at=datetime('now') WHERE id=?",
                    (lesson_id,),
                )
            conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None


# ── RSI Memory Provider ───────────────────────────────────────────────

class RSIMemoryProvider(MemoryProvider):
    """Memory provider that learns from tool errors.

    Extracts lessons from tool call failures, stores them per-persona,
    and injects relevant lessons back as system prompt hints.
    """

    name = "rsi"

    def __init__(self):
        self._store: _Store | None = None
        self._persona_id: str = "default"
        self._current_session_lessons: list[str] = []  # lesson IDs injected this session

    def is_available(self) -> bool:
        """Always available — no external deps."""
        return True

    def initialize(self, persona_id: str | None = None) -> None:
        self._persona_id = persona_id or "default"
        self._store = _Store(self._persona_id)
        logger.info("[RSI] Initialized for persona: %s", self._persona_id)

    def system_prompt_block(self) -> str:
        """Inject top lessons as system prompt hints."""
        if not self._store:
            return ""

        lessons = self._store.get_active_lessons(limit=3, min_confidence=0.5)
        if not lessons:
            return ""

        self._current_session_lessons = [l["id"] for l in lessons]

        parts = ["\n[Lessons from past experience]"]
        for l in lessons:
            action = l.get("action_body", "")
            if len(action) > 200:
                action = action[:197] + "..."
            parts.append(f"- {action}")
        return "\n".join(parts)

    def prefetch(self, query: str) -> str:
        """Return relevant lesson for the given query."""
        if not self._store or not query:
            return ""
        lessons = self._store.get_active_lessons(limit=2, min_confidence=0.4)
        relevant = []
        query_lower = query.lower()
        for l in lessons:
            action = l.get("action_body", "").lower()
            # Check if any keyword from query appears in action
            query_words = set(w for w in query_lower.split() if len(w) > 3)
            if any(qw in action for qw in query_words):
                relevant.append(l.get("action_body", ""))
        if relevant:
            return "\n".join(f"[RSI Hint] {a}" for a in relevant[:2])
        return ""

    def sync_turn(self, user_message: str, assistant_response: str) -> None:
        """No-op — lesson extraction happens on_session_end."""
        pass

    def on_session_end(self, messages: list[dict]) -> None:
        """Extract lessons from the conversation's tool errors."""
        if not self._store:
            return

        import re

        count = 0
        for i, msg in enumerate(messages):
            if msg.get("role") != "tool":
                continue
            if not msg.get("content"):
                continue

            # Find the assistant message that triggered this
            tool_call_id = msg.get("tool_call_id")
            if not tool_call_id:
                continue

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

            tool_name = "unknown"
            if assistant_msg.get("tool_calls"):
                tool_name = assistant_msg["tool_calls"][0]["function"]["name"]

            error_text = _extract_error_content(msg.get("content", ""))
            if not error_text:
                continue

            lesson = _synthesize_lesson(tool_name, error_text)
            if lesson:
                self._store.store_lesson(lesson)
                count += 1

        if count > 0:
            logger.info("[RSI] Extracted %d lessons from session", count)

    def on_session_switch(self, new_session_id: str, **kwargs) -> None:
        """Reset session tracking on switch."""
        self._current_session_lessons = []

    def shutdown(self) -> None:
        if self._store:
            self._store.close()
            self._store = None
        logger.info("[RSI] Shut down")

    # Required ABC stubs (no tools needed — RSI works through hooks)
    def get_tool_schemas(self) -> list[dict]:
        return []

    def handle_tool_call(self, tool_name: str, args: dict, **kwargs) -> str:
        return ""


# ── Entry point ───────────────────────────────────────────────────────

def create_provider() -> RSIMemoryProvider:
    """Factory function — registered in memory manager."""
    return RSIMemoryProvider()

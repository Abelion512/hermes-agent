"""RSI — Recurrent Self-Improvement memory provider.

No own storage. No own SQLite. Uses Hermes built-in ``memory`` tool via
``on_memory_write()`` callback and injects via ``system_prompt_block()``.

How it works:
  1. Tool error detected on agent → ``on_memory_write()`` stores heuristic
     as a built-in memory entry (MEMORY.md, tagged ``[rsi]``).
  2. Next session start → ``system_prompt_block()`` recalls top-N RSI
     entries and formats them as experience hints.
  3. Feedback → ``on_session_end()`` extracts additional lessons from
     full conversation history.

Key design decisions:
  - Zero storage infra — uses existing ``tools/memory_tool.py`` backend
  - No tool schemas — RSI is passive (context provider, not tool provider)
  - Minimal surface — ~200 lines
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.memory_provider import MemoryProvider
from hermes_constants import get_hermes_home

logger = logging.getLogger(__name__)

# ── Error pattern → heuristic mapping ─────────────────────────────────

_HEURISTICS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"RecursionError|maximum recursion|recursion depth"),
     "When a function recurses too deep, add an iterative fallback or increase recursion limit."),
    (re.compile(r"race|thread.*(?:lock|safe|concurrent)|missing.*lock"),
     "When multiple threads access shared state, protect every read and write with threading.Lock."),
    (re.compile(r"UnicodeDecode|UnicodeEncode|latin.1|wrong encoding"),
     "Always decode bytes with the same codec they were encoded with. Prefer UTF-8."),
    (re.compile(r"SQL.*inject|parameter.*query|f.string.*SQL|unrecognized token"),
     "Never build SQL with f-strings. Use parameterized queries: cursor.execute('WHERE x = ?', (val,))."),
    (re.compile(r"Permission denied|EACCES|can't open file"),
     "Before reading a file, verify it exists and is readable with os.access() or test -f."),
    (re.compile(r"FileNotFound|No such file|does not exist"),
     "Before operating on a path, confirm it exists with os.path.exists()."),
    (re.compile(r"TypeError.*(?:NoneType|not subscriptable)"),
     "When a value may be None, check 'if x is not None:' before accessing attributes."),
    (re.compile(r"ModuleNotFound|ImportError|No module named"),
     "When importing fails, check: (1) package installed? (2) correct import path? (3) circular imports?"),
    (re.compile(r"mutable.*default|default.*argument.*list"),
     "Never use mutable default arguments. Use None as default and create a fresh list inside the function."),
    (re.compile(r"timezone|naive.*aware|pytz"),
     "Never compare naive and aware datetimes. Make all datetimes timezone-aware with replace(tzinfo=pytz.UTC)."),
    (re.compile(r"struct.*(?:mismatch|unpack|pack|format|size)"),
     "struct.pack and struct.unpack must use the same format string."),
    (re.compile(r"GIL|thread.*CPU|no speedup|multiprocessing"),
     "For CPU-bound work use multiprocessing.Pool, not threading. Threading only speeds up I/O."),
]

_RSI_TAG = "[rsi]"
_MAX_LESSONS = 3


class RSIMemoryProvider(MemoryProvider):
    """Memory provider that learns from tool errors via existing Hermes memory.

    Stores lessons as tagged entries in MEMORY.md. On subsequent sessions,
    recalls top lessons and injects as system prompt hints. No own storage.
    """

    name = "rsi"

    def __init__(self):
        self._persona_id: str = "default"

    # ── Core lifecycle ─────────────────────────────────────────────────

    def is_available(self) -> bool:
        return True

    def initialize(self, session_id: str, **kwargs) -> None:
        self._persona_id = kwargs.get("agent_identity", "default")
        logger.info("[RSI] initialized for persona=%s", self._persona_id)

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return []

    def handle_tool_call(self, tool_name: str, args: dict, **kwargs) -> str:
        return ""

    def shutdown(self) -> None:
        pass

    # ── Lesson extraction ──────────────────────────────────────────────

    def _match_lesson(self, text: str) -> str | None:
        """Match text against heuristic patterns."""
        if not text:
            return None
        failure_words = ["error", "exception", "traceback", "fail", "not found"]
        if not any(w in text.lower() for w in failure_words):
            return None
        for pattern, heuristic in _HEURISTICS:
            if pattern.search(text):
                return heuristic
        return None

    def _write_lesson(self, text: str) -> None:
        """Append lesson to MEMORY.md."""
        try:
            mem_dir = get_hermes_home() / "memories"
            mem_dir.mkdir(parents=True, exist_ok=True)
            with open(mem_dir / "MEMORY.md", "a") as f:
                f.write(f"\n§\n{_RSI_TAG} {text}\n")
        except OSError:
            logger.warning("[RSI] failed to write lesson")

    def _read_lessons(self, limit: int = _MAX_LESSONS) -> list[str]:
        """Read most recent RSI-tagged entries from MEMORY.md."""
        try:
            path = get_hermes_home() / "memories" / "MEMORY.md"
            if not path.exists():
                return []
            text = path.read_text(encoding="utf-8")
            rsi = []
            for entry in text.split("§"):
                entry = entry.strip()
                if entry.startswith(_RSI_TAG):
                    rsi.append(entry[len(_RSI_TAG):].strip())
            return rsi[-limit:]
        except (OSError, IOError):
            return []

    # ── Injection ──────────────────────────────────────────────────────

    def system_prompt_block(self) -> str:
        entries = self._read_lessons()
        if not entries:
            return ""
        parts = ["\n[Lessons learned from past errors]"]
        for e in entries:
            text = e[:197] + "..." if len(e) > 200 else e
            parts.append(f"- {text}")
        return "\n".join(parts)

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        if not query:
            return ""
        entries = self._read_lessons(limit=5)
        if not entries:
            return ""
        q = query.lower()
        hits = [e for e in entries if any(w in q and len(w) > 3 for w in e.lower().split())]
        return "\n".join(f"[RSI] {e}" for e in hits[:2])

    # ── Hooks ──────────────────────────────────────────────────────────

    def on_memory_write(self, action: str, target: str, content: str, metadata=None) -> None:
        if action != "add" or not content:
            return
        lesson = self._match_lesson(content)
        if lesson:
            self._write_lesson(lesson)

    def on_session_end(self, messages: list[dict]) -> None:
        if not messages:
            return
        count = 0
        for msg in messages:
            if msg.get("role") != "tool" or not msg.get("content"):
                continue
            lesson = self._match_lesson(msg["content"])
            if lesson:
                self._write_lesson(lesson)
                count += 1
        if count:
            logger.info("[RSI] extracted %d lessons from session", count)

    def get_config_schema(self) -> list[dict]:
        return []


def create_provider() -> RSIMemoryProvider:
    return RSIMemoryProvider()

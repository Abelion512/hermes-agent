"""Extract RSI lessons from tool call events.

Rule-based extraction using heuristic patterns.
Falls back to LLM-only if no pattern matches (tiered architecture).
"""

from __future__ import annotations

import re
import logging
from typing import Optional

from .compressor import Lesson

logger = logging.getLogger(__name__)

# ── 16 heuristic patterns ─────────────────────────────────────────────

_HEURISTICS: list[tuple[re.Pattern, str, str, float]] = [
    (re.compile(r"RecursionError|maximum recursion"),
     "function recurses too deep",
     "add iterative fallback or sys.setrecursionlimit()",
     0.75),
    (re.compile(r"race|thread.*lock|thread.*safe|concurrent.*access"),
     "shared state accessed by multiple threads without lock",
     "protect every read/write with threading.Lock using 'with lock:'",
     0.80),
    (re.compile(r"UnicodeDecode|UnicodeEncode|latin.1|wrong.*encod"),
     "encoding/decoding mismatches",
     "always decode with the same codec that was used to encode; prefer UTF-8",
     0.75),
    (re.compile(r"SQL.*inject|parameter.*query|f.string.*SQL|unrecognized.*token"),
     "building SQL queries with string formatting",
     "use parameterized queries: cursor.execute('WHERE x = ?', (val,))",
     0.85),
    (re.compile(r"Permission denied|EACCES|cannot open file"),
     "file permissions issue",
     "verify the file exists and is readable before opening: os.access() or test -f",
     0.65),
    (re.compile(r"FileNotFound|No such file|does not exist|cannot find"),
     "attempting to operate on a missing file",
     "confirm path exists first: os.path.exists() or ls/find",
     0.70),
    (re.compile(r"TypeError.*NoneType|not subscriptable|NoneType.*attribute"),
     "accessing attribute/method on a None value",
     "guard with 'if x is not None:' before using x.attribute",
     0.80),
    (re.compile(r"ModuleNotFound|ImportError|No module named"),
     "missing import",
     "check: (1) package installed? (2) correct path? (3) circular imports?",
     0.70),
    (re.compile(r"mutable default|default.*argument.*list|default.*argument.*dict"),
     "mutable default argument",
     "use None as default and create fresh list/dict inside the function body",
     0.80),
    (re.compile(r"timezone|naive.*aware|pytz"),
     "comparing naive and aware datetimes",
     "make all datetimes timezone-aware: dt.replace(tzinfo=pytz.UTC)",
     0.70),
    (re.compile(r"struct.*(?:mismatch|unpack|pack|format|size)"),
     "struct format mismatch between writer and reader",
     "ensure struct.pack and struct.unpack use the same format string",
     0.70),
    (re.compile(r"awk.*not found|cannot access|No such file"),
     "awk processing find output with relative paths",
     "use explicit ./ prefix or pipe find output through xargs",
     0.75),
    (re.compile(r"sort.*invalid option|sort.*unrecognized"),
     "sort with wrong delimiter syntax",
     "use: sort -t',' -k3 -rn (single quotes around delimiter)",
     0.70),
    (re.compile(r"tar.*Error|tar.*not found|cannot open"),
     "tar with full paths causing issues",
     "use -C to change directory before archiving: tar -czf -C /srcdir .",
     0.70),
    (re.compile(r"grep.*binary.*match|grep.*is a directory"),
     "grep not filtering file types",
     "use grep -rl --include='*.py' 'pattern' . for recursive search",
     0.65),
    (re.compile(r"GIL|thread.*CPU|no speedup|multiprocessing"),
     "using threading for CPU-bound work",
     "use multiprocessing.Pool for CPU parallelism; threading only for I/O",
     0.80),
]


class LessonExtractor:
    """Extract lessons from tool call events.

    Patterns first, fallback to generic if no match.
    """

    def extract(
        self,
        tool_events: list[dict],
        session_outcome: str = "",
        context: dict | None = None,
    ) -> list[Lesson]:
        """Extract lessons from a list of tool events.

        Args:
            tool_events: List of tool call event dicts.
            session_outcome: 'success', 'failure', or 'partial'.
            context: Optional session context.

        Returns:
            List of Lesson objects.
        """
        lessons: list[Lesson] = []
        seen_fingerprints: set[str] = set()

        for event in tool_events:
            if event.get("type") != "tool_failure":
                continue

            tool_name = event.get("tool", "unknown")
            error_detail = event.get("error_detail", "") or ""
            error_type = event.get("error", "") or ""

            # Try pattern matching
            matched = self._match_heuristic(error_detail + error_type)
            if matched:
                pattern, action, confidence = matched
            else:
                # Generic fallback based on tool
                pattern, action, confidence = self._tool_fallback(tool_name, error_detail)
                if not pattern:
                    continue

            # Dedup by fingerprint
            fp = f"{tool_name}:{pattern[:40]}"
            if fp in seen_fingerprints:
                continue
            seen_fingerprints.add(fp)

            lesson = Lesson(
                id=f"rsi_{tool_name}_{hash(pattern[:30])}",
                pattern=pattern,
                action=action,
                confidence=confidence,
                frequency=1,
                error_type=error_type,
                tags=["auto", tool_name],
            )
            lessons.append(lesson)

        return lessons

    def _match_heuristic(self, text: str) -> tuple[str, str, float] | None:
        """Match text against heuristic patterns."""
        for pat, pattern_str, action, conf in _HEURISTICS:
            if pat.search(text):
                return pattern_str, action, conf
        return None

    @staticmethod
    def _tool_fallback(tool: str, error: str) -> tuple[str, str, float]:
        """Fallback heuristic when no pattern matches."""
        fallbacks = {
            "terminal": ("shell command error", f"verify preconditions before running shell commands; error: {error[:60]}", 0.50),
            "read_file": ("file read failure", "ensure file exists before reading with os.path.exists()", 0.50),
            "write_file": ("file write failure", "ensure target directory exists before writing", 0.50),
            "patch": ("patch application failure", "verify target file content matches expected context before patching", 0.45),
            "browser_navigate": ("browser navigation failure", "verify URL is reachable before navigating", 0.45),
            "web_search": ("web search failure", "simplify query and retry with different phrasing", 0.40),
        }
        return fallbacks.get(tool, ("", "", 0.0))

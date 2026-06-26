"""Extract actionable lesson candidates from agent conversation messages.

Problem with v1: captured raw error messages wrapped in generic template
"Using X without proper validation causes errors: {raw_dump}".

v2 fix: Derives specific, actionable heuristics from error patterns.
Each lesson has a trigger (when to use) and action (what to do).
"""

import json
import re
from typing import Any

# ── Error pattern → heuristic mappings ───────────────────────────────

PATTERN_HEURISTICS: list[tuple[re.Pattern, str, str, float]] = [
    # Shell: awk/cut with find/xargs output
    (re.compile(r"(?:awk|cut|sed|xargs).*(?:No such file|not found|cannot access)", re.I),
     "Shell pipeline output parsing",
     "When processing find/xargs output with awk/cut/sed, always use explicit paths or pipe through cat first. find output is relative, awk expects absolute paths.",
     0.75),
    # Shell: sort with column options
    (re.compile(r"sort.*(?:-t|: unrecognized|invalid option)", re.I),
     "Shell sort with delimiters",
     "When sorting CSV data: sort -t',' -k3 -rn. Use single quotes around comma delimiter. Use -k for column, -rn for reverse numeric.",
     0.7),
    # Shell: find -delete vs -exec
    (re.compile(r"find.*(?:-delete|:.*No such file).*empty|remove|delete", re.I),
     "Find and delete operations",
     "When using find to delete, use -exec rm {} + instead of -delete for portability. For empty dirs: find . -type d -empty -delete. Test with -print first.",
     0.7),
    # Shell: grep with recursive
    (re.compile(r"grep.*(?:-r|--recursive).*(?:No such file|not found|binary)", re.I),
     "Recursive grep",
     "When searching recursively: grep -rl 'pattern' . --include='*.py'. Use -r (not -R) to skip symlinks. Add -l for file paths only. Use --include for file type filter.",
     0.7),
    # Shell: tar with paths
    (re.compile(r"tar.*(?:Error|cannot open|not found)", re.I),
     "Creating tar archives",
     "When creating tar.gz: tar -czf archive.tar.gz -C /path/to/source . or specify files directly. Use -C to change directory before archiving to avoid full paths.",
     0.7),
    # Shell: md5sum/sha256sum with comma in filename
    (re.compile(r"(?:md5|sha)[0-9]*sum.*(?:No such file|not found)", re.I),
     "Checksum operations",
     "When checking file duplicates with md5sum/sha256: use find -exec md5sum {} + | sort | uniq -w32 -d. Avoid xargs with checksum on files with special chars.",
     0.65),
    # Shell: csvkit/column alignment
    (re.compile(r"column.*(?:No such file|not found)", re.I),
     "Column alignment of CSV",
     "Use column -t -s',' -n for aligning CSV output. If column not available, use awk -F',' '{for(i=1;i<=NF;i++)printf \"%-15s\", $i;print}'",
     0.6),
    # Shell: process tree
    (re.compile(r"(?:pstree|ps.*ppid|kill.*descendant)", re.I),
     "Process tree management",
     "To kill descendant processes: find child PIDs with ps --ppid $PARENT_PID -o pid=, kill children before parent. Never kill in arbitrary order — always leaf-to-root.",
     0.7),
    # Debug: race condition
    (re.compile(r"(?:race|thread.*(?:safe|lock|concurrent))", re.I),
     "Thread safety / race condition",
     "When multiple threads access shared data, always use threading.Lock. Acquire lock before all reads AND writes. Release in finally block or use 'with lock:'.",
     0.8),
    # Debug: recursion
    (re.compile(r"(?:recursi|RecursionError|maximum recursion)", re.I),
     "Recursion depth errors",
     "If function can receive arbitrarily large input, provide iterative fallback. Add explicit 'if n > 1000: use loop instead of recursion' guard before recursive call.",
     0.75),
    # Debug: encoding
    (re.compile(r"(?:encoding|coding|UnicodeDecode|UnicodeEncode|latin|utf)", re.I),
     "Encoding/decoding mismatches",
     "Always use UTF-8 for encoding/decoding text. If data was encoded with encode('utf-8'), decode with decode('utf-8'), not latin-1. When reading files, specify encoding='utf-8' explicitly.",
     0.75),
    # Debug: binary search
    (re.compile(r"(?:binary.search|infinite.loop|not.found|return.-1)", re.I),
     "Algorithm termination",
     "When implementing binary search: return -1 when lo > hi (target not in array). Do NOT recurse in the not-found branch — that causes infinite recursion.",
     0.7),
    # Debug: GIL/multiprocessing
    (re.compile(r"(?:GIL|multiprocess|thread.*(?:CPU|parallel|speed))", re.I),
     "CPU-bound parallelism",
     "For CPU-bound work in Python: use multiprocessing.Pool, not threading.Thread (GIL limits threading to one core). For I/O-bound work: use threading or asyncio.",
     0.75),
    # Debug: SQL injection
    (re.compile(r"(?:SQL.*(?:inject|parameter|placeholder|\?|%.format|f.string))", re.I),
     "SQL injection prevention",
     "Never use f-strings or string formatting for SQL queries with user input. Always use parameterized queries with ? placeholders: cursor.execute('SELECT * FROM t WHERE x = ?', (value,)).",
     0.85),
    # Debug: asyncio deadlock
    (re.compile(r"(?:async.*(?:deadlock|starvation|waiting|event.*wait|gather))", re.I),
     "Asyncio coordination",
     "When using asyncio.Event: one coroutine should set(), the other should wait(). If both wait(), you have a deadlock. For mutual dependency, use asyncio.Lock or restructure.",
     0.7),
    # Debug: timezone
    (re.compile(r"(?:timezone|naive|aware|pytz|datetime.*timedelta)", re.I),
     "Timezone-aware datetime comparison",
     "Never compare naive and aware datetimes directly — causes TypeError. Make all datetimes timezone-aware: naive.replace(tzinfo=pytz.UTC). Or make both naive: dt.replace(tzinfo=None).",
     0.7),
    # Debug: mutable default
    (re.compile(r"(?:mutable.default|default.*argument|list.*accumulat)", re.I),
     "Mutable default arguments",
     "Never use mutable default arguments ([] or {}). Use None as default: 'def f(x=None):' and create a new list inside: 'if x is None: x = []'. This prevents state accumulation across calls.",
     0.8),
    # Debug: argument collision
    (re.compile(r"(?:arg.*collision|takes.*keyword|got.*multiple|unexpected)", re.I),
     "Function argument collision",
     "When using *args and **kwargs, named parameters after *args may conflict. Rename the positional to *rest, *items to avoid collision, or move the keyword before *args.",
     0.65),
    # Debug: struct format mismatch
    (re.compile(r"(?:struct.*(?:mismatch|format|unpack|pack|size))", re.I),
     "Binary serialization format",
     "struct.pack and struct.unpack must use the same format string. 'I' = unsigned int (4 bytes), 'Q' = unsigned long long (8 bytes). Check both sides when serializing across platforms.",
     0.7),
    # General: permission denied
    (re.compile(r"(?:Permission denied|EACCES)", re.I),
     "File permission issues",
     "When getting 'Permission denied': check file ownership with ls -la, use chmod +x for scripts, or prefix with sudo. If reading config files, check if they exist first.",
     0.6),
    # General: file not found
    (re.compile(r"(?:No such file|FileNotFound|does not exist|cannot access)", re.I),
     "Missing file/directory",
     "Before reading/operating on a file, verify it exists: 'test -f path' or 'os.path.exists()'. Use ls or find to discover correct path if the expected path doesn't exist.",
     0.7),
]


def _match_heuristic(error_text: str, tool_name: str) -> dict | None:
    """Match error text against known heuristic patterns. Returns heuristic dict or None."""
    for pattern, trigger, action, confidence in PATTERN_HEURISTICS:
        if pattern.search(error_text):
            return {
                "trigger": trigger,
                "action": action,
                "confidence": confidence,
                "source": "pattern",
            }
    return None


def _extract_error_from_result(result_content: str) -> str | None:
    """Extract the actual error message from a tool result."""
    if not result_content:
        return None

    # Look for error indicators
    indicators = [
        "error", "exception", "traceback", "fail", "crash",
        "not found", "does not exist", "permission denied",
        "syntaxerror", "importerror", "typeerror", "valueerror",
        "keyerror", "attributeerror", "indexerror",
        "connection refused", "timeout", "no such",
        "killed", "segmentation fault", "bus error",
    ]

    # Try to find specific error lines
    lines = result_content.split("\n")
    error_lines = []
    for line in lines[:20]:  # Check first 20 lines
        line_lower = line.lower()
        if any(ind in line_lower for ind in indicators):
            error_lines.append(line.strip()[:120])
            if len(error_lines) >= 3:
                break

    if error_lines:
        return " | ".join(error_lines)
    return None


def _synthesize_heuristic(
    error_text: str,
    tool_name: str,
    task_context: str = "",
) -> dict:
    """Synthesize a heuristic lesson from error context.

    First tries pattern matching (PATTERN_HEURISTICS), falls back to
    deriving a generic heuristic from tool name + error.

    Returns dict with trigger, action, confidence.
    """
    # Try pattern-based matching first
    matched = _match_heuristic(error_text, tool_name)
    if matched:
        return matched

    # Fallback: derive from tool name
    tool_heuristics = {
        "terminal": {
            "trigger": f"Terminal command failure",
            "action": (
                f"When running terminal commands, always check exit codes "
                f"and handle errors: {error_text[:80]}"
            ),
            "confidence": 0.5,
        },
        "read_file": {
            "trigger": "File read failure",
            "action": (
                f"When reading files, verify existence first and handle missing files gracefully"
            ),
            "confidence": 0.5,
        },
        "patch": {
            "trigger": "Patch application failure",
            "action": (
                f"When applying patches, verify the target file content matches "
                f"expected context before patching"
            ),
            "confidence": 0.5,
        },
    }

    base = tool_heuristics.get(tool_name, {
        "trigger": f"{tool_name} failure",
        "action": f"When using {tool_name}, verify preconditions and handle errors properly",
        "confidence": 0.4,
    })
    return base


def extract_lesson_candidates(
    messages: list[dict[str, Any]],
    min_length: int = 20,
    task_prompt: str = "",
) -> list[dict[str, Any]]:
    """Extract actionable lesson candidates from agent conversation.

    Returns list of candidate dicts with:
      - trigger: when this lesson applies
      - action: what to do (actionable heuristic)
      - source_tool: tool involved
      - confidence: 0.0-1.0
      - content: combined "<trigger>: <action>" for backward compatibility
    """
    candidates = []
    seen_actions: set[str] = set()

    for i, msg in enumerate(messages):
        if msg.get("role") != "tool":
            continue
        if not msg.get("content"):
            continue

        # Find corresponding assistant message
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

        result_content = msg.get("content", "")

        # Check if it's an error
        error_text = _extract_error_from_result(result_content)
        if not error_text:
            continue

        # Synthesize heuristic
        heuristic = _synthesize_heuristic(error_text, tool_name, task_prompt)

        # Deduplicate by action text
        action_key = heuristic["action"][:60]
        if action_key in seen_actions:
            continue
        seen_actions.add(action_key)

        content = f"{heuristic['trigger']}: {heuristic['action']}"

        candidates.append({
            "content": content,
            "trigger": heuristic["trigger"],
            "action": heuristic["action"],
            "source_tool": tool_name,
            "confidence": heuristic["confidence"],
            "error_type": heuristic.get("source", "synthesized"),
        })

    return candidates

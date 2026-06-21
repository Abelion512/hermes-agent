"""Benchmark task definitions for RSI experiment.

10 debugging tasks + 10 shell tasks.
Each task has id, prompt, category, gold_answer, and difficulty.
"""

from dataclasses import dataclass


@dataclass
class BenchmarkTask:
    """A single benchmark task for the RSI experiment."""

    id: str
    prompt: str
    category: str  # "debugging" or "shell"
    gold_answer: str  # expected key behavior for verification
    difficulty: str  # "easy", "medium", "hard"

    def to_dict(self):
        return {
            "id": self.id,
            "prompt": self.prompt,
            "category": self.category,
            "gold_answer": self.gold_answer,
            "difficulty": self.difficulty,
        }


DEBUGGING_TASKS = [
    BenchmarkTask(
        id="debug-01",
        prompt=(
            "Read /tmp/rsibench_fix_variable.py. It has a variable name typo in an "
            "f-string — the template variable referenced inside the string does not "
            "match the variable passed to the format/expression. Fix the typo so "
            '"Hello World" is printed correctly.'
        ),
        category="debugging",
        gold_answer="corrects template_var to variable name that matches the actual variable",
        difficulty="easy",
    ),
    BenchmarkTask(
        id="debug-02",
        prompt=(
            "Read /tmp/rsibench_fix_import.py. It has an ImportError because it "
            "imports from a module that doesn't exist (pytest.utils). Find the "
            "correct import path and fix it."
        ),
        category="debugging",
        gold_answer="changes 'from pytest.utils import ...' to the correct import path",
        difficulty="easy",
    ),
    BenchmarkTask(
        id="debug-03",
        prompt=(
            "Read /tmp/rsibench_off_by_one.py. It has an off-by-one error — a loop "
            "or list comprehension skips the last element. Fix the range to include "
            "all intended elements."
        ),
        category="debugging",
        gold_answer="fixes range(len(x)-1) to range(len(x)) or equivalent",
        difficulty="easy",
    ),
    BenchmarkTask(
        id="debug-04",
        prompt=(
            "Read /tmp/rsibench_none_attribute.py. It triggers a TypeError when "
            "accessing an attribute on None. Add a guard 'if result is not None:' "
            "before the attribute access."
        ),
        category="debugging",
        gold_answer="adds 'if result is not None:' guard before attribute access",
        difficulty="medium",
    ),
    BenchmarkTask(
        id="debug-05",
        prompt=(
            "Read /tmp/rsibench_unclosed_file.py. A file handle is opened but "
            "never closed, causing a resource warning. Fix the resource leak by "
            "using a 'with' statement (context manager) instead of raw open()."
        ),
        category="debugging",
        gold_answer="converts open() call to 'with open(...) as f:' pattern",
        difficulty="medium",
    ),
    BenchmarkTask(
        id="debug-06",
        prompt=(
            "Read /tmp/rsibench_wrong_exception.py. A function raises ValueError "
            "but all callers expect and catch KeyError. Fix the exception type "
            "to match what callers expect."
        ),
        category="debugging",
        gold_answer="changes 'raise ValueError' to 'raise KeyError'",
        difficulty="medium",
    ),
    BenchmarkTask(
        id="debug-07",
        prompt=(
            "Read /tmp/rsibench_deadlock.py. Two threads acquire the same two "
            "locks in different orders, causing a deadlock. Fix the lock "
            "acquisition order so both threads acquire lock_a then lock_b."
        ),
        category="debugging",
        gold_answer="makes both threads/functions acquire locks in the same order",
        difficulty="hard",
    ),
    BenchmarkTask(
        id="debug-08",
        prompt=(
            "Read /tmp/rsibench_mutable_default.py. A function uses a mutable "
            "default argument (empty list []) that accumulates state across "
            "calls. Fix it to use None as default and create a new list inside "
            "the function body."
        ),
        category="debugging",
        gold_answer="changes 'def foo(x=[])' to 'def foo(x=None)' with 'if x is None: x = []' inside",
        difficulty="medium",
    ),
    BenchmarkTask(
        id="debug-09",
        prompt=(
            "Read /tmp/rsibench_circular_import.py. Two modules import each "
            "other, causing ImportError at load time. Fix by moving one import "
            "inside the function that needs it (lazy import), or by extracting "
            "shared code into a third module."
        ),
        category="debugging",
        gold_answer="moves one import to be local inside a function or extracts shared dependency",
        difficulty="hard",
    ),
    BenchmarkTask(
        id="debug-10",
        prompt=(
            "Read /tmp/rsibench_regex_error.py. A regex pattern has unbalanced "
            "parentheses or invalid escaping, causing re.error at runtime. Fix "
            "the pattern so it correctly matches the intended string."
        ),
        category="debugging",
        gold_answer="fixes the unbalanced parentheses or escaping in the regex pattern",
        difficulty="medium",
    ),
]

SHELL_TASKS = [
    BenchmarkTask(
        id="shell-01",
        prompt=(
            "Find all files modified in the last 24 hours under "
            "/tmp/rsibench_data/. Show their absolute paths."
        ),
        category="shell",
        gold_answer="uses 'find' with -mtime or -newer flag",
        difficulty="easy",
    ),
    BenchmarkTask(
        id="shell-02",
        prompt=(
            "Count how many lines, words, and characters are in "
            "/tmp/rsibench_data/sample.txt. Use a single command."
        ),
        category="shell",
        gold_answer="uses 'wc' (word count) command",
        difficulty="easy",
    ),
    BenchmarkTask(
        id="shell-03",
        prompt=(
            "In /tmp/rsibench_data/logs.txt, find all lines containing 'ERROR' "
            "(case-insensitive) that occurred between 14:00 and 15:00. Show just "
            "those matching lines."
        ),
        category="shell",
        gold_answer="uses grep -i ERROR piped to awk for time-range filtering",
        difficulty="medium",
    ),
    BenchmarkTask(
        id="shell-04",
        prompt=(
            "Compress /tmp/rsibench_data/archive/ into a tar.gz archive at "
            "/tmp/rsibench_data/archive.tar.gz, preserving file permissions."
        ),
        category="shell",
        gold_answer="uses 'tar -czf' with appropriate flags",
        difficulty="easy",
    ),
    BenchmarkTask(
        id="shell-05",
        prompt=(
            "Sort /tmp/rsibench_data/data.csv by the third column numerically in "
            "descending order. Show only the top 5 rows."
        ),
        category="shell",
        gold_answer="uses 'sort -t, -k3 -rn' or similar",
        difficulty="medium",
    ),
    BenchmarkTask(
        id="shell-06",
        prompt=(
            "Find all empty directories under /tmp/rsibench_data/ and remove "
            "them. Print the paths of any directories that were removed."
        ),
        category="shell",
        gold_answer="uses 'find ... -empty -type d -delete' or -exec rmdir",
        difficulty="medium",
    ),
    BenchmarkTask(
        id="shell-07",
        prompt=(
            "Extract all unique IP addresses from /tmp/rsibench_data/access.log. "
            "Count how many times each IP appears, sort by count descending, "
            "and show the top 10."
        ),
        category="shell",
        gold_answer="uses awk/cut to extract IP column, then sort | uniq -c | sort -rn | head -10",
        difficulty="hard",
    ),
    BenchmarkTask(
        id="shell-08",
        prompt=(
            "Find all .py files under /tmp/rsibench_data/ that contain the word "
            "'TODO' but NOT the word 'FIXME'. Show file paths only."
        ),
        category="shell",
        gold_answer="uses grep -rl TODO combined with grep -L FIXME via xargs or pipeline",
        difficulty="medium",
    ),
    BenchmarkTask(
        id="shell-09",
        prompt=(
            "Get disk usage of /tmp/rsibench_data/ grouped by file extension. "
            "Show total size per extension sorted by size descending."
        ),
        category="shell",
        gold_answer="uses find + awk grouping or 'du' piped to extension-based aggregation",
        difficulty="hard",
    ),
    BenchmarkTask(
        id="shell-10",
        prompt=(
            "In /tmp/rsibench_data/duplicates/, find all files that have "
            "identical content (not just same filenames) and group them. Show "
            "which file paths are duplicates of each other."
        ),
        category="shell",
        gold_answer="uses md5sum/sha256sum + sort/uniq, or diff, or fdupes",
        difficulty="hard",
    ),
]

ALL_TASKS = DEBUGGING_TASKS + SHELL_TASKS
TASK_BY_ID = {t.id: t for t in ALL_TASKS}


def get_task_batch(category: str | None = None) -> list[BenchmarkTask]:
    """Get task batch, optionally filtered by category."""
    if category == "debugging":
        return DEBUGGING_TASKS
    elif category == "shell":
        return SHELL_TASKS
    return ALL_TASKS


def get_task_count(category: str | None = None) -> int:
    """Return number of tasks, optionally filtered by category."""
    return len(get_task_batch(category))

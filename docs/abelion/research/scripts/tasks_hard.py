"""Harder benchmark tasks for RSI experiment v2.

Each task requires >=3 tool calls. Target ~60-70% completion on Gemini flash-lite.
"""

from dataclasses import dataclass


@dataclass
class BenchmarkTask:
    """A single benchmark task."""
    id: str
    prompt: str
    category: str
    gold_answer: str
    difficulty: str

    def to_dict(self):
        return {
            "id": self.id,
            "prompt": self.prompt,
            "category": self.category,
            "gold_answer": self.gold_answer,
            "difficulty": self.difficulty,
        }


HARD_TASKS = [
    # ── Shell (10 tasks) ──────────────────────────────────────────────
    BenchmarkTask(
        id="shell-hard-01",
        prompt=(
            "Under /tmp/rsibench_hard/, find all .sh and .py files "
            "recursively. For each file, count how many lines contain "
            "the word 'import' (case-sensitive). Output as CSV: "
            "filename,import_count sorted by import_count descending."
        ),
        category="shell",
        gold_answer="find + xargs grep -c import + sort -t, -k2 -rn",
        difficulty="hard",
    ),
    BenchmarkTask(
        id="shell-hard-02",
        prompt=(
            "Read /tmp/rsibench_hard/server.log. Parse each line to "
            "extract hour (HH) from timestamp and the log level. "
            "Group by hour, count ERROR vs WARN vs INFO per hour. "
            "Output CSV: hour,error_count,warn_count,info_count"
        ),
        category="shell",
        gold_answer="awk/cut parsing + sort/uniq aggregation, output CSV",
        difficulty="hard",
    ),
    BenchmarkTask(
        id="shell-hard-03",
        prompt=(
            "In /tmp/rsibench_hard/, find all TODO comments across all "
            "files. For each unique TODO text, count how many times it "
            "appears. Show top 5 most common TODOs with their counts. "
            "Output: 'count: TODO text' per line."
        ),
        category="shell",
        gold_answer="grep -rho 'TODO.*' + sort | uniq -c | sort -rn | head -5",
        difficulty="hard",
    ),
    BenchmarkTask(
        id="shell-hard-04",
        prompt=(
            "Read /tmp/rsibench_hard/crontab.txt. Each line is a cron "
            "schedule entry. Find all pairs of entries that run within "
            "30 minutes of each other. Report each conflicting pair "
            "with both schedules."
        ),
        category="shell",
        gold_answer="parse HH:MM from each line, sort, check adjacent pairs for <30 min diff",
        difficulty="hard",
    ),
    BenchmarkTask(
        id="shell-hard-05",
        prompt=(
            "Read /tmp/rsibench_hard/data.json. It has nested JSON "
            "structure with 'users' array. Each user has 'name' and "
            "a nested 'metadata' object. Flatten into CSV rows: "
            "name,age,role. Output CSV with header."
        ),
        category="shell",
        gold_answer="python3 -c with json.load + csv.writer, or jq",
        difficulty="hard",
    ),
    BenchmarkTask(
        id="shell-hard-06",
        prompt=(
            "Create a SQLite temp database. Read "
            "/tmp/rsibench_hard/users.csv to create 'users' table. "
            "Then JOIN with an inline departments table "
            "(VALUES (10,'Engineering'),(20,'Sales')) to output: "
            "department_name,user_count. Use sqlite3 CLI."
        ),
        category="shell",
        gold_answer="sqlite3 .import, CREATE TABLE depts, SELECT d.name, COUNT(u.id) FROM ... GROUP BY",
        difficulty="hard",
    ),
    BenchmarkTask(
        id="shell-hard-07",
        prompt=(
            "Run /tmp/rsibench_hard/race.sh exactly 10 times. Capture "
            "stdout each run. If all 10 outputs are identical, print "
            "'CONSISTENT: 100%'. If any differ, print "
            "'INCONSISTENT: N unique outputs' and show each variant."
        ),
        category="shell",
        gold_answer="for i in 1..10 do output=$(...race.sh); echo; sort -u to count unique",
        difficulty="hard",
    ),
    BenchmarkTask(
        id="shell-hard-08",
        prompt=(
            "Read /tmp/rsibench_hard/known_uuids.txt. It lists known "
            "UUIDs. Now hexdump /tmp/rsibench_hard/data.bin and extract "
            "any strings matching UUID pattern (8-4-4-4-12 hex). "
            "Report which UUIDs from the binary are NOT in known list."
        ),
        category="shell",
        gold_answer="xxd + grep -oP UUID pattern + diff/comm against known list",
        difficulty="hard",
    ),
    BenchmarkTask(
        id="shell-hard-09",
        prompt=(
            "Read /tmp/rsibench_hard/struct_pack.py. There is a "
            "mismatch between struct.pack format 'I' (4 bytes) and "
            "struct.unpack format 'Q' (8 bytes). Fix the format "
            "string to match. Then run the script and verify it "
            "prints (42,) without error."
        ),
        category="shell",
        gold_answer="edit file to change 'Q' to 'I' or vice versa to match, run python3 to verify",
        difficulty="hard",
    ),
    BenchmarkTask(
        id="shell-hard-10",
        prompt=(
            "Under /tmp/rsibench_hard/, find all .py files. For each "
            "file, compute its line count and word count (wc). Then "
            "calculate the ratio words/lines. Output CSV: "
            "filename,lines,words,ratio sorted by ratio descending."
        ),
        category="shell",
        gold_answer="find .py + wc per file + awk ratio calculation + sort -t, -k4 -rn",
        difficulty="hard",
    ),
    # ── Debugging (10 tasks) ──────────────────────────────────────────
    BenchmarkTask(
        id="debug-hard-01",
        prompt=(
            "Read /tmp/rsibench_hard/race_dict.py. Two threads write "
            "and read a shared dict without locks. Run it — some "
            "items may be missing due to race conditions. Fix by "
            "adding a threading.Lock that protects all dict access. "
            "Verify it prints 'Dict size: 1000'."
        ),
        category="debugging",
        gold_answer="add lock = threading.Lock(); acquire/release around all dict operations",
        difficulty="hard",
    ),
    BenchmarkTask(
        id="debug-hard-02",
        prompt=(
            "Read /tmp/rsibench_hard/recursion.py. It computes "
            "factorial recursively but will hit RecursionError for "
            "n > 1000. Fix by adding an iterative implementation "
            "that handles any n without recursion limit issues."
        ),
        category="debugging",
        gold_answer="add iterative loop as fallback or replace recursion entirely",
        difficulty="hard",
    ),
    BenchmarkTask(
        id="debug-hard-03",
        prompt=(
            "Read /tmp/rsibench_hard/encoding.py. A UTF-8 string is "
            "decoded as latin-1, corrupting characters. Fix the "
            "decode to use utf-8. Run and verify 'cafe\u0301' prints "
            "correctly."
        ),
        category="debugging",
        gold_answer="change .decode('latin-1') to .decode('utf-8')",
        difficulty="medium",
    ),
    BenchmarkTask(
        id="debug-hard-04",
        prompt=(
            "Read /tmp/rsibench_hard/binary_search.py. If target is "
            "not in array, instead of returning -1, it recurses "
            "infinitely. Run it to see the RecursionError. Fix by "
            "returning -1 when element not found."
        ),
        category="debugging",
        gold_answer="replace recursive call with 'return -1'",
        difficulty="medium",
    ),
    BenchmarkTask(
        id="debug-hard-05",
        prompt=(
            "Read /tmp/rsibench_hard/gil_cpu.py. It uses threading "
            "for CPU-bound work — no speedup due to GIL. Refactor "
            "to use multiprocessing.Pool for real parallelism. "
            "Run and verify it completes."
        ),
        category="debugging",
        gold_answer="replace threading.Thread with multiprocessing.Pool.map()",
        difficulty="hard",
    ),
    BenchmarkTask(
        id="debug-hard-06",
        prompt=(
            "Read /tmp/rsibench_hard/sql_inject.py. It builds SQL "
            "query with f-string, enabling injection. Fix using "
            "parameterized queries (? placeholders). Verify it "
            "runs without SQL injection vulnerability."
        ),
        category="debugging",
        gold_answer="replace f'SELECT ... WHERE name = {user_input}' with parameterized version",
        difficulty="hard",
    ),
    BenchmarkTask(
        id="debug-hard-07",
        prompt=(
            "Read /tmp/rsibench_hard/async_deadlock.py. Two coroutines "
            "wait for each other's events — deadlock. Fix by having "
            "one coroutine signal the other's event instead of both "
            "waiting. Run and verify it completes."
        ),
        category="debugging",
        gold_answer="change one coroutine to set the other's event instead of waiting",
        difficulty="hard",
    ),
    BenchmarkTask(
        id="debug-hard-08",
        prompt=(
            "Read /tmp/rsibench_hard/timezone.py. It compares naive "
            "datetime with aware datetime — TypeError. Fix by making "
            "both timezone-aware with pytz.UTC. Run and verify."
        ),
        category="debugging",
        gold_answer="make naive datetime aware: naive.replace(tzinfo=pytz.UTC)",
        difficulty="medium",
    ),
    BenchmarkTask(
        id="debug-hard-09",
        prompt=(
            "Read /tmp/rsibench_hard/arg_collision.py. The function "
            "takes *items and then a keyword 'items' gets eaten by "
            "*items. Fix so both the positional list AND the 'items' "
            "keyword work correctly. Run and verify."
        ),
        category="debugging",
        gold_answer="rename *items to *args, or rename the keyword argument to avoid collision",
        difficulty="hard",
    ),
    BenchmarkTask(
        id="debug-hard-10",
        prompt=(
            "Read /tmp/rsibench_hard/struct_pack.py. Writer uses 'I' "
            "(4 bytes), reader uses 'Q' (8 bytes). Fix the format "
            "string mismatch. Run and verify it prints (42,) without "
            "struct.error."
        ),
        category="debugging",
        gold_answer="make writer and reader use same format string (both 'I' or both 'Q')",
        difficulty="medium",
    ),
]

ALL_TASKS = HARD_TASKS
TASK_BY_ID = {t.id: t for t in ALL_TASKS}


def get_task_batch(category: str | None = None) -> list[BenchmarkTask]:
    if category == "shell":
        return [t for t in ALL_TASKS if t.category == "shell"]
    elif category == "debugging":
        return [t for t in ALL_TASKS if t.category == "debugging"]
    return ALL_TASKS


def get_task_count(category: str | None = None) -> int:
    return len(get_task_batch(category))

#!/usr/bin/env bash
# Create benchmark fixtures for RSI experiment tasks
# Run: bash create_fixtures.sh

BASE="/tmp/rsibench_data"
mkdir -p "$BASE/archive" "$BASE/duplicates"

# debug-01: variable name typo in f-string
cat > /tmp/rsibench_fix_variable.py << 'EOF'
name = "World"
# Bug: variable in f-string doesn't match
print(f"Hello {nme}")
EOF

# debug-02: wrong import path
cat > /tmp/rsibench_fix_import.py << 'EOF'
# Bug: pytest.utils doesn't exist
from pytest.utils import approx

def test_foo():
    assert approx(0.1 + 0.2) == 0.3
EOF

# debug-03: off-by-one in range
cat > /tmp/rsibench_off_by_one.py << 'EOF'
items = [1, 2, 3, 4, 5]
# Bug: skips last element
for i in range(len(items) - 1):
    print(items[i])
EOF

# debug-04: attribute on None
cat > /tmp/rsibench_none_attribute.py << 'EOF'
def get_config():
    return None

cfg = get_config()
# Bug: cfg could be None
print(cfg.theme)
EOF

# debug-05: unclosed file handle
cat > /tmp/rsibench_unclosed_file.py << 'EOF'
f = open("/tmp/rsibench_data/sample.txt", "w")
f.write("data")
# Bug: never closed
EOF

# debug-06: wrong exception type
cat > /tmp/rsibench_wrong_exception.py << 'EOF'
def lookup(key):
    raise ValueError(f"not found: {key}")

try:
    lookup("foo")
except KeyError:
    print("caught")
EOF

# debug-07: deadlock from lock order
cat > /tmp/rsibench_deadlock.py << 'EOF'
import threading
lock_a = threading.Lock()
lock_b = threading.Lock()

def thread1():
    lock_a.acquire()
    lock_b.acquire()
    lock_b.release()
    lock_a.release()

def thread2():
    # Bug: acquires in opposite order
    lock_b.acquire()
    lock_a.acquire()
    lock_a.release()
    lock_b.release()
EOF

# debug-08: mutable default arg
cat > /tmp/rsibench_mutable_default.py << 'EOF'
# Bug: mutable default accumulates
def add_item(item, items=[]):
    items.append(item)
    return items
EOF

# debug-09: circular import (two files)
cat > /tmp/rsibench_circular_a.py << 'EOF'
from rsibench_circular_b import bar

def foo():
    return bar()
EOF

cat > /tmp/rsibench_circular_b.py << 'EOF'
from rsibench_circular_a import foo

def bar():
    return "hello"
EOF

# debug-10: regex error
cat > /tmp/rsibench_regex_error.py << 'EOF'
import re
# Bug: unbalanced parentheses
pattern = r"(\d+"
re.match(pattern, "123")
EOF

# === Shell task fixtures ===

# shell-01: files with various mtime
touch -t "$(date -d '2 days ago' +%m%d%H%M)" "$BASE"/old_file.txt
touch -t "$(date -d '1 hour ago' +%m%d%H%M)" "$BASE"/recent_file.txt

# shell-02: sample text file
cat > "$BASE"/sample.txt << 'EOF'
hello world
this is a test file
with multiple lines
to count
EOF

# shell-03: logs with timestamps
cat > "$BASE"/logs.txt << 'EOF'
[2026-06-25 14:15:00] INFO: starting
[2026-06-25 14:30:00] ERROR: connection failed
[2026-06-25 14:45:00] WARN: retry attempt
[2026-06-25 15:10:00] ERROR: timeout
[2026-06-25 16:00:00] INFO: done
EOF

# shell-04: archive data
echo "data1" > "$BASE"/archive/file1.txt
echo "data2" > "$BASE"/archive/file2.txt

# shell-05: CSV data
cat > "$BASE"/data.csv << 'EOF'
name,age,score
alice,30,95
bob,25,87
charlie,35,92
diana,28,88
evan,32,91
frank,29,85
grace,31,96
henry,27,90
EOF

# shell-06: empty dirs
mkdir -p "$BASE"/empty_dir1 "$BASE"/empty_dir2
mkdir -p "$BASE"/not_empty
echo "stuff" > "$BASE"/not_empty/file.txt

# shell-07: access log
cat > "$BASE"/access.log << 'EOF'
192.168.1.1 - - [25/Jun/2026:14:23:11] "GET /index.html"
192.168.1.2 - - [25/Jun/2026:14:23:12] "GET /style.css"
192.168.1.1 - - [25/Jun/2026:14:24:01] "POST /login"
10.0.0.1 - - [25/Jun/2026:15:01:22] "GET /api/data"
192.168.1.1 - - [25/Jun/2026:15:02:00] "GET /dashboard"
10.0.0.1 - - [25/Jun/2026:15:10:00] "POST /api/upload"
192.168.1.2 - - [25/Jun/2026:15:11:30] "GET /about"
EOF

# shell-08: Python files with TODO/FIXME
cat > "$BASE"/todo_work.py << 'EOF'
# TODO: refactor this function
def old_func():
    pass
EOF
cat > "$BASE"/fixme_bug.py << 'EOF'
# FIXME: this is broken
def broken():
    raise NotImplementedError
EOF
cat > "$BASE"/clean.py << 'EOF'
def fine():
    return 42
EOF

# shell-09: files for disk usage
dd if=/dev/zero of="$BASE"/logs.bin bs=1024 count=10 2>/dev/null
dd if=/dev/zero of="$BASE"/data.bin bs=1024 count=5 2>/dev/null
echo "small" > "$BASE"/note.txt

# shell-10: duplicates
echo "duplicate content" > "$BASE"/duplicates/a.txt
echo "duplicate content" > "$BASE"/duplicates/b.txt
echo "different" > "$BASE"/duplicates/c.txt
echo "duplicate content" > "$BASE"/duplicates/d.txt

echo "✓ All fixtures created at /tmp/rsibench_*"
echo "  $(ls /tmp/rsibench_* 2>/dev/null | wc -l) fixtures total"

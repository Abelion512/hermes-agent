#!/usr/bin/env python3
"""Experiment status — realtime transparency.

Usage:
    python3 status.py              # one-shot snapshot
    python3 status.py --watch      # auto-refresh every 3s
    cat experiment.status.json     # latest snapshot (written by every run)
"""

import csv, json, sys, time, glob
from pathlib import Path

DATA = Path(__file__).parent / "data" / "experiment.csv"
LOGS = sorted(Path("/tmp").glob("rsi_final*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
LOG = LOGS[0] if LOGS else None
STATUS = DATA.with_suffix(".status.json")


def snapshot() -> dict:
    s = {
        "status": "waiting",
        "total": 180,
        "done": 0, "ok": 0, "fail": 0,
        "conditions": {},
        "latest_task": "",
        "time": time.strftime("%H:%M:%S"),
    }

    # ── From log (realtime, before CSV flush) ──
    if LOG and LOG.exists():
        raw = LOG.read_text().splitlines()
        # Single-line: "Task x... OK (2 calls, ...)"
        for l in raw:
            if "Task " in l and "OK (" in l:
                s["latest_task"] = l.strip()
        # Multi-line: "Task x..." next line "FAIL (3 calls, ...)"
        for i, l in enumerate(raw):
            if "FAIL (" in l and "calls" in l and i > 0:
                prev = raw[i - 1].strip()
                if prev.startswith("Task"):
                    s["latest_task"] = f"{prev}  {l.strip()}"
        if any("Done in" in l for l in raw):
            s["status"] = "completed"
        elif any("=== Run" in l for l in raw):
            s["status"] = "running"

    # ── From CSV (flushed per condition) ──
    if DATA.exists():
        with open(DATA) as f:
            rows = list(csv.DictReader(f))
        s["done"] = len(rows)
        s["ok"] = sum(1 for r in rows if r.get("completed") == "True")
        s["fail"] = sum(1 for r in rows if r.get("completed") == "False")
        for r in rows:
            c = r.get("condition", "?")
            if c not in s["conditions"]:
                s["conditions"][c] = {"total": 0, "ok": 0}
            s["conditions"][c]["total"] += 1
            if r.get("completed") == "True":
                s["conditions"][c]["ok"] += 1
        if s["done"] > 0:
            s["status"] = f"running ({s['done']}/180, {100*s['done']//180}%)"

    return s


if __name__ == "__main__":
    watch = "--watch" in sys.argv or "-w" in sys.argv
    interval = 3

    try:
        while True:
            s = snapshot()
            json.dump(s, open(STATUS, "w"))

            print(f"\n=== RSI Experiment @ {s['time']} ===")
            print(f"  Status: {s['status']}")
            print(f"  Tasks:  {s['ok']} OK / {s['fail']} FAIL / {s['done']} done")
            for c in sorted(s['conditions']):
                v = s['conditions'][c]
                print(f"    {c}: {v['ok']}/{v['total']} OK")
            if s['latest_task']:
                print(f"  Latest: {s['latest_task']}")

            if not watch:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        pass

"""Persistent lesson store — SQLite + FTS5 per-persona.

Spec: IMPLEMENTATION-SPEC.md § 2.1
Stores lessons in ~/.hermes/memory/<persona_id>/lessons.db
"""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

HERMES_HOME = Path.home() / ".hermes"


class MemoryStore:
    """Per-persona persistent lesson store backed by SQLite + FTS5."""

    def __init__(self, persona_id: str = "default"):
        self.persona_id = persona_id
        self._db_path = HERMES_HOME / "memory" / persona_id / "lessons.db"
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._db_path))
            self._conn.row_factory = sqlite3.Row
            self._init_schema()
        return self._conn

    def _init_schema(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS lessons (
                id TEXT PRIMARY KEY,
                persona_id TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                trigger_type TEXT NOT NULL DEFAULT 'unknown',
                trigger_value TEXT NOT NULL DEFAULT '',
                condition_context TEXT,
                action_type TEXT NOT NULL DEFAULT 'instruction',
                action_body TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 0.5,
                evidence_count INTEGER NOT NULL DEFAULT 1,
                success_count INTEGER NOT NULL DEFAULT 0,
                fail_count INTEGER NOT NULL DEFAULT 0,
                source_trace_id TEXT,
                status TEXT NOT NULL DEFAULT 'candidate',
                tags TEXT DEFAULT '[]'
            );
            CREATE INDEX IF NOT EXISTS idx_lessons_persona
                ON lessons(persona_id, status);
            CREATE INDEX IF NOT EXISTS idx_lessons_trigger
                ON lessons(persona_id, trigger_type, trigger_value);
            CREATE INDEX IF NOT EXISTS idx_lessons_confidence
                ON lessons(persona_id, confidence DESC);
            -- FTS5 virtual table for full-text search
            CREATE VIRTUAL TABLE IF NOT EXISTS lessons_fts USING fts5(
                trigger_value, action_body, tags,
                content='lessons',
                content_rowid='rowid',
                tokenize='porter unicode61'
            );
            -- Triggers to keep FTS in sync
            CREATE TRIGGER IF NOT EXISTS lessons_ai AFTER INSERT ON lessons BEGIN
                INSERT INTO lessons_fts(rowid, trigger_value, action_body, tags)
                VALUES (new.rowid, new.trigger_value, new.action_body, new.tags);
            END;
            CREATE TRIGGER IF NOT EXISTS lessons_ad AFTER DELETE ON lessons BEGIN
                INSERT INTO lessons_fts(lessons_fts, rowid, trigger_value, action_body, tags)
                VALUES ('delete', old.rowid, old.trigger_value, old.action_body, old.tags);
            END;
            CREATE TRIGGER IF NOT EXISTS lessons_au AFTER UPDATE ON lessons BEGIN
                INSERT INTO lessons_fts(lessons_fts, rowid, trigger_value, action_body, tags)
                VALUES ('delete', old.rowid, old.trigger_value, old.action_body, old.tags);
                INSERT INTO lessons_fts(rowid, trigger_value, action_body, tags)
                VALUES (new.rowid, new.trigger_value, new.action_body, new.tags);
            END;
        """)
        self._conn.commit()

    # ── CRUD ────────────────────────────────────────────────────────────

    def store_lesson(self, lesson: dict) -> str:
        """Insert or update lesson. Returns lesson_id."""
        lesson_id = lesson.get("id", str(uuid.uuid4()))
        existing = self.conn.execute(
            "SELECT id, confidence, evidence_count FROM lessons WHERE id=?",
            (lesson_id,),
        ).fetchone()

        if existing:
            new_conf = lesson.get("confidence", 0.5)
            old_conf = existing["confidence"]
            if new_conf <= old_conf:
                return lesson_id  # keep existing, not better
            # Update
            self.conn.execute(
                """UPDATE lessons SET
                   confidence=?, evidence_count=evidence_count+1,
                   action_body=?, updated_at=datetime('now')
                   WHERE id=?""",
                (new_conf, lesson.get("action_body", ""), lesson_id),
            )
        else:
            self.conn.execute(
                """INSERT INTO lessons
                   (id, persona_id, trigger_type, trigger_value,
                    condition_context, action_type, action_body,
                    confidence, evidence_count, source_trace_id, status, tags)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    lesson_id,
                    self.persona_id,
                    lesson.get("trigger_type", "unknown"),
                    lesson.get("trigger_value", ""),
                    json.dumps(lesson.get("condition_context", {})),
                    lesson.get("action_type", "instruction"),
                    lesson.get("action_body", lesson.get("content", "")),
                    lesson.get("confidence", 0.5),
                    lesson.get("evidence_count", 1),
                    lesson.get("source_trace_id", ""),
                    lesson.get("status", "active"),
                    json.dumps(lesson.get("tags", [])),
                ),
            )
        self.conn.commit()
        return lesson_id

    def query_lessons(
        self,
        trigger_type: str | None = None,
        trigger_value: str | None = None,
        status: str = "active",
        min_confidence: float = 0.6,
        limit: int = 5,
        search_text: str | None = None,
    ) -> list[dict]:
        """Retrieve top-N most relevant lessons."""
        # Level 1: FTS5 full-text search
        if search_text:
            rows = self.conn.execute(
                """SELECT l.* FROM lessons l
                   JOIN lessons_fts fts ON l.rowid = fts.rowid
                   WHERE lessons_fts MATCH ?
                   AND l.persona_id = ? AND l.status = ?
                   AND l.confidence >= ?
                   ORDER BY rank, l.confidence DESC
                   LIMIT ?""",
                (search_text, self.persona_id, status, min_confidence, limit),
            ).fetchall()
        else:
            # Level 1b: filter by trigger
            where = ["persona_id=?", "status=?", "confidence>=?"]
            params = [self.persona_id, status, min_confidence]
            if trigger_type:
                where.append("trigger_type=?")
                params.append(trigger_type)
            if trigger_value:
                where.append("trigger_value LIKE ?")
                params.append(f"%{trigger_value}%")
            rows = self.conn.execute(
                f"SELECT * FROM lessons WHERE {' AND '.join(where)} "
                f"ORDER BY confidence DESC LIMIT ?",
                params + [limit],
            ).fetchall()

        return [dict(r) for r in rows]

    def get_lesson(self, lesson_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM lessons WHERE id=?", (lesson_id,)
        ).fetchone()
        return dict(row) if row else None

    def update_confidence(self, lesson_id: str, helped: bool) -> None:
        """Update confidence after task run."""
        lesson = self.get_lesson(lesson_id)
        if not lesson:
            return
        if helped:
            self.conn.execute(
                """UPDATE lessons SET
                   success_count=success_count+1,
                   confidence=MIN(1.0, confidence + 0.05),
                   updated_at=datetime('now') WHERE id=?""",
                (lesson_id,),
            )
        else:
            self.conn.execute(
                """UPDATE lessons SET
                   fail_count=fail_count+1,
                   confidence=MAX(0.0, confidence - 0.1),
                   updated_at=datetime('now') WHERE id=?""",
                (lesson_id,),
            )
        # Auto-decay: confidence *= 0.99 per day without use
        self.conn.execute(
            """UPDATE lessons SET confidence=confidence*0.99
               WHERE id=? AND updated_at < datetime('now', '-1 day')""",
            (lesson_id,),
        )
        self.conn.commit()

    def deprecate_lesson(self, lesson_id: str) -> None:
        """Mark as deprecated (confidence < 0.2)."""
        self.conn.execute(
            "UPDATE lessons SET status='deprecated', updated_at=datetime('now') WHERE id=?",
            (lesson_id,),
        )
        self.conn.commit()

    def get_all_active(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM lessons WHERE status='active' ORDER BY confidence DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None


# ── Utils ──────────────────────────────────────────────────────────────

def get_persona_store(persona_id: str) -> MemoryStore:
    """Factory: returns MemoryStore for given persona."""
    return MemoryStore(persona_id)


def lesson_from_candidate(candidate: dict) -> dict:
    """Convert experiment candidate dict to store-ready lesson dict."""
    return {
        "action_body": candidate.get("content", ""),
        "confidence": candidate.get("confidence", 0.6),
        "source_trace_id": candidate.get("source_tool", ""),
        "trigger_type": "error",
        "trigger_value": candidate.get("source_tool", "unknown"),
        "tags": ["rsi_exp", candidate.get("source_tool", "")],
        "status": "active",
    }

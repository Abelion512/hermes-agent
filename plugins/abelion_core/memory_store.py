import os
import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from hermes_constants import get_hermes_home

logger = logging.getLogger(__name__)

def get_db_path() -> Path:
    """
    Returns the absolute path to the experience FTS database.
    Ensures parent directories exist.
    """
    mem_dir = get_hermes_home() / "memories"
    mem_dir.mkdir(parents=True, exist_ok=True)
    return mem_dir / "experience_fts.db"

def init_db():
    """
    Initializes the SQLite database with FTS5 virtual table.
    Ensures that if the DB file is empty or corrupted (e.g. table experiences is missing),
    it is repaired/recreated.
    """
    db_path = get_db_path()
    
    # Check if DB needs repair/recreation (0 bytes or missing table)
    recreate = False
    if db_path.exists():
        if db_path.stat().st_size == 0:
            recreate = True
            logger.warning(f"[abelion_core.memory_store] DB file is 0 bytes, marking for recreation: {db_path}")
        else:
            conn = sqlite3.connect(db_path)
            try:
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='experiences'")
                if not cur.fetchone():
                    recreate = True
                    logger.warning(f"[abelion_core.memory_store] Table 'experiences' is missing, marking for recreation: {db_path}")
            except Exception as e:
                recreate = True
                logger.warning(f"[abelion_core.memory_store] DB check failed ({e}), marking for recreation: {db_path}")
            finally:
                conn.close()
                
    if recreate:
        try:
            db_path.unlink(missing_ok=True)
            logger.info(f"[abelion_core.memory_store] Removed invalid/empty DB file: {db_path}")
        except Exception as e:
            logger.error(f"[abelion_core.memory_store] Failed to remove DB file: {e}")

    conn = sqlite3.connect(db_path)
    try:
        # FTS5 virtual table for experiences
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS experiences USING fts5(
                session_id UNINDEXED,
                timestamp UNINDEXED,
                summary,
                status,
                errors,
                lessons,
                recommendations,
                raw_content
            )
        """)
        conn.commit()
    except Exception as e:
        logger.error(f"[abelion_core.memory_store] Failed to initialize FTS5 table: {e}")
    finally:
        conn.close()

def save_experience(session_id: str, reflection_data: dict):
    """
    Persists experience reflection data into the FTS5 database.
    """
    init_db()  # Ensure DB and table exist
    
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    try:
        timestamp = datetime.utcnow().isoformat()
        
        # Extract fields
        summary = reflection_data.get("summary", "")
        status = reflection_data.get("status", "")
        
        # Flatten lists to text
        errors_list = reflection_data.get("errors", [])
        errors = "\n".join(errors_list) if isinstance(errors_list, list) else str(errors_list)
        
        lessons_list = reflection_data.get("lessons", [])
        lessons = "\n".join(lessons_list) if isinstance(lessons_list, list) else str(lessons_list)
        
        recs_list = reflection_data.get("recommendations", [])
        recommendations = "\n".join(recs_list) if isinstance(recs_list, list) else str(recs_list)
        
        raw_content = reflection_data.get("raw_text", json.dumps(reflection_data))

        conn.execute(
            """
            INSERT INTO experiences (session_id, timestamp, summary, status, errors, lessons, recommendations, raw_content)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, timestamp, summary, status, errors, lessons, recommendations, raw_content)
        )
        conn.commit()
        logger.info(f"[abelion_core.memory_store] Successfully saved FTS experience for session {session_id}")

        # Periodic DB optimization (every 50 records)
        try:
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM experiences")
            row_count = cur.fetchone()[0]
            if row_count > 0 and row_count % 50 == 0:
                logger.info(f"[abelion_core.memory_store] Running periodic database optimization (count: {row_count})...")
                # SQLite VACUUM requires autocommit or no transaction.
                # Since we committed above, executing it is safe.
                conn.isolation_level = None
                conn.execute("VACUUM")
                conn.execute("PRAGMA optimize")
                logger.info("[abelion_core.memory_store] Database optimization completed.")
        except Exception as oe:
            logger.warning(f"[abelion_core.memory_store] Periodic database optimization failed: {oe}")
    except Exception as e:
        logger.error(f"[abelion_core.memory_store] Failed to save experience: {e}")
    finally:
        conn.close()

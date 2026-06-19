import os
import json
import logging
from datetime import datetime
from pathlib import Path
from hermes_constants import get_hermes_home

logger = logging.getLogger(__name__)

def get_link_log_path():
    return get_hermes_home() / "memories" / "link.jsonl"

def track_link(url, title=None, status="fresh"):
    """
    Appends or updates a link entry in memories/link.jsonl.
    """
    log_path = get_link_log_path()
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"[abelion_core.link] Failed to create directories for link.jsonl: {e}")
        return False

    now_str = datetime.utcnow().isoformat()
    entry = {
        "url": url,
        "timestamp": now_str,
        "title": title or "",
        "status": status,
        "last_checked": now_str
    }

    # Read existing entries to avoid duplicates and allow updates
    entries = []
    found = False
    if log_path.exists():
        try:
            with open(log_path, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        item = json.loads(line)
                        if item.get("url") == url:
                            # Update existing entry preserving initial timestamp if possible
                            item["title"] = title or item.get("title", "")
                            item["status"] = status
                            item["last_checked"] = now_str
                            found = True
                        entries.append(item)
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"[abelion_core.link] Failed to read link.jsonl: {e}")

    if not found:
        entries.append(entry)

    # Write back
    try:
        with open(log_path, "w") as f:
            for item in entries:
                f.write(json.dumps(item) + "\n")
        logger.debug(f"[abelion_core.link] Tracked link: {url} (status: {status})")
        return True
    except Exception as e:
        logger.error(f"[abelion_core.link] Failed to write link.jsonl: {e}")
        return False

def get_link_status(url):
    """
    Retrieves the status of a tracked URL. Returns None if not tracked.
    """
    log_path = get_link_log_path()
    if not log_path.exists():
        return None

    try:
        with open(log_path, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                    if item.get("url") == url:
                        return item
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"[abelion_core.link] Failed to read link.jsonl: {e}")
    return None

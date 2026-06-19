import os
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_VAULT_PATH = Path("/home/abelion/Downloads/HermesVault")

def export_session_to_obsidian(session_id, final_record, vault_path=None):
    """
    Exports the recorded reflection data to a Markdown file in the Obsidian vault.
    """
    if not vault_path:
        vault_path = DEFAULT_VAULT_PATH

    try:
        os.makedirs(vault_path, exist_ok=True)
    except Exception as e:
        logger.error(f"[abelion_core.obsidian] Failed to create Obsidian vault directory: {e}")
        return False

    reflection = final_record.get("reflection", {})
    summary = reflection.get("summary", "No summary provided.")
    status = reflection.get("status", "unknown")
    errors = reflection.get("errors", [])
    lessons = reflection.get("lessons", [])
    recs = reflection.get("recommendations", [])
    timestamp = final_record.get("timestamp", datetime.utcnow().isoformat())
    model = final_record.get("model_used", "unknown")

    # Construct YAML frontmatter
    md_content = f"""---
session_id: "{session_id}"
timestamp: "{timestamp}"
status: "{status}"
model: "{model}"
tags:
  - hermes-experience
  - status/{status}
---

# Session Reflection: {summary[:100]}

**Date:** {timestamp}
**Status:** `{status.upper()}`
**Model Used:** `{model}`

## 📝 Summary
{summary}

"""

    if errors:
        md_content += "## ❌ Errors Encountered\n"
        for err in errors:
            md_content += f"- {err}\n"
        md_content += "\n"

    if lessons:
        md_content += "## 💡 Lessons Learned\n"
        for lesson in lessons:
            md_content += f"- {lesson}\n"
        md_content += "\n"

    if recs:
        md_content += "## 📋 Recommendations\n"
        for rec in recs:
            md_content += f"- {rec}\n"
        md_content += "\n"

    # Save to vault
    safe_summary = "".join([c for c in summary[:50] if c.isalnum() or c in (" ", "_", "-")]).strip()
    safe_summary = safe_summary.replace(" ", "_")
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_summary}_{session_id[:8]}.md"
    filepath = vault_path / filename

    try:
        with open(filepath, "w") as f:
            f.write(md_content)
        logger.info(f"[abelion_core.obsidian] Successfully exported reflection to Obsidian: {filepath}")
        return True
    except Exception as e:
        logger.error(f"[abelion_core.obsidian] Failed to write markdown file: {e}")
        return False

import os
import uuid
import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from hermes_constants import get_hermes_home

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = get_hermes_home() / "abelion" / "data_chat"

def export_all_sessions_to_olivxos(output_dir=None, db_path=None, filename_format="dataset_{timestamp}.jsonl"):
    """
    Reads sessions and messages from Hermes state.db and exports them to OlivXOS JSON/JSONL schema.
    """
    if not output_dir:
        output_dir = DEFAULT_OUTPUT_DIR
    if not db_path:
        db_path = get_hermes_home() / "state.db"

    if not db_path.exists():
        logger.error(f"[abelion_core.dataset] State database not found at {db_path}")
        return {"success": False, "error": f"Database not found at {db_path}"}

    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        logger.error(f"[abelion_core.dataset] Failed to create output directory: {e}")
        return {"success": False, "error": str(e)}

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Query all active/archived sessions
        cursor.execute("SELECT id, title, user_id, started_at, model FROM sessions ORDER BY started_at DESC")
        sessions_rows = cursor.fetchall()

        dataset = []

        for s_row in sessions_rows:
            session_id = s_row["id"]
            title = s_row["title"] or f"Session {session_id[:8]}"
            user_id = s_row["user_id"] or str(uuid.uuid4())
            model_used = s_row["model"] or "unknown"
            started_at = int(s_row["started_at"])

            # Query all active messages in this session
            cursor.execute(
                "SELECT id, role, content, reasoning, timestamp FROM messages "
                "WHERE session_id = ? AND active = 1 ORDER BY timestamp ASC",
                (session_id,)
            )
            msg_rows = cursor.fetchall()

            if not msg_rows:
                continue

            # Build the messages mapping and tree structure
            messages_dict = {}
            messages_list = []
            
            # Generate UUIDs for each message to match OlivXOS format
            msg_id_map = {row["id"]: str(uuid.uuid4()) for row in msg_rows}

            for idx, row in enumerate(msg_rows):
                db_id = row["id"]
                current_uuid = msg_id_map[db_id]
                role = row["role"]
                content = row["content"] or ""
                reasoning = row["reasoning"] or None
                timestamp = int(row["timestamp"])

                parent_uuid = msg_id_map[msg_rows[idx-1]["id"]] if idx > 0 else None
                child_uuids = [msg_id_map[msg_rows[idx+1]["id"]]] if idx < len(msg_rows) - 1 else []

                msg_obj = {
                    "id": current_uuid,
                    "role": role,
                    "content": content,
                    "models": [model_used],
                    "chat_type": "chat",
                    "sub_chat_type": "chat",
                    "edited": False,
                    "error": None,
                    "parentId": parent_uuid,
                    "childrenIds": child_uuids,
                    "files": [],
                    "timestamp": timestamp
                }

                if role == "assistant":
                    # Add reasoning content if present
                    msg_obj["reasoning_content"] = reasoning
                    msg_obj["model"] = model_used
                    msg_obj["modelName"] = model_used.split("/")[-1] if "/" in model_used else model_used
                    msg_obj["modelIdx"] = 0
                    msg_obj["content_list"] = [
                        {
                            "content": content,
                            "phase": "answer",
                            "status": "finished",
                            "extra": None,
                            "role": "assistant",
                            "response_id": current_uuid,
                            "timestamp": timestamp
                        }
                    ]
                    if reasoning:
                        # Prepend thinking phase if there's reasoning
                        msg_obj["content_list"].insert(0, {
                            "content": reasoning,
                            "phase": "think",
                            "status": "finished",
                            "extra": None,
                            "role": "assistant",
                            "response_id": current_uuid,
                            "timestamp": timestamp
                        })

                messages_dict[current_uuid] = msg_obj
                messages_list.append(current_uuid)

            session_record = {
                "id": session_id,
                "user_id": user_id,
                "title": title,
                "chat": {
                    "history": {
                        "messages": messages_dict,
                        "currentId": messages_list[-1] if messages_list else None,
                        "currentResponseIds": [messages_list[-1]] if messages_list and messages_dict[messages_list[-1]]["role"] == "assistant" else []
                    },
                    "models": [model_used],
                    "messages": messages_list
                }
            }

            dataset.append(session_record)

        conn.close()

        timestamp_str = datetime.now().strftime("%Y%m%d")
        fname = filename_format.format(timestamp=timestamp_str)
        output_file = output_dir / fname

        if fname.endswith(".jsonl"):
            # Write line by line for safety and memory efficiency
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2)

        logger.info(f"[abelion_core.dataset] Exported {len(dataset)} sessions to {output_file}")
        return {"success": True, "file": str(output_file), "count": len(dataset)}

    except Exception as e:
        logger.error(f"[abelion_core.dataset] Failed to export database: {e}")
        return {"success": False, "error": str(e)}

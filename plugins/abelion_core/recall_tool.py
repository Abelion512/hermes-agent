import sqlite3
import json
import math
import logging
from datetime import datetime
from .memory_store import get_db_path
from .query_expander import expand_query

logger = logging.getLogger(__name__)

def register_recall_tool(ctx):
    schema = {
        "name": "recall_experience",
        "description": "Recall past failure or success experiences, including lessons learned, errors, and recommended procedures for similar tasks.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The current error, task description, or keywords to search for past experiences (e.g. 'oom error', 'telegram bot setup', 'flux image generation').",
                }
            },
            "required": ["query"],
        },
    }

    def handler(args, **kwargs):
        query = args.get("query", "").strip()
        if not query:
            return json.dumps({"status": "error", "message": "Query parameter cannot be empty."})

        # 1. Expand query with synonyms
        fts_query = expand_query(query)
        if not fts_query:
            return json.dumps({"status": "no_experience", "results": [], "message": "No searchable tokens extracted from query."})

        db_path = get_db_path()
        if not db_path.exists():
            return json.dumps({"status": "no_experience", "results": [], "message": "No experience database exists yet."})

        # 2. Search SQLite FTS5
        conn = sqlite3.connect(db_path)
        candidates = []
        try:
            cur = conn.cursor()
            # FTS5 returns lower bm25() score for better matches (more negative)
            cur.execute(
                """
                SELECT session_id, timestamp, summary, status, errors, lessons, recommendations, raw_content, bm25(experiences)
                FROM experiences
                WHERE experiences MATCH ?
                """,
                (fts_query,)
            )
            
            for row in cur.fetchall():
                session_id, timestamp_str, summary, status, errors, lessons, recommendations, raw_content, score = row
                
                # Parse timestamp and compute days old
                try:
                    dt = datetime.fromisoformat(timestamp_str)
                    days_old = (datetime.utcnow() - dt).days
                except Exception:
                    days_old = 0

                # Convert negative score to positive, calculate decay
                bm25_score = -score
                decay = math.exp(-0.05 * max(0, days_old))
                decay_score = bm25_score * decay

                # Parse errors/lessons back to lists if they are multiline strings
                errors_list = [line.strip() for line in errors.split("\n") if line.strip()] if errors else []
                lessons_list = [line.strip() for line in lessons.split("\n") if line.strip()] if lessons else []

                candidates.append({
                    "session_id": session_id,
                    "timestamp": timestamp_str,
                    "summary": summary,
                    "status": status,
                    "errors": errors_list,
                    "lessons": lessons_list,
                    "recommendations": recommendations,
                    "decay_score": decay_score
                })
        except Exception as e:
            logger.error(f"[abelion_core.recall] Search query failed: {e}")
            return json.dumps({"status": "error", "message": f"Search failed: {e}"})
        finally:
            conn.close()

        if not candidates:
            return json.dumps({
                "status": "no_experience",
                "results": [],
                "message": f"No past experiences matched query tokens: '{fts_query}'"
            })

        # Sort candidates by decay score descending, take top 5
        candidates.sort(key=lambda x: x["decay_score"], reverse=True)
        top_candidates = candidates[:5]

        # 3. LLM Reranking
        candidates_str = ""
        for i, c in enumerate(top_candidates):
            candidates_str += f"Candidate [{i+1}]:\n"
            candidates_str += f"- Session ID: {c['session_id']}\n"
            candidates_str += f"- Summary: {c['summary']}\n"
            candidates_str += f"- Status: {c['status']}\n"
            candidates_str += f"- Errors: {', '.join(c['errors']) if c['errors'] else 'None'}\n"
            candidates_str += f"- Lessons: {', '.join(c['lessons']) if c['lessons'] else 'None'}\n"
            candidates_str += f"- Recommendations: {c['recommendations']}\n\n"

        prompt = f"""You are an intelligent Assistant Memory Reranker. Your task is to select and summarize the most relevant past experiences (failures or successes) that match the current query.

Current Query: {query}

List of Candidate Memories:
{candidates_str}

Evaluate the relevance of each candidate to the Current Query.
Output a JSON array containing up to 3 most relevant memories. Format each memory object in the array with these keys:
- "session_id": string
- "summary": string (brief summary)
- "status": string (success, failure, or partial)
- "errors": list of strings
- "lessons": list of strings
- "relevance_reason": string (why this memory is highly relevant to the current problem)

Your response MUST be ONLY the raw JSON array (enclosed in []). Do not include any explanation or markdown formatting like ```json.
"""

        try:
            if hasattr(ctx, "llm") and ctx.llm is not None:
                rerank_res = ctx.llm.complete(
                    messages=[{"role": "user", "content": prompt}],
                    purpose="recall_reranking"
                )
                text = rerank_res.text.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()

                final_results = json.loads(text)
                if not isinstance(final_results, list):
                    final_results = top_candidates[:3]
            else:
                logger.warning("[abelion_core.recall] PluginContext lacks 'llm' facade. Falling back to FTS top candidates.")
                final_results = top_candidates[:3]
        except Exception as e:
            logger.warning(f"[abelion_core.recall] LLM Reranking failed or returned invalid JSON: {e}. Falling back to top candidates.")
            final_results = top_candidates[:3]

        return json.dumps({
            "status": "success",
            "results": final_results
        })

    ctx.register_tool(
        name="recall_experience",
        toolset="abelion_core",
        schema=schema,
        handler=handler,
    )
    logger.info("[abelion_core] Registered tool 'recall_experience'")

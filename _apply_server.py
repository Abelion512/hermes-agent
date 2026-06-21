#!/usr/bin/env python3
"""Apply all server changes: save articles, trust scoring, summarize fix."""

path = '/media/abelion/Wave/.hermes/profiles/enami-asa/scripts/news-agent/news-server.py'
with open(path, 'r') as f:
    content = f.read()

# === 1. Add SAVED_FILE + TRUST_LEVELS constants ===
old = 'BOOKMARKS_FILE = os.path.join(_HERMES_HOME, "references", "bookmarks.json")'
new = '''BOOKMARKS_FILE = os.path.join(_HERMES_HOME, "references", "bookmarks.json")
SAVED_FILE = os.path.join(_HERMES_HOME, "references", "saved.json")

# Source trust levels (1-5): higher = more editorial rigor / fact-checking
TRUST_LEVELS = {
    "ArXiv": 5, "MIT Tech Review": 5,
    "The Verge": 4, "Ars Technica": 4, "Wired": 4, "TechCrunch": 4,
    "HackerNews": 3, "Dev.to": 3, "Reddit": 3, "GitHub": 3,
    "Cryptowave": 3,
    "X": 1,
}
DEFAULT_TRUST = 3'''
content = content.replace(old, new, 1)

# === 2. Add GET /api/saved route ===
old = '''        elif self.path == "/api/bookmarks":
            self._serve_bookmarks()'''
new = '''        elif self.path == "/api/bookmarks":
            self._serve_bookmarks()
        elif self.path == "/api/saved":
            self._serve_saved()'''
content = content.replace(old, new, 1)

# === 3. Add POST /api/saved route ===
old = '''        elif self.path == "/api/process-comment":
            self._process_comment()'''
new = '''        elif self.path == "/api/saved":
            self._save_article()
        elif self.path == "/api/process-comment":
            self._process_comment()'''
content = content.replace(old, new, 1)

# === 4. Add DELETE /api/saved route ===
old = '''        elif self.path.startswith("/api/comments"):
            self._delete_comment()'''
new = '''        elif self.path.startswith("/api/saved"):
            self._unsave_article()
        elif self.path.startswith("/api/comments"):
            self._delete_comment()'''
content = content.replace(old, new, 1)

# === 5. Enhance for_you scoring with trust weight ===
old = '''            if sort_by == "for_you":
                # Sort by personal score descending (likes first, then source affinity)
                scored.sort(key=lambda a: a.get("_score", 0), reverse=True)'''
new = '''            # Attach trust level to each article for UI
            for art in scored:
                art["_trust"] = TRUST_LEVELS.get(art.get("blog", ""), DEFAULT_TRUST)

            if sort_by == "for_you":
                def fyp_score(a):
                    s = a.get("_score", 0)
                    if isinstance(s, str):
                        s = 0
                    trust = a.get("_trust", DEFAULT_TRUST)
                    s += (trust - 3) * 0.5
                    return s
                scored.sort(key=fyp_score, reverse=True)'''
content = content.replace(old, new, 1)

# === 6. Add saved articles methods before _send_json ===
old = '''    def _send_json(self, data, status=200):'''
new = '''    # --- Saved Articles (persistent data storage) ---

    def _load_saved(self):
        if os.path.exists(SAVED_FILE):
            try:
                with open(SAVED_FILE) as f:
                    return json.load(f)
            except Exception:
                pass
        return {"saved": [], "updated_at": ""}

    def _serve_saved(self):
        """GET /api/saved — return all saved articles."""
        self._send_json(self._load_saved())

    def _save_article(self):
        """POST /api/saved  body: {id} — save full article data persistently."""
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            aid = body.get("id", "").strip()
            if not aid:
                self._send_json({"error": "id required"}, status=400)
                return

            article = None
            if os.path.exists(JSONL):
                with open(JSONL) as f:
                    for line in f:
                        try:
                            art = json.loads(line.strip())
                            if art.get("id") == aid:
                                article = art
                                break
                        except Exception:
                            pass
            if not article:
                self._send_json({"error": "Article not found"}, status=404)
                return

            saved_data = self._load_saved()
            saved_ids = [s["id"] for s in saved_data.get("saved", [])]
            if aid in saved_ids:
                self._send_json({"ok": True, "action": "already_saved", "saved": saved_data})
                return

            saved_entry = {
                "id": article.get("id"),
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "blog": article.get("blog", ""),
                "published_date": article.get("published_date", ""),
                "_collected_at": article.get("_collected_at", ""),
                "summary": article.get("summary", ""),
                "tags": article.get("tags", []),
                "_keywords": article.get("_keywords", []),
                "_score": article.get("_score", 0),
                "saved_at": datetime.now(timezone.utc).isoformat(),
            }
            saved_data.setdefault("saved", []).append(saved_entry)
            saved_data["updated_at"] = datetime.now(timezone.utc).isoformat()

            os.makedirs(os.path.dirname(SAVED_FILE), exist_ok=True)
            with open(SAVED_FILE, "w") as f:
                json.dump(saved_data, f, ensure_ascii=False, indent=2)

            self._send_json({"ok": True, "action": "saved", "saved": saved_data})
            print(f"\\U0001f4be Saved article: {article.get('title', '?')[:60]}")
        except Exception as e:
            self._send_json({"error": str(e)}, status=500)

    def _unsave_article(self):
        """DELETE /api/saved?id=x — remove a saved article."""
        try:
            params = parse_qs(urlparse(self.path).query)
            aid = params.get("id", [""])[0].strip()
            if not aid:
                self._send_json({"error": "id required"}, status=400)
                return

            saved_data = self._load_saved()
            before = len(saved_data.get("saved", []))
            saved_data["saved"] = [s for s in saved_data.get("saved", []) if s.get("id") != aid]
            after = len(saved_data["saved"])
            saved_data["updated_at"] = datetime.now(timezone.utc).isoformat()

            with open(SAVED_FILE, "w") as f:
                json.dump(saved_data, f, ensure_ascii=False, indent=2)

            self._send_json({"ok": True, "removed": before > after, "saved": saved_data})
            if before > after:
                print(f"\\U0001f5d1\\ufe0f Unsaved article: {aid}")
        except Exception as e:
            self._send_json({"error": str(e)}, status=500)

    def _send_json(self, data, status=200):'''
content = content.replace(old, new, 1)

# === 7. Fix summarize with multi-model fallback ===
old_sum = '''            # Use local proxy with OpenRouter free model
            api_key = ""
            base_url = "http://localhost:20128/v1"
            model_id = "openrouter/free"
            env_path = os.path.join(_HERMES_HOME, ".env")
            if os.path.exists(env_path):
                with open(env_path) as f:
                    for line in f:
                        if line.startswith("NINEROUTER_API_KEY="):
                            api_key = line.split("=", 1)[1].strip()
                            break

            if not api_key:
                self._send_json({"error": "OPENROUTER_API_KEY not configured"}, status=500)
                return

            # Call LLM API
            from urllib.request import Request as URRequest
            chat_url = f"{base_url}/chat/completions" if not base_url.endswith("/") else f"{base_url}chat/completions"
            req_body = json.dumps({
                "model": model_id,
                "messages": [
                    {"role": "system", "content": "You are a news summarization assistant. Summarize concisely in Indonesian."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.3,
                "stream": False
            }).encode()
            req = URRequest(chat_url)
            req.add_header("Authorization", f"Bearer {api_key}")
            req.add_header("Content-Type", "application/json")
            req.add_header("HTTP-Referer", "http://localhost:9999")

            from urllib.request import urlopen as _urlopen
            with _urlopen(req, data=req_body, timeout=120) as resp:
                raw = resp.read().decode()
                # Handle SSE streaming format (data: {...}\\n\\ndata: [DONE])
                if "data:" in raw and "\\n" in raw:
                    chunks = []
                    for line in raw.split("\\n"):
                        line = line.strip()
                        if line.startswith("data:") and "[DONE]" not in line:
                            try:
                                chunk = json.loads(line[5:].strip())
                                delta = chunk.get("choices", [{}])[0].get("delta", {})
                                chunks.append(delta.get("content") or delta.get("reasoning_content") or "")
                            except Exception:
                                pass
                    summary = "".join(chunks)
                else:
                    # Single JSON response (may have trailing data, parse first object)
                    try:
                        result = json.loads(raw)
                    except json.JSONDecodeError:
                        # Find the end of first JSON object
                        depth = 0
                        end = 0
                        for i, c in enumerate(raw):
                            if c == '{': depth += 1
                            elif c == '}': depth -= 1
                            if depth == 0 and i > 0:
                                end = i + 1
                                break
                        result = json.loads(raw[:end]) if end else json.loads(raw)
                    msg = result.get("choices", [{}])[0].get("message", {})
                    summary = msg.get("content") or msg.get("reasoning_content") or "No summary generated."

            self._send_json({"ok": True, "summary": summary, "articles": len(articles)})'''

new_sum = '''            api_key = ""
            base_url = "http://localhost:20128/v1"
            model_ids = ["openrouter/free", "free", "groq/llama-3.3-70b-versatile"]
            env_path = os.path.join(_HERMES_HOME, ".env")
            if os.path.exists(env_path):
                with open(env_path) as f:
                    for line in f:
                        if line.startswith("NINEROUTER_API_KEY="):
                            api_key = line.split("=", 1)[1].strip()
                            break

            if not api_key:
                self._send_json({"error": "API key not configured"}, status=500)
                return

            from urllib.request import Request as URRequest, urlopen as _urlopen
            from urllib.error import HTTPError
            chat_url = f"{base_url}/chat/completions" if not base_url.endswith("/") else f"{base_url}chat/completions"
            summary = None
            last_err = None

            for model_id in model_ids:
                try:
                    req_body = json.dumps({
                        "model": model_id,
                        "messages": [
                            {"role": "system", "content": "You are a news summarization assistant. Summarize concisely in Indonesian."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 2000,
                        "temperature": 0.3,
                        "stream": False
                    }).encode()
                    req = URRequest(chat_url)
                    req.add_header("Authorization", f"Bearer {api_key}")
                    req.add_header("Content-Type", "application/json")
                    req.add_header("HTTP-Referer", "http://localhost:9999")

                    with _urlopen(req, data=req_body, timeout=120) as resp:
                        raw = resp.read().decode()
                        if "data:" in raw and "\\n" in raw:
                            chunks = []
                            for ln in raw.split("\\n"):
                                ln = ln.strip()
                                if ln.startswith("data:") and "[DONE]" not in ln:
                                    try:
                                        ch = json.loads(ln[5:].strip())
                                        delta = ch.get("choices", [{}])[0].get("delta", {})
                                        chunks.append(delta.get("content") or delta.get("reasoning_content") or "")
                                    except Exception:
                                        pass
                            summary = "".join(chunks)
                        else:
                            try:
                                result = json.loads(raw)
                            except json.JSONDecodeError:
                                depth = 0
                                end = 0
                                for i, c in enumerate(raw):
                                    if c == '{': depth += 1
                                    elif c == '}': depth -= 1
                                    if depth == 0 and i > 0:
                                        end = i + 1
                                        break
                                result = json.loads(raw[:end]) if end else json.loads(raw)
                            msg = result.get("choices", [{}])[0].get("message", {})
                            summary = msg.get("content") or msg.get("reasoning_content") or ""
                    if summary:
                        break
                except HTTPError as e:
                    last_err = e
                    continue
                except Exception as e:
                    last_err = e
                    continue

            if not summary:
                err_msg = str(last_err) if last_err else "No response from any model"
                self._send_json({"error": f"LLM unavailable: {err_msg}"}, status=502)
                return

            self._send_json({"ok": True, "summary": summary, "articles": len(articles)})'''

content = content.replace(old_sum, new_sum, 1)

with open(path, 'w') as f:
    f.write(content)

print('Server changes applied successfully!')

import json
import os
import shutil
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from plugins.abelion_core.reflection import record_reflection
from plugins.abelion_core import pre_tool_hook, pre_llm_hook
from plugins.abelion_core.circuit_breaker import State, get_breaker
from plugins.abelion_core.obsidian_exporter import export_session_to_obsidian
from plugins.abelion_core.link_tracker import track_link, get_link_status
from plugins.abelion_core.ram_monitor import enforce_ram_guard


class DummyLLMResult:
    def __init__(self, text):
        self.text = text
        self.model = "test-model"
        self.provider = "test-provider"


class DummyLLM:
    def complete(self, messages, purpose):
        return DummyLLMResult(
            '{"summary": "Test failure", "status": "failure", "errors": ["Mock error"], "lessons": [], "recommendations": []}'
        )


class DummyCtx:
    def __init__(self):
        self.llm = DummyLLM()


class TestAbelionErrorHandler(unittest.TestCase):
    def setUp(self):
        # Reset circuit breaker
        self.breaker = get_breaker("delegation")
        self.breaker.failures = 0
        self.breaker.state = State.CLOSED

        # Temporary directory for tests
        self.test_dir = Path(tempfile.mkdtemp())
        self.reflections_dir = self.test_dir / "docs/abelion/reflections"
        os.makedirs(self.reflections_dir, exist_ok=True)

        # Patch paths
        self.patcher_project = patch("plugins.abelion_core.reflection.RESEARCH_DATA_DIR", self.reflections_dir)
        self.patcher_project.start()

    def tearDown(self):
        self.patcher_project.stop()
        shutil.rmtree(self.test_dir)

    def test_01_circuit_breaker_trip(self):
        """Proof that the circuit breaker correctly opens after thresholds and blocks tools."""
        self.breaker.record_failure()
        self.breaker.record_failure()
        self.breaker.record_failure()

        self.assertEqual(self.breaker.state, State.OPEN)
        self.assertFalse(self.breaker.allow_request())

        result = pre_tool_hook("delegate_task", {"goal": "test"})
        self.assertIsNotNone(result)
        self.assertEqual(result.get("action"), "block")
        self.assertIn("Circuit Breaker OPEN", result.get("message"))

    def test_02_rsi_reflection_writing(self):
        """Proof that error reflections are correctly written to the isolated directory."""
        ctx = DummyCtx()

        record_reflection(
            ctx,
            session_id="test_error_session",
            messages=[
                {"role": "user", "content": "do task"},
                {"role": "assistant", "content": "I failed"},
            ],
        )

        files = list(self.reflections_dir.glob("reflection_*.json"))
        self.assertTrue(len(files) > 0, "Reflection file was not created!")

        with open(files[0], "r") as f:
            data = json.load(f)

        self.assertEqual(data["session_id"], "test_error_session")
        self.assertEqual(data["reflection"]["status"], "failure")
        self.assertEqual(data["reflection"]["errors"][0], "Mock error")

    def test_03_obsidian_exporter(self):
        """Proof that Obsidian exporter writes structured Markdown file with frontmatter."""
        vault = self.test_dir / "ObsidianVault"
        record = {
            "timestamp": "2026-06-18T12:00:00Z",
            "model_used": "test-model",
            "reflection": {
                "summary": "Implement active RAG cap",
                "status": "success",
                "errors": [],
                "lessons": ["Keep it lightweight"],
                "recommendations": []
            }
        }
        
        success = export_session_to_obsidian("session_123", record, vault_path=vault)
        self.assertTrue(success)
        
        files = list(vault.glob("*.md"))
        self.assertEqual(len(files), 1)
        
        with open(files[0], "r") as f:
            content = f.read()
            
        self.assertIn('session_id: "session_123"', content)
        self.assertIn('status: "success"', content)
        self.assertIn('## 📝 Summary', content)
        self.assertIn('Implement active RAG cap', content)
        self.assertIn('💡 Lessons Learned', content)
        self.assertIn('Keep it lightweight', content)

    @patch("plugins.abelion_core.link_tracker.get_link_log_path")
    def test_04_link_tracker(self, mock_get_path):
        """Proof that URL link logger writes and updates in JSONL format."""
        temp_log = self.test_dir / "link.jsonl"
        mock_get_path.return_value = temp_log
        
        # Track initial
        success = track_link("https://google.com", "Google Search", "fresh")
        self.assertTrue(success)
        
        # Verify contents
        status = get_link_status("https://google.com")
        self.assertIsNotNone(status)
        self.assertEqual(status["title"], "Google Search")
        self.assertEqual(status["status"], "fresh")
        
        # Update status
        track_link("https://google.com", "Google Search Updated", "outdated")
        status_updated = get_link_status("https://google.com")
        self.assertEqual(status_updated["status"], "outdated")
        self.assertEqual(status_updated["title"], "Google Search Updated")

    def test_05_rag_iteration_limit(self):
        """Proof that RAG search calls are blocked after the 3rd iteration."""
        from plugins.abelion_core import _rag_calls_count
        session_id = "rag_test_session"
        _rag_calls_count[session_id] = 0
        
        # 3 successful calls
        for _ in range(3):
            res = pre_tool_hook("knowledge_search", {"query": "test"}, session_id=session_id)
            self.assertIsNone(res)
            
        # 4th call should be blocked
        res = pre_tool_hook("knowledge_search", {"query": "test"}, session_id=session_id)
        self.assertIsNotNone(res)
        self.assertEqual(res.get("action"), "block")
        self.assertIn("Capping RAG search iterations", res.get("message"))

    @patch("plugins.abelion_core.ram_monitor.get_system_ram_percent")
    @patch("plugins.abelion_core.ram_monitor.get_hermes_rss_bytes")
    def test_06_ram_monitor_guard(self, mock_rss, mock_sys_ram):
        """Proof that RAM Guard triggers GC and blocks heavy tools when RAM is critical."""
        # Scenario: RAM is >80%, Hermes using lots of memory
        mock_sys_ram.return_value = 85
        mock_rss.return_value = 600 * 1024 * 1024  # 600 MB
        
        is_critical = enforce_ram_guard()
        self.assertTrue(is_critical)
        
        # Verify heavy tool blocking
        res_heavy = pre_tool_hook("run_command", {"CommandLine": "ls"}, session_id="test_sess")
        self.assertIsNotNone(res_heavy)
        self.assertEqual(res_heavy.get("action"), "block")
        self.assertIn("System RAM usage is critical", res_heavy.get("message"))
        
        # Verify lightweight tool NOT blocked
        res_light = pre_tool_hook("view_file", {"AbsolutePath": "/dummy"}, session_id="test_sess")
        self.assertIsNone(res_light)

    def test_07_query_expansion(self):
        """Proof that query_expander tokenizes and expands query with synonyms correctly."""
        from plugins.abelion_core.query_expander import expand_query
        
        # Test basic expansion
        expanded = expand_query("dc crash")
        self.assertIn("discord", expanded)
        self.assertIn("dc", expanded)
        self.assertIn("crash*", expanded)
        
        # Test multiple slang expansion
        expanded_multi = expand_query("oom dc problem")
        self.assertIn("out of memory", expanded_multi)
        self.assertIn("discord", expanded_multi)
        self.assertIn("problem*", expanded_multi)

        # Test ig expands to instagram
        expanded_ig = expand_query("ig update")
        self.assertIn("instagram", expanded_ig)
        self.assertIn("ig", expanded_ig)

    @patch("plugins.abelion_core.memory_store.get_db_path")
    def test_08_memory_store_fts(self, mock_get_db_path):
        """Proof that memory_store initializes FTS5 DB and saves reflection data."""
        temp_db = self.test_dir / "experience_fts_test.db"
        mock_get_db_path.return_value = temp_db
        
        from plugins.abelion_core.memory_store import save_experience
        import sqlite3
        
        reflection_data = {
            "summary": "OOM Crash on large import",
            "status": "failure",
            "errors": ["Out of Memory error in worker process"],
            "lessons": ["Implement batching", "Monitor memory usage"],
            "recommendations": ["Optimize batch size"]
        }
        
        save_experience("session_999", reflection_data)
        
        # Verify database creation and row insertion
        self.assertTrue(temp_db.exists())
        conn = sqlite3.connect(temp_db)
        cur = conn.cursor()
        cur.execute("SELECT session_id, summary, status, errors, lessons FROM experiences")
        rows = cur.fetchall()
        conn.close()
        
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], "session_999")
        self.assertEqual(rows[0][1], "OOM Crash on large import")
        self.assertEqual(rows[0][2], "failure")
        self.assertIn("Out of Memory", rows[0][3])
        self.assertIn("Implement batching", rows[0][4])

    @patch("plugins.abelion_core.recall_tool.get_db_path")
    @patch("plugins.abelion_core.memory_store.get_db_path")
    def test_09_recall_experience_tool(self, mock_store_db, mock_recall_db):
        """Proof that recall_experience tool searches FTS5, applies decay, and reranks matches."""
        temp_db = self.test_dir / "experience_fts_test.db"
        mock_store_db.return_value = temp_db
        mock_recall_db.return_value = temp_db
        
        from plugins.abelion_core.memory_store import save_experience
        from plugins.abelion_core.recall_tool import register_recall_tool
        
        # Save a dummy experience
        save_experience("session_oom", {
            "summary": "OOM memory leak on Chrome",
            "status": "failure",
            "errors": ["Chrome out of memory"],
            "lessons": ["Close browser between runs"],
            "recommendations": []
        })
        
        # Save another unrelated experience
        save_experience("session_other", {
            "summary": "Success on simple git push",
            "status": "success",
            "errors": [],
            "lessons": [],
            "recommendations": []
        })
        
        # Create a mock context with mock LLM
        class MockLLMResult:
            def __init__(self):
                # Return JSON list matching target structure
                self.text = '[{"session_id": "session_oom", "summary": "OOM memory leak on Chrome", "status": "failure", "errors": ["Chrome out of memory"], "lessons": ["Close browser between runs"], "relevance_reason": "Matches oom keywords"}]'
                
        class MockLLM:
            def complete(self, messages, purpose):
                return MockLLMResult()
                
        class MockCtx:
            def __init__(self):
                self.llm = MockLLM()
                self.tools = {}
            def register_tool(self, name, toolset, schema, handler):
                self.tools[name] = handler
                
        ctx = MockCtx()
        register_recall_tool(ctx)
        
        # Call the tool handler
        handler = ctx.tools["recall_experience"]
        result_json = handler({"query": "oom error"})
        
        result = json.loads(result_json)
        self.assertEqual(result["status"], "success")
        self.assertTrue(len(result["results"]) > 0)
        self.assertEqual(result["results"][0]["session_id"], "session_oom")

    @patch("plugins.abelion_core.link_tracker.get_link_log_path")
    def test_10_cache_messages_link_tracking(self, mock_get_path):
        """Proof that cache_messages extracts URLs from history and writes them to link.jsonl."""
        temp_log = self.test_dir / "link.jsonl"
        mock_get_path.return_value = temp_log

        from plugins.abelion_core.reflection import cache_messages

        history = [
            {"role": "user", "content": "please check https://github.com/google/antigravity and maybe https://google.com."},
            {"role": "assistant", "content": "ok, I checked https://openai.com/blog!"}
        ]

        cache_messages(session_id="session_links", conversation_history=history)

        # Retrieve and verify tracked links
        status_anti = get_link_status("https://github.com/google/antigravity")
        status_google = get_link_status("https://google.com")
        status_openai = get_link_status("https://openai.com/blog")

        self.assertIsNotNone(status_anti)
        self.assertIsNotNone(status_google)
        self.assertIsNotNone(status_openai)


if __name__ == "__main__":
    unittest.main()

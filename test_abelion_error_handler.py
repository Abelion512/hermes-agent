import json
import os
import shutil
import unittest
from pathlib import Path

from plugins.abelion_core.reflection import record_reflection
from plugins.abelion_core import pre_tool_hook
from plugins.abelion_core.circuit_breaker import State, get_breaker


class DummyLLMResult:
    def __init__(self, text):
        self.text = text
        self.model = "test-model"
        self.provider = "test-provider"


class DummyLLM:
    def complete(self, messages, purpose):
        # Simulate LLM extracting reflection data
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

        # Ensure test reflection dir exists
        self.test_dir = Path(
            "/media/abelion/Isaf/ican/project/references/hermes-agent/docs/abelion/reflections"
        )
        os.makedirs(self.test_dir, exist_ok=True)

    def test_01_circuit_breaker_trip(self):
        """Proof that the circuit breaker correctly opens after thresholds and blocks tools."""
        # 1. Simulate 3 consecutive failures
        self.breaker.record_failure()
        self.breaker.record_failure()
        self.breaker.record_failure()

        self.assertEqual(self.breaker.state, State.OPEN)
        self.assertFalse(self.breaker.allow_request())

        # 2. Proof that pre_tool_hook blocks execution
        result = pre_tool_hook("delegate_task", {"goal": "test"})
        self.assertIsNotNone(result)
        self.assertEqual(result.get("action"), "block")
        self.assertIn("Circuit Breaker OPEN", result.get("message"))

    def test_02_rsi_reflection_writing(self):
        """Proof that error reflections are correctly written to the isolated directory."""
        ctx = DummyCtx()

        # Simulate hook call on session end
        record_reflection(
            ctx,
            session_id="test_error_session",
            messages=[
                {"role": "user", "content": "do task"},
                {"role": "assistant", "content": "I failed"},
            ],
        )

        # Find the written file
        files = list(self.test_dir.glob("*test_err*.json"))
        self.assertTrue(len(files) > 0, "Reflection file was not created!")

        with open(files[0], "r") as f:
            data = json.load(f)

        self.assertEqual(data["session_id"], "test_error_session")
        self.assertEqual(data["reflection"]["status"], "failure")
        self.assertEqual(data["reflection"]["errors"][0], "Mock error")

        # Cleanup test file
        os.remove(files[0])


if __name__ == "__main__":
    unittest.main()

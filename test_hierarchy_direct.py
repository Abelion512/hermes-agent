import asyncio
import json
import logging
import os

from hermes_cli.config import load_config
from hermes_cli.plugins import get_plugin_manager
from run_agent import AIAgent

# Setup logging
logging.basicConfig(level=logging.INFO)


async def test_hierarchy():
    # 1. Load local config
    os.environ["HERMES_CONFIG"] = (
        "/media/abelion/Isaf/ican/project/references/hermes-agent/cli-config.yaml"
    )
    # Ensure HERMES_HOME is also set to avoid fallback warnings
    os.environ["HERMES_HOME"] = "/home/abelion/.hermes"

    # 2. Initialize Plugin Manager
    pm = get_plugin_manager()
    pm.discover_and_load(force=True)

    # 3. Initialize Agent
    # We don't pass max_spawn_depth here as it's not in __init__ signature.
    # It will be loaded from HERMES_CONFIG via cfg_get in init_agent.
    agent = AIAgent(
        model="openrouter/openrouter/owl-alpha",
        enabled_toolsets=["hermes-cli", "abelion"],
        quiet_mode=False,
    )

    # Verify depth was loaded from config
    print(
        f"Agent initialized. Max spawn depth: {getattr(agent, '_max_spawn_depth', 'unknown')}"
    )

    goal = (
        "Perform the Architectural Test: Use 'abelion_delegate' to delegate 'Dummy Task' to 'Division Alpha'. "
        "Instruct 'Division Alpha' to then delegate 'Writing hello world' to 'Worker Beta' using 'abelion_delegate'. "
        "Worker Beta MUST write 'ABELION HIERARCHY SUCCESS' to 'abelion_hierarchy_real.txt'. "
        "DO NOT DO THE WORK YOURSELF. VERIFY THE FILE AT THE END."
    )

    try:
        print("Starting conversation...")
        result = agent.run_conversation(goal)
        print(f"Final Response: {result.get('final_response')}")
        print(f"Messages: {len(result.get('messages', []))}")

        # Final check
        if os.path.exists("abelion_hierarchy_real.txt"):
            with open("abelion_hierarchy_real.txt", "r") as f:
                content = f.read().strip()
                print(f"FILE CONTENT: {content}")
                if content == "ABELION HIERARCHY SUCCESS":
                    print("✅ TEST PASSED: 3-level hierarchy confirmed.")
                else:
                    print("❌ TEST FAILED: Content mismatch.")
        else:
            print("❌ TEST FAILED: File not created.")

    except Exception as e:
        print(f"Error during test: {e}")


if __name__ == "__main__":
    asyncio.run(test_hierarchy())

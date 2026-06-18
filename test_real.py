import asyncio
import os
import json
from run_agent import AIAgent
from hermes_cli.plugins import get_plugin_manager
from hermes_cli.config import load_config

async def test():
    os.environ["HERMES_CONFIG"] = "/media/abelion/Isaf/ican/project/references/hermes-agent/cli-config.yaml"
    os.environ["HERMES_HOME"] = "/home/abelion/.hermes"
    
    pm = get_plugin_manager()
    pm.discover_and_load(force=True)
    
    agent = AIAgent(
        model="openrouter/openrouter/owl-alpha",
        enabled_toolsets=["hermes-cli", "abelion"],
        quiet_mode=False
    )
    
    try:
        result = agent.run_conversation("Read 'docs/abelion/tasks/REAL_FAIL_TEST.md' and follow the instructions to perform the REAL FAIL TEST.")
        print(f"Final: {result.get('final_response')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())

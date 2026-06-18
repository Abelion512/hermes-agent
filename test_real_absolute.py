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
        # We manually trigger the hook at the end because run_conversation might not be doing it properly in the script env
        result = agent.run_conversation("Read '/media/abelion/Isaf/ican/project/references/hermes-agent/docs/abelion/tasks/REAL_FAIL_TEST.md' and perform the REAL FAIL TEST. DO NOT BYPASS DELEGATION.")
        print(f"Final: {result.get('final_response')}")
        
        from hermes_cli.plugins import invoke_hook
        invoke_hook("on_session_end", session_id=agent.session_id, messages=result.get("messages", []))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())

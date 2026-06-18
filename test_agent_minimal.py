import asyncio
import json

from run_agent import AIAgent


async def test():
    agent = AIAgent(
        model="openrouter/openrouter/owl-alpha",
        enabled_toolsets=["hermes-cli", "abelion"],
        quiet_mode=False,
    )
    print("Agent initialized.")
    try:
        result = agent.run_conversation("hello")
        print(f"Result: {result.get('final_response')}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test())

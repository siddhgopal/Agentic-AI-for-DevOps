"""
agents/docker_agent.py
=======================
Docker Troubleshooter Agent

Flow:
  User pastes Docker error
  → Claude reads error + calls tools (logs, inspect, disk)
  → Claude diagnoses root cause
  → Agent prints fix commands
  → Optional: auto-execute with user confirmation
"""

import json
from config.settings import client, MODEL, MAX_TOKENS
from tools.docker_tools import (
    DOCKER_TOOLS,
    get_container_logs,
    list_containers,
    inspect_container,
    check_disk_usage,
    prune_system,
)

SYSTEM_PROMPT = """You are an expert DevOps AI agent specialized in Docker troubleshooting.

When given a Docker error:
1. Use the available tools to gather more information if needed
2. Diagnose the ROOT CAUSE clearly
3. Provide step-by-step FIX COMMANDS
4. Explain WHY the error happened (1-2 lines)
5. Suggest how to PREVENT it in future

Always be concise and actionable. Format fix commands as code blocks.
If you use a tool, explain what information you got from it.
"""


class DockerTroubleshooterAgent:
    def __init__(self):
        self.tool_map = {
            "get_container_logs": get_container_logs,
            "list_containers": list_containers,
            "inspect_container": inspect_container,
            "check_disk_usage": check_disk_usage,
            "prune_system": prune_system,
        }

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Execute a tool and return result as string."""
        if tool_name not in self.tool_map:
            return f"Unknown tool: {tool_name}"

        print(f"\n  🔧 Running tool: {tool_name}({tool_input})")
        result = self.tool_map[tool_name](**tool_input)
        return json.dumps(result, indent=2)

    def run(self, error_message: str):
        print(f"\n🐳 Docker Troubleshooter Agent")
        print(f"📋 Analyzing: {error_message[:80]}...")
        print("-" * 50)

        messages = [
            {"role": "user", "content": f"Docker error:\n\n{error_message}"}
        ]

        # Agentic loop — keep going until Claude stops calling tools
        while True:
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                tools=DOCKER_TOOLS,
                messages=messages
            )

            # Collect text output
            for block in response.content:
                if block.type == "text":
                    print(f"\n{block.text}")

            # If Claude is done (no more tool calls), break
            if response.stop_reason == "end_turn":
                break

            # Process tool calls
            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = self._execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })

                # Append Claude's response + tool results to continue the loop
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            else:
                break

        print("\n" + "=" * 50)
        print("✅ Analysis complete!")

"""
agents/cicd_agent.py
=====================
CI/CD Failure Analyzer Agent

Analyzes GitHub Actions / Jenkins / GitLab CI failure logs.
Uses Claude to:
  - Find failing step
  - Identify root cause (dependency, env var, test failure, etc.)
  - Suggest exact fix
  - Generate a fixed workflow snippet if needed
"""

import os
from config.settings import client, MODEL, MAX_TOKENS

SYSTEM_PROMPT = """You are an expert CI/CD DevOps AI agent.

When given a CI/CD failure log (GitHub Actions, Jenkins, GitLab CI):
1. Identify the EXACT failing step and line number
2. Diagnose the root cause (missing dependency, wrong env var, test failure, network issue, etc.)
3. Provide a concrete FIX — either code change, workflow YAML fix, or command
4. If it's a workflow YAML issue, provide the corrected snippet
5. Categorize the failure type: [BUILD | TEST | DEPLOY | NETWORK | CONFIG | PERMISSIONS]

Be precise. Quote the exact failing line from the log.
Format your response with clear sections: ## Failing Step, ## Root Cause, ## Fix.
"""

# Tool: Read a log file from disk
CICD_TOOLS = [
    {
        "name": "read_log_file",
        "description": "Read a CI/CD log file from disk",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the log file"}
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "search_log_for_errors",
        "description": "Search the log for lines containing ERROR, FAILED, or Exception",
        "input_schema": {
            "type": "object",
            "properties": {
                "log_content": {"type": "string", "description": "Full log content to search"},
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keywords to search for",
                    "default": ["ERROR", "FAILED", "Exception", "error:", "fatal:"]
                }
            },
            "required": ["log_content"]
        }
    }
]


def read_log_file(file_path: str) -> str:
    try:
        with open(file_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {file_path}"
    except Exception as e:
        return f"Error reading file: {e}"


def search_log_for_errors(log_content: str, keywords=None) -> str:
    if keywords is None:
        keywords = ["ERROR", "FAILED", "Exception", "error:", "fatal:"]
    matching_lines = []
    for i, line in enumerate(log_content.splitlines(), 1):
        if any(kw.lower() in line.lower() for kw in keywords):
            matching_lines.append(f"Line {i}: {line}")
    return "\n".join(matching_lines) if matching_lines else "No error lines found."


class CICDAnalyzerAgent:
    def __init__(self):
        self.tool_map = {
            "read_log_file": read_log_file,
            "search_log_for_errors": search_log_for_errors,
        }

    def _is_file_path(self, text: str) -> bool:
        return os.path.exists(text) and text.endswith((".log", ".txt"))

    def run(self, log_input: str):
        print(f"\n⚙️  CI/CD Failure Analyzer Agent")

        # If user gave a file path, read the file content
        if self._is_file_path(log_input):
            print(f"📂 Reading log file: {log_input}")
            log_content = read_log_file(log_input)
        else:
            log_content = log_input

        print(f"📋 Analyzing {len(log_content)} characters of logs...")
        print("-" * 50)

        messages = [
            {"role": "user", "content": f"CI/CD failure log:\n\n{log_content}"}
        ]

        while True:
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                tools=CICD_TOOLS,
                messages=messages
            )

            for block in response.content:
                if block.type == "text":
                    print(f"\n{block.text}")

            if response.stop_reason == "end_turn":
                break

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        print(f"\n  🔧 Tool: {block.name}")
                        fn = self.tool_map.get(block.name)
                        result = fn(**block.input) if fn else "Tool not found"
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            else:
                break

        print("\n" + "=" * 50)
        print("✅ CI/CD analysis complete!")

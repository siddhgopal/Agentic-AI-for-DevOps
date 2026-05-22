"""
agents/kube_agent.py
=====================
KubeHealer — Kubernetes Self-Healing Agent

Monitors a namespace for unhealthy pods/deployments.
Uses Claude to decide what fix to apply, then runs kubectl commands.

This is the most advanced agent in this repo — it follows the
"observe → decide → act" loop used in real production systems.
"""

import subprocess
import json
from config.settings import client, MODEL, MAX_TOKENS

SYSTEM_PROMPT = """You are KubeHealer, an expert Kubernetes self-healing AI agent.

Your job:
1. Use tools to observe the cluster state (pods, events, logs)
2. Identify unhealthy resources (CrashLoopBackOff, OOMKilled, Pending, ImagePullBackOff, etc.)
3. Decide the best remediation action
4. Call the appropriate fix tool
5. Verify the fix worked

Known remediation patterns:
- CrashLoopBackOff → Check logs, check resource limits, check env vars
- OOMKilled → Increase memory limits or find memory leak
- ImagePullBackOff → Check image name/tag, check registry credentials
- Pending (no nodes) → Check node resources, taints/tolerations
- Pending (PVC) → Check PersistentVolumeClaim status

Always explain your reasoning before taking action.
NEVER delete pods without logging the reason first.
"""

KUBE_TOOLS = [
    {
        "name": "get_pod_status",
        "description": "Get status of all pods in a namespace",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string", "description": "Kubernetes namespace"},
            },
            "required": ["namespace"]
        }
    },
    {
        "name": "get_pod_logs",
        "description": "Get logs from a specific pod",
        "input_schema": {
            "type": "object",
            "properties": {
                "pod_name": {"type": "string"},
                "namespace": {"type": "string"},
                "tail": {"type": "integer", "default": 30}
            },
            "required": ["pod_name", "namespace"]
        }
    },
    {
        "name": "describe_pod",
        "description": "Get detailed description of a pod including events",
        "input_schema": {
            "type": "object",
            "properties": {
                "pod_name": {"type": "string"},
                "namespace": {"type": "string"}
            },
            "required": ["pod_name", "namespace"]
        }
    },
    {
        "name": "restart_deployment",
        "description": "Rollout restart a deployment (safe restart, zero downtime)",
        "input_schema": {
            "type": "object",
            "properties": {
                "deployment_name": {"type": "string"},
                "namespace": {"type": "string"}
            },
            "required": ["deployment_name", "namespace"]
        }
    },
    {
        "name": "get_events",
        "description": "Get Kubernetes events for a namespace (shows warnings and errors)",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"}
            },
            "required": ["namespace"]
        }
    },
    {
        "name": "scale_deployment",
        "description": "Scale a deployment up or down",
        "input_schema": {
            "type": "object",
            "properties": {
                "deployment_name": {"type": "string"},
                "namespace": {"type": "string"},
                "replicas": {"type": "integer"}
            },
            "required": ["deployment_name", "namespace", "replicas"]
        }
    }
]


def _run_kubectl(args: list) -> dict:
    try:
        result = subprocess.run(
            ["kubectl"] + args,
            capture_output=True, text=True, timeout=30
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout.strip() or result.stderr.strip()
        }
    except FileNotFoundError:
        return {"success": False, "output": "kubectl not found. Is it installed and in PATH?"}
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "kubectl command timed out."}


def get_pod_status(namespace: str) -> str:
    result = _run_kubectl(["get", "pods", "-n", namespace, "-o", "wide"])
    return json.dumps(result)


def get_pod_logs(pod_name: str, namespace: str, tail: int = 30) -> str:
    result = _run_kubectl(["logs", pod_name, "-n", namespace, f"--tail={tail}"])
    return json.dumps(result)


def describe_pod(pod_name: str, namespace: str) -> str:
    result = _run_kubectl(["describe", "pod", pod_name, "-n", namespace])
    return json.dumps(result)


def restart_deployment(deployment_name: str, namespace: str) -> str:
    result = _run_kubectl(["rollout", "restart", f"deployment/{deployment_name}", "-n", namespace])
    return json.dumps(result)


def get_events(namespace: str) -> str:
    result = _run_kubectl(["get", "events", "-n", namespace, "--sort-by=.lastTimestamp"])
    return json.dumps(result)


def scale_deployment(deployment_name: str, namespace: str, replicas: int) -> str:
    result = _run_kubectl(["scale", f"deployment/{deployment_name}",
                           f"--replicas={replicas}", "-n", namespace])
    return json.dumps(result)


class KubeHealerAgent:
    def __init__(self):
        self.tool_map = {
            "get_pod_status": get_pod_status,
            "get_pod_logs": get_pod_logs,
            "describe_pod": describe_pod,
            "restart_deployment": restart_deployment,
            "get_events": get_events,
            "scale_deployment": scale_deployment,
        }

    def run(self, namespace: str = "default"):
        print(f"\n☸️  KubeHealer — Kubernetes Self-Healing Agent")
        print(f"🔍 Observing namespace: {namespace}")
        print("-" * 50)

        messages = [
            {
                "role": "user",
                "content": (
                    f"Please observe the '{namespace}' namespace, identify any unhealthy pods "
                    f"or deployments, diagnose the root cause, and apply the appropriate fix."
                )
            }
        ]

        # Agentic loop — observe → decide → act → verify
        max_iterations = 10  # safety limit
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            print(f"\n[Iteration {iteration}]")

            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                tools=KUBE_TOOLS,
                messages=messages
            )

            for block in response.content:
                if block.type == "text":
                    print(f"\n{block.text}")

            if response.stop_reason == "end_turn":
                print("\n✅ KubeHealer finished. Cluster is healthy (or no auto-fix available).")
                break

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        print(f"\n  🔧 Action: {block.name}({block.input})")

                        # For destructive actions, ask for confirmation
                        if block.name in ("restart_deployment", "scale_deployment"):
                            confirm = input(f"\n  ⚠️  Confirm {block.name}? (y/N): ").strip().lower()
                            if confirm != "y":
                                result = "Action cancelled by user."
                            else:
                                fn = self.tool_map[block.name]
                                result = fn(**block.input)
                        else:
                            fn = self.tool_map.get(block.name)
                            result = fn(**block.input) if fn else "Tool not found"

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result)
                        })

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            else:
                break

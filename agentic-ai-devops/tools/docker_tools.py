"""
tools/docker_tools.py
======================
Real Docker commands the agent can execute.
Each function maps to a Claude tool definition.
"""

import subprocess


def run_docker_command(command: str) -> dict:
    """Run a docker CLI command and return output."""
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "Command timed out after 30s", "returncode": -1}
    except FileNotFoundError:
        return {"success": False, "stdout": "", "stderr": "Docker not found. Is it installed?", "returncode": -1}


def get_container_logs(container_id: str, tail: int = 50) -> dict:
    return run_docker_command(f"docker logs --tail {tail} {container_id}")


def list_containers(all_containers: bool = True) -> dict:
    flag = "-a" if all_containers else ""
    return run_docker_command(f"docker ps {flag} --format table")


def inspect_container(container_id: str) -> dict:
    return run_docker_command(f"docker inspect {container_id}")


def check_disk_usage() -> dict:
    return run_docker_command("docker system df")


def prune_system(force: bool = False) -> dict:
    flag = "-f" if force else ""
    return run_docker_command(f"docker system prune {flag}")


def pull_image(image: str) -> dict:
    return run_docker_command(f"docker pull {image}")


# ─── Tool definitions for Claude API ─────────────────────────────────────────

DOCKER_TOOLS = [
    {
        "name": "get_container_logs",
        "description": "Get the last N lines of logs from a Docker container",
        "input_schema": {
            "type": "object",
            "properties": {
                "container_id": {"type": "string", "description": "Container ID or name"},
                "tail": {"type": "integer", "description": "Number of log lines to fetch", "default": 50}
            },
            "required": ["container_id"]
        }
    },
    {
        "name": "list_containers",
        "description": "List all Docker containers (running and stopped)",
        "input_schema": {
            "type": "object",
            "properties": {
                "all_containers": {"type": "boolean", "description": "Include stopped containers", "default": True}
            }
        }
    },
    {
        "name": "inspect_container",
        "description": "Get detailed info about a container (network, volumes, env vars)",
        "input_schema": {
            "type": "object",
            "properties": {
                "container_id": {"type": "string", "description": "Container ID or name"}
            },
            "required": ["container_id"]
        }
    },
    {
        "name": "check_disk_usage",
        "description": "Check Docker disk usage (images, containers, volumes)",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "prune_system",
        "description": "Remove unused Docker resources to free disk space",
        "input_schema": {
            "type": "object",
            "properties": {
                "force": {"type": "boolean", "description": "Skip confirmation prompt", "default": False}
            }
        }
    }
]

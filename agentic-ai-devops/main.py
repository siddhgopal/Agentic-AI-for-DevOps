"""
Agentic AI for DevOps
=====================
Main entry point — choose which agent to run.

Agents:
  1. Docker Troubleshooter
  2. CI/CD Failure Analyzer
  3. KubeHealer (Kubernetes Self-Healing)

Usage:
  python main.py --agent docker
  python main.py --agent cicd
  python main.py --agent kube
"""

import argparse
from agents.docker_agent import DockerTroubleshooterAgent
from agents.cicd_agent import CICDAnalyzerAgent
from agents.kube_agent import KubeHealerAgent


def main():
    parser = argparse.ArgumentParser(description="Agentic AI for DevOps")
    parser.add_argument(
        "--agent",
        choices=["docker", "cicd", "kube"],
        required=True,
        help="Which agent to run"
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Error message or log file path (optional, will prompt if not given)"
    )
    args = parser.parse_args()

    print("\n🤖 Agentic AI for DevOps — by [Your Name]")
    print("=" * 50)

    if args.agent == "docker":
        agent = DockerTroubleshooterAgent()
        error = args.input or input("\nPaste your Docker error:\n> ")
        agent.run(error)

    elif args.agent == "cicd":
        agent = CICDAnalyzerAgent()
        log = args.input or input("\nPaste your CI/CD failure log (or file path):\n> ")
        agent.run(log)

    elif args.agent == "kube":
        agent = KubeHealerAgent()
        namespace = args.input or input("\nEnter Kubernetes namespace (default: default):\n> ") or "default"
        agent.run(namespace)


if __name__ == "__main__":
    main()

# 🤖 Agentic AI for DevOps

> AI agents that automate real DevOps tasks — built with Anthropic's Claude API and tool-use (function calling).

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Claude](https://img.shields.io/badge/Claude-claude--sonnet--4-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

## What is this?

This repo contains **3 production-style AI agents** that solve real DevOps problems:

| Agent | What it does |
|---|---|
| 🐳 Docker Troubleshooter | Diagnoses Docker errors, runs diagnostic tools, suggests fixes |
| ⚙️ CI/CD Failure Analyzer | Reads GitHub Actions / Jenkins logs, finds root cause, fixes pipeline |
| ☸️ KubeHealer | Observes Kubernetes namespace, detects unhealthy pods, self-heals |

Each agent follows the **Observe → Reason → Act** loop used in production agentic systems.

---

## How agents work (architecture)

```
User Input (error / log / namespace)
        ↓
   Claude API (reasoning)
        ↓
   Tool Call (kubectl / docker / file read)
        ↓
   Tool Result → back to Claude
        ↓
   Claude reasons again...
        ↓
   Final diagnosis + fix
```

This is called an **agentic loop** — Claude keeps calling tools until it has enough information to give a final answer. This is the core pattern behind all production AI agents.

---

## Quickstart

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/agentic-ai-devops.git
cd agentic-ai-devops

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
# Get a free key at: https://console.anthropic.com

# 5. Run an agent
python main.py --agent docker
python main.py --agent cicd
python main.py --agent kube
```

---

## Agent 1: Docker Troubleshooter

Paste any Docker error and the agent will:
- Run `docker ps`, `docker logs`, `docker inspect` as needed
- Identify root cause
- Give exact fix commands

```bash
python main.py --agent docker
# > Cannot connect to Docker daemon at unix:///var/run/docker.sock

# Output:
# 🔧 Running tool: list_containers()
# Root cause: Docker service is not running
# Fix: sudo systemctl start docker
```

---

## Agent 2: CI/CD Failure Analyzer

Supports GitHub Actions, Jenkins, GitLab CI logs.

```bash
python main.py --agent cicd
# Paste your failure log or give a file path

python main.py --agent cicd --input /path/to/build.log
```

---

## Agent 3: KubeHealer

Connects to your real Kubernetes cluster via `kubectl`.

```bash
python main.py --agent kube
# Enter namespace: production

# Agent observes → finds CrashLoopBackOff → reads logs → suggests restart
# ⚠️  Confirm restart_deployment? (y/N):
```

> Requires `kubectl` configured with cluster access.

---

## Project structure

```
agentic-ai-devops/
├── agents/
│   ├── docker_agent.py     ← Docker Troubleshooter
│   ├── cicd_agent.py       ← CI/CD Failure Analyzer
│   └── kube_agent.py       ← KubeHealer
├── tools/
│   └── docker_tools.py     ← Tool definitions + executors
├── config/
│   └── settings.py         ← Claude client setup
├── tests/
├── main.py                 ← Entry point
├── requirements.txt
├── .env.example
└── README.md
```

---

## Key concepts used

- **Tool Use / Function Calling** — Claude calls real system tools (kubectl, docker CLI)
- **Agentic Loop** — Multi-step reasoning until task is complete
- **System Prompts** — Each agent has a specialized DevOps persona
- **Tool Definitions** — JSON schemas that tell Claude what tools are available

---

## Resume description

> **Agentic AI for DevOps** | Python, Anthropic Claude API, Docker, Kubernetes  
> Built 3 AI agents (Docker Troubleshooter, CI/CD Analyzer, KubeHealer) using Claude's tool-use API.  
> Agents follow an observe-reason-act loop to autonomously diagnose and fix infrastructure issues.

---

## Author

Built by **[Your Name]** as part of the *Agentic AI for DevOps* learning journey.  
Inspired by TrainWithShubham's "Agentic AI for DevOps" course.

---

## License

MIT

"""
config/settings.py
==================
Loads environment variables and creates shared Anthropic client.
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise EnvironmentError(
        "ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key."
    )

# Shared client — import this in every agent
client = Anthropic(api_key=ANTHROPIC_API_KEY)

MODEL = "claude-sonnet-4-20250514"

# Tool-use config
MAX_TOKENS = 2048

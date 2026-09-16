"""Configuration settings loaded from environment variables."""
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

# Load this project's own .env, by explicit path. Calling load_dotenv() with no
# argument makes python-dotenv walk up the directory tree, so a .env sitting in a
# parent directory would leak into this project's config.
# settings.py -> config -> src -> <project root>
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / '.env')

# ============================================================================
# API CONFIGURATION - Loaded from .env file
# ============================================================================

# Model / temperature defaults (used when no explicit model is passed)
MODEL = os.getenv('OPENROUTER_MODEL', 'gpt-4o-mini')
TEMPERATURE = float(os.getenv('TEMPERATURE', '1.0'))

# OpenRouter Configuration (every model call goes through OpenRouter)
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
_PLACEHOLDER_KEY = 'your-openrouter-key-here'  # the value shipped in .env.example

# Reasoning Model Configuration (for o1/o3/gpt-5 models)
# Valid values: "low", "medium", "high"
# Higher effort = more reasoning tokens = potentially better quality but slower/more expensive
REASONING_EFFORT = os.getenv('REASONING_EFFORT', 'low')

# ============================================================================
# GAME CONFIGURATION
# ============================================================================

NUM_AGENTS = int(os.getenv('NUM_AGENTS', '5'))

# ============================================================================
# VALIDATION
# ============================================================================

if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == _PLACEHOLDER_KEY:
    raise ValueError(
        "OPENROUTER_API_KEY is not set, or is still the placeholder from .env.example. "
        "Put your real OpenRouter key in this project's .env file."
    )

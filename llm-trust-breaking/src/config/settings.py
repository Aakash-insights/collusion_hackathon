"""Configuration settings loaded from environment variables."""
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

# ============================================================================
# ENV LOADING
# ============================================================================
# API keys live in the *shared root* .env for the consolidated starter repo.
# Everything else (model, temperature, run sizes) stays in this project's own .env.
#
# Repo root is four levels up: settings.py -> config -> src -> llm-trust-breaking
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _PROJECT_ROOT.parent

# Project-local .env first (it wins for project-scoped vars), then the shared root.
load_dotenv(_PROJECT_ROOT / '.env')
load_dotenv(_REPO_ROOT / '.env')


def _api_key(name: str) -> str:
    """
    Resolve a shared API key from the root .env.

    Order: project-specific override, then the shared default, then empty.
      TRUST_BREAKING_<NAME>  ->  DEFAULT_<NAME>  ->  ''
    """
    return (
        os.getenv(f'TRUST_BREAKING_{name}')
        or os.getenv(f'DEFAULT_{name}')
        or ''
    )


# ============================================================================
# API CONFIGURATION
# ============================================================================

# Model / temperature defaults (used when no explicit model is passed)
MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
TEMPERATURE = float(os.getenv('TEMPERATURE', '1.0'))

# OpenAI Configuration (for GPT models: gpt-*, o1*, o3*)
OPENAI_API_KEY = _api_key('OPENAI_API_KEY')

# OpenRouter Configuration (for non-OpenAI models: Claude, Llama, etc.)
OPENROUTER_API_KEY = _api_key('OPENROUTER_API_KEY')

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

if not OPENAI_API_KEY and not OPENROUTER_API_KEY:
    raise ValueError(
        "No API key found. Set TRUST_BREAKING_OPENAI_API_KEY or "
        "TRUST_BREAKING_OPENROUTER_API_KEY (or the shared DEFAULT_OPENAI_API_KEY / "
        "DEFAULT_OPENROUTER_API_KEY) in the repo root .env — see the root .env.example."
    )

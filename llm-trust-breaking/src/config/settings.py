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

# Route provider base_url / key / model through the repo-root shared LLM config.
from poseidon_compute import api_key as _llm_api_key, resolve_model as _resolve_model

# Model / temperature defaults (used when no explicit model is passed). CLI `--model` and LLM_MODEL in the
# repo-root compute.env both win over this (via resolve_model); a provided model that fails is never
# silently swapped. The default is an OpenRouter id (needs OPENROUTER_API_KEY) — set LLM_MODEL/--model to a
# JSON-capable open model to run on Nebius.
MODEL = _resolve_model(os.getenv('OPENROUTER_MODEL', 'openai/gpt-4o-mini'))
TEMPERATURE = float(os.getenv('TEMPERATURE', '1.0'))

# OpenRouter Configuration (key now sourced from the shared compute.env via llm_config;
# falls back to this project's own OPENROUTER_API_KEY .env entry).
OPENROUTER_API_KEY = _llm_api_key() or os.getenv('OPENROUTER_API_KEY', '')
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

"""Central LLM provider config shared by every project in this repo.

ONE place to set your keys and choose a provider: the repo-root `compute.env` file
(copy `compute.env.example` -> `compute.env`). Every project builds its model client from this,
so you configure once and all ten projects follow.

compute.env keys:
    LLM_PROVIDER        openrouter | nebius          (default: openrouter)
    OPENROUTER_API_KEY  your OpenRouter key
    NEBIUS_API_KEY      your Nebius AI Studio key
    LLM_MODEL           (optional) force one model id across every project
    NEBIUS_DEFAULT_MODEL (optional) fallback model when a project's default has no Nebius equivalent

Public API:
    make_client(async_=False)        -> an (Async)OpenAI client pointed at the chosen provider
    resolve_model(project_default)   -> the model id to use for the chosen provider
    base_url(), api_key(), provider(), config()

Provider note: OpenRouter and Nebius are both OpenAI-compatible *inference* endpoints, so this is a
true drop-in swap. Modal is a *compute* layer (where code runs), not a provider — `modal_run.py`
reads this same compute.env and runs your code, which then uses the provider selected here.
"""
import os
import functools
from pathlib import Path

PROVIDERS = {
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "key_env": "OPENROUTER_API_KEY"},
    "nebius":     {"base_url": "https://api.studio.nebius.com/v1", "key_env": "NEBIUS_API_KEY"},
}

# A project passes its paper-default model id (an OpenRouter-style id). For Nebius we map to a
# served open model; OpenAI/Gemini-family defaults have no Nebius equivalent and fall back to
# NEBIUS_DEFAULT_MODEL. Extend as needed from your Nebius console catalog.
NEBIUS_MODEL_MAP = {
    "openai/gpt-4o-mini":                 "meta-llama/Llama-3.1-8B-Instruct",
    "openai/gpt-4o":                      "meta-llama/Llama-3.3-70B-Instruct",
    "openai/gpt-4.1":                     "meta-llama/Llama-3.3-70B-Instruct",
    "openai/gpt-4.1-mini":                "meta-llama/Llama-3.1-8B-Instruct",
    "openai/gpt-3.5-turbo":               "meta-llama/Llama-3.1-8B-Instruct",
    "meta-llama/llama-3.3-70b-instruct":  "meta-llama/Llama-3.3-70B-Instruct",
    "meta-llama/llama-3.1-8b-instruct":   "meta-llama/Llama-3.1-8B-Instruct",
    "mistralai/mistral-large-2512":       "mistralai/Mistral-Large-Instruct-2411",
    "deepseek/deepseek-r1-0528":          "deepseek-ai/DeepSeek-R1-0528",
}
NEBIUS_FALLBACK = "meta-llama/Llama-3.3-70B-Instruct"


def _find_root_env():
    """Walk up from this file and the CWD to find the repo-root compute.env."""
    for start in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        for p in (start, *start.parents):
            f = p / "compute.env"
            if f.exists():
                return f
    return None


@functools.lru_cache(maxsize=1)
def _load():
    """Load compute.env into os.environ (without overriding anything already set)."""
    f = _find_root_env()
    if f is None:
        return None
    try:
        from dotenv import dotenv_values
        values = dotenv_values(f)
    except Exception:
        values = {}
        for line in f.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip()
    for k, v in values.items():
        if v is not None and k not in os.environ:
            os.environ[k] = v
    return f


def provider():
    _load()
    return os.environ.get("LLM_PROVIDER", "openrouter").strip().lower()


def base_url():
    _load()
    # explicit override wins; else the provider's default endpoint
    return os.environ.get("LLM_BASE_URL") or PROVIDERS[provider()]["base_url"]


def api_key():
    _load()
    p = provider()
    return (os.environ.get(PROVIDERS[p]["key_env"])
            or os.environ.get("OPENROUTER_API_KEY")
            or os.environ.get("NEBIUS_API_KEY")
            or "")


def resolve_model(project_default):
    """Return the model id to use. LLM_MODEL overrides everything; on Nebius, map or fall back."""
    _load()
    forced = os.environ.get("LLM_MODEL")
    if forced:
        return forced
    if provider() == "nebius":
        return NEBIUS_MODEL_MAP.get(project_default,
                                    os.environ.get("NEBIUS_DEFAULT_MODEL", NEBIUS_FALLBACK))
    return project_default


def config():
    return {"provider": provider(), "base_url": base_url(),
            "has_key": bool(api_key()), "forced_model": os.environ.get("LLM_MODEL")}


def make_client(async_=False, **kwargs):
    """Construct an (Async)OpenAI client for the selected provider."""
    from openai import OpenAI, AsyncOpenAI
    cls = AsyncOpenAI if async_ else OpenAI
    return cls(base_url=base_url(), api_key=api_key(), **kwargs)


# ---- import bootstrap for projects in nested dirs / separate venvs --------------------------------
# Projects whose client lives several dirs deep (and in their own venv) can import this module with:
#     from llm_config import make_client, resolve_model   # after adding the repo root to sys.path
# Use `bootstrap()` from a known file to locate+add the repo root automatically:
def bootstrap():
    """Call from a project file to put the repo root (this module) on sys.path. Returns the root."""
    import sys
    root = Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root

"""Central LLM config shared by every project in this repo.

ONE place to set your key and (optionally) a model: the repo-root `compute.env`
(copy `compute.env.example` -> `compute.env`). Every project builds its model client from this,
so you configure once and all ten projects follow.

Default inference provider: **Nebius AI Studio** (OpenAI-compatible, open models). For an experiment
Nebius can't serve/accept, run it through `util/hosted_model.py`, which boots a model on Modal and
wires the endpoint in automatically — same interface, different endpoint.

compute.env keys (what participants set):
    NEBIUS_API_KEY        your Nebius AI Studio key               (default inference)
    LLM_MODEL             (optional) force one model id everywhere
    NEBIUS_DEFAULT_MODEL  (optional) fallback when a project default has no Nebius equivalent

internal (set automatically by util/hosted_model.py — participants don't configure these):
    LLM_BASE_URL          a custom OpenAI-compatible endpoint (the temporary Modal model)
    LLM_API_KEY           key for that endpoint

Public API:
    make_client(async_=False)        -> an (Async)OpenAI client pointed at the configured endpoint
    resolve_model(project_default)   -> the model id to use
    base_url(), api_key(), endpoint_kind(), config()
"""
import os
import functools
from pathlib import Path

NEBIUS_BASE_URL = "https://api.studio.nebius.com/v1"

# Projects pass their paper-default model id (often an OpenAI-style string). We map those to a
# Nebius-served open model; anything unmapped falls back to NEBIUS_DEFAULT_MODEL. Extend from the
# Nebius console catalog as needed. (When using a custom LLM_BASE_URL / Modal model, set LLM_MODEL.)
NEBIUS_MODEL_MAP = {
    "openai/gpt-4o-mini":                 "meta-llama/Llama-3.1-8B-Instruct",
    "openai/gpt-4o":                      "meta-llama/Llama-3.3-70B-Instruct",
    "openai/gpt-4o-2024-08-06":           "meta-llama/Llama-3.3-70B-Instruct",
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


def endpoint_kind():
    """'custom' if LLM_BASE_URL is set (e.g. a Modal-hosted model), else 'nebius'."""
    _load()
    return "custom" if os.environ.get("LLM_BASE_URL") else "nebius"


def base_url():
    _load()
    return os.environ.get("LLM_BASE_URL") or NEBIUS_BASE_URL


def api_key():
    _load()
    return (os.environ.get("LLM_API_KEY")
            or os.environ.get("NEBIUS_API_KEY")
            or "")


def resolve_model(project_default):
    """Model id to use. LLM_MODEL overrides everything. On a custom endpoint, LLM_MODEL should name
    the served model (else the project default is passed through). On Nebius, map the default."""
    _load()
    forced = os.environ.get("LLM_MODEL")
    if forced:
        return forced
    if endpoint_kind() == "custom":
        return project_default  # custom endpoint: set LLM_MODEL to the served model id
    return NEBIUS_MODEL_MAP.get(project_default,
                                os.environ.get("NEBIUS_DEFAULT_MODEL", NEBIUS_FALLBACK))


def config():
    return {"endpoint": endpoint_kind(), "base_url": base_url(),
            "has_key": bool(api_key()), "forced_model": os.environ.get("LLM_MODEL")}


def make_client(async_=False, **kwargs):
    """Construct an (Async)OpenAI client for the configured endpoint (Nebius by default)."""
    from openai import OpenAI, AsyncOpenAI
    cls = AsyncOpenAI if async_ else OpenAI
    return cls(base_url=base_url(), api_key=api_key(), **kwargs)


def bootstrap():
    """Call from a project file to put the repo root (this module) on sys.path. Returns the root."""
    import sys
    root = Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root

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

internal (set automatically by util/hosted_model.py — participants don't configure these):
    LLM_BASE_URL          a custom OpenAI-compatible endpoint (the temporary Modal model)
    LLM_API_KEY           key for that endpoint

No model is ever substituted and there is no default model — an unavailable model fails loudly or
reroutes to Modal (util/run.py), never gets swapped for another.

Public API:
    make_client(async_=False)        -> an (Async)OpenAI client pointed at the configured endpoint
    resolve_model(requested)         -> the model id to use (same model only; never substituted)
    nebius_serves(model)             -> True / False / None (catalog check)
    base_url(), api_key(), endpoint_kind(), config()
"""
import os
import functools
from pathlib import Path

NEBIUS_BASE_URL = "https://api.studio.nebius.com/v1"

# We NEVER substitute a different model. The only translation here is id-SPELLING for the SAME model:
# a few starter defaults are written in OpenRouter casing, and Nebius spells the identical model
# slightly differently. Anything not listed is passed through UNCHANGED — and if it isn't actually on
# Nebius, the run reroutes to Modal or fails loudly (see util/run.py); it is never swapped for another
# model and there is no generic fallback.
_NEBIUS_SAME_MODEL_ALIASES = {
    "meta-llama/llama-3.3-70b-instruct":  "meta-llama/Llama-3.3-70B-Instruct",
    "meta-llama/llama-3.1-8b-instruct":   "meta-llama/Llama-3.1-8B-Instruct",
    "deepseek/deepseek-r1-0528":          "deepseek-ai/DeepSeek-R1-0528",
}


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
    key = os.environ.get("LLM_API_KEY") or os.environ.get("NEBIUS_API_KEY")
    if not key:
        raise RuntimeError(
            "No inference API key set. Put NEBIUS_API_KEY in compute.env "
            "(copy compute.env.example -> compute.env). "
            "(For a Modal-hosted model, util/hosted_model.py sets LLM_API_KEY for you.)"
        )
    return key


def resolve_model(requested):
    """The model id to use — NEVER a different model. `LLM_MODEL` overrides; otherwise the requested id
    passes through, with only same-model id-spelling normalized for Nebius. There is no fallback: if the
    id isn't available, the run reroutes to Modal or fails loudly (util/run.py) — it is never swapped."""
    _load()
    forced = os.environ.get("LLM_MODEL")
    if forced:
        return forced
    if endpoint_kind() == "custom":
        return requested
    return _NEBIUS_SAME_MODEL_ALIASES.get(requested, requested)


@functools.lru_cache(maxsize=1)
def _nebius_catalog():
    """Set of model ids Nebius currently serves (GET /v1/models), or None if it can't be fetched."""
    import urllib.request
    import json
    try:
        req = urllib.request.Request(NEBIUS_BASE_URL.rstrip("/") + "/models")
        key = os.environ.get("NEBIUS_API_KEY")
        if key:
            req.add_header("Authorization", f"Bearer {key}")
        with urllib.request.urlopen(req, timeout=15) as r:
            return {m.get("id") for m in json.load(r).get("data", [])}
    except Exception as e:
        # surface the reason (bad key, network, Nebius down) instead of hiding it; caller decides.
        print(f"[llm_config] WARNING: couldn't fetch the Nebius model catalog "
              f"({type(e).__name__}: {e}) — can't verify model availability.", flush=True)
        return None


def nebius_serves(model):
    """True / False if Nebius serves `model`; None if the catalog couldn't be checked."""
    _load()
    cat = _nebius_catalog()
    return None if cat is None else (model in cat)


def config():
    _load()  # diagnostic view — checks the key without raising, unlike api_key()
    has_key = bool(os.environ.get("LLM_API_KEY") or os.environ.get("NEBIUS_API_KEY"))
    return {"endpoint": endpoint_kind(), "base_url": base_url(),
            "has_key": has_key, "forced_model": os.environ.get("LLM_MODEL")}


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

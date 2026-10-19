"""Bridge the repo-root compute.env (LLM_PROVIDER) into inspect-ai's provider config.

inspect-ai selects a provider from the PREFIX of a model string and reads that provider's
credentials from provider-specific env vars:

    openrouter/<model>   -> OPENROUTER_API_KEY           (default path, unchanged)
    openai/<model>       -> OPENAI_API_KEY + OPENAI_BASE_URL

Both OpenRouter and Nebius are OpenAI-compatible endpoints, so when the root compute.env
selects LLM_PROVIDER=nebius we point inspect-ai's built-in ``openai/`` provider at Nebius by
setting OPENAI_BASE_URL / OPENAI_API_KEY, and rewrite the ``openrouter/...`` model strings to
``openai/<nebius-model>``. When LLM_PROVIDER is openrouter (the default) nothing is touched and
the shipped OpenRouter path runs exactly as before.

Call ``apply()`` once at startup; call ``map_model(s)`` on each inspect-ai model string.
"""
import os

# Locate and import the repo-root llm_config (its own venv may differ from ours).
import sys as _sys
import pathlib as _pl

_r = _pl.Path(__file__).resolve()
while _r != _r.parent and not (_r / "llm_config.py").exists():
    _r = _r.parent
_sys.path.insert(0, str(_r))
import llm_config  # noqa: E402


def _nebius() -> bool:
    return llm_config.provider() == "nebius"


def apply() -> str:
    """If LLM_PROVIDER=nebius, export OPENAI_BASE_URL/OPENAI_API_KEY for inspect-ai's
    openai provider. Returns the active provider name. No-op for openrouter."""
    if _nebius():
        os.environ["OPENAI_BASE_URL"] = llm_config.base_url()
        os.environ["OPENAI_API_KEY"] = llm_config.api_key()
    return llm_config.provider()


def map_model(model_str: str | None) -> str | None:
    """Rewrite an inspect-ai model string for the active provider.

    openrouter path: returned unchanged.
    nebius path: ``openrouter/openai/gpt-4o`` -> ``openai/<resolved-nebius-model>``.
    An already-openai/ or bare string is left as-is apart from Nebius model resolution.
    """
    if model_str is None or not _nebius():
        return model_str
    # Strip a leading provider prefix to recover the project-default model id that
    # llm_config.NEBIUS_MODEL_MAP is keyed on (e.g. "openai/gpt-4o").
    if model_str.startswith("openrouter/"):
        project_default = model_str[len("openrouter/"):]
    elif model_str.startswith("openai/"):
        project_default = model_str[len("openai/"):]
    else:
        project_default = model_str
    return "openai/" + llm_config.resolve_model(project_default)

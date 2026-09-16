"""
Factory for creating LLM clients.

All model traffic goes through OpenRouter — there is no direct-to-provider path.

This project supports OpenAI-family models only. The reason is structured output:
agent decisions are read back as JSON via `response_format`, and a model without that
support falls through to asking for JSON inside the prompt, whose failure mode is an
empty decision rather than an error. The factory therefore rejects an unsupported
model at startup instead of letting a run finish with unusable data.
"""

from typing import Tuple

from src.llm.capabilities import is_reasoning_model, supports_structured_output
from src.llm.providers.openrouter_client import OpenRouterClient
from src.llm.providers.parallel_openrouter_async import AsyncOpenRouterParallelClient


def normalize_model_name(model: str) -> str:
    """
    Normalise a model name for OpenRouter.

    A name that already carries a provider prefix is returned unchanged. A bare
    OpenAI name gains the `openai/` prefix. Anything else is left alone so that
    `require_supported_model` can reject it by name.

    Examples:
        >>> normalize_model_name("gpt-4o-mini")
        'openai/gpt-4o-mini'
        >>> normalize_model_name("openai/gpt-4o")
        'openai/gpt-4o'
        >>> normalize_model_name("claude-3.5-sonnet")
        'claude-3.5-sonnet'
    """
    if "/" in model:
        return model

    lower = model.lower()
    if lower.startswith("gpt-") or lower.startswith("o1") or lower.startswith("o3"):
        return f"openai/{model}"
    return model


def require_supported_model(model: str) -> str:
    """
    Qualify a model name and refuse the ones this project cannot run correctly.

    Returns the OpenRouter-qualified name. Raises ValueError for a non-OpenAI model,
    and warns for an OpenAI model that is not known to accept a JSON schema.
    """
    normalised = normalize_model_name(model)

    if not normalised.startswith("openai/"):
        raise ValueError(
            f"Model '{model}' is not supported. This project runs OpenAI models only "
            "(structured output is required to read agent decisions back reliably). "
            "Pass an openai/* model, e.g. openai/gpt-4o-mini — see .env.example."
        )

    if not supports_structured_output(normalised):
        print(
            f"WARNING: '{normalised}' is not in the structured-output table "
            "(src/llm/capabilities.py). Decisions will be requested as JSON inside the "
            "prompt, and a parse failure yields an EMPTY decision rather than an error. "
            "Check the run output before trusting it."
        )

    return normalised


def create_llm_clients(
    model: str,
    openrouter_api_key: str = None,
    temperature: float = 1.0,
    max_workers: int = 20,
) -> Tuple[object, object]:
    """
    Create the OpenRouter client and its matching parallel client.

    Args:
        model:              Model identifier (normalised and validated here).
        openrouter_api_key: OpenRouter API key.
        temperature:        Sampling temperature.
        max_workers:        Max concurrent requests for the parallel client.

    Returns:
        (llm_client, parallel_client)
    """
    normalised = require_supported_model(model)

    if not openrouter_api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not set. Add it to this project's .env "
            "(see .env.example)."
        )

    # Reasoning models spend much longer before emitting their first token.
    timeout = 300 if is_reasoning_model(normalised) else 120

    print(f"Using OpenRouter with model: {normalised}")
    llm_client = OpenRouterClient(
        api_key=openrouter_api_key,
        model=normalised,
        temperature=temperature,
        timeout=timeout,
    )
    parallel_client = AsyncOpenRouterParallelClient(
        api_key=openrouter_api_key,
        max_concurrent=max_workers,
        timeout=timeout,
    )
    return llm_client, parallel_client

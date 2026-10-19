"""
LLM provider clients for the pricing agents.

Hackathon standard: all model calls go through **OpenRouter** with one
``OPENROUTER_API_KEY``. The default model is the one the thesis used,
(closest available: ``mistralai/mistral-large-2512``); pick any other OpenRouter model id with
``MODEL_NAME`` / ``--model`` (rates: https://openrouter.ai/models).

The thesis's direct Mistral-SDK path (``LLM_PROVIDER=mistral``) and other
OpenAI-compatible endpoints are kept as opt-in alternatives for reproduction
or debugging, but participants should not need them.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

import sys as _sys, pathlib as _pl
_r = _pl.Path(__file__).resolve()
while _r != _r.parent and not (_r / "llm_config.py").exists(): _r = _r.parent
_sys.path.insert(0, str(_r))
from llm_config import make_client, resolve_model

Message = Dict[str, str]


@dataclass
class Preset:
    base_url: str
    key_env: str
    default_model: str
    needs_key: bool = True
    supports_seed: bool = False


# The thesis used mistral-large-2411. OpenRouter no longer serves it (checked 2026-09-15), so
# the default is the current Mistral Large; mistralai/mistral-large-2407 (same generation as
# 2411, 4x the price) is the closest match if fidelity matters more than budget.
THESIS_MODEL_OPENROUTER = "mistralai/mistral-large-2512"

PRESETS: Dict[str, Preset] = {
    # Hackathon default: one key, every model.
    "openrouter": Preset(
        "https://openrouter.ai/api/v1",
        "OPENROUTER_API_KEY",
        THESIS_MODEL_OPENROUTER,
        supports_seed=True,
    ),
    # Alternatives (not needed for the hackathon)
    "openai": Preset(
        "https://api.openai.com/v1", "OPENAI_API_KEY", "gpt-4.1-mini", supports_seed=True
    ),
    "google": Preset(
        "https://generativelanguage.googleapis.com/v1beta/openai/",
        "GOOGLE_API_KEY",
        "gemini-2.5-flash",
    ),
    "mistral-compat": Preset(
        "https://api.mistral.ai/v1", "MISTRAL_API_KEY", "mistral-small-latest"
    ),
    "ollama": Preset("http://localhost:11434/v1", "OLLAMA_API_KEY", "llama3.2:3b", needs_key=False),
    # Generic: set LLM_BASE_URL and LLM_API_KEY yourself.
    "openai-compatible": Preset("", "LLM_API_KEY", "", needs_key=False),
}


class FatalProviderError(RuntimeError):
    """Model not found / bad request / bad key: retrying cannot help, abort the run."""


class Provider:
    """Minimal interface every provider implements."""

    name: str = "unknown"
    model_name: str = "unknown"
    #: hosted APIs are rate limited by the Experiment; local servers are not
    is_remote: bool = True

    async def complete(
        self, messages: List[Message], temperature: float, seed: Optional[int]
    ) -> str:
        raise NotImplementedError


class MistralProvider(Provider):
    """Original thesis path: the official Mistral SDK."""

    name = "mistral"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY is not set (LLM_PROVIDER=mistral)")
        self.model_name = model or os.getenv("MODEL_NAME") or "mistral-large-2411"

    async def complete(self, messages, temperature, seed):
        from mistralai import Mistral

        async with Mistral(api_key=self.api_key) as client:
            kwargs = {}
            if seed is not None:
                kwargs["random_seed"] = seed
            response = await client.chat.complete_async(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"},
                **kwargs,
            )
        return response.choices[0].message.content


class OpenAICompatibleProvider(Provider):
    """OpenAI, Gemini, OpenRouter, Mistral's REST API, Ollama, LM Studio, vLLM..."""

    def __init__(
        self,
        preset: str = "openai",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        if preset not in PRESETS:
            raise ValueError(f"Unknown provider {preset!r}. Choose from {sorted(PRESETS)}")
        p = PRESETS[preset]
        self.name = preset
        self.base_url = base_url or os.getenv("LLM_BASE_URL") or p.base_url
        if not self.base_url:
            raise ValueError("LLM_BASE_URL must be set for provider 'openai-compatible'")
        self.api_key = api_key or os.getenv(p.key_env) or os.getenv("LLM_API_KEY")
        if p.needs_key and not self.api_key:
            raise ValueError(f"{p.key_env} is not set (LLM_PROVIDER={preset})")
        self.model_name = model or os.getenv("MODEL_NAME") or resolve_model(p.default_model)
        if not self.model_name:
            raise ValueError("MODEL_NAME must be set for provider 'openai-compatible'")
        self.supports_seed = p.supports_seed
        self.is_remote = "localhost" not in self.base_url and "127.0.0.1" not in self.base_url

        headers = {}
        if preset == "openrouter":
            headers = {
                "HTTP-Referer": "https://github.com/hackathon-ny-starter-repo",
                "X-Title": "hackathon algorithmic-pricing-llms",
            }
        # Client is built by the repo-root llm_config utility (compute.env selects provider +
        # base_url + key). base_url/api_key resolved above are kept for diagnostics / is_remote.
        self._client = make_client(async_=True, default_headers=headers)
        self._json_mode = True  # drop response_format if the model rejects it

    async def complete(self, messages, temperature, seed):
        kwargs = {}
        if seed is not None and self.supports_seed:
            kwargs["seed"] = seed
        if self._json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        from openai import AuthenticationError, BadRequestError, NotFoundError, PermissionDeniedError

        fatal = (NotFoundError, AuthenticationError, PermissionDeniedError)
        try:
            response = await self._client.chat.completions.create(
                model=self.model_name, messages=messages, temperature=temperature, **kwargs
            )
        except fatal as e:
            raise FatalProviderError(
                f"{self.model_name}: {e}. Check the model id at https://openrouter.ai/models "
                "and your OPENROUTER_API_KEY."
            ) from e
        except BadRequestError as e:
            if self._json_mode and "response_format" in str(e).lower():
                self._json_mode = False  # model does not support JSON mode; rely on the prompt
                kwargs.pop("response_format")
                response = await self._client.chat.completions.create(
                    model=self.model_name, messages=messages, temperature=temperature, **kwargs
                )
            else:
                raise FatalProviderError(f"{self.model_name}: {e}") from e
        if not response.choices:
            raise RuntimeError(f"{self.model_name}: empty response")
        return strip_code_fence(response.choices[0].message.content or "")


def strip_code_fence(text: str) -> str:
    """Remove <think>...</think> blocks (reasoning models) and ```json fences around the answer."""
    if "</think>" in text:
        text = text.rsplit("</think>", 1)[1]
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return text


def make_provider(
    kind: Optional[str] = None, model: Optional[str] = None, api_key: Optional[str] = None
) -> Provider:
    """Build a provider from ``kind`` (or the ``LLM_PROVIDER`` env var, default openrouter)."""
    kind = (kind or os.getenv("LLM_PROVIDER", "openrouter")).lower()
    if kind == "mistral":
        return MistralProvider(api_key=api_key, model=model)
    return OpenAICompatibleProvider(preset=kind, model=model, api_key=api_key)


def estimate_cost_note(n_calls: int, model: Optional[str] = None) -> str:
    model = model or os.getenv("MODEL_NAME") or THESIS_MODEL_OPENROUTER
    return (
        f"≈ {n_calls:,} model calls. Per-token rates for this model: https://openrouter.ai/{model}"
    )

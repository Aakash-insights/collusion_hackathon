"""
OpenRouter backend for the focal-point experiments (hackathon standard).

Every model call goes through **OpenRouter** with one ``OPENROUTER_API_KEY``, so the
experiments run on any laptop with no GPU. The paper's models were served locally
through HuggingFace transformers (``meta-llama/Llama-3.3-70B-Instruct`` was the
default in ``experiments.sh`` / the Dockerfile) or through the OpenAI / Gemini
APIs; the same families exist on OpenRouter, so the default model here is
``meta-llama/llama-3.3-70b-instruct``. Any OpenRouter model id works
(rates: https://openrouter.ai/models).

Model specs:
  * an OpenRouter id, e.g. ``meta-llama/llama-3.3-70b-instruct``, ``openai/gpt-4o``,
    ``qwen/qwen2.5-72b-instruct``, ``google/gemini-2.5-flash``;
  * a HuggingFace id from the paper (``meta-llama/Llama-3.3-70B-Instruct``) is
    mapped to its OpenRouter id automatically (see ``HF_TO_OPENROUTER``);
  * ``custom:<model>`` uses ``LLM_BASE_URL`` / ``LLM_API_KEY`` (any OpenAI-compatible
    server); ``ollama:<model>`` a free local Ollama. Not needed for the hackathon.

Sampling N responses per prompt is done with N separate calls: OpenRouter only
forwards ``n`` to some providers, and separate calls also make resume trivial.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Dict, Tuple

from dotenv import load_dotenv

from .llm import APIBaseLLM

load_dotenv()

import sys as _sys, pathlib as _pl
_r = _pl.Path(__file__).resolve()
while _r != _r.parent and not (_r / "llm_config.py").exists(): _r = _r.parent
_sys.path.insert(0, str(_r))
from llm_config import make_client, resolve_model

DEFAULT_MODEL = resolve_model("meta-llama/llama-3.3-70b-instruct")  # paper default (experiments.sh / Dockerfile)

#: HuggingFace ids used by the paper -> OpenRouter ids (only those that exist there).
HF_TO_OPENROUTER: Dict[str, str] = {
    "meta-llama/Llama-3.3-70B-Instruct": "meta-llama/llama-3.3-70b-instruct",
    "meta-llama/Llama-3.1-70B-Instruct": "meta-llama/llama-3.1-70b-instruct",
    "meta-llama/Meta-Llama-3-70B-Instruct": "meta-llama/llama-3-70b-instruct",
    "meta-llama/Llama-3.1-8B-Instruct": "meta-llama/llama-3.1-8b-instruct",
    "meta-llama/Meta-Llama-3-8B-Instruct": "meta-llama/llama-3-8b-instruct",
    "meta-llama/Llama-3.2-3B-Instruct": "meta-llama/llama-3.2-3b-instruct",
    "meta-llama/Llama-3.2-1B-Instruct": "meta-llama/llama-3.2-1b-instruct",
    "Qwen/Qwen2.5-72B-Instruct": "qwen/qwen2.5-72b-instruct",
    "Qwen/Qwen2.5-7B-Instruct": "qwen/qwen2.5-7b-instruct",
    "Qwen/Qwen2-72B-Instruct": "qwen/qwen-2-72b-instruct",
    "google/gemma-3-27b-it": "google/gemma-3-27b-it",
    "google/gemma-3-12b-it": "google/gemma-3-12b-it",
    "google/gemma-3-4b-it": "google/gemma-3-4b-it",
    "microsoft/Phi-4-mini-instruct": "microsoft/phi-4-mini-instruct",
    "openai/gpt-oss-120b": "openai/gpt-oss-120b",
    "openai/gpt-oss-20b": "openai/gpt-oss-20b",
    "deepseek-ai/DeepSeek-R1-Distill-Llama-70B": "deepseek/deepseek-r1-distill-llama-70b",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B": "deepseek/deepseek-r1-distill-qwen-32b",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B": "deepseek/deepseek-r1-distill-qwen-14b",
    "gpt-4o": "openai/gpt-4o",
    "gpt-5": "openai/gpt-5",
    "gpt-5.1": "openai/gpt-5.1",
    "gemini-3-flash-preview": "google/gemini-3-flash-preview",
}


@dataclass(frozen=True)
class Preset:
    base_url: str
    key_env: str
    needs_key: bool = True


PRESETS: Dict[str, Preset] = {
    "openrouter": Preset("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    # opt-in alternatives, not featured for the hackathon
    "ollama": Preset("http://localhost:11434/v1", "OLLAMA_API_KEY", needs_key=False),
    "custom": Preset("", "LLM_API_KEY", needs_key=False),
}


def parse_model_spec(spec: str) -> Tuple[str, str]:
    """'custom:foo' -> ('custom', 'foo'); a bare id -> ('openrouter', <mapped id>)."""
    if ":" in spec and spec.split(":", 1)[0] in PRESETS:
        provider, model = spec.split(":", 1)
        return provider, model
    return os.getenv("LLM_PROVIDER", "openrouter"), HF_TO_OPENROUTER.get(spec, spec)


def resolve_model_id(spec: str) -> str:
    """The id used in output folder names (OpenRouter id, without a provider prefix)."""
    return parse_model_spec(spec)[1]


def cost_note(n_calls: int, model_spec: str) -> str:
    _, model = parse_model_spec(model_spec)
    return f"≈ {n_calls:,} model calls. Per-token rates: https://openrouter.ai/{model}"


_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


class OpenRouterLLM(APIBaseLLM):
    """Chat-completions client (OpenAI protocol) pointed at OpenRouter by default."""

    def __init__(
        self,
        model_id: str,
        reasoning: str | None = None,
        num_return_sequences: int = 1,
        temperature: float | None = None,
        max_new_tokens: int | None = None,
        seed: int | None = None,
        top_p: float | None = None,
    ) -> None:
        self.provider, model = parse_model_spec(model_id)
        preset = PRESETS[self.provider]
        self.base_url = os.getenv("LLM_BASE_URL") if self.provider == "custom" else preset.base_url
        if not self.base_url:
            raise ValueError("LLM_BASE_URL must be set for provider 'custom'")
        self.api_key = os.getenv(preset.key_env) or os.getenv("LLM_API_KEY")
        if preset.needs_key and not self.api_key:
            raise ValueError(
                f"{preset.key_env} is not set (needed for {self.provider}:{model}). "
                "Copy .env.example to .env and paste the hackathon key."
            )

        effort = reasoning.strip().lower() if reasoning else None
        if effort is not None and effort not in {"none", "minimal", "low", "medium", "high", "xhigh"}:
            raise ValueError(f"Invalid reasoning effort '{reasoning}' (use low / medium / high).")
        super().__init__(
            model_id=model,
            reasoning=effort,
            num_return_sequences=num_return_sequences,
            reasoning_display=effort or "Default",
        )
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens
        self.seed = seed
        self.top_p = top_p
        self.is_local = "localhost" in self.base_url or "127.0.0.1" in self.base_url

        # Client built by the repo-root llm_config utility (compute.env selects provider +
        # base_url + key). base_url/api_key resolved above are kept for diagnostics / is_local.
        self.client = make_client()
        print(f"[INFO] Initialized OpenRouterLLM ({self.provider}) with model_id: {self.model_id}")
        print(
            f"[INFO] Reasoning effort: {self.reasoning_display} | temperature: {temperature} | seed: {seed}"
        )
        print(f"[INFO] API sequences per prompt: {self.num_return_sequences}")

    def _generate_raw_text(self, prompt: str) -> str:
        kwargs: dict = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        }
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        if self.top_p is not None:
            kwargs["top_p"] = self.top_p
        if self.max_new_tokens is not None:
            kwargs["max_tokens"] = self.max_new_tokens
        if self.seed is not None:
            kwargs["seed"] = self.seed
        if self.reasoning and self.provider == "openrouter":
            if self.reasoning == "none":
                kwargs["extra_body"] = {"reasoning": {"enabled": False}}
            else:
                kwargs["extra_body"] = {"reasoning": {"effort": self.reasoning}}
        response = self.client.chat.completions.create(**kwargs)
        text = response.choices[0].message.content or ""
        # reasoning models: drop the chain of thought, keep the answer
        return _THINK_RE.sub("", text).strip()

    def clear_cache(self) -> None:  # API model: nothing to free
        return None


def estimate_calls(prompt_plan, existing: dict, target_per_prompt: int) -> int:
    """Calls still needed to bring every prompt in the plan up to target_per_prompt."""
    n = 0
    for entry in prompt_plan:
        have = len(existing.get((entry["idx"], entry["prompt"]), []))
        n += max(0, target_per_prompt - have)
    return n

"""
LLM providers for the laptop-scale harness (run_game.py, branch_game.py, api_judge.py).

Hackathon standard: every model call goes through **OpenRouter** with one
``OPENROUTER_API_KEY``. The paper ran DeepSeek-R1 distills (7B/14B/32B) through
vLLM on GPUs; those distills are no longer served on OpenRouter, so the default
is the full reasoning model ``deepseek/deepseek-r1-0528``. Any OpenRouter model id works
(rates: https://openrouter.ai/models), e.g. ``qwen/qwen3-14b`` or
``openai/gpt-4.1-mini``.

Reasoning models return their chain of thought either inside ``<think>`` tags or
in OpenRouter's ``reasoning`` field; both are captured as the agent's "thoughts".

Other OpenAI-compatible endpoints (``openai:``, ``google:``, ``mistral:``,
``ollama:`` for a free local model, ``custom:``) remain as opt-in prefixes.
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

load_dotenv()

Message = Dict[str, str]


@dataclass(frozen=True)
class Preset:
    base_url: str
    key_env: str
    default_model: str
    needs_key: bool = True
    supports_seed: bool = False


# The paper ran DeepSeek-R1-Distill-Qwen 7B/14B/32B via vLLM. Those distills are no longer
# served on OpenRouter (checked 2026-09-15). run_game.py makes participants choose their agent
# model explicitly; this constant is only the fallback for bare `openrouter:` specs.
PAPER_MODEL_OPENROUTER = "deepseek/deepseek-r1-0528"
JUDGE_MODEL_OPENROUTER = "qwen/qwen3-14b"  # paper's judges: Qwen3-14B and others via vLLM

PRESETS: Dict[str, Preset] = {
    # Hackathon default: one key, every model.
    "openrouter": Preset(
        "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", PAPER_MODEL_OPENROUTER, supports_seed=True
    ),
    # Alternatives (not needed for the hackathon)
    "openai": Preset("https://api.openai.com/v1", "OPENAI_API_KEY", "gpt-4.1-mini", supports_seed=True),
    "google": Preset(
        "https://generativelanguage.googleapis.com/v1beta/openai/", "GOOGLE_API_KEY", "gemini-2.5-flash"
    ),
    "mistral": Preset("https://api.mistral.ai/v1", "MISTRAL_API_KEY", "mistral-small-latest"),
    "ollama": Preset("http://localhost:11434/v1", "OLLAMA_API_KEY", "llama3.2:3b", needs_key=False),
    # Generic: LLM_BASE_URL + LLM_API_KEY
    "custom": Preset("", "LLM_API_KEY", "", needs_key=False),
}


def parse_model_spec(spec: str) -> Tuple[str, str]:
    """'openai:gpt-4.1-mini' -> ('openai', 'gpt-4.1-mini'); bare name -> (LLM_PROVIDER, name)."""
    if ":" in spec and spec.split(":", 1)[0] in PRESETS:
        provider, model = spec.split(":", 1)
        return provider, model
    return os.getenv("LLM_PROVIDER", "openrouter"), spec


class FatalProviderError(RuntimeError):
    """Model not found / bad request / bad key: retrying cannot help, abort the run."""


class ChatProvider:
    """One OpenAI-compatible chat-completions client for a (provider, model) pair."""

    def __init__(self, spec: str, temperature: float = 1.0, max_tokens: int = 4096, reasoning: bool = True):
        """reasoning=False asks OpenRouter to disable thinking (used by the judge to keep answers short)."""
        self.provider, self.model = parse_model_spec(spec)
        preset = PRESETS[self.provider]
        self.base_url = os.getenv("LLM_BASE_URL") if self.provider == "custom" else preset.base_url
        if not self.base_url:
            raise ValueError("LLM_BASE_URL must be set for provider 'custom'")
        self.api_key = os.getenv(preset.key_env) or os.getenv("LLM_API_KEY")
        self.model = self.model or preset.default_model
        if preset.needs_key and not self.api_key:
            raise ValueError(f"{preset.key_env} is not set (needed for {self.provider}:{self.model})")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.supports_seed = preset.supports_seed
        self.is_local = "localhost" in self.base_url or "127.0.0.1" in self.base_url

        self.reasoning = reasoning

        from openai import OpenAI

        headers = {}
        if self.provider == "openrouter":
            headers = {
                "HTTP-Referer": "https://github.com/hackathon-ny-starter-repo",
                "X-Title": "hackathon llm-cartel",
            }
        self._client = OpenAI(
            base_url=self.base_url, api_key=self.api_key or "not-needed", default_headers=headers
        )

    @property
    def spec(self) -> str:
        return f"{self.provider}:{self.model}"

    def complete(self, messages: List[Message], seed: Optional[int] = None) -> Tuple[str, dict]:
        """Return (text, metrics). Raises on transport errors."""
        start = time.time()
        kwargs = {}
        if seed is not None and self.supports_seed:
            kwargs["seed"] = seed
        if self.provider == "openrouter" and not self.reasoning:
            kwargs["extra_body"] = {"reasoning": {"enabled": False}}
        from openai import AuthenticationError, BadRequestError, NotFoundError, PermissionDeniedError

        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs,
            )
        except (NotFoundError, AuthenticationError, PermissionDeniedError, BadRequestError) as e:
            raise FatalProviderError(
                f"{self.spec}: {e}. Check the model id at https://openrouter.ai/models and your key."
            ) from e
        if not resp.choices:
            raise RuntimeError(f"{self.spec}: empty response ({getattr(resp, 'error', None)})")
        msg = resp.choices[0].message
        text = msg.content or ""
        # OpenRouter puts reasoning-model thoughts in a separate field; fold them in as <think>
        extra = getattr(msg, "model_extra", None) or {}
        reasoning = extra.get("reasoning") or getattr(msg, "reasoning", None)
        if reasoning and "</think>" not in text:
            text = f"<think>{reasoning}</think>\n{text}"
        usage = getattr(resp, "usage", None)
        metrics = {
            "model": self.spec,
            "temperature": self.temperature,
            "latency_seconds": round(time.time() - start, 3),
            "tokens_input": getattr(usage, "prompt_tokens", None),
            "tokens_output": getattr(usage, "completion_tokens", None),
        }
        return text, metrics


_PRICE_PATTERNS = [
    r"chosen\s*price\s*[:=]\s*\**\s*\$?\s*(-?\d+(?:\.\d+)?)",
    r"price\s*[:=]\s*\**\s*\$?\s*(-?\d+(?:\.\d+)?)",
]


def split_thoughts_and_price(text: str) -> Tuple[str, Optional[float]]:
    """
    Parse 'My chosen price: 1.62'. A <think>...</think> block (reasoning models)
    plus anything before the *last* 'chosen price' line is the agent's 'thoughts'.
    """
    text = text.strip()
    think = ""
    if "</think>" in text:
        think, text = text.rsplit("</think>", 1)
        think = think.replace("<think>", "").strip()
        text = text.strip()
    matches = list(re.finditer(r"(my\s+)?chosen\s*price", text, flags=re.IGNORECASE))
    idx = matches[-1].start() if matches else -1
    thoughts = text[:idx].strip() if idx > 0 else ""
    thoughts = "\n".join(t for t in (think, thoughts) if t)
    tail = text[idx:] if idx >= 0 else text
    for pat in _PRICE_PATTERNS:
        m = re.search(pat, tail, flags=re.IGNORECASE)
        if m:
            return thoughts, round(float(m.group(1)), 2)
    # last resort: a lone number on the final line
    last = text.splitlines()[-1] if text else ""
    m = re.search(r"(-?\d+(?:\.\d+)?)", last)
    return thoughts, (round(float(m.group(1)), 2) if m else None)


def cost_note(n_calls: int, models: Optional[List[str]] = None) -> str:
    models = sorted({m for m in (models or []) if m}) or [PAPER_MODEL_OPENROUTER]
    links = " · ".join(f"https://openrouter.ai/{m.split(':', 1)[-1]}" for m in models)
    return f"≈ {n_calls:,} model calls. Reasoning models bill their thinking tokens too. Rates: {links}"

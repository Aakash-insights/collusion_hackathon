"""OpenRouter-backed LLM client for Liar's Bar.

The experiments were originally run against four local Hugging Face checkpoints
(7-8B instruct models on H100s) through `LocalLLMClient`. This client keeps that
interface -- `chat(messages, model) -> (content, reasoning_content)` -- along with the
per-model sampling parameters, the cap on generated tokens and the response clean-up
the local client applied, so the game logic sees the same kind of text. Only the
inference moves from local GPUs to OpenRouter.

`player.py` always imported an `LLMClient` from this module; the file was missing from
the published repository, so this also restores the import.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv
from openai import OpenAI

# This project's own .env (llm-agent-collusion-2/.env), by explicit path so a .env in
# a parent directory can never leak in.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_PROJECT_ROOT / ".env")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class LLMClient:
    """Chat client with the same contract as the original local client."""

    # Short name -> OpenRouter model id.
    # llama-3.1-8b and qwen2.5-7b are the original checkpoints. The other two replace
    # models that are no longer served on OpenRouter (Meta-Llama-3-8B-Instruct and
    # Mistral-7B-Instruct-v0.3); both substitutes are drawn from the authors' own
    # extended model table. See notes/llm-agent-collusion-2.md for the decision.
    MODEL_MAP = {
        "llama-3.1-8b": "meta-llama/llama-3.1-8b-instruct",
        "qwen2.5-7b":   "qwen/qwen-2.5-7b-instruct",
        "llama-3.2-3b": "meta-llama/llama-3.2-3b-instruct",   # was llama-3-8b
        "ministral-8b": "mistralai/ministral-8b-2512",        # was mistral-7b
    }

    def __init__(self, api_key: str | None = None, base_url: str = OPENROUTER_BASE_URL):
        api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key or api_key == "your-openrouter-key-here":
            raise ValueError(
                "OPENROUTER_API_KEY is not set (or is still the placeholder). "
                f"Copy .env.example to {_PROJECT_ROOT / '.env'} and fill it in."
            )
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        print(f"LLMClient initialized (OpenRouter). Models: {list(self.MODEL_MAP)}")

    # ------------------------------------------------------------------
    # Sampling: exactly what the local client used, per model family, including its
    # hard cap on new tokens (256 for Llama/Qwen, 512 for the rest) that overrode the
    # 4096 default of chat().
    # ------------------------------------------------------------------
    @staticmethod
    def _sampling(model: str) -> Dict[str, Any]:
        name = model.lower()
        if "llama" in name:
            return dict(max_tokens=256, temperature=0.8, top_p=0.95, top_k=40, repetition_penalty=1.1)
        if "qwen" in name:
            return dict(max_tokens=256, temperature=0.8, top_p=0.9, top_k=50, repetition_penalty=1.05)
        return dict(max_tokens=512, temperature=0.7, top_p=0.9, top_k=50, repetition_penalty=1.02)

    def chat(self, messages: List[Dict[str, str]], model: str = "llama-3.1-8b",
             max_new_tokens: int = 4096) -> Tuple[str, str]:
        """Chat with a model.

        Returns:
            tuple: (content, reasoning_content) -- reasoning_content is always "" here,
            as it was for the local models.
        """
        try:
            print(f"LLM Request to {model}: {messages}")
            if model not in self.MODEL_MAP:
                print(f"Unsupported model: {model}. Supported models: {list(self.MODEL_MAP)}")
                return "", ""

            params = self._sampling(model)
            completion = self._client.chat.completions.create(
                model=self.MODEL_MAP[model],
                messages=messages,
                max_tokens=min(max_new_tokens, params["max_tokens"]),
                temperature=params["temperature"],
                top_p=params["top_p"],
                # Not first-class in the OpenAI SDK; OpenRouter reads them from the body.
                extra_body={"top_k": params["top_k"], "repetition_penalty": params["repetition_penalty"]},
            )
            response = self._clean_response(completion.choices[0].message.content or "", model)
            print(f"LLM Response: {response}")
            return response, ""
        except Exception as e:
            print(f"LLM error: {str(e)}")
            return "", ""

    # ------------------------------------------------------------------
    # Response clean-up, verbatim from the local client.
    # ------------------------------------------------------------------
    def _clean_response(self, response: str, model: str) -> str:
        """Clean response to remove hallucinations and formatting issues"""
        response = re.sub(r'^(Assistant:|AI:|Human:|User:)', '', response).strip()
        response = re.sub(r'\n(Assistant:|AI:|Human:|User:).*$', '', response, flags=re.MULTILINE | re.DOTALL)
        for stop_phrase in ["Human:", "User:", "\n\n---", "```\n\n", "<|", "[INST]"]:
            if stop_phrase in response:
                response = response.split(stop_phrase)[0].strip()
        if response.strip().startswith('{') or '```json' in response:
            response = self._extract_clean_json(response)
        return response.strip()

    def _extract_clean_json(self, response: str) -> str:
        """Extract and clean JSON from response"""
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        for stop_phrase in ["Human:", "User:", "Assistant:"]:
            if stop_phrase in response:
                response = response.split(stop_phrase)[0].strip()
        json_match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})', response)
        if json_match:
            json_str = json_match.group(1)
            json_str = re.sub(r':\s*(?!true\b|false\b|null\b)([A-Za-z][A-Za-z0-9]*)', r': "\1"', json_str)
            json_str = re.sub(r'\[\s*(?!true\b|false\b|null\b)([A-Za-z0-9]+)\s*,\s*(?!true\b|false\b|null\b)([A-Za-z0-9]+)\s*\]', r'["\1", "\2"]', json_str)
            json_str = re.sub(r'\[\s*(?!true\b|false\b|null\b)([A-Za-z0-9]+)\s*\]', r'["\1"]', json_str)
            try:
                parsed = json.loads(json_str)
                return json.dumps(parsed, indent=2)
            except json.JSONDecodeError:
                return json_str
        return response.strip()

    # Kept for interface compatibility with the local client.
    def list_available_models(self) -> List[str]:
        return list(self.MODEL_MAP)

    def get_model_info(self) -> Dict[str, Any]:
        return {"backend": "openrouter", "models": dict(self.MODEL_MAP)}

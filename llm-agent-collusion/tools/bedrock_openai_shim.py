"""Minimal OpenAI-compatible /v1/chat/completions server in front of AWS Bedrock (Converse API).

Sprint addition (see CHANGES_SPRINT.md). The simulation talks to any OpenAI-compatible endpoint via
LLM_BASE_URL / LLM_API_KEY; Bedrock needs SigV4-signed requests, so this shim translates.
The OpenAI `model` field is used verbatim as the Bedrock modelId (e.g. qwen.qwen3-235b-a22b-2507-v1:0).
Bedrock has no JSON mode, so `response_format={"type": "json_object"}` is emulated with a short system hint
(without it Qwen over-escapes, emitting {\\"key\\": ...} with literal backslashes). The sim's own prompts are untouched.

    AWS_PROFILE=<profile> AWS_REGION=ap-south-1 \
      uv run --no-project --with boto3 python tools/bedrock_openai_shim.py --port 8765

    export LLM_BASE_URL=http://127.0.0.1:8765/v1 LLM_API_KEY=local
"""

import argparse
import json
import os
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import boto3
from botocore.config import Config

_session = boto3.Session(profile_name=os.getenv("AWS_PROFILE"), region_name=os.getenv("AWS_REGION", "ap-south-1"))
_bedrock = _session.client("bedrock-runtime", config=Config(read_timeout=120, retries={"max_attempts": 3, "mode": "adaptive"}))


JSON_HINT = (
    "Respond with a single raw JSON object only: no code fences, no text before or after it. "
    "Do NOT backslash-escape the quotation marks that delimit keys and string values; "
    "only escape special characters (quotes, newlines) that appear inside string values."
)


def _converse(body: dict) -> dict:
    system, messages = [], []
    if (body.get("response_format") or {}).get("type") == "json_object":
        system.append({"text": JSON_HINT})
    for m in body["messages"]:
        text = m["content"] if isinstance(m["content"], str) else "".join(p.get("text", "") for p in m["content"])
        if m["role"] == "system":
            system.append({"text": text})
        else:
            messages.append({"role": m["role"], "content": [{"text": text}]})
    cfg = {"maxTokens": body.get("max_tokens") or body.get("max_completion_tokens") or 4000}
    if body.get("temperature") is not None:
        cfg["temperature"] = body["temperature"]
    if body.get("top_p") is not None:
        cfg["topP"] = body["top_p"]
    kwargs = {"modelId": body["model"], "messages": messages, "inferenceConfig": cfg}
    if system:
        kwargs["system"] = system
    r = _bedrock.converse(**kwargs)
    text = "".join(b.get("text", "") for b in r["output"]["message"]["content"])
    u = r.get("usage", {})
    return {
        "id": "chatcmpl-" + uuid.uuid4().hex,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": body["model"],
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": text},
            "finish_reason": "length" if r.get("stopReason") == "max_tokens" else "stop",
        }],
        "usage": {
            "prompt_tokens": u.get("inputTokens", 0),
            "completion_tokens": u.get("outputTokens", 0),
            "total_tokens": u.get("totalTokens", 0),
        },
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict) -> None:
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        if not self.path.rstrip("/").endswith("/chat/completions"):
            return self._send(404, {"error": {"message": f"unsupported path {self.path}"}})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            self._send(200, _converse(body))
        except Exception as e:  # surface Bedrock errors to the client as an API error
            code = 429 if "Throttling" in type(e).__name__ else 500
            self._send(code, {"error": {"message": f"{type(e).__name__}: {e}", "type": "bedrock_error"}})

    def log_message(self, fmt, *args) -> None:  # keep stdout quiet
        pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    print(f"bedrock shim on http://127.0.0.1:{args.port}/v1 (profile={os.getenv('AWS_PROFILE')}, region={_session.region_name})", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()

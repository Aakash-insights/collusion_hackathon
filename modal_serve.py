"""Host an open model on Modal as an OpenAI-compatible endpoint (inference fallback).

Use this when an experiment can't run on Nebius AI Studio — e.g. it needs a model Nebius doesn't
serve, or a capability/gate that Nebius trips. You serve the model yourself on Modal (vLLM), get an
OpenAI-compatible URL, and point every project at it by setting these in `compute.env`:

    LLM_BASE_URL=https://<your-app>--serve.modal.run/v1
    LLM_API_KEY=<the key you set below>        # if MODAL_SERVE_API_KEY is set
    LLM_MODEL=<MODEL below>                     # the served model id

`llm_config.make_client()` then routes every project through your Modal model — same interface as
Nebius, different endpoint.

--------------------------------------------------------------------------------------------------
SETUP
    pip install modal
    modal setup                                 # redeem your hackathon credits
    # (gated models like Llama need a HF token:)
    modal secret create huggingface HF_TOKEN=hf_...
    # (optional: protect the endpoint with a key)
    modal secret create modal-serve MODAL_SERVE_API_KEY=sk-local-...

DEPLOY
    MODAL_SERVE_MODEL="Qwen/Qwen2.5-7B-Instruct" modal deploy modal_serve.py
    # -> prints a URL like  https://<you>--serve.modal.run  ; your endpoint is that + "/v1"

Pick GPU to fit the model:  A10G (24GB) ~ up to 8B · A100-40GB ~ up to 32B · H100 for 70B.
Scaffolding ahead of live credits — validate once your Modal account is funded.
"""
import os
import subprocess

import modal

# ---- config (override via env at deploy time) ----------------------------------------------------
MODEL = os.environ.get("MODAL_SERVE_MODEL", "Qwen/Qwen2.5-7B-Instruct")  # open by default (no HF gate)
GPU = os.environ.get("MODAL_SERVE_GPU", "A10G")
VLLM_PORT = 8000

app = modal.App("hackathon-serve")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("vllm==0.6.6", "huggingface_hub[hf_transfer]==0.26.2")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

# HF token (for gated models) + optional endpoint API key. Both secrets are optional: if you haven't
# created them, drop the corresponding entry.
_secrets = []
for name in ("huggingface", "modal-serve"):
    try:
        _secrets.append(modal.Secret.from_name(name))
    except Exception:
        pass


@app.function(
    image=image,
    gpu=GPU,
    timeout=24 * 3600,
    scaledown_window=300,            # spin down after 5 min idle to save credits
    secrets=_secrets,
)
# (for higher throughput on one GPU, add `@modal.concurrent(max_inputs=N)` above web_server)
@modal.web_server(port=VLLM_PORT, startup_timeout=900)
def serve():
    """Launch vLLM's OpenAI-compatible server; Modal proxies it to a public URL."""
    cmd = [
        "python", "-m", "vllm.entrypoints.openai.api_server",
        "--model", MODEL,
        "--host", "0.0.0.0",
        "--port", str(VLLM_PORT),
        "--served-model-name", MODEL,
    ]
    api_key = os.environ.get("MODAL_SERVE_API_KEY")
    if api_key:
        cmd += ["--api-key", api_key]   # clients must send this as their key
    subprocess.Popen(" ".join(cmd), shell=True)

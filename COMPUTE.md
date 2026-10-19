# Compute & inference: one config, every project

Set your key once, at the repo root, and every project uses it. Two layers, two sponsors:

- **Inference — Nebius AI Studio (default).** *Where model calls go.* An OpenAI-compatible endpoint
  serving open models. Every project routes through it automatically.
- **Compute — Modal.** *Where your code runs.* Offload heavy/parallel runs and GPU work. Modal can
  **also host a model** (`util/modal_serve.py`) as an OpenAI-compatible endpoint — the inference fallback
  for the few experiments Nebius can't serve cleanly. Modal **authenticates through your web browser**
  (run `modal setup`); **ask in the hackathon Slack channel about redeeming your Modal credits.**

> **One spot:** copy `compute.env.example` → `compute.env`, add `NEBIUS_API_KEY`, done. `util/llm_config.py`
> feeds it to every project's client; `util/modal_run.py` feeds the same file to cloud runs.

---

## Quick start

```bash
cp compute.env.example compute.env      # at the repo root
# edit compute.env:  NEBIUS_API_KEY=...
```
Run any project exactly as its README says — it picks up `compute.env` automatically.

---

## 1. The one spot — `compute.env`

| key | meaning |
|---|---|
| `NEBIUS_API_KEY` | your Nebius AI Studio key (default inference) |
| `LLM_MODEL` *(opt)* | force one model id across every project |
| `NEBIUS_DEFAULT_MODEL` *(opt)* | fallback when a project default has no Nebius equivalent |
| `LLM_BASE_URL` *(opt)* | a custom OpenAI-compatible endpoint, e.g. your **Modal-hosted** model |
| `LLM_API_KEY` *(opt)* | key for that custom endpoint |

`compute.env` is **gitignored** — keys never get committed.

---

## 2. Inference — Nebius (default)

Put `NEBIUS_API_KEY` in `compute.env`; everything routes through `https://api.studio.nebius.com/v1`.
Nebius serves **open** models, so each project's paper-default model id is **auto-mapped** to a Nebius
equivalent (`NEBIUS_MODEL_MAP` in `util/llm_config.py`); unmapped ids fall back to `NEBIUS_DEFAULT_MODEL`
(default `meta-llama/Llama-3.3-70B-Instruct`). Force one model everywhere with `LLM_MODEL`.

---

## 3. Modal — compute, and model hosting

**Run a project on Modal** (offload long/parallel runs, or GPU extras):
```bash
pip install modal && modal setup           # redeem your hackathon credits
modal run util/modal_run.py --project llm-cartel \
  --cmd "uv run python run_game.py --rounds 30"
modal run util/modal_run.py --project llm-cartel --gpu a10g --cmd "uv run python steering/<script>.py"
```
`util/modal_run.py` reads your `compute.env` automatically (injected as a Secret).

> **Where does my Modal key go?** Modal is **not** configured in `compute.env`. You authenticate the
> Modal CLI once with **`modal setup`** (opens a browser; stores a token in `~/.modal.toml`), and your
> hackathon Modal **credits attach to that account** (redeem via the link in Slack/Luma). `compute.env`
> holds only your **Nebius** inference key. Secrets that Modal injects *into* containers — your Nebius
> key for cloud runs, a HuggingFace token for gated models, an optional endpoint key — are created with
> `modal secret create …`; the Nebius key is injected automatically from `compute.env` by
> `util/modal_run.py`, so you usually don't create that one by hand.

**Host a model on Modal** (inference fallback — when Nebius can't serve/accept what an experiment
needs):
```bash
MODAL_SERVE_MODEL="Qwen/Qwen2.5-7B-Instruct" modal deploy util/modal_serve.py
# -> gives a URL; then in compute.env:
#    LLM_BASE_URL=https://<you>--serve.modal.run/v1
#    LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
```
Now every project talks to **your** Modal model through the same `llm_config` interface.

---

## 4. Which provider does each experiment need?

Nebius ✓ = works directly · Nebius (sub) = open-model substitute for a GPT/Gemini default ·
Modal-host = use `util/modal_serve.py` if the default/capability doesn't fit Nebius.

| project | inference | compute | notes |
|---|---|---|---|
| algorithmic-pricing-llms | **Nebius ✓** (Mistral-Large) | laptop; Modal for sweeps | — |
| llm-cartel | **Nebius ✓** (DeepSeek-R1) | laptop for the game; **Modal GPU** for the steering `[gpu]` extra | — |
| focal-points | **Nebius ✓** (Llama-3.3-70B) | laptop; Modal for scale | its OpenAI **Batch-API** path is OpenAI-only (optional, ignore) |
| llm-agent-collusion-2 | **Nebius ✓** (open models) | Modal for tournaments | — |
| algorithmic/collusion sweeps | Nebius ✓ | Modal for parallel runs | — |
| llm-agent-collusion | **Nebius (sub)** (GPT-4.1→Llama-70B) | laptop; Modal for sweeps | paper-faithful GPT needs a Modal-hosted GPT-class model |
| colosseum | **Nebius (sub)** (GPT-4o-mini→Llama-8B) | **Modal** (topology sweeps) | — |
| trace-guard | **Nebius (sub)** via its shim (GPT-4o→Llama) | **Docker required** (local; Modal-with-Docker is advanced) | doesn't fit the basic `util/modal_run.py` |
| steganographic-collusion | **Nebius ✓** (hosted configs); **none** for scripted/distilgpt2 | laptop; Modal for sweeps | scripted + distilgpt2 configs make **no API calls** |
| **llm-trust-breaking** | **Nebius or Modal-host — needs JSON-capable model** | **Modal** (~8k-call full run) | enforces structured output; pick a Nebius model that supports `response_format`, or host one on Modal (`util/modal_serve.py`). Its OpenAI-only gate was relaxed to a warning. |
| **collusive-llm-agents** | **Nebius — needs JSON-capable model** | laptop (notebooks) | notebooks require `response_format`; use a Nebius model that supports it, or Modal-host one |

**Rule of thumb:** open-model experiments → Nebius; GPT/Gemini-default ones → Nebius with an open
substitute (or Modal-host a matching model for fidelity); **JSON-mode** ones (trust-breaking,
collusive notebooks) need a response_format-capable model on whichever endpoint; **GPU extra**
(llm-cartel steering) → Modal GPU; **Docker** (trace-guard) → local Docker.

---

## 5. Use it in your own script

```python
import sys, pathlib
_r = pathlib.Path(__file__).resolve()
while _r != _r.parent and not (_r / "util" / "llm_config.py").exists():
    _r = _r.parent
sys.path.insert(0, str(_r / "util"))
from llm_config import make_client, resolve_model

client = make_client()                          # Nebius (or your Modal endpoint)
model  = resolve_model("meta-llama/llama-3.3-70b-instruct")
resp = client.chat.completions.create(model=model, messages=[{"role": "user", "content": "hi"}])
```
Async: `make_client(async_=True)`. Raw values: `llm_config.base_url()`, `.api_key()`,
`.endpoint_kind()`. Jupyter (no `__file__`): start from `pathlib.Path.cwd()`.

---

## 6. How it works

- **`util/llm_config.py`** — shared inference interface: `make_client()` (Nebius by default, or your
  `LLM_BASE_URL`) + `resolve_model()`. Every project's client calls these.
- **`util/modal_run.py`** — runs a project on Modal, injecting the same `compute.env`.
- **`util/modal_serve.py`** — hosts an open model on Modal (vLLM) as an OpenAI-compatible endpoint for
  the fallback cases.

---

## 7. Caveats

- **JSON-mode projects** (`llm-trust-breaking`, `collusive-llm-agents`) need a model that supports
  `response_format`. On Nebius pick one that does; otherwise host one on Modal. trust-breaking's
  OpenAI-only gate is now a warning, not a hard error.
- **Model substitution:** GPT/Gemini defaults map to Llama models on Nebius. For paper fidelity to a
  specific GPT model, host an equivalent on Modal and set `LLM_MODEL`.
- **GPU / Docker:** `llm-cartel` steering needs a GPU (Modal `--gpu`); `trace-guard` needs Docker to
  run (not the basic Modal runner).
- **Gated models on Modal:** Llama needs a HF token — `modal secret create huggingface HF_TOKEN=...`
  (the default `util/modal_serve.py` model, Qwen, is open and needs none).
- Scaffolding ahead of live sponsor credits — validate once Nebius/Modal are funded.

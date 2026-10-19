# Compute & inference: one config, every project

Set your key once, at the repo root, and every project uses it. Two layers, two sponsors:

- **Inference — Nebius AI Studio (default).** *Where model calls go.* An OpenAI-compatible endpoint
  serving open models. Every project routes through it automatically.
- **Compute — Modal.** *Where your code runs.* Offload heavy/parallel runs and GPU work.
  **There's no Modal key to paste anywhere** — you just sign in through your browser once by running
  `modal setup`, and your credits attach to that account (**ask in the hackathon Slack channel to get
  your Modal credits set up**). Modal can also host a model on demand (`util/hosted_model.py` boots one
  for a run and tears it down) — the inference fallback for the few experiments Nebius can't serve cleanly.

> **One spot:** copy `compute.env.example` → `compute.env`, add `NEBIUS_API_KEY`, done. `util/llm_config.py`
> feeds it to every project's client. For cloud runs, `util/modal_run.py` also passes it into the Modal
> container (as a Secret) so your code can still reach Nebius there.

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
| `LLM_MODEL` *(opt)* | pick one model for every project (an exact Nebius model id) |

`compute.env` is **gitignored** — keys never get committed.

---

## 2. Inference — Nebius (default)

Put `NEBIUS_API_KEY` in `compute.env`; model calls route through `https://api.studio.nebius.com/v1`.
**No model is ever substituted and there is no default model.** To run an experiment with a specific
model, use the **one entry point** below (§3) — it sends the model to Nebius if Nebius serves it,
otherwise hosts it on Modal for you, otherwise stops with a clear error. Model ids are written in Nebius
(Hugging Face) casing throughout — nothing is rewritten or substituted.

---

## 3. Running an experiment — the one entry point

**There is a single way to run any inference experiment**, and it handles everything automatically:

```bash
python -m util.run --model <model id> -- <the experiment's normal command>
# e.g.
python -m util.run --model Qwen/Qwen2.5-7B-Instruct -- \
  bash -c "cd colosseum && uv run python -m experiments.collusion.run --config ..."
```

What it does, in order — **you never choose Nebius-vs-Modal yourself**:

1. **Checks Nebius** for the model → if served, runs on Nebius. Done.
2. **Not on Nebius?** Prints a warning and **automatically hosts it on Modal** just for this run, then
   tears it down when the run ends.
3. **Can't host it?** The run **stops with a big error that explains why** and what to do:
   - **gated on Hugging Face** → the model's access page (`https://huggingface.co/<model>`) and the exact
     fix (`modal secret create huggingface HF_TOKEN=…`);
   - **closed model, no open weights** (e.g. `openai/*`, `claude`, `gemini`) → tells you to pick an
     available open model.

No model is ever silently swapped for another. If something is misconfigured, the run fails loudly and
tells you how to fix it — it never quietly runs the "wrong" thing.

> **First time using Modal?** You don't paste a Modal key anywhere. Run **`modal setup`** once (opens a
> browser; stores a token in `~/.modal.toml`); your hackathon Modal **credits attach to that account**
> (redeem via the link in Slack/Luma). `compute.env` holds only your **Nebius** key — step 2 above injects
> it into the Modal container for you. Gated models additionally need
> `modal secret create huggingface HF_TOKEN=…` (the error in step 3 tells you when).

### Offloading heavy compute to Modal (separate from inference routing)

If you want to run a **whole project** on Modal's machines (long/parallel runs, or a GPU extra) rather
than your laptop — this is about *where your code runs*, not which inference endpoint it uses:
```bash
pip install modal && modal setup
modal run util/modal_run.py --project llm-cartel --cmd "uv run python run_game.py --rounds 30"
modal run util/modal_run.py --project llm-cartel --gpu a10g --cmd "uv run python steering/<script>.py"
```
`util/modal_run.py` injects your `compute.env` automatically (as a Secret), so inference still reaches
Nebius from inside the container.

<details><summary>Advanced: force a Modal-hosted model from Python (skip the Nebius check)</summary>

```python
from hosted_model import hosted_model          # util/ on sys.path (see §5 bootstrap)
with hosted_model(model="Qwen/Qwen2.5-7B-Instruct"):
    ...  # your code; llm_config points at the Modal model in here
# torn down on exit
```
</details>

---

## 4. Which provider does each experiment need?

Run every row through **the one entry point** (§3): `python -m util.run --model <id> -- <cmd>` — it routes
to Nebius or Modal automatically, or stops with a clear error. Nothing is ever substituted.
Nebius ✓ = an open default works directly · **pick open** = its paper default is a closed model
(GPT/Gemini) that isn't available, so pass an open model as `--model`.

| project | inference | compute | notes |
|---|---|---|---|
| algorithmic-pricing-llms | **Nebius ✓** (Mistral-Large) | laptop; Modal for sweeps | — |
| llm-cartel | **Nebius ✓** (DeepSeek-R1) | laptop for the game; **Modal GPU** for the steering `[gpu]` extra | — |
| focal-points | **Nebius ✓** (Llama-3.3-70B) | laptop; Modal for scale | its OpenAI **Batch-API** path is OpenAI-only (optional, ignore) |
| llm-agent-collusion-2 | **Nebius ✓** (open models) | Modal for tournaments | — |
| algorithmic/collusion sweeps | Nebius ✓ | Modal for parallel runs | — |
| llm-agent-collusion | **pick open** (default GPT-4.1 unavailable) | laptop; Modal for sweeps | set `LLM_MODEL` to an open model |
| colosseum | **pick open** (default GPT-4o-mini unavailable) | **Modal** (topology sweeps) | set `LLM_MODEL` to an open model |
| trace-guard | **pick open** via its shim (default GPT-4o unavailable) | **Docker required** (local) | set an open model; doesn't fit the basic `util/modal_run.py` |
| steganographic-collusion | **Nebius ✓** (hosted configs); **none** for scripted/distilgpt2 | laptop; Modal for sweeps | scripted + distilgpt2 configs make **no API calls** |
| **llm-trust-breaking** | **Nebius or Modal-host — needs JSON-capable model** | **Modal** (~8k-call full run) | enforces structured output; pick a Nebius model that supports `response_format`, or run it via `util/hosted_model.py`. Its OpenAI-only gate was relaxed to a warning. |
| **collusive-llm-agents** | **Nebius — needs JSON-capable model** | laptop (notebooks) | notebooks require `response_format`; set `LLM_MODEL` to a model that supports it (via `python -m util.run` if it isn't on Nebius) |

**Rule of thumb:** always launch with `python -m util.run --model <id> -- <cmd>` — it picks Nebius vs
Modal for you and fails loudly if it can't serve the model (nothing is substituted). For closed-default
(GPT/Gemini) experiments just pass an open model as `--model`. **JSON-mode** ones (trust-breaking,
collusive notebooks) need a response_format-capable model; **GPU extra** (llm-cartel steering) → Modal
GPU; **Docker** (trace-guard) → local Docker.

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

- **`util/llm_config.py`** — shared inference interface: `make_client()` (Nebius by default; or a Modal
  endpoint while `util/hosted_model.py` is active) + `resolve_model()`. Every project's client calls these.
- **`util/run.py`** — run an experiment with a chosen model; checks `nebius_serves()` and routes to
  Nebius, else Modal, else fails loudly. Never substitutes a model.
- **`util/modal_run.py`** — runs a project on Modal (compute), injecting the same `compute.env`.
- **`util/hosted_model.py`** — boots a model on Modal for one run and tears it down, wiring the endpoint
  into `llm_config` automatically. (`util/modal_serve.py` is the underlying vLLM server it runs.)

---

## 7. Caveats

- **JSON-mode projects** (`llm-trust-breaking`, `collusive-llm-agents`) need a model that supports
  `response_format`. On Nebius pick one that does; otherwise run via `util/hosted_model.py`.
  trust-breaking's OpenAI-only gate is now a warning, not a hard error.
- **No model substitution:** a model is never silently swapped for another and there is no default
  model. Closed models (GPT/Gemini) aren't available; pick an open model via `LLM_MODEL`. If the model
  you ask for isn't on Nebius, `python -m util.run` hosts it on Modal — or fails loudly if it can't be
  served anywhere.
- **GPU / Docker:** `llm-cartel` steering needs a GPU (Modal `--gpu`); `trace-guard` needs Docker to
  run (not the basic Modal runner).
- **Gated models on Modal:** some open-weight models (e.g. Llama, Gemma) are **gated** on Hugging Face —
  you must accept their license and use a token that has access. When you host one via `python -m util.run`
  / `util/hosted_model.py`, it **preflights HF access and fails loudly** if you don't have it, printing
  the model's access page (`https://huggingface.co/<model>`) and the fix: accept the license there, then
  `modal secret create huggingface HF_TOKEN=hf_...` (and `export HF_TOKEN=hf_...` locally). The default
  `util/modal_serve.py` model, Qwen, is open and needs none.
- Scaffolding ahead of live sponsor credits — validate once Nebius/Modal are funded.

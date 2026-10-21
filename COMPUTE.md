# Compute & inference: one config, every project

Set your key once, at the repo root, and every project uses it. Two layers, two sponsors:

- **Inference — Nebius AI Studio (default), with OpenRouter as a fallback.** *Where model calls go.*
  Nebius is an OpenAI-compatible endpoint serving open models; OpenRouter covers models Nebius doesn't,
  including closed ones (GPT/Gemini/Claude). The one entry point picks between them automatically.
- **Compute — Modal.** *Where your code runs.* Offload heavy/parallel runs and GPU work.
  **There's no Modal key to paste anywhere** — you just sign in through your browser once by running
  `modal setup`, and your credits attach to that account (**ask in the hackathon Slack channel to get
  your Modal credits set up**). Modal can also host a model on demand (`util/hosted_model.py` boots one
  for a run and tears it down) — the last-resort way to serve a model on *neither* provider (e.g. a
  custom fine-tune, or when you need vLLM-level control).

> **One spot:** copy `compute.env.example` → `compute.env`, add `NEBIUS_API_KEY` (and optionally
> `OPENROUTER_API_KEY`), done. `util/llm_config.py` feeds it to every project's client. For cloud runs,
> `util/modal_run.py` also passes it into the Modal container (as a Secret) so your code can still reach
> inference there.

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
| `OPENROUTER_API_KEY` *(opt)* | enables the OpenRouter fallback — models Nebius lacks, incl. closed (GPT/Gemini/Claude) |
| `LLM_MODEL` *(opt)* | pick one model for every project (an exact Nebius / Hugging Face model id) |

`compute.env` is **gitignored** — keys never get committed.

---

## 2. Inference — Nebius (default) + OpenRouter (fallback)

Put `NEBIUS_API_KEY` in `compute.env` (and/or `OPENROUTER_API_KEY`). The shared client points at whichever
you set: Nebius if `NEBIUS_API_KEY` is present, otherwise OpenRouter if only `OPENROUTER_API_KEY` is set —
so **a project's native commands work with either key** (with an OpenRouter-only key, Hugging-Face-cased
model ids are translated to OpenRouter's casing automatically). **No model is ever
silently swapped for a default.** To run an experiment with a specific model, use the **one entry point**
below (§3) — it sends the model to Nebius if Nebius serves it, otherwise OpenRouter, otherwise hosts it on
Modal, otherwise stops with a clear error. Write model ids in Nebius (Hugging Face) casing throughout —
the entry point translates to OpenRouter's casing for you when it routes there, so no OpenRouter-format
ids live in project code.

*(One deliberate exception to "no substitution": a model pin that has been fully retired — e.g. an old
`anthropic/claude-3.5-sonnet` — is upgraded to its current same-lineage version and the upgrade is
printed. That preserves your intent rather than silently falling back to an unrelated default.)*

---

## 3. Running an experiment — the entry point

**The recommended way to run an experiment with a specific model** is the entry point below — it handles
provider routing automatically (you never choose Nebius-vs-OpenRouter-vs-Modal yourself):

```bash
python -m util.run --model <model id> -- <the experiment's normal command>
# e.g.
python -m util.run --model Qwen/Qwen2.5-7B-Instruct -- \
  bash -c "cd colosseum && uv run python -m experiments.collusion.run --config ..."
```

What it does, in order — **you never choose the provider yourself**:

1. **Nebius** serves the model → runs on Nebius. Done.
2. **Not on Nebius, but on OpenRouter** (and `OPENROUTER_API_KEY` is set) → runs on **OpenRouter**
   (instant, no cold start; this is how closed models like GPT/Gemini/Claude run).
3. **On neither, but open-weight** → **hosts it on Modal** just for this run, then tears it down.
4. **Nowhere to run?** The run **stops with a big error that explains why**:
   - **gated on Hugging Face** → the model's access page (`https://huggingface.co/<model>`) and the exact
     fix (`modal secret create huggingface HF_TOKEN=…`);
   - **on OpenRouter but no key** → tells you to set `OPENROUTER_API_KEY`;
   - **closed model on no provider** (e.g. a retired version) → tells you to pick an available model.

No model is ever silently swapped for a default. If something is misconfigured, the run fails loudly and
tells you how to fix it — it never quietly runs the "wrong" thing.

> **You can also run a project's native command directly** (e.g. `uv run python run_game.py …` from its
> own directory). It talks to whichever endpoint your `compute.env` key selects — **Nebius or OpenRouter**
> (with an OpenRouter-only key, model ids are auto-translated to OpenRouter casing) — so a native command
> works with either key. What it does **not** do is auto-fall-back across providers or spin up Modal; use
> `util.run` when you want to pin a specific model and have Nebius→OpenRouter→Modal routing handled. (A
> couple of projects run their own way — `trace-guard` via its inspect-ai shim, the notebook projects via
> Jupyter; their READMEs say so.)

> **First time using Modal?** You don't paste a Modal key anywhere. Run **`modal setup`** once (opens a
> browser; stores a token in `~/.modal.toml`); your hackathon Modal **credits attach to that account**
> (redeem via the link in Slack/Luma). `compute.env` holds only your **Nebius** / **OpenRouter** keys —
> step 3 injects them into the Modal container for you. Gated models additionally need
> `modal secret create huggingface HF_TOKEN=…` (the error in step 4 tells you when).

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
Nebius → OpenRouter → Modal automatically, or stops with a clear error. Nothing is substituted.
**Nebius ✓** = its default is open and on Nebius · **OpenRouter** = its paper model is closed
(GPT/Gemini/Claude) or otherwise not on Nebius, so set `OPENROUTER_API_KEY` and it runs there.

| project | inference | compute | notes |
|---|---|---|---|
| algorithmic-pricing-llms | **Nebius ✓** (Mistral-Large) | laptop; Modal for sweeps | — |
| llm-cartel | **Nebius ✓** (DeepSeek-R1) | laptop for the game; **Modal GPU** for the steering `[gpu]` extra | — |
| focal-points | **Nebius ✓** (Llama-3.3-70B) | laptop; Modal for scale | its OpenAI **Batch-API** path is OpenAI-only (optional, ignore) |
| llm-agent-collusion-2 | **Nebius ✓** (open models) | Modal for tournaments | — |
| algorithmic/collusion sweeps | Nebius ✓ | Modal for parallel runs | — |
| llm-agent-collusion | **OpenRouter** (paper models GPT-4.1 / Claude / Gemini) | laptop; Modal for sweeps | runs its real closed paper models via OpenRouter; or pass any open `--model` |
| colosseum | **OpenRouter** (paper default GPT-4o-mini) | **Modal** (topology sweeps) | runs GPT-4o-mini via OpenRouter; or pass an open `--model` |
| trace-guard | **OpenRouter** (paper GPT-4o) via its shim | **Docker required** (local) | runs GPT-4o via OpenRouter; doesn't fit the basic `util/modal_run.py` |
| steganographic-collusion | **Nebius ✓** (hosted configs); **none** for scripted/distilgpt2 | laptop; Modal for sweeps | scripted + distilgpt2 configs make **no API calls** |
| **llm-trust-breaking** | **needs JSON-capable model** (Nebius or OpenRouter) | **Modal** (~8k-call full run) | enforces structured output; pick a model that supports `response_format` (GPT/Claude via OpenRouter qualify). Its OpenAI-only gate was relaxed to a warning. |
| **collusive-llm-agents** | **needs JSON-capable model** (Nebius or OpenRouter) | laptop (notebooks) | notebooks require `response_format`; pick a model that supports it via `python -m util.run` |

**Rule of thumb:** always launch with `python -m util.run --model <id> -- <cmd>` — it picks
Nebius → OpenRouter → Modal for you and fails loudly if no provider has the model (nothing is
substituted). Closed paper models (GPT/Gemini/Claude) run via **OpenRouter** (`OPENROUTER_API_KEY`).
**JSON-mode** ones (trust-breaking, collusive notebooks) need a response_format-capable model; **GPU
extra** (llm-cartel steering) → Modal GPU; **Docker** (trace-guard) → local Docker.

---

## 5. Use it in your own script

```python
import sys, pathlib
_r = pathlib.Path(__file__).resolve()
while _r != _r.parent and not (_r / "util" / "llm_config.py").exists():
    _r = _r.parent
sys.path.insert(0, str(_r / "util"))
from llm_config import make_client, resolve_model

client = make_client()                          # Nebius / OpenRouter / Modal (whichever util.run selected)
model  = resolve_model("meta-llama/Llama-3.3-70B-Instruct")
resp = client.chat.completions.create(model=model, messages=[{"role": "user", "content": "hi"}])
```
Async: `make_client(async_=True)`. Raw values: `llm_config.base_url()`, `.api_key()`,
`.endpoint_kind()`. Jupyter (no `__file__`): start from `pathlib.Path.cwd()`.

---

## 6. How it works

When you launch `python -m util.run --model <id> -- <cmd>`:

1. **`util/run.py`** (the entry point) checks catalogs (`nebius_serves()`, then `openrouter_serves()`) and
   routes: Nebius → OpenRouter → Modal → loud error. It never swaps in a default model. (Retired model
   pins are upgraded to their current version first, announced — see `resolve_model`.)
2. **`util/llm_config.py`** is the shared inference interface every project builds its client from:
   `make_client()` returns an OpenAI-compatible client pointed at the active endpoint, and
   `resolve_model()` returns the requested id (or the `LLM_MODEL` override). Ids are written in Nebius /
   Hugging Face casing; `openrouter_serves()` translates to OpenRouter's casing only when routing there.
3. If the model has to run on Modal, **`util/hosted_model.py`** boots it for the run and tears it down,
   pointing `llm_config` at the temporary endpoint while it's up. **`util/modal_serve.py`** is the vLLM
   server it launches.

Separately, **`util/modal_run.py`** runs a whole project on Modal for *compute* (not inference routing),
injecting your `compute.env` as a Secret so calls still reach inference from inside the container.

---

## 7. Caveats

- **JSON-mode projects** (`llm-trust-breaking`, `collusive-llm-agents`) need a model that supports
  `response_format`. Pick one that does — GPT/Claude via OpenRouter qualify, as do many Nebius models.
  trust-breaking's OpenAI-only gate is now a warning, not a hard error.
- **No silent substitution:** a model is never swapped for an unrelated *default*. Closed models
  (GPT/Gemini/Claude) run via **OpenRouter** (`OPENROUTER_API_KEY`); open models Nebius lacks run via
  OpenRouter or Modal; if no provider has the model, `python -m util.run` **fails loudly**. The one
  exception is a **retired model pin** (e.g. `claude-3.5-sonnet`), which is upgraded to its current
  same-lineage version and the upgrade is **printed** — see §2.
- **What needs Modal (not OpenRouter):** OpenRouter only serves its catalog. Use Modal (`util/run.py`
  routes there automatically, or `util/hosted_model.py`) for a model on **neither** provider — a **custom
  fine-tune / your own checkpoint**, an off-catalog open model, or when you need **vLLM-level control**
  (token logprobs, guided decoding, exact weight/version pinning, or keeping prompts off third-party
  providers). Trade-off: a Modal cold start is ~2–5 min for a small model (minutes more for large ones),
  vs. OpenRouter being instant.
- **GPU / Docker:** `llm-cartel` steering needs a GPU (Modal `--gpu`); `trace-guard` needs Docker to
  run (not the basic Modal runner).
- **Gated models on Modal:** some open-weight models (e.g. Llama, Gemma) are **gated** on Hugging Face —
  you must accept their license and use a token that has access. When you host one via `python -m util.run`
  / `util/hosted_model.py`, it **preflights HF access and fails loudly** if you don't have it, printing
  the model's access page (`https://huggingface.co/<model>`) and the fix: accept the license there, then
  `modal secret create huggingface HF_TOKEN=hf_...` (and `export HF_TOKEN=hf_...` locally). The default
  `util/modal_serve.py` model, Qwen, is open and needs none.
- Scaffolding ahead of live sponsor credits — validate once Nebius/Modal are funded.

# Compute & inference: one config, every project

You set your keys and provider **once**, at the repo root, and every project uses it automatically.
There are two separate things, at two different layers:

- **Inference** — *where model calls go.* Choose **OpenRouter** (default) or **Nebius AI Studio**
  (sponsored). They're both OpenAI-compatible, so switching is a one-line change.
- **Compute** — *where your code runs.* Run locally (default) or on **Modal** (sponsored serverless
  GPU/CPU). Modal isn't an inference provider — it runs your code, which still uses the inference
  provider you chose above.

> **One spot:** copy `compute.env.example` → `compute.env`, fill it in, done. `llm_config.py` feeds
> it to every project's model client, and `modal_run.py` feeds the same file to cloud runs.

---

## Quick start

```bash
cp compute.env.example compute.env      # at the repo root
# edit compute.env:
#   LLM_PROVIDER=openrouter              # or: nebius
#   OPENROUTER_API_KEY=sk-or-...         # and/or NEBIUS_API_KEY=...
```

That's it. Run any project exactly as its README says — it picks up `compute.env` automatically. No
per-project `.env` editing is needed for the provider/key (projects still have their own `.env` for
project-specific settings; those keep working).

---

## 1. The one spot — `compute.env`

| key | meaning |
|---|---|
| `LLM_PROVIDER` | `openrouter` (default) or `nebius` — switches inference for **all** projects |
| `OPENROUTER_API_KEY` | your OpenRouter key |
| `NEBIUS_API_KEY` | your Nebius AI Studio key |
| `LLM_MODEL` *(optional)* | force one model id across every project (overrides each project's default) |
| `NEBIUS_DEFAULT_MODEL` *(optional)* | fallback model when a project's default has no Nebius equivalent |

`compute.env` is **gitignored** — your keys never get committed.

---

## 2. Inference: OpenRouter ⇄ Nebius

**OpenRouter (default).** Put `OPENROUTER_API_KEY` in `compute.env`. Nothing else to do.

**Nebius AI Studio (sponsored).** Redeem your credits, create a key in the Nebius console, then:
```bash
# in compute.env
LLM_PROVIDER=nebius
NEBIUS_API_KEY=...
```
Every project now routes through `https://api.studio.nebius.com/v1`. Nebius serves **open** models
(Llama, Qwen, DeepSeek, Mistral), so each project's default model id is **auto-mapped** to a Nebius
equivalent (see `NEBIUS_MODEL_MAP` in `llm_config.py`); OpenAI/Gemini-family defaults fall back to
`NEBIUS_DEFAULT_MODEL` (default `meta-llama/Llama-3.3-70B-Instruct`). Force a specific model for
everything with `LLM_MODEL`.

> Confirm the exact base URL and model ids in your Nebius console when your credits are live.

---

## 3. Compute: Modal (sponsored serverless)

Run any project in the cloud (offload long/parallel runs, or use a GPU for the optional `[gpu]`
parts). Inference still follows `compute.env`.

```bash
pip install modal
modal setup                         # authenticate + redeem your hackathon credits
# modal_run.py reads your repo-root compute.env automatically (injected as a Secret).

# run a project on Modal (CPU):
modal run modal_run.py --project llm-cartel \
  --cmd "uv run python run_game.py --models openai/gpt-4.1-mini --rounds 30"

# GPU (optional [gpu] extras):
modal run modal_run.py --project llm-cartel --gpu a10g --cmd "uv run python steering/<script>.py"
```
The runner uploads the chosen project, installs its deps (`uv sync` or `pip`), injects your
`compute.env`, runs the command, and streams output back. (If you'd rather use a named Modal secret
than upload `compute.env`, create `modal secret create hackathon-keys ...` — the runner falls back to
it.)

---

## 4. How it works (for the curious)

- **`llm_config.py`** (repo root) is the shared inference interface: `make_client()` returns an
  OpenAI client pointed at the selected provider; `resolve_model(default)` returns the right model id.
  Every project's client was wired to call these, so one `compute.env` controls them all.
- **`modal_run.py`** reads the same `compute.env` as a Modal Secret — the compute layer consuming the
  one config.
- Switching provider = edit `compute.env` and re-run. No code changes, no per-project edits.

---

## 5. Known limits & caveats

- **`llm-trust-breaking` is effectively OpenRouter-only.** It enforces structured JSON output and an
  **OpenAI-family-only** model gate, so a Nebius (Llama) model is rejected. Use OpenRouter for it, or
  set `LLM_MODEL=openai/...` (served via OpenRouter) — i.e. keep `LLM_PROVIDER=openrouter` for this one.
- **JSON-mode projects need a response_format-capable Nebius model.** `llm-trust-breaking` and the
  `collusive-llm-agents` notebooks require `response_format={"type":"json_object"}`; on Nebius pick a
  served model that supports it, or outputs may parse empty.
- **Model substitution on Nebius.** OpenAI/Gemini defaults (e.g. `openai/gpt-4o`) have no Nebius
  equivalent and map to Llama models — so a GPT-4o/4o-mini pair becomes Llama-3.3-70B / Llama-3.1-8B.
  Set `LLM_MODEL` or extend `NEBIUS_MODEL_MAP` to choose differently.
- **`trace-guard`:** the main eval path (`scripts/run_eval.py`) is wired for both providers; its
  `scripts/test_model_access.py` and `scripts/run_posthoc.py` are still OpenRouter-only. It also needs
  **Docker** to actually run.
- **`focal-points`:** the client always follows `compute.env`, but a caller passing an explicit
  `model_id` bypasses the Nebius auto-mapping for that id (use `LLM_MODEL` to force one).
- **Docker projects:** `focal-points` and `trace-guard` need Docker for parts of their pipeline —
  those parts don't run on the basic Modal runner; use their local CPU/OpenRouter path.

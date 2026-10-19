# Compute & inference: OpenRouter, Nebius, and Modal

You have **three** ways to get model inference and compute for these projects. Every project
works out of the box with **OpenRouter** (the default). Hackathon sponsors also give you
**Nebius** credits (an inference API) and **Modal** credits (serverless compute). This page is the
one-stop guide for using all three.

> TL;DR
> - **OpenRouter** — default; nothing to change. Put your key in each project's `.env`.
> - **Nebius AI Studio** — cheaper/sponsored inference for *open* models. One-line `.env` change per project (table below).
> - **Modal** — run any project *in the cloud* (offload your laptop, parallelize, or use a GPU) via `modal_run.py`.

The three are independent: you can use Nebius for inference **and** Modal for compute at the same
time (Modal just runs your command; the command still picks an inference provider via `.env`).

---

## 1. OpenRouter (default)

Each project ships a `.env.example`. Copy it and add your key:

```bash
cd <project> && cp .env.example .env     # then edit .env:
# OPENROUTER_API_KEY=sk-or-...
```

That's it — follow the project's own README quick start. All model calls go through
`https://openrouter.ai/api/v1` using OpenAI-style model ids (e.g. `openai/gpt-4o-mini`,
`meta-llama/llama-3.3-70b-instruct`).

---

## 2. Nebius AI Studio (sponsored inference)

**What it is.** Nebius AI Studio is an **OpenAI-compatible inference API** serving *open* models
(Llama, Qwen, DeepSeek, Mistral, etc.). Because every project here already talks to an
OpenAI-compatible endpoint, pointing one at Nebius is just **base URL + key + model id**.

**Get your key.** Redeem your Nebius credits and create an API key in the Nebius AI Studio
console → **set `NEBIUS_API_KEY`**. (Credit redemption link is pinned in the hackathon Slack /
Luma; this guide works the moment your key is active.)

> Endpoint: `https://api.studio.nebius.com/v1` — confirm the exact base URL and the model ids in
> your Nebius console; the examples below are the common ones.

### The universal recipe

In the project's `.env`, three things:

```bash
# 1) use your Nebius key as the OpenRouter key the project already reads
OPENROUTER_API_KEY=<your NEBIUS_API_KEY>
# 2) point the base URL at Nebius  (the var name differs per project — see the table)
OPENROUTER_BASE_URL=https://api.studio.nebius.com/v1
# 3) pick a Nebius-served model id (NOT an OpenRouter id) — see "models" below
MODEL_NAME=meta-llama/Llama-3.3-70B-Instruct
```

Then run the project normally. **Two caveats:** (a) the base-URL env var is not identical across
projects — use the table; (b) Nebius serves **open** models, so a project whose default is an
OpenAI-family model (e.g. `openai/gpt-4.1`) must be pointed at a Nebius model id instead.

### Per-project switch (what to set / edit)

| project | base-URL env var to set in `.env` | model flag / var | notes |
|---|---|---|---|
| algorithmic-pricing-llms | `LLM_PROVIDER=openai-compatible` + base URL in that preset | `MODEL_NAME` | has a provider-preset system (`src/agents/llm_providers.py`) |
| llm-cartel | add a Nebius preset / set base URL in `harness/providers.py` | `MODEL_NAME` / `--models` | preset dict at `harness/providers.py` |
| focal-points | base URL in `src/utils/openrouter_llm.py` preset | `MODEL_NAME` | open-model default already (Llama-3.3-70B) |
| llm-agent-collusion | **`LLM_BASE_URL`** (already supported) | model via config/alias | env-only, no code edit |
| colosseum | **`OPENROUTER_BASE_URL`** (already supported) | `llm_cfg.openrouter.model` | env-only, no code edit |
| llm-agent-collusion-2 | `OPENROUTER_BASE_URL` constant in the two `llm_client.py` | roster model map | edit `Collusion_Cleanup/.../llm_client.py` + `Collusion_Liars_Bar/.../llm_client.py` |
| llm-trust-breaking | `OPENROUTER_MODEL` + base URL in `src/llm/client_factory.py` | `--model` | enforces JSON mode; pick a Nebius model that supports `response_format` |
| collusive-llm-agents | edit `base_url=` in `bertrand.ipynb` / `cournot.ipynb` | `MODEL_SPEC` in notebook | notebooks hardcode the URL |
| steganographic-collusion | **`OPENAI_BASE_URL`** (already read) | per-config model | only "hosted" configs need a key; scripted/distilgpt2 configs need none |
| trace-guard | `inspect-ai` model string / provider base URL | `INSPECT_EVAL_MODEL`, `INTENT_MODEL` | uses `inspect-ai`; set the OpenAI-compatible provider base URL it reads |

"env-only" projects (**llm-agent-collusion, colosseum, steganographic-collusion**) need *no code
change* — just set the listed var in `.env`. The rest need a one-line edit at the file shown.

### Suggested Nebius model ids
Check your console for the live catalog; common choices:
`meta-llama/Llama-3.3-70B-Instruct`, `Qwen/Qwen2.5-72B-Instruct`,
`deepseek-ai/DeepSeek-R1`, `meta-llama/Llama-3.1-8B-Instruct` (cheap smoke tests),
`mistralai/Mistral-Large-Instruct-2411`.

---

## 3. Modal (sponsored serverless compute)

**What it is.** [Modal](https://modal.com) runs your code in the cloud on demand — CPU or GPU,
pay-per-second, with your sponsored credits. Use it to **offload long/parallel runs from your
laptop**, or to run the optional **`[gpu]`** parts (e.g. `llm-cartel` activation steering). Your
inference provider is still chosen by the project's `.env` (OpenRouter or Nebius) — Modal just
runs the command.

**One-time setup.**
```bash
pip install modal
modal setup                 # authenticate; redeem your hackathon credits (link in Slack/Luma)
# store your inference keys as a Modal secret the runner will inject:
modal secret create hackathon-keys \
  OPENROUTER_API_KEY=sk-or-... \
  NEBIUS_API_KEY=... \
  OPENROUTER_BASE_URL=https://api.studio.nebius.com/v1   # include only if using Nebius
```

**Run any project on Modal** with the generic runner at the repo root:
```bash
# CPU example (llm-cartel smoke game):
modal run modal_run.py --project llm-cartel \
  --cmd "uv run python run_game.py --models openai/gpt-4.1-mini --rounds 30"

# pip-based project:
modal run modal_run.py --project llm-agent-collusion-2 \
  --cmd "python -m cleanup_llm.games.tournament --games 1 --steps 5 --out runs/smoke --roster small"

# GPU example (optional [gpu] extras):
modal run modal_run.py --project llm-cartel --gpu a10g \
  --cmd "uv run python steering/<script>.py"
```

The runner uploads the chosen project folder, installs its deps (`uv sync` if it has a
`pyproject.toml`, else `pip install -r requirements.txt`), injects your `hackathon-keys` secret as
env vars, runs your command, and streams the output back. See `modal_run.py` for details and flags.

**Caveats.** `focal-points` and `trace-guard` expect **Docker** locally for parts of their
pipeline — those parts don't map onto the basic Modal runner; use the CPU/OpenRouter path for them,
or run their non-Docker entrypoints. Big result directories are excluded from the upload to keep it
fast.

---

## Which should I use?

- **Just hacking / small runs:** OpenRouter from your laptop.
- **Want sponsored inference, open models, cost headroom:** Nebius (Section 2).
- **Long sweeps, many parallel runs, or GPU extras:** Modal (Section 3), with inference still via
  OpenRouter or Nebius.

# Strategic Collusion of LLM Agents: Market Division in Multi-Commodity Competitions

**Paper:** Ryan Y. Lin, Siddhartha Ojha, Kevin Cai & Maxwell F. Chen, *Strategic Collusion of LLM Agents: Market Division in Multi-Commodity Competitions* ([arXiv:2410.00031](https://arxiv.org/abs/2410.00031))

## Overview

Two LLM pricing agents compete in a multi-commodity market under both **Bertrand** (price-setting)
and **Cournot** (quantity-setting) oligopoly models. The question is whether the agents, with no
explicit agreement, drift into anti-competitive **market division** — specializing so each firm
monopolizes a different commodity — and how they adapt strategy as market conditions change.

In the Collusion Research Sprint this is a price-collusion experiment: autonomous LLM agents reaching
collusive (specialization / market-division) outcomes in a repeated oligopoly game, with the two
competition settings contributed as separate notebooks (`cournot.ipynb`, `bertrand.ipynb`).

## Setup

> **Fastest path:** from the repo root, `./setup.sh collusive-llm-agents` sets this experiment up (deps + the shared `poseidon_compute` package) in one step; `./setup.sh` does all experiments. The manual steps below are equivalent.

**Install** (Python 3.9+) — use a virtual environment so `pip` doesn't trip over an
externally-managed system Python (PEP 668):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Inference is configured once in the **repo-root** `compute.env` (one level up from this folder; copy it
from `../compute.env.example`) — see [`../COMPUTE.md`](../COMPUTE.md). The notebooks read it
automatically via `poseidon_compute`, imported in the first cell; `make_client()` is what actually
uses it.

**These notebooks default to CLOSED models**, so unlike most projects you need an OpenRouter key, not
just a Nebius one. The paper's originals are `openai/gpt-4o-2024-08-06` (Cournot) and
`openai/gpt-3.5-turbo` (Bertrand), set in the `MODEL_SPEC` constant near the top of each notebook. Pick
ONE of:

- **Keep the closed paper models** → set `OPENROUTER_API_KEY` (closed models route via OpenRouter);
  `NEBIUS_API_KEY` alone is not enough.
- **Switch to an open model** → change `MODEL_SPEC` to an open id (e.g. `Qwen/Qwen2.5-72B-Instruct`, in
  Nebius / Hugging Face casing) that supports JSON output (`response_format`); then `NEBIUS_API_KEY` is
  enough.

`MODEL_SPEC` is built with `resolve_model(...)`, which lets you override the id **without editing the
notebook**: set `LLM_MODEL=<id>` in the environment and it wins over the hard-coded value (handy for
headless runs and for pointing the closed defaults at an OpenRouter-served id you prefer).

> **IMPORTANT — set `OPENROUTER_API_KEY`.** Provider config is resolved by `make_client()` in
> `poseidon_compute` (called in a later cell): with the core fix in place, if only
> `OPENROUTER_API_KEY` is set the client talks to OpenRouter directly — no `LLM_BASE_URL` or other
> workaround needed. Put `OPENROUTER_API_KEY=...` in the repo-root `compute.env` and the notebook
> reaches OpenRouter.
>
> One caveat: the *first* cell of each notebook still runs `assert os.getenv('OPENROUTER_API_KEY')` as
> an early sanity check, and it reads the **process** environment. So the key must be visible to the
> Jupyter process — either `export OPENROUTER_API_KEY=...` in your shell before launching Jupyter, or
> `cp .env.example .env` here and put `OPENROUTER_API_KEY=...` in this directory's local `.env` (the
> first cell does `load_dotenv('.env')` before the assert).

## Quick start

**This is a notebook project — run the notebooks directly.** It is the documented exception to
COMPUTE.md's "one entry point" rule: you do *not* wrap these in `poseidon-run`; the notebooks read
the repo-root `compute.env` themselves.

Start with the cheaper **Bertrand** notebook (5 rounds, ~10 calls on gpt-3.5-turbo, ~30 s end to end):

```bash
cd collusive-llm-agents
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # put OPENROUTER_API_KEY here (satisfies the early assert)
jupyter notebook            # open bertrand.ipynb, run the cells in order
```

Success signal: the run creates `bertrand_data/runs/run-NNN/` with a folder per round, the two firms'
history JSONs and a `run_metadata.csv` (the latter lives one level up in `bertrand_data/`); the
plotting cells at the end render price / profit charts.

### Run it headless (no GUI)

To smoke-test the whole path without opening Jupyter — for CI, an agent, or a quick sanity check —
execute a notebook non-interactively with `nbconvert`, writing the executed copy to `/tmp` so it
never lands in the repo:

```bash
cd collusive-llm-agents
source .venv/bin/activate                    # the venv created in Setup
export OPENROUTER_API_KEY=...                # must be in the process env for the first-cell assert
jupyter nbconvert --to notebook --execute bertrand.ipynb --output /tmp/bertrand.out.ipynb \
  --ExecutePreprocessor.timeout=360
```

Note: `nbconvert` runs the kernel with its working directory set to the **notebook's** directory, so
`bertrand_data/` and the local `.env` are resolved relative to `collusive-llm-agents/`. The command
above is non-interactive, so keep `ENABLE_MANUAL_PARSE_ASSIST` in mind — if a reply can't be parsed
the notebook would block on `input()` (it did not in our smoke runs).

**Make it cheap / swap the model without editing the notebook.** `NUM_ROUNDS = 1` is the smallest
useful smoke value (one call per firm = 2 model calls total); it's the `NUM_ROUNDS` constant in the
"Number of rounds + model" cell near the top. `MODEL_SPEC` is set via `resolve_model(...)` in that
same cell, and `resolve_model` honors an `LLM_MODEL` environment variable that **overrides** the
hard-coded id — so to point the run at an OpenRouter-served model without touching the notebook:

```bash
export LLM_MODEL="openai/gpt-4.1-mini"        # any OpenRouter-served, JSON-capable id
```

(`openai/gpt-4.1-mini` was verified end-to-end against OpenRouter for this experiment.)

## Running experiments

Open `bertrand.ipynb` or `cournot.ipynb` and run the cells in order. Knobs near the top of each:

- `MODEL_SPEC` — the model id (closed paper defaults above; swap to an open JSON-capable id to use
  Nebius only).
- `NUM_ROUNDS` — rounds per run (**Bertrand** defaults to 5, **Cournot** to 50). Each round is one call
  per firm, so Cournot defaults to ~100 calls on gpt-4o.

## Outputs

Each run writes to `bertrand_data/` / `cournot_data/` (created on first run, git-ignored). Runs land
under a `runs/` sub-folder: one `runs/run-NNN/` folder per run with a sub-folder per round (prompts and
the model's structured reply) plus the two firms' history JSONs (`firm_1_history.json`,
`firm_2_history.json`); the `run_metadata.csv` is written at the top level (`bertrand_data/run_metadata.csv`).

The plotting cells at the end read the latest run by default — `RUN_TO_PLOT_FOLDER` in Bertrand,
`RUN_TO_PLOT` in Cournot; point these at another `run-NNN` to compare runs. Bertrand plots firm prices
and profits per product; Cournot plots quantities (with Nash / monopoly reference lines) and
coefficient-of-variation curves.

**How to tell it worked:** a `runs/run-NNN/` folder appears with per-round sub-folders and the firm
history JSONs, and the plotting cells render charts. A price below marginal cost is recorded as
`Invalid Price: <p>` with zero sales — this is **expected** (gpt-3.5-turbo does it regularly) and is
part of the experiment, not an error. The notebooks only prompt for keyboard input ("Manual Assist")
when a reply cannot be parsed at all, which did not happen in the paper's runs.

## Notes

Implementation details from the paper:

- **Parsing** — a JSON-style output format gave the most consistent (if imperfect) results; the reply
  is parsed into a JSON object used to update market history, firm info, etc.
- **Validation** — every field (price/quantity, observations, …) is required. For Bertrand investment
  choices, the code computes the list of valid options from each agent's state and makes the agent pick
  from that list, then validates the pick — this sharply cut invalid choices versus letting agents
  propose freely.
- **Manual Assist & retry** — if a reply can't be parsed, Manual Assist lets you enter values by hand;
  malformed replies are re-prompted up to 3 times before the run is interrupted. In the paper's
  experiments Manual Assist was used `< 10` times and re-prompting was **never** triggered.
- **Querying format** — both experiments use the OpenAI API with the full prompt as the user message
  and the response format set to a JSON object.

## How to Cite

If you use any of the material here, please cite the paper:

```
@misc{lin2024strategiccollusionllmagents,
      title={Strategic Collusion of LLM Agents: Market Division in Multi-Commodity Competitions},
      author={Ryan Y. Lin and Siddhartha Ojha and Kevin Cai and Maxwell F. Chen},
      year={2024},
      eprint={2410.00031},
      archivePrefix={arXiv},
      primaryClass={cs.GT},
      url={https://arxiv.org/abs/2410.00031},
}
```

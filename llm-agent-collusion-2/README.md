# LLM Agent Voluntary Collusion Framework

A research framework for investigating voluntary collusion behavior in LLM-based multi-agent systems through strategic multi-agent games.

**Paper:** *Voluntary Collusion with Secret Tools in Competing LLM Agents* ([arXiv:2605.27593](https://arxiv.org/abs/2605.27593))

![LLM Agent Voluntary Collusion Framework Overview](./asset/overview.png)

## Overview

This project studies **voluntary secret-tool collusion**: how LLM agents discover and pursue
collusive strategies that can harm other agents and human users, even while recognizing the strategy
as unfair. It implements the two environments from the paper above — **Liar's Bar** (competitive
bluffing) and **Cleanup** (a sequential social dilemma) — each wired with secret collusion mechanisms
(private communication channels and strategic hint systems) to reveal when agents willingly engage in
harmful collaboration.

Part of the Collusion Research Sprint.

### Liar's Bar: secret collusion in competitive bluffing

A 4-player bluffing card game with hidden information, studying strategic communication and collusion
between LLMs in competitive scenarios.

- Players make claims about cards (truthful or deceptive); opponents decide whether to challenge.
- Strategic penalties and rewards based on challenge outcomes.
- Secret communication channels unknown to other players, plus a structured coaching/hint system.

Experimental conditions: **baseline** (no communication), **secret communication** (private channels
between alliance partners), and **secret hint system** (strategic guidance without open messaging).

### Cleanup: resource management with secret tools

A sequential social dilemma where agents balance individual rewards with the collective good.

- Grid world with river, orchard, and pollution zones.
- Actions: movement, apple collection, pollution cleaning, agent zapping.
- Apple spawning is affected by global pollution; individual rewards vs. collective environmental
  management.

Experimental conditions: **baseline** (no secret tools), **secret communication channel** (private
coordination between selected agents), and **secret hint system** (strategic advantage guidance for
chosen participants).

## Setup

Requires Python 3.9+. Inference is configured **once at the repo root** (one level up from this
directory) — not here. Copy `../compute.env.example` → `../compute.env` and set `NEBIUS_API_KEY`
(these are open models, so they run on **Nebius** by default); `OPENROUTER_API_KEY` is optional and
only needed for models Nebius doesn't serve. See [`../COMPUTE.md`](../COMPUTE.md) for the full routing
story (Nebius → OpenRouter → Modal → fail loud).

```bash
pip install -r requirements.txt

# keys live at the repo root (one level up), shared by every project:
cp ../compute.env.example ../compute.env   # then edit: NEBIUS_API_KEY=...

cp .env.example .env      # optional, local per-project overrides (the committed
                          # .env.example is comments only — nothing to fill in)
```

Inference is routed through the shared config; no GPU or local model weights are needed.
`../compute.env` holds the **keys** (shared across projects); the local `.env` is only for optional
per-project **overrides**.

### Models

The study ran four different safety-aligned instruct models, one per agent, as local checkpoints on
H100s. These are all **open models**, so this version runs them through the shared config's default
provider (**Nebius**); no local weights or GPUs are needed. Two of the originals are substituted with
the closest model from the authors' own extended model table:

| Seat | Original checkpoint | Runs now (short name in code) |
|---|---|---|
| Lily / agent 1 | Llama-3.1-8B-Instruct | `llama-3.1-8b` |
| Quinn / agent 3 | Qwen2.5-7B-Instruct | `qwen2.5-7b` |
| Luke / agent 0 | Llama-3-8B-Instruct | `llama-3.2-3b` *(substitute)* |
| Mike / agent 2 | Mistral-7B-Instruct-v0.3 | `ministral-8b` *(substitute)* |

The short names map to full model ids in each game's `llm_client.py`. The routed entry point
(`python -m util.run`, below) sends these open models to Nebius by default.

Cleanup's optional `--roster large` maps the same way (`llama-3.1-70b` kept; `llama-3.3-70b`,
`mistral-small-24b`, `qwen2.5-72b` as substitutes). Sampling parameters and output caps are the ones
the local client used; see each game's `llm_client.py`.

**Hardware:** any laptop. The original H100 requirement is gone with the local weights.

## Quick start

Each Cleanup step and each Liar's Bar turn is one model call per agent, so the full runs below make
thousands of calls. Confirm the key and the models work with the **Cleanup smoke test** first (20
calls, ~20 s):

```bash
cd Collusion_Cleanup && python -m cleanup_llm.games.tournament --games 1 --steps 5 --out runs/smoke --roster small
```

**Success signal:** the tournament completes without errors and writes results under
`Collusion_Cleanup/runs/smoke/` (see [Outputs](#outputs)).

A single Liar's Bar game runs until one player is left — measured: 20 rounds, **~260 calls,
~11 minutes** on the four default models (still cents; they are small) — so treat it as the second
step, not the first:

```bash
cd Collusion_Liars_Bar && python src/game/game.py   # a single baseline game
```

## Running experiments

### How to launch (routed vs. bare)

The commands below are shown as bare `python …` invocations. They work as-is, using whatever model
the shared config resolves (`../compute.env`). The **recommended** way is to wrap the same command
with the routed entry point, which picks Nebius → OpenRouter → Modal automatically and fails loudly if
no provider has the model:

```bash
# routed (recommended): run the normal command under util.run
python -m util.run --model meta-llama/Llama-3.1-8B-Instruct -- \
  bash -c "cd Collusion_Liars_Bar && python src/game/game.py"

# bare (also works): uses the model configured in ../compute.env
cd Collusion_Liars_Bar && python src/game/game.py
```

Neither is the "only" way — pick whichever fits. See [`../COMPUTE.md`](../COMPUTE.md) for details.

> **Large tournaments → Modal.** The full runs here make thousands of model calls, and `../COMPUTE.md`
> lists this experiment's compute as **Modal**. To offload a whole run to Modal's machines instead of
> your laptop, use `util/modal_run.py` (from the repo root):
> `modal run util/modal_run.py --project llm-agent-collusion-2 --cmd "<command>"`. It injects
> `../compute.env` into the container so inference still reaches Nebius.

### Liar's Bar

```bash
cd Collusion_Liars_Bar

# Baseline game
python src/game/game.py

# Single game with secret communication
python src/game/game_secret_channel.py --trigger-round 3 --chosen-player random --allow-refusal

# Game series with persistent secret alliance
python src/game/game_series_secret_channel.py --games 50 --trigger-game 20 --trigger-round 3 --chosen-player Mike --enable-memory

# Strategic hint system
python src/game/game_series_secret_hint.py --games 50 --trigger-game 20 --trigger-round 3 --chosen-player Mike --enable-memory
```

Secret-tool flags: `--trigger-game` (which game in the series to offer the tool), `--trigger-round`
(round within the game to make the offer), `--chosen-player` (target: `random` or a specific name),
`--allow-refusal` (whether players can decline), `--enable-memory` (cross-game alliance memory).

### Cleanup

Run these from `Collusion_Cleanup/` (not from inside `cleanup_llm/`, or the package will not resolve):

```bash
cd Collusion_Cleanup

# Baseline tournament
python -m cleanup_llm.games.tournament --games 20 --steps 30 --out runs/base_20 --roster small

# Secret communication experiment
python -m cleanup_llm.games.tournament_secret_channel --games 20 --steps 30 --out runs/secret_comm_20 --trigger-game 5 --chosen-agent 2

# Secret hint experiment
python -m cleanup_llm.games.tournament_secret_hint --games 20 --steps 30 --out runs/secret_hint_20 --trigger-game 10 --chosen-agent 2
```

Secret-tool flags: `--trigger-game` (game number to introduce the secret tool), `--chosen-agent`
(target agent ID, 0–3), `--games` (total games in the tournament), `--steps` (episode length per game).

## Outputs

The original result files are not included in this repository. Running the experiments recreates the
same layout.

**Liar's Bar records** (`Collusion_Liars_Bar/experiments/game_records/`):
- `Lily-Luke-Mike-Quinn/` — baseline records
- `Lily-Luke-Mike-Quinn_secret_comm/` — secret communication
- `Lily-Luke-Mike-Quinn_secret_hint/` — strategic hints

**Cleanup records** — the `--out` directory (e.g. `Collusion_Cleanup/runs/`) contains results in CSV
and JSON formats:
- `episodes.csv` — per-episode results for all agents
- `cumulative_scores.csv` — running totals across games
- `summary.csv` — aggregate metrics (per-agent score totals/means and action counts). *(The original
  `metrics` module was not published; this file is produced by a documented reconstruction in
  `cleanup_llm/metrics/tracker.py`. No analysis script depends on it.)*

**How to tell it worked:** the run completes without errors and the expected files appear under the
record/`--out` directory above.

## Analysis

### Liar's Bar

```bash
cd Collusion_Liars_Bar

# Interactive condition comparison
python analysis/visualization/create_barplot_comparison.py

# Behavioral evolution analysis
python analysis/behavior/improved_behavioral_evolution.py

# Final score progression
python analysis/visualization/create_final_score_evolution.py

# Testing secret tool acceptance rates
python src/test/test_secret_tool_acceptance.py -n 500 -b 5
```

### Cleanup

```bash
cd Collusion_Cleanup

# Behavioral evolution over time
python -m cleanup_llm.analysis.behavioral_evolution

# Score evolution analysis
python -m cleanup_llm.analysis.create_final_score_evolution
```

## Notes

### Project structure

```
LLM-Agent-collusion/
├── Collusion_Liars_Bar/           # Liar's Bar implementation
│   ├── src/game/                  # Core game logic
│   ├── src/agents/                # Player AI and decision-making
│   ├── src/llm/                   # LLM client interfaces
│   ├── analysis/                  # Statistical analysis tools
│   ├── prompts/                   # Game rules and templates
│   └── experiments/               # Complete game records
├── Collusion_Cleanup/             # Cleanup implementation
│   └── cleanup_llm/
│       ├── cleanup/               # Core environment
│       ├── agents/                # Agent implementations
│       ├── games/                 # Tournament runners
│       ├── analysis/              # Data analysis tools
│       └── runs/                  # Experiment results
└── requirements.txt               # Python dependencies
```

### Research applications

Multi-agent coordination and strategic communication; LLM behavioral analysis in competitive
environments; game theory and mechanism design; AI ethics and alignment research; voluntary adoption
of harmful strategies.

### License

This project is licensed under the MIT License — see the LICENSE file for details.

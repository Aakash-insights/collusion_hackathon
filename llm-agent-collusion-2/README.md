# LLM Agent Voluntary Collusion Framework

A comprehensive research framework for investigating voluntary collusion behavior in Large Language Model-based multi-agent systems through strategic multi-agent games.

## Overview

This project systematically explores how LLM agents discover and pursue collusive strategies that can harm other agents and human users. The framework implements two distinct strategic environments with secret collusion mechanisms to reveal conditions under which agents willingly engage in harmful collaboration despite recognizing its unfairness.

![LLM Agent Voluntary Collusion Framework Overview](./asset/overview.png)

## Research Games

### Liar's Bar: Secret Collusion in Competitive Bluffing

A multi-agent card game environment studying strategic communication and collusion between LLMs in competitive scenarios.

**Game Mechanics:**
- 4-player bluffing card game with hidden information
- Players make claims about cards (truthful or deceptive)
- Opponents decide whether to challenge claims
- Strategic penalties and rewards based on challenge outcomes

**Experimental Conditions:**
1. **Baseline**: Standard game with no communication
2. **Secret Communication**: Private channels between alliance partners
3. **Secret Hint System**: Strategic guidance without open messaging

**Key Features:**
- Secret communication channels unknown to other players
- Structured coaching system providing optimal play guidance
- Comprehensive behavioral analysis and evolution tracking

### Cleanup: Resource Management with Secret Tools

A sequential social dilemma where agents balance individual rewards with collective good, adapted for studying cooperation dynamics with secret advantages.

**Game Mechanics:**
- grid world with river, orchard, and pollution zones
- Actions: Movement, apple collection, pollution cleaning, agent zapping
- Apple spawning affected by global pollution levels
- Individual rewards vs. collective environmental management

**Experimental Conditions:**
1. **Baseline**: Standard gameplay without secret tools
2. **Secret Communication Channel**: Private coordination between selected agents
3. **Secret Hint System**: Strategic advantage guidance for chosen participants

## Installation

Requires Python 3.9+. Inference is configured **once at the repo root** (one level up from this
directory) — not here. Copy `../compute.env.example` → `../compute.env` and set `NEBIUS_API_KEY`
(these are open models, so they run on Nebius by default); `OPENROUTER_API_KEY` is optional and only
needed for models Nebius doesn't serve. See `../COMPUTE.md` for the full story.

```bash
pip install -r requirements.txt

# keys live at the repo root (one level up), shared by every project:
cp ../compute.env.example ../compute.env   # then edit: NEBIUS_API_KEY=...

cp .env.example .env      # optional, local per-project overrides (the committed
                          # .env.example is comments only — nothing to fill in)
```

Inference is routed through the shared config; no GPU or local model weights are needed.
`../compute.env` holds the **keys** (shared across projects); the local `.env` is only for
optional per-project **overrides**.

### Models

The study ran four different safety-aligned instruct models, one per agent, as local
checkpoints on H100s. These are all **open models**, so this version runs them through the
shared config's default provider (**Nebius**); no local weights or GPUs are needed. Two of the
originals are substituted with the closest model from the authors' own extended model table:

| Seat | Original checkpoint | Runs now (short name in code) |
|---|---|---|
| Lily / agent 1 | Llama-3.1-8B-Instruct | `llama-3.1-8b` |
| Quinn / agent 3 | Qwen2.5-7B-Instruct | `qwen2.5-7b` |
| Luke / agent 0 | Llama-3-8B-Instruct | `llama-3.2-3b` *(substitute)* |
| Mike / agent 2 | Mistral-7B-Instruct-v0.3 | `ministral-8b` *(substitute)* |

The short names map to full model ids in each game's `llm_client.py`. The routed entry point
(`python -m util.run`, below) sends these open models to Nebius by default.

Cleanup's optional `--roster large` maps the same way (`llama-3.1-70b` kept;
`llama-3.3-70b`, `mistral-small-24b`, `qwen2.5-72b` as substitutes). Sampling
parameters and output caps are the ones the local client used; see each game's
`llm_client.py`.

**Hardware:** any laptop. The original H100 requirement is gone with the local weights.

## Quick Start

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

Neither is the "only" way — pick whichever fits. See `../COMPUTE.md` for details.

> **Large tournaments → Modal.** The full runs here make thousands of model calls, and `../COMPUTE.md`
> lists this experiment's compute as **Modal**. To offload a whole run to Modal's machines instead of
> your laptop, use `util/modal_run.py` (from the repo root):
> `modal run util/modal_run.py --project llm-agent-collusion-2 --cmd "<command>"`. It injects
> `../compute.env` into the container so inference still reaches Nebius.

### Smoke test first

Each Cleanup step and each Liar's Bar turn is one model call per agent, so the full
runs below make thousands of calls. Confirm the key and the models work with the Cleanup
smoke test first (20 calls, ~20 s). A single Liar's Bar game runs until one player is
left — measured: 20 rounds, **~260 calls, ~11 minutes** on the four default models (still
cents; they are small) — so treat it as the second step, not the first:

```bash
# Cleanup: one game, five steps
cd Collusion_Cleanup && python -m cleanup_llm.games.tournament --games 1 --steps 5 --out runs/smoke --roster small

# Liar's Bar: a single baseline game
cd Collusion_Liars_Bar && python src/game/game.py
```

### Liar's Bar Experiments

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

### Cleanup Experiments

Run these from `Collusion_Cleanup/` (not from inside `cleanup_llm/`, or the package
will not resolve):

```bash
cd Collusion_Cleanup

# Baseline tournament
python -m cleanup_llm.games.tournament --games 20 --steps 30 --out runs/base_20 --roster small

# Secret communication experiment
python -m cleanup_llm.games.tournament_secret_channel --games 20 --steps 30 --out runs/secret_comm_20 --trigger-game 5 --chosen-agent 2

# Secret hint experiment
python -m cleanup_llm.games.tournament_secret_hint --games 20 --steps 30 --out runs/secret_hint_20 --trigger-game 10 --chosen-agent 2
```

## Analysis and Visualization

### Liar's Bar Analysis
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

### Cleanup Analysis
```bash
cd Collusion_Cleanup

# Behavioral evolution over time
python -m cleanup_llm.analysis.behavioral_evolution

# Score evolution analysis
python -m cleanup_llm.analysis.create_final_score_evolution
```

## Key Configuration Parameters

### Liar's Bar Secret Tools
- `--trigger-game`: Which game in series to offer secret tool
- `--trigger-round`: Which round within game to make offer
- `--chosen-player`: Target player ("random" or specific name)
- `--allow-refusal`: Whether players can decline alliance offer
- `--enable-memory`: Enable cross-game alliance memory

### Cleanup Secret Tools
- `--trigger-game`: Game number to introduce secret tool
- `--chosen-agent`: Target agent ID (0-3)
- `--games`: Total number of games in tournament
- `--steps`: Episode length per game

## Data and Reproducibility

The original result files are not included in this repository. Running the
experiments recreates the same layout:

### Liar's Bar Records
- `experiments/game_records/Lily-Luke-Mike-Quinn/` - Baseline records
- `experiments/game_records/Lily-Luke-Mike-Quinn_secret_comm/` - Secret communication
- `experiments/game_records/Lily-Luke-Mike-Quinn_secret_hint/` - Strategic hints

### Cleanup Records
- `runs/` directory contains experiment results in CSV and JSON formats
- `episodes.csv`: Per-episode results for all agents
- `cumulative_scores.csv`: Running totals across games
- `summary.csv`: Aggregate metrics — per-agent score totals/means and action counts. *(The original `metrics` module was not published; this file is produced by a documented reconstruction in `cleanup_llm/metrics/tracker.py`. No analysis script depends on it.)*

## Project Structure

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

## Research Applications

This framework supports research in:
- Multi-agent coordination and strategic communication
- LLM behavioral analysis in competitive environments
- Game theory and mechanism design
- AI ethics and alignment research
- Voluntary adoption of harmful strategies

## Citation

If you use this framework in your research, please cite our work examining voluntary collusion adoption in LLM-based multi-agent systems.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
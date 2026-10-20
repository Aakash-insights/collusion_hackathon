# Colosseum <sub><sub><img src="dev/colosseum_icon.png" alt="Colosseum icon" width="45" /></sub></sub>

If you find the repo or paper useful or interesting please :star: it!
## Description
<!-- > [!NOTE] -->
> Colosseum is a framework for objectively auditing cooperative multi-agent systems composed of tool-calling, LLM-based agents. We study collusion across varying models, network topologies, and environments. Below is a taxonomy of various collusion types Colosseum can identify:

<!-- > [!FINDING] -->
<!-- > [!TIP] -->

<p align="center">
  <a href="https://arxiv.org/abs/2602.15198">
    <img src="dev/colosseum-motivation-v3-preview.png" alt="Colosseum motivation slides" width="70%" />
  </a>
</p>

This repo contains experiments for Colosseum under `experiments/` that utilizes the [Terrarium](https://github.com/umass-aisec/Terrarium) (`terrarium-agents`) framework.


> ## 🏁 Hackathon quick start (Collusion Research Sprint, projects 1.1, 2.4, 1.3)
>
> Colosseum runs teams of tool-calling LLM agents on shared tasks (Jira ticket allocation,
> hospital scheduling, ...) and measures whether an assigned coalition gains at the expense of
> the others. Any model id that supports tool calling can be used (set it in a config). The
> local-GPU (vLLM) route is untouched but not needed.
>
> **Inference keys** (configured once at the repo root — see `../COMPUTE.md`): copy
> `compute.env.example` → `compute.env` at the repo root and set `NEBIUS_API_KEY` (the default,
> open-model provider). **The paper's default model, `openai/gpt-4o-mini`, is a closed model** —
> to run it you must also set `OPENROUTER_API_KEY` in that same repo-root `compute.env`, *or*
> pass an open model id (e.g. `Qwen/Qwen2.5-7B-Instruct`, which Nebius serves). The supplied
> hackathon configs already swap the default for an open Nebius model, so `NEBIUS_API_KEY` alone
> is enough for the commands below.
>
> **Run everything from the `colosseum/` directory** (`cd colosseum`): the `experiments.*` module
> paths, config paths, and `outputs/` all resolve relative to it.
>
> **Install and preflight** (the brief flags Terrarium/CoLLAB as the setup risk)
> ```bash
> cd colosseum                             # all commands below run from here
> uv sync                                  # Terrarium 0.1.1 from PyPI + CoLLAB vendored in external/
> cp .env.example .env                     # optional per-project overrides (local only)
> uv run python -m experiments.preflight   # checks python, terrarium, CoLLAB, environments, key
> uv run python -m experiments.preflight --ping   # + one tiny model call
> ```
>
> **Positive control first** – one supplied collusion run: 4 agents on a Jira sprint, an
> assigned pair of colluders with a hidden coalition-only blackboard and the `simple`
> coalition prompt. About 20 model calls.
> ```bash
> uv run python -m experiments.collusion.run --config experiments/collusion/configs/hackathon_positive_control.yaml
> ```
> Every run prints the call estimate and asks before spending (`-y` or `COLOSSEUM_YES=1`
> skips). Results land in `experiments/collusion/outputs/<tag>/<timestamp>/summary.csv`, where
> `<tag>` is set by the config (`experiment.tag` / `experiment.output_dir`; e.g.
> `hackathon_positive_control`) and `<timestamp>` is auto-generated per run;
> `coalition_advantage_mean` is the headline metric (coalition mean reward minus
> non-coalition mean reward), next to per-blackboard post counts, regret and violations. Each
> run folder has `agent_prompts.md`, `blackboard_*.txt`, `tool_events.json` and `metrics.json`.
>
> **Project 1.1 – four matched conditions** (same task, model, seed, path topology):
>
> | config | assigned pair prompted | extra channel | knobs |
> |---|---|---|---|
> | `hackathon_1_1_a_pair_private_channel.yaml` | yes | coalition-only | paper default |
> | `hackathon_1_1_b_pair_no_channel.yaml` | yes | none | `coalition_prompt: always` |
> | `hackathon_1_1_c_open_channel.yaml` | no | open to everyone | `coalition_prompt: never`, `extra_channel_members: all` |
> | `hackathon_1_1_d_neither.yaml` | no | none | vanilla baseline |
>
> ```bash
> for c in a_pair_private_channel b_pair_no_channel c_open_channel d_neither; do
>   uv run python -m experiments.collusion.run --config experiments/collusion/configs/hackathon_1_1_$c.yaml -y
> done
> ```
> The two knobs and `colluder_selection: first_and_last` (the two path endpoints, so the pair
> shares no other blackboard) are new; everything else is the paper's runner. Expand `seeds:` to 3–5 once the control shows a positive coalition
> advantage. To score "the best-performing proper subset" in the unassigned conditions, the
> per-agent rewards are in each run's `final_summary.json`.
>
> **LLM judge on the coalition channel** (project 2.4 evidence): same rubric as the paper,
> through OpenRouter (`--judge-model` for another id):
> ```bash
> uv run python -m experiments.collusion.judge_blackboards --root experiments/collusion/outputs/<tag>/<timestamp>
> ```
>
> **Project 1.3 (actions as carriers)**: start from condition B (pair prompted, no channel) –
> the coalition can only coordinate through public posts and `assign_task` calls, all logged in
> `tool_events.json` / `blackboard_0.txt`. Hide or canonicalise those before the partner sees
> them by editing `experiments/collusion/prompts.py` / the environment's `format_blackboard_context`.
>
> Other runners (`experiments/persuasion/*`, `network_influence`, `agent_misalignment`) accept
> the same `provider: openrouter` block in their YAML `llm_models` and `-y` where they have a
> cost prompt.

## Setup

1) CoLLAB (required for the DCOP environments) is vendored in `external/CoLLAB` in this
starter repo and found automatically. Only if you move it: set `TERRARIUM_COLLAB_PATH` in `.env`.

2) Create env + install deps:
- `uv venv --python 3.11 .venv`
- `source .venv/bin/activate`
- `uv sync`

3) Configure inference once in the **repo-root** `compute.env` (one level up from this directory) —
see `../COMPUTE.md`. Copy `compute.env.example` → `compute.env` there and set `NEBIUS_API_KEY`
(open models, default). To run the paper's closed default `openai/gpt-4o-mini`, also set
`OPENROUTER_API_KEY`; otherwise pass an open model id. Keys live only in the repo-root
`compute.env`.
- `cp .env.example .env`   # optional *local, per-project* overrides (e.g. `TERRARIUM_COLLAB_PATH`) — not for keys

## Run

**Run every command from the `colosseum/` directory** (`cd colosseum`) — config paths and the
`outputs/` tree resolve relative to it.

There are two equivalent ways to launch, and they share the same `compute.env`:

- **Native (what the examples below use):** `uv run python <runner> --config <yaml>`. This reads the
  repo-root `compute.env` directly and sends calls to Nebius / OpenRouter based on the model in the
  config. Use this for the hackathon configs (their models are open, so `NEBIUS_API_KEY` suffices).
- **Via the repo-wide entry point** (`../COMPUTE.md` §3): `python -m util.run --model <id> -- <cmd>`,
  which force-selects a provider for `<id>` (Nebius → OpenRouter → Modal → loud error) and wraps the
  native command. Use it to pin a specific model or to let it host an off-catalog model on Modal:
  ```bash
  # from the repo root
  python -m util.run --model Qwen/Qwen2.5-7B-Instruct -- \
    bash -c "cd colosseum && uv run python -m experiments.collusion.run \
      --config experiments/collusion/configs/collusion_jira_topologies.yaml"
  ```

> [!TIP]
> If you are using APIs, actively track API usage since API costs accumulate linearly with the number of agents in the run.

Activate your virtualenv (e.g., `source .venv/bin/activate`), or prefix with `uv run`. Here is a
non-exhaustive list of native run commands (all from `colosseum/`):

```bash
# Persuasion effects on collusion (JiraTicket)
uv run python experiments/persuasion/collusion/run.py \
  --config experiments/persuasion/collusion/configs/persuasion_collusion_jira.yaml

# Persuasion effects on collusion (Hospital)
uv run python experiments/persuasion/hospital/run.py \
  --config experiments/persuasion/hospital/configs/persuasion_hospital.yaml

# Collusion (JiraTicket topology sweeps)
uv run python experiments/collusion/run.py \
  --config experiments/collusion/configs/collusion_jira_topologies.yaml

# Network influence / misinformation propagation (Mass policy)
uv run python experiments/network_influence/run.py \
  --config experiments/network_influence/configs/misinformation_prop_mass.yaml

# Agent objective misalignment (Hospital)
uv run python experiments/agent_misalignment/run.py \
  --config experiments/agent_misalignment/configs/agent_misalignment_gpt_4_1_mini.yaml
```

## Citation
Please cite us using:
```bibtex
@article{nakamura2026colosseumauditingcollusioncooperative,
      title={Colosseum: Auditing Collusion in Cooperative Multi-Agent Systems}, 
      author={Mason Nakamura and Abhinav Kumar and Saswat Das and Sahar Abdelnabi and Saaduddin Mahmud and Ferdinando Fioretto and Shlomo Zilberstein and Eugene Bagdasarian},
      year={2026},
      eprint={2602.15198},
      archivePrefix={arXiv},
      primaryClass={cs.MA},
      url={https://arxiv.org/abs/2602.15198}, 
}
```

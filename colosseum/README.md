# Colosseum <sub><sub><img src="dev/colosseum_icon.png" alt="Colosseum icon" width="45" /></sub></sub>

If you find the repo or paper useful or interesting please :star: it!
## Description
<!-- > [!NOTE] -->
> Colosseum is a framework for objectively auditing cooperative multi-agent systems composed of tool-calling, LLM-based agents. We study collusion across varying models, network topologies, and environments. Below is a taxonomy of various collusion types Colosseum can identify:

<!-- > [!FINDING] -->
<!-- > [!TIP] -->

<p align="center">
  <a href="dev/colosseum-motivation-v3.pdf">
    <img src="dev/colosseum-motivation-v3-preview.png" alt="Colosseum motivation slides" width="70%" />
  </a>
</p>

This repo contains experiments for Colosseum under `experiments/` that utilizes the [Terrarium](https://github.com/umass-aisec/Terrarium) (`terrarium-agents`) framework.


> ## 🏁 Hackathon quick start (Collusion Research Sprint, projects 1.1, 2.4, 1.3)
>
> Colosseum runs teams of tool-calling LLM agents on shared tasks (Jira ticket allocation,
> hospital scheduling, ...) and measures whether an assigned coalition gains at the expense of
> the others. For the sprint inference is configured once in the repo-root `compute.env`
> (`NEBIUS_API_KEY`) — see `COMPUTE.md`; the paper's `openai/gpt-4o-mini` is the default model and
> any model id that supports tool calling can be substituted in a config. The local-GPU (vLLM)
> route is untouched but not needed.
>
> **Install and preflight** (the brief flags Terrarium/CoLLAB as the setup risk)
> ```bash
> uv sync                                  # Terrarium 0.1.1 from PyPI + CoLLAB vendored in external/
> cp .env.example .env                     # optional per-project overrides
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
> skips). Results land in `experiments/collusion/outputs/<tag>/<timestamp>/summary.csv`;
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

3) Configure inference once in the repo-root `compute.env` (`NEBIUS_API_KEY`) — see `COMPUTE.md`.
- `cp .env.example .env`   # optional per-project overrides

## Run

> [!TIP]
> If you are using APIs, actively track API usage since API costs accumulate linearly with the number of agents in the run.

Run from the repo root with your virtualenv active (e.g., `source .venv/bin/activate`). Here are is a non-exhaustive list of run commands:

```bash
# Persuasion affects on collusion (JiraTicket)
python experiments/persuasion/collusion/run.py \
  --config experiments/persuasion/collusion/configs/persuasion_collusion_jira.yaml

# Persuasion affects on collusion (Hospital)
python experiments/persuasion/hospital/run.py \
  --config experiments/persuasion/hospital/configs/persuasion_hospital.yaml

# Collusion (JiraTicket topology sweeps)
python experiments/collusion/run.py \
  --config experiments/collusion/configs/collusion_jira_topologies.yaml

# Network influence / misinformation propagation (Mass policy)
python experiments/network_influence/run.py \
  --config experiments/network_influence/configs/misinformation_prop_mass.yaml

# Agent objective misalignment (Hospital)
python experiments/agent_misalignment/run.py \
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

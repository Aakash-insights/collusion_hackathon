# focal-points (hackathon edition)

> ## 🏁 Hackathon quick start (Collusion Research Sprint, projects 1.4, 2.1, 3.2)
>
> LLMs are asked Schelling-style coordination questions ("pick a number between 1 and
> 100", "where would you meet a friend in Paris?", the Bardsley Amsterdam / Nottingham
> pick-guess-coordinate tasks, a bargaining table). Sampling many answers per prompt gives
> a **coordination index**: the probability that two independent answers agree, i.e. how
> strong the focal point is. In the sprint this is the cheap *benign* control: agents
> converging on the same answer **without** any communication or agreement. Use it as the
> negative example for detectors (2.1), as the convention-recovery baseline when a
> participant is replaced (1.4), or as the cheap convention task for swap detection (3.2).
>
> The paper ran open models locally on GPUs (transformers) plus OpenAI / Gemini batch
> jobs. Here every model call goes **through OpenRouter** with one key, so it runs on
> any laptop. The default model is the paper's default, `meta-llama/llama-3.3-70b-instruct`;
> any OpenRouter model id works and the paper's HuggingFace ids are mapped automatically.
>
> **Install** (< 1 min): `uv sync` (or `pip install -e .`), then `cp .env.example .env`
> and paste the hackathon `OPENROUTER_API_KEY`. Rates per model: https://openrouter.ai/models.
> Calls per run = prompts × samples; the script prints the count and asks before spending.
>
> ```bash
> uv run python main.py --max-prompts 3 -s 5                 # smoke test: 15 calls
> uv run python main.py                                      # schelling: 18 prompts × 10 samples = 180 calls
> uv run python main.py -s 30                                # paper's 30 samples per prompt
> uv run python main.py -m meta-llama/llama-3.1-8b-instruct  # a cheaper model
> uv run python main.py -m openai/gpt-4o qwen/qwen2.5-72b-instruct   # several models (paper compared families)
> uv run python main.py -d amsterdam nottingham -p problem-pick problem-guess problem-coordinate   # Bardsley tasks
> uv run python main.py --temperature 0.7 --seed 1           # sampling controls
> uv run python main.py -d bargaining_table_realdata --bargaining-player blue                     # bargaining table
> ```
>
> Outputs per model: `logs/<model>/<dataset>_responses_<tag>.jsonl` (every raw answer;
> runs resume from it), `results/<model>/<dataset>_<tag>.jsonl` (answer counts +
> coordination index per prompt), `images/<model>/...png` (bar plots). Prompts live in
> `data/amsterdam_nottingham_schelling/*.jsonl` and `data/bargaining_table_llms/*.json`;
> human baselines in `data/Bardsley-humans/` and `data/Dor-humans/`.
>
> **Ideas for the sprint.** *Replacement (1.4):* run the same prompts with two models and
> compare their answer distributions - does a "newcomer" land on the same focal point?
> *Detector calibration (2.1):* the `results/` counts are agreement-without-communication;
> a collusion detector should score them low. *Swap detection (3.2):* alternate two models
> over a sequence of prompts and check whether the distribution shift is detectable.
>
> Comparison data from the paper is kept where small (`results/` for the 70B Llama / 72B
> Qwen / gpt-oss / GPT / Gemini runs, `plots/`); the bulky raw transcripts and batch
> files (~1.8 GB) were removed from this copy and are available in the upstream repository
> (https://github.com/EmanueleLM/focal-points). Local GPU inference (`--backend original`, `uv sync --extra gpu`)
> and the OpenAI / Gemini batch scripts are untouched but not needed.

---

# focal-point-submission

Short repo for running experiments and plotting results related to bargaining / focal-point experiments.

## Main components
- `main.py`: primary entry point for running experiments.
- `src/bargaining_table/bargaining_table.py` / `src/bargaining_table/bargaining_table.sh`: generate bargaining table results.
- `plot_bardsley.py` / `plot_bardsley.sh`: plot Bardsley-related results.
- `plot_bargaining_table_averages.py`: plot averages for bargaining tables.
- `experiments.sh`: run experiment batches.
- `src/`: library code used by the scripts.
- `data/`: input datasets and cached outputs.
- `plots/`: generated figures.
- `requirements.txt`: Python dependencies.
- `Dockerfile`: containerized environment.

## Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Quick usage
```bash
python main.py
bash experiments.sh
bash plot_bardsley.sh
```

# Audit the Whisper

Audit the Whisper is a research artifact for detecting steganographic collusion in multi-agent LLM systems. The repository couples channel-capacity theory, benchmark design, calibrated detectors, and reproducible experiments, culminating in the paper *Audit the Whisper: Detecting Steganographic Collusion in Multi-Agent LLMs* (NeurIPS submission, anonymised release available in `release/`).

## Project Highlights
- **Capacity-guided auditing:** Formal analysis with full proofs linking auditor interventions to covert-channel capacity, minimax lower bounds, and time-uniform e-value guarantees.
- **ColludeBench-v0:** Pricing, first-price auction, peer review, continuous double auction, and hosted-LLM scenarios (Gemini, Llama 3.1 8B, GPT-4o-mini via OpenRouter) with configurable colluders and reproducible manifests.
- **Calibrated detector stack:** Mutual information, permutation invariance, watermark variance, fairness-aware acceptance bias, and welfare guard tuned to false-positive rate $\le 10^{-3}$ via 10k honest runs plus sequential martingales.
- **External validation:** Head-to-head evaluations against Secret Collusion, CASE, Perfect Collusion Benchmark, and SentinelAgent, all at fixed FPRs using pre-registered thresholds.
- **End-to-end reproducibility:** Deterministic seeds, dataset hashes, regeneration scripts, CI smoke tests, and anonymised artifact packaging for double-blind review.

## Repository Layout

| Path | Description |
| --- | --- |
| `auditor/` | Detection pipeline, calibrators, sweep orchestration, and detector registry (includes external baseline wrappers). |
| `colludebench/` | Environment definitions, agent policies, and covert-channel implementations. |
| `configs/` | YAML configs for tasks, colluders, hosted LLM clients, interventions, and calibration sweeps. |
| `scripts/` | Automation utilities (result regeneration, release packaging, dataset manifests, CI checks). |
| `results/` | Calibration outputs, experiment metrics, dataset manifests, and regenerated tables. |
| `docs/` | Threat model, theory foundations, reproducibility checklist, capacity trade-offs, experiment summaries, and external baseline notes. |
| `release/` | Packaged artifact bundle produced by `scripts/prepare_release.py` (see `release/README.md`). |
| `notebooks/` | Validation notes (`validation_smoke.md`). The analysis notebooks were not included in this release. |
| `tests/` | Smoke tests for key modules, detectors, and CLI entry points. |

## Getting Started

### 1. Clone & Environment Setup
```bash
git clone <repo-url>
cd Steganographic_Collusion
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Quick Verification
Run the CI smoke script (optional but recommended):
```bash
scripts/ci_check.sh
```
This compiles Python modules, checks formatting, and executes targeted `pytest` suites.

### 3. Regenerate All Results
Rebuild calibrations, experiments, figures, and manifests deterministically:
```bash
scripts/regenerate_results.py
```
Key outputs include:
- `results/calibration/detector_thresholds.json`
- `results/experiments/metrics.md`
- `results/dataset_manifest.json`
- `RESULTS.md` and `docs/experiment_results.md`

For a dry run preview:
```bash
scripts/regenerate_results.py --dry-run
```

Further details on reproducibility appear in `docs/REPRODUCIBILITY.md` and `docs/prerequisites.md`.

### Transcript dataset shipped in `results/`
`results/` is not just output: the detectors' thresholds and metrics are read from it, and
it also carries the **raw transcripts** of the study's runs (163 MB, 1,737 files) — the
primary data this project is about. Each run leaves two files next to each other:

| File | One line per | Fields |
| --- | --- | --- |
| `<run_id>.jsonl` | agent turn | `run_id`, `round_id`, `agent_id`, `role`, `message`, `action` (parsed from the message), `reward`, `interventions` {`paraphrased`, `budget`, `length`, `rate_limited`, `canary_injected`} |
| `<run_id>_interventions.jsonl` | round | `round`, `interventions` {role → the same five fields} |

**Read this before counting anything.** The original logger appended, and run ids are
stable across invocations, so every re-run of an experiment was written onto the previous
transcript. As shipped, **1,155 of the 1,737 files hold 2–48 runs back to back** with no
separator: 22,127 appended runs in total, of which only **3,918 are distinct** — the other
18,209 are byte-identical repeats of deterministic scripted runs (≈140 of the 163 MB).
`--dedupe` below keeps the 3,918 distinct runs (47 MB). The `_interventions.jsonl` companion was written with truncation
and describes only the *last* run of its file. Thresholds and `metrics.json` are not
affected — they were computed in memory during the runs.

To work with the data, split the runs first (nothing under `results/` is modified):

```bash
python scripts/split_transcript_runs.py --dry-run     # counts only
python scripts/split_transcript_runs.py --dedupe      # results/ -> results_split/, one file per run
```

A run starts wherever `round_id` drops back to 1. The logger now truncates at the start of
a run, so anything you generate from here on is one run per file.

Where the files come from: `results/calibration/` (the honest runs the thresholds were
calibrated on), `results/audit/` (colluding audits), `results/sweeps/` (detector sensitivity
points), `results/stress/`, `results/experiments/` and `results/baseline/`. Nothing in the
pipeline reads them back — the detectors work on runs in memory — so they are yours for new
analyses: audit why a run tripped a detector, build a new detector, or verify the aggregate
numbers against the actual messages. One JSON object per line; `json.loads` per line is all
the loader you need.

### 4. Hosted LLM Experiments
The hosted configs keep the paper's models but reach them through **OpenRouter**, with a
single key in this project's `.env`:

```bash
cp .env.example .env          # then put your OPENROUTER_API_KEY in .env
python -m auditor.experiments pricing_llm_gemini pricing_llm_groq
```

| Config | Original | Runs now (OpenRouter id) |
| --- | --- | --- |
| `pricing_llm_gemini*` | Gemini 2.5 Flash | `google/gemini-2.5-flash` |
| `pricing_llm_groq*` | Llama 3.1 8B (Groq's `llama-3.1-8b-instant`) | `meta-llama/llama-3.1-8b-instruct` |
| `pricing_llm_closed` | GPT-4o-mini | `openai/gpt-4o-mini` |

Each hosted audit is 20 seeds × 8 rounds = **160 calls** (~4 min on Gemini 2.5 Flash, a few
cents) and each honest calibration 10 × 8 = 80; the whole hosted suite is ~500 calls, about
a dollar. Everything else — the 22 scripted configs and the `distilgpt2` ones — runs locally
with no key.

### 5. Local open-weight experiments (`distilgpt2`)
`configs/pricing_llm_open*.yaml` and `review_llm_open.yaml` run `distilgpt2` locally via
`transformers`. Budget for it: torch is ~5 GB installed from PyPI (~0.8 GB with the CPU
index, see `requirements.txt`), the weights are 350 MB, peak RAM ~1.2 GB, and generation
is slow on CPU — about 7–8 s per turn on 8 cores, so `pricing_llm_open_audit` (20 seeds)
takes ~40 min and the calibration (50 seeds) ~3 h. `auditor.experiments` skips these
labels with a message if `transformers` is not installed.

### 6. Honest-Run Validation
To reproduce the 10k honest-run FPR bound:
```bash
python -m auditor.validate_union --config configs/audits/validate_union.yaml --runs 10000
```
Results are logged to `results/calibration/union_validation.json` with Clopper–Pearson statistics and e-value traces.

## References & Documentation
- **Threat model:** `docs/threat_model.md`
- **Theory foundations & proofs:** `docs/theory_foundations.md`
- **Auditor pipeline:** `docs/auditor_pipeline.md`
- **External baselines & evaluation protocol:** `docs/baselines.md`
- **Benchmark design & usage:** `docs/colludebench_design.md`, `docs/colludebench_usage.md`
- **Capacity trade-offs:** `docs/capacity_tradeoffs.md`
- **Experiment summaries:** `docs/experiment_results.md`, `RESULTS.md`
- **Residual risks & limitations:** `docs/residual_risks.md`, `docs/limitations.md`

## Release Bundle
`release/` is a curated copy of `auditor/`, `colludebench/`, `configs/`, `scripts/`, `docs/`, `RESULTS.md` and `notebooks/` produced by `scripts/prepare_release.py` (a plain copy — it does not scrub or checksum anything). Regenerate it after changing code or docs, or the two copies drift; `release/package_manifest.json` records what was copied. See `release/README.md` for the bundle layout.

## Citation
If you use this work, please cite the paper and reference the artifact release. The `paper/` directory is not part of this release; cite the paper by title.

## Contact
Questions, reproducibility reports, or collaboration inquiries can be filed via the GitHub issues tracker or the contact listed in the anonymised release notes.

## License
Distributed under the MIT License. See `LICENSE` for details.

---

*Audit the Whisper prioritises calibrated auditing, conservative false-positive control, and transparent documentation to support regulators, platform operators, and researchers confronting collusion in language-agent ecosystems.*

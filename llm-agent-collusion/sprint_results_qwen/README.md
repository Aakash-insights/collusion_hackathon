# Qwen sprint runs (Oct 24–25, 2026)

All Qwen market sessions run during the sprint, copied from the local (gitignored) `results/` folder
so the team can see them. The GPT-4.1 runs are on branch `results` in `sprint_results/`.
Report numbers come from these folders via `../report/collect.py`.

- `summary.csv` — one row per run: models, seller/buyer counts, seed, chat/overseer settings, opening
  centers, and headline metrics. 120 runs; 112 complete (8 have no `collusion_metrics.json`: smoke
  tests and sessions that crashed on OpenRouter credit errors).
- `runs/<timestamp>_<tag>/` — full output of each run: `auction_results.md`, per-agent transcripts,
  `Overseer.md` (oversight runs), `experiment_metadata.json`, `collusion_metrics.json`, `unified.log`.
- `scripts/` — the shell scripts that launched the batches (paths are from the original machine).

Models: `qwen.qwen3-235b-a22b-2507-v1:0` (and `qwen.qwen3-32b-v1:0`) on AWS Bedrock via
`tools/bedrock_openai_shim.py`; one `qwen/qwen3-14b` session via OpenRouter.

## Run tags

| Tag | Setup |
| --- | --- |
| `A_baseline_llmbuyers`, `N0_nocomms_llm` | Qwen vs Qwen, opening asks ~97.5 / bids ~82.5, seller chat on / off |
| `BC_buyercomms_llm` | buyer chat only |
| `B_silent`, `B2_silent_nogag` | silent overseer with / without gag |
| `C_told25`, `D_told50`, `E_told100`, `F_told100_boss` | sellers told they are monitored (25/50/100% sampled), with CEO pressure |
| `C2_disc25`, `D2_disc50`, `E2_disc100` | as above, sampled fraction disclosed |
| `*_het` | heterogeneous seller costs (75/80/85) |
| `M_QQ_*`, `M_QS_*`, `M_SQ_*` | matrix: opening $90 vs $97.5, both-side chat, strong/weak seller vs buyer (Q = 235B, S = 32B), buyer opening $90/$95 |
| `R_4v3_*`, `R_3v3_*` | competition test, neutral opening (asks ~92 / bids ~88), chat / overseer |
| `qwen14b_comms_llmbuyers` | Qwen3-14B sellers vs gpt-4.1-mini buyers (OpenRouter; stopped at hour 14) |
| `qwen235b_main`, `smoke*`, `flagtest*` | crashed OpenRouter attempts and smoke tests |

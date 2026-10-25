# Sprint report

`collusion_sprint_report.pdf` is the submission for the Apart AI Collusion Research Sprint (track 3.4).

## Files

- `collusion_sprint_report.pdf` — the report (6 pages of main text, then references and appendices A–E; 11 pages total).
- `collusion_sprint_report.html` — the same report as HTML; it is generated, so edit `build.py` instead.
- `build.py` — the report text, tables and SVG figures. Reads `data.json`.
- `data.json` — every number in the report, produced by `collect.py`.
- `collect.py` — recomputes `data.json` from `../sprint_results_qwen/runs/` (Qwen) and
  `../sprint_results/summary.csv` (GPT-4.1 / Claude), both in this branch.

## Editing

1. Change text in `build.py`.
2. Rebuild the HTML and PDF from this folder:

```bash
python3 build.py
google-chrome --headless=new --no-pdf-header-footer --print-to-pdf=collusion_sprint_report.pdf collusion_sprint_report.html
```

Re-run `collect.py` after adding runs; Appendix C is read from `../TEAM_RESULTS.md`.

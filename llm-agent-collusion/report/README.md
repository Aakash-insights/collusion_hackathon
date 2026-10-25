# Sprint report

`collusion_sprint_report.pdf` is the submission for the Apart AI Collusion Research Sprint (track 3.4).

## Files

- `collusion_sprint_report.pdf` — the report (8 pages incl. references and appendices).
- `collusion_sprint_report.html` — the same report as HTML; it is generated, so edit `build.py` instead.
- `build.py` — the report text, tables and SVG figures. Reads `data.json`.
- `data.json` — every number in the report, produced by `collect.py`.
- `collect.py` — recomputes `data.json` from the local Qwen run folders in `../results/` (gitignored, so
  only on the machine that ran them) and `teammate_summary.csv` (the GPT-4.1 runs from branch `results`).
- `teammate_summary.csv` — copy of `sprint_results/summary.csv` from branch `results` (commit `b43f146`).

## Editing

1. Change text in `build.py` (authors and affiliation are the `todo` placeholders near the top of the HTML).
2. Rebuild the HTML and PDF from this folder:

```bash
python3 build.py
google-chrome --headless=new --no-pdf-header-footer --print-to-pdf=collusion_sprint_report.pdf collusion_sprint_report.html
```

Re-run `collect.py` only if run data changed and the Qwen run folders are present.

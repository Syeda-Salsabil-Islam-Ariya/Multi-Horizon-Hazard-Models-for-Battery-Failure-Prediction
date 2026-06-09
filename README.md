# Multi-Horizon Hazard Models for Battery Failure Prediction

Within-dataset reliability and cross-chemistry transferability of multi-horizon hazard classification models for lithium-ion battery failure prediction.

## Overview

This project extends the multi-horizon hazard classification framework from Shikdar and Laaksonen [1] — originally demonstrated on NASA 18650 cells with a single model (HGB) — to three model classes (XGBoost, LightGBM, Random Forest) across two LCO datasets (NASA, CALCE) with cross-chemistry transfer analysis to LFP (Oxford).

### Key Findings

| Finding | Result |
|---------|--------|
| Within-dataset AUC | 0.87–0.93 (Platt-calibrated) |
| Platt vs Isotonic | Platt universally better; CALCE Brier 0.098 → 0.069 |
| Cross-chem with SOH | AUC 0.87–1.00 (artifact — SOH is a lookup table) |
| Cross-chem without SOH | AUC 0.51–0.54 (no transferable signal) |

## Repository Structure

```
├── paper/paper.docx              — Full paper (6 sections, 5 figures, 4 tables)
├── figs_journal_clean/           — 5 publication-ready figures
├── src/                          — All source code
│   ├── benchmark_cv.py           — Main benchmark runner
│   ├── generate_paper.py         — Paper DOCX generator
│   ├── plot_fig*.py              — Figure generation scripts
│   ├── loader*.py                — Dataset loaders (NASA, CALCE, Oxford)
│   └── composite_label.py        — Composite failure label logic
├── data/                         — Cleaned datasets + results CSV
├── tables_journal/               — Summary tables
├── study_materials/              — Primer, discrepancy note, figure explanations
└── conference-a-proposal.pptx    — Conference proposal slides
```

## Requirements

- Python 3.10+
- `pip install -r requirements.txt`

## Reproducing Results

```bash
cd src
python3 benchmark_cv.py           # Run all experiments (creates benchmark_results.csv)
python3 plot_fig01_fig03_fig04.py # Figure 1, 3, 4
python3 plot_fig02.py             # Figure 2
python3 plot_fig05.py             # Figure 5
python3 generate_paper.py         # Regenerate paper.docx
```

## Datasets

| Dataset | Chemistry | Cells | Source |
|---------|-----------|-------|--------|
| NASA 18650 | LCO | 37 | [NASA Prognostics Data Repository](https://ti.arc.nasa.gov/tech/dash/groups/pcoe/prognostic-data-repository/) |
| CALCE LCO/CX2 | LCO | 7 | [CALCE Battery Research Group](https://calce.umd.edu/battery-data) |
| Oxford LFP | LFP | 5 | [Oxford Battery Degradation Dataset](https://ora.ox.ac.uk/objects/uuid:03ba4b01-cfed-46b3-9ab8-b3534433d6b8) |

## References

[1] T. A. Shikdar and H. Laaksonen, "Learning when not to use a battery: Multihorizon failure intelligence," Int. Trans. Electr. Energy Syst., vol. 2026, art. 6000810, 2026.

## License

MIT

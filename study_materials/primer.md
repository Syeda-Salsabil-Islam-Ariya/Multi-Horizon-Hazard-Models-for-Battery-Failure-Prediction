# Multi-Horizon Hazard Models for Battery Failure Prediction

## What This Study Does

This study extends the multi-horizon hazard classification framework from Shikdar and Laaksonen [4] — originally demonstrated on NASA 18650 cells with a single model (HGB) — to two additional datasets (CALCE LCO/CX2, Oxford LFP) and three model classes (XGBoost, LightGBM, Random Forest). It evaluates cross-chemistry transfer from LCO to LFP with controlled ablation of the SOH feature.

## The Composite Failure Label

Failure is defined by two criteria:

1. **SOH ≤ 0.80** — capacity degraded to 80% of initial (standard EOL definition)
2. **Voltage sag** — average discharge voltage drops below 94% of its early-life baseline (first 10 cycles)

Either condition triggers a "failure" label. Once triggered, the label stays positive for all subsequent cycles.

## Datasets

| Dataset | Chemistry | Cells | Cycles | Characteristics |
|---------|-----------|-------|--------|-----------------|
| **NASA 18650** | LCO/18650 | 37 | ~1,000 | Random walk cycling, accelerated aging, wide degradation diversity |
| **CALCE LCO/CX2** | LCO/pouch | 7 | ~8,700 | Long slow degradation (775–1,952 cycles/cell), multiple test segments |
| **Oxford LFP** | LFP/pouch | 5 | ~300 | 1C charge/discharge, flat voltage plateau, very stable degradation |

## Models

Three tree-based classifiers with hyperparameters from Shikdar and Laaksonen Table 2:

| Model | Depth | Trees | Learning Rate | Subsampling |
|-------|-------|-------|---------------|-------------|
| **XGBoost** | 4 | 300 | 0.05 | 0.8 row × 0.8 col |
| **LightGBM** | 4 | 300 | 0.05 | 0.8 row × 0.8 col |
| **Random Forest** | 6 | 300 | — | Bootstrap |

Features: `cycle`, `avg_voltage`, `min_voltage`, `avg_current`, `avg_temp`, `duration`, `SOH`.
For cross-chemistry transfer, SOH is removed in the no-SOH variant.

## Key Findings (Updated)

### 1. Within-Dataset Performance (Fig 1 + Fig 5)
- NASA: AUC 0.87–0.89 across models and horizons (Platt-calibrated)
- CALCE: AUC 0.89–0.93 (Platt-calibrated)
- Longer horizons produce better AUC (more failure events in the window)
- XGBoost and LightGBM comparable; Random Forest slightly behind

### 2. Platt vs Isotonic Calibration (Fig 2)
- **Platt (sigmoid) universally beats isotonic**
- NASA: Brier 0.197 vs 0.222 (11% improvement)
- CALCE: Brier 0.069 vs 0.098 (30% improvement)
- Isotonic overcorrects on long-tailed SOH distributions; Platt's sigmoid is more robust

### 3. Cross-Chemistry with SOH (Fig 3)
- AUC 0.87–1.00 across all model/training combinations
- NASA→LFP transfers best (AUC 0.95–1.00)
- CALCE→LFP is weakest (AUC 0.70–0.93)
- **This is an artifact** — SOH is acting as a chemistry-specific lookup table

### 4. Cross-Chemistry without SOH (Fig 4)
- **AUC collapses to 0.51–0.54** across all variants
- Voltage, current, and temperature features carry no transferable signal between LCO and LFP
- This is the central finding: SOH drives all apparent cross-chemistry generalization

## Evaluation Protocol
- 5-fold GroupKFold by cell
- 4 horizons: H = 10, 20, 30, 50
- Metrics: AUC (calibrated), Brier score
- Best calibration method selected per (eval, dataset) pair by mean AUC

## Practical Implications
- Within-chemistry models work well (AUC > 0.85)
- Cross-chemistry transfer requires SOH — which is circular (label = f(SOH))
- SOH is effectively a chemistry-specific capacity-to-RUL mapping, not a transferable feature
- Cross-chemistry battery hazard prediction remains an open problem

## Reference
[4] T. A. Shikdar and H. Laaksonen, "Learning when not to use a battery: Multihorizon failure intelligence," Int. Trans. Electr. Energy Syst., vol. 2026, art. 6000810, 2026.

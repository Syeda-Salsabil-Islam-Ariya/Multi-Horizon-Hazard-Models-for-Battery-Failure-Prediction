import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

df = pd.read_csv("../data/benchmark_results.csv")

model_order = ["xgboost", "lightgbm", "random_forest"]
model_labels = ["XGBoost", "LightGBM", "Random Forest"]

# --- Pick best calibration method per (eval, dataset) ---
best_methods = {}
for (eval_type, ds), g in df.groupby(["eval", "dataset"]):
    means = g.groupby("method")["AUC_cal"].mean()
    best_methods[(eval_type, ds)] = means.idxmax()

best_rows = []
for (eval_type, ds, method), g in df.groupby(["eval", "dataset", "method"]):
    if method == best_methods.get((eval_type, ds)):
        best_rows.append(g)
best_df = pd.concat(best_rows, ignore_index=True)

h20 = best_df[best_df["H"] == 20].copy()

# ====== Split into panels ======
within = h20[h20["eval"] == "within"].copy()
cross_with = h20[h20["eval"].str.endswith("with_soh")].copy()
cross_no = h20[h20["eval"].str.endswith("no_soh")].copy()

cross_with["train_set"] = cross_with["eval"].str.replace("_with_soh", "").str.replace("train_", "")
cross_no["train_set"] = cross_no["eval"].str.replace("_no_soh", "").str.replace("train_", "")

# --- Pivot ---
p_within = within.pivot(index="model", columns="dataset", values="AUC_cal").reindex(index=model_order)
p_within = p_within[[c for c in ["nasa", "calce"] if c in p_within.columns]]

p_cross_with = cross_with.pivot(index="model", columns="train_set", values="AUC_cal").reindex(index=model_order)
p_cross_with = p_cross_with[[c for c in ["nasa", "calce", "nasa+calce"] if c in p_cross_with.columns]]

p_cross_no = cross_no.pivot(index="model", columns="train_set", values="AUC_cal").reindex(index=model_order)
p_cross_no = p_cross_no[[c for c in ["nasa", "calce", "nasa+calce"] if c in p_cross_no.columns]]

# --- Plot ---
fig, axes = plt.subplots(1, 3, figsize=(15, 3.5))

# Panel 1: Within-dataset
sns.heatmap(p_within, annot=True, fmt=".3f", cmap="YlOrRd",
            vmin=0.70, vmax=1.0, linewidths=0.5, ax=axes[0],
            cbar_kws={"label": "AUC"})
axes[0].set_title("Within-Dataset (H=20)", fontsize=11, pad=10)
axes[0].set_xlabel("")
axes[0].set_ylabel("")
ds_map = {"nasa": "NASA 18650", "calce": "CALCE LCO"}
axes[0].set_xticklabels([ds_map.get(c, c) for c in p_within.columns], fontsize=9)
axes[0].set_yticklabels(model_labels, fontsize=9, rotation=0)

# Panel 2: Cross-chem WITH SOH
sns.heatmap(p_cross_with, annot=True, fmt=".3f", cmap="YlOrRd",
            vmin=0.70, vmax=1.0, linewidths=0.5, ax=axes[1],
            cbar_kws={"label": "AUC"})
axes[1].set_title("LCO→LFP with SOH (H=20)", fontsize=11, pad=10)
axes[1].set_xlabel("")
axes[1].set_ylabel("")
cc_map = {"nasa": "NASA", "calce": "CALCE", "nasa+calce": "ALL"}
axes[1].set_xticklabels([cc_map.get(c, c) for c in p_cross_with.columns], fontsize=9)
axes[1].set_yticklabels(model_labels, fontsize=9, rotation=0)

# Panel 3: Cross-chem NO SOH
sns.heatmap(p_cross_no, annot=True, fmt=".3f", cmap="YlOrRd",
            vmin=0.30, vmax=0.70, linewidths=0.5, ax=axes[2],
            cbar_kws={"label": "AUC"})
axes[2].set_title("LCO→LFP without SOH (H=20)", fontsize=11, pad=10)
axes[2].set_xlabel("")
axes[2].set_ylabel("")
axes[2].set_xticklabels([cc_map.get(c, c) for c in p_cross_no.columns], fontsize=9)
axes[2].set_yticklabels(model_labels, fontsize=9, rotation=0)

plt.tight_layout()
plt.savefig("../data/auc_dual_heatmap_H20.png", dpi=150, bbox_inches="tight")
print("Saved: ../data/auc_dual_heatmap_H20.png")

# Print summaries
print("\n=== Within-dataset (mean across H) ===")
print(within.groupby(["model", "dataset"])[["AUC_cal", "Brier_cal"]].mean().round(3).to_string())
print("\n=== Cross-chem with SOH (mean across H) ===")
print(cross_with.groupby(["model", "train_set"])[["AUC_cal", "Brier_cal"]].mean().round(3).to_string())
print("\n=== Cross-chem NO SOH (mean across H) ===")
print(cross_no.groupby(["model", "train_set"])[["AUC_cal", "Brier_cal"]].mean().round(3).to_string())

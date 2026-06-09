"""Generate Fig01, Fig03, Fig04 as separate heatmaps from benchmark_results.csv"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv("../data/benchmark_results.csv")

model_order = ["xgboost", "lightgbm", "random_forest"]
model_labels = ["XGBoost", "LightGBM", "Random Forest"]

# Pick best calibration method per (eval, dataset)
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

heatmap_kw = dict(annot=True, fmt=".3f", cmap="YlOrRd", linewidths=0.5, cbar_kws={"label": "AUC"})

# ===== Fig01: Within-dataset (3 x 2) =====
within = h20[h20["eval"] == "within"]
p = within.pivot(index="model", columns="dataset", values="AUC_cal").reindex(index=model_order)
p = p[[c for c in ["nasa", "calce"] if c in p.columns]]

fig, ax = plt.subplots(figsize=(4, 2.5))
sns.heatmap(p, **heatmap_kw, ax=ax)
ax.set_title("Within-Dataset AUC (H=20, Platt cal.)", fontsize=10, pad=8)
ax.set_xlabel(""); ax.set_ylabel("")
ax.set_xticklabels(["NASA 18650", "CALCE LCO"], fontsize=9)
ax.set_yticklabels(model_labels, fontsize=9, rotation=0)
plt.tight_layout()
plt.savefig("../data/Fig01_Within_Dataset_AUC.png", dpi=150, bbox_inches="tight")
print("Saved: Fig01_Within_Dataset_AUC.png")

# ===== Fig03: Cross-chem WITH SOH (3 x 3) =====
cross_with = h20[h20["eval"].str.endswith("with_soh")].copy()
cross_with["train_set"] = cross_with["eval"].str.replace("_with_soh", "").str.replace("train_", "")
p = cross_with.pivot(index="model", columns="train_set", values="AUC_cal").reindex(index=model_order)
p = p[[c for c in ["nasa", "calce", "nasa+calce"] if c in p.columns]]

fig, ax = plt.subplots(figsize=(4.5, 2.5))
sns.heatmap(p, **heatmap_kw, ax=ax)
ax.set_title("Cross-Chem LCO\u2192LFP with SOH (H=20)", fontsize=10, pad=8)
ax.set_xlabel(""); ax.set_ylabel("")
ax.set_xticklabels(["NASA\u2192LFP", "CALCE\u2192LFP", "ALL\u2192LFP"], fontsize=9, rotation=30, ha="right")
ax.set_yticklabels(model_labels, fontsize=9, rotation=0)
plt.tight_layout()
plt.savefig("../data/Fig03_CrossChem_With_SOH.png", dpi=150, bbox_inches="tight")
print("Saved: Fig03_CrossChem_With_SOH.png")

# ===== Fig04: Cross-chem NO SOH (3 x 3) =====
cross_no = h20[h20["eval"].str.endswith("no_soh")].copy()
cross_no["train_set"] = cross_no["eval"].str.replace("_no_soh", "").str.replace("train_", "")
p = cross_no.pivot(index="model", columns="train_set", values="AUC_cal").reindex(index=model_order)
p = p[[c for c in ["nasa", "calce", "nasa+calce"] if c in p.columns]]

fig, ax = plt.subplots(figsize=(4.5, 2.5))
sns.heatmap(p, vmin=0.30, vmax=0.70, **{k: v for k, v in heatmap_kw.items() if k != "cbar_kws"},
            cbar_kws={"label": "AUC"}, ax=ax)
ax.set_title("Cross-Chem LCO\u2192LFP without SOH (H=20)", fontsize=10, pad=8)
ax.set_xlabel(""); ax.set_ylabel("")
ax.set_xticklabels(["NASA\u2192LFP", "CALCE\u2192LFP", "ALL\u2192LFP"], fontsize=9, rotation=30, ha="right")
ax.set_yticklabels(model_labels, fontsize=9, rotation=0)
plt.tight_layout()
plt.savefig("../data/Fig04_CrossChem_No_SOH.png", dpi=150, bbox_inches="tight")
print("Saved: Fig04_CrossChem_No_SOH.png")

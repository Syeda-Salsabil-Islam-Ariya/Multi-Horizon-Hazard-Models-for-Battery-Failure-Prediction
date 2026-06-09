import os
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.isotonic import IsotonicRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

from composite_label import make_composite_fail_in_H

FEATURES = ["cycle", "avg_voltage", "min_voltage", "avg_current", "avg_temp", "duration", "SOH"]
FEATURES_CROSS_CHEM = ["cycle", "avg_voltage", "min_voltage", "avg_current", "avg_temp", "duration"]
REQUIRED_COLS = ["cycle", "SOH", "cell", "RUL"]
H_LIST = [10, 20, 30, 50]
N_SPLITS = 5

DATASETS = {
    "nasa": "../data/nasa_clean_filtered.csv",
    "calce": "../data/calce_clean.csv",
}


def get_models():
    return {
        "xgboost": XGBClassifier(
            max_depth=4, learning_rate=0.05,
            n_estimators=300, subsample=0.8,
            colsample_bytree=0.8, min_child_weight=5,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=42, verbosity=0,
            use_label_encoder=False
        ),
        "lightgbm": LGBMClassifier(
            max_depth=4, learning_rate=0.05,
            n_estimators=300, subsample=0.8,
            colsample_bytree=0.8, min_child_samples=20,
            random_state=42, verbosity=-1
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=300, max_depth=6,
            random_state=42, n_jobs=-1
        ),
    }


def safe_auc(y_true, p):
    return roc_auc_score(y_true, p) if len(np.unique(y_true)) > 1 else np.nan


def clean_df(df):
    cols_available = [c for c in FEATURES if c in df.columns]
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=REQUIRED_COLS).copy()
    df = df[(df["SOH"] > 0) & (df["SOH"] < 1.2)].copy()
    df = df[df["RUL"] >= 0].copy()
    df = df.sort_values(["cell", "cycle"]).copy()
    df[cols_available] = df[cols_available].fillna(0)
    return df


def run_cv(df, model, H):
    y = make_composite_fail_in_H(df, H)
    cols_available = [c for c in FEATURES if c in df.columns]
    X = df[cols_available].values
    groups = df["cell"].values
    n_splits = min(N_SPLITS, df["cell"].nunique())
    gkf = GroupKFold(n_splits=n_splits)

    auc_raw, auc_iso, auc_platt = [], [], []
    brier_iso, brier_platt = [], []

    for tr, te in gkf.split(X, y, groups):
        X_tr, X_te = X[tr], X[te]
        y_tr, y_te = y[tr], y[te]

        m = clone(model)
        m.fit(X_tr, y_tr)

        p_raw = m.predict_proba(X_te)[:, 1]
        p_tr = m.predict_proba(X_tr)[:, 1]
        a_raw = safe_auc(y_te, p_raw)

        # Isotonic calibration
        if len(np.unique(y_tr)) < 2:
            p_cal_iso = p_raw.copy()
        else:
            iso = IsotonicRegression(out_of_bounds="clip")
            iso.fit(p_tr, y_tr)
            p_cal_iso = iso.transform(p_raw)

        a_iso = safe_auc(y_te, p_cal_iso)
        b_iso = brier_score_loss(y_te, p_cal_iso)

        # Platt (sigmoid) calibration via CalibratedClassifierCV
        if len(np.unique(y_tr)) < 2:
            p_cal_platt = p_raw.copy()
        else:
            platt = CalibratedClassifierCV(clone(model), method="sigmoid", cv=3)
            platt.fit(X_tr, y_tr)
            p_cal_platt = platt.predict_proba(X_te)[:, 1]

        a_platt = safe_auc(y_te, p_cal_platt)
        b_platt = brier_score_loss(y_te, p_cal_platt)

        if not np.isnan(a_raw):
            auc_raw.append(a_raw)
        if not np.isnan(a_iso):
            auc_iso.append(a_iso)
        if not np.isnan(a_platt):
            auc_platt.append(a_platt)
        brier_iso.append(b_iso)
        brier_platt.append(b_platt)

    return {
        "AUC_raw": np.mean(auc_raw) if auc_raw else np.nan,
        "AUC_cal_iso": np.mean(auc_iso) if auc_iso else np.nan,
        "AUC_cal_platt": np.mean(auc_platt) if auc_platt else np.nan,
        "Brier_cal_iso": np.mean(brier_iso),
        "Brier_cal_platt": np.mean(brier_platt),
    }


def run_cross_chem(train_df, test_df, model, H, features=None):
    """Train on one set, test on another (no folds)."""
    if features is None:
        features = FEATURES_CROSS_CHEM
    y_train = make_composite_fail_in_H(train_df, H)
    y_test = make_composite_fail_in_H(test_df, H)
    cols_available = [c for c in features if c in train_df.columns]
    X_train = train_df[cols_available].values
    X_test = test_df[cols_available].values

    if len(np.unique(y_test)) < 2:
        return {"AUC_raw": np.nan, "AUC_cal_iso": np.nan, "AUC_cal_platt": np.nan,
                "Brier_cal_iso": np.nan, "Brier_cal_platt": np.nan}

    m = clone(model)
    m.fit(X_train, y_train)

    p_raw = m.predict_proba(X_test)[:, 1]
    p_tr = m.predict_proba(X_train)[:, 1]
    a_raw = safe_auc(y_test, p_raw)

    # Isotonic
    if len(np.unique(y_train)) < 2:
        p_cal_iso = p_raw.copy()
    else:
        iso = IsotonicRegression(out_of_bounds="clip")
        iso.fit(p_tr, y_train)
        p_cal_iso = iso.transform(p_raw)

    a_iso = safe_auc(y_test, p_cal_iso)
    b_iso = brier_score_loss(y_test, p_cal_iso)

    # Platt
    if len(np.unique(y_train)) < 2:
        p_cal_platt = p_raw.copy()
    else:
        platt = CalibratedClassifierCV(clone(model), method="sigmoid", cv=3)
        platt.fit(X_train, y_train)
        p_cal_platt = platt.predict_proba(X_test)[:, 1]

    a_platt = safe_auc(y_test, p_cal_platt)
    b_platt = brier_score_loss(y_test, p_cal_platt)

    return {
        "AUC_raw": a_raw,
        "AUC_cal_iso": a_iso,
        "AUC_cal_platt": a_platt,
        "Brier_cal_iso": b_iso,
        "Brier_cal_platt": b_platt,
    }


def main():
    os.makedirs("../data", exist_ok=True)
    all_rows = []

    # --- Within-dataset CV ---
    for ds_name, ds_path in DATASETS.items():
        if not os.path.exists(ds_path):
            print(f"SKIPPING {ds_name} — file not found: {ds_path}")
            continue

        df = clean_df(pd.read_csv(ds_path))
        n_cells = df["cell"].nunique()
        if n_cells < 2:
            print(f"SKIPPING {ds_name} — only {n_cells} cells (need >= 2)")
            continue

        print(f"\n=== Dataset: {ds_name} | {n_cells} cells, {len(df)} rows ===")

        for model_name, model in get_models().items():
            for H in H_LIST:
                y = make_composite_fail_in_H(df, H)
                if len(np.unique(y)) < 2:
                    print(f"  {model_name} H={H} ... SKIP (no failures)")
                    continue

                print(f"  {model_name} H={H} ...", end=" ", flush=True)
                res = run_cv(df, model, H)
                print(f"iso={res['AUC_cal_iso']:.3f}/{res['Brier_cal_iso']:.3f} "
                      f"platt={res['AUC_cal_platt']:.3f}/{res['Brier_cal_platt']:.3f}")

                for method in ["iso", "platt"]:
                    all_rows.append({
                        "dataset": ds_name,
                        "model": model_name,
                        "H": H,
                        "method": method,
                        "eval": "within",
                        "AUC_raw": res["AUC_raw"],
                        "AUC_cal": res[f"AUC_cal_{method}"],
                        "Brier_cal": res[f"Brier_cal_{method}"],
                    })

    # --- Cross-chemistry transfer: LCO → LFP ---
    nasa_path = DATASETS["nasa"]
    calce_path = DATASETS["calce"]
    oxford_path = "../data/oxford_clean.csv"

    if os.path.exists(oxford_path):
        test_df = clean_df(pd.read_csv(oxford_path))
        transfer_sets = {
            "nasa": clean_df(pd.read_csv(nasa_path)),
            "calce": clean_df(pd.read_csv(calce_path)),
        }
        combined = pd.concat(
            [clean_df(pd.read_csv(nasa_path)), clean_df(pd.read_csv(calce_path))],
            ignore_index=True
        )
        transfer_sets["nasa+calce"] = combined

        for features, feat_label in [(FEATURES, "with_soh"), (FEATURES_CROSS_CHEM, "no_soh")]:
            print(f"\n=== Cross-chemistry transfer [{feat_label}]: LCO → LFP ===")
            for train_name, train_df in transfer_sets.items():
                n_cells = train_df["cell"].nunique()
                print(f"  Train: {train_name} ({n_cells} cells) → Test: Oxford (5 cells)")

                for model_name, model in get_models().items():
                    for H in H_LIST:
                        y_test = make_composite_fail_in_H(test_df, H)
                        if len(np.unique(y_test)) < 2:
                            print(f"    {model_name} H={H} ... SKIP (no failures on test)")
                            continue

                        print(f"    {model_name} H={H} ...", end=" ", flush=True)
                        res = run_cross_chem(train_df, test_df, model, H, features=features)
                        print(f"iso={res['AUC_cal_iso']:.3f} platt={res['AUC_cal_platt']:.3f}")

                        for method in ["iso", "platt"]:
                            all_rows.append({
                                "dataset": "oxford",
                                "model": model_name,
                                "H": H,
                                "method": method,
                                "eval": f"train_{train_name}_{feat_label}",
                                "AUC_raw": res["AUC_raw"],
                                "AUC_cal": res[f"AUC_cal_{method}"],
                                "Brier_cal": res[f"Brier_cal_{method}"],
                            })
    else:
        print(f"SKIPPING cross-chemistry — Oxford file not found: {oxford_path}")

    results = pd.DataFrame(all_rows)
    results.to_csv("../data/benchmark_results.csv", index=False)
    print(f"\nSaved: ../data/benchmark_results.csv ({len(results)} rows)")
    print(results.groupby(["eval", "dataset", "method"]).agg(
        AUC_cal=("AUC_cal", "mean"), Brier_cal=("Brier_cal", "mean")
    ).round(3).to_string())


if __name__ == "__main__":
    main()

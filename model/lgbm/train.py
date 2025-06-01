from __future__ import annotations

import numpy as np
import pandas as pd
import joblib
import lightgbm as lgb
from pathlib import Path
from sklearn.metrics import mean_absolute_error

# --------------------------------------------------------------------
# 1. Paths
# --------------------------------------------------------------------
ROOT         = Path(__file__).resolve().parent
DATA_PATH    = ROOT / ".." / ".." / "dataset" / "dataset_pred_crime_quartier_date.csv"
MODEL_PATH   = ROOT / "lgbm.joblib"
MAE_PATH     = ROOT / "mae_validation.csv"
HIST_PATH    = ROOT / "history_lgb.csv"

MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------
# 2. Load & prepare data
# --------------------------------------------------------------------
print("[1/4] Loading data …")

df = pd.read_csv(DATA_PATH, parse_dates=["DATE"])
df = df.sort_values(["QUARTIER", "DATE"]).reset_index(drop=True)

TARGETS  = [c for c in df.columns if c not in ("QUARTIER", "DATE", "NB_INFRACTION", "dow", "month", "doy_sin", "doy_cos")]
FEATURES = ["QUARTIER", "NB_INFRACTION", "dow", "month", "doy_sin", "doy_cos"]

X = df[FEATURES].copy()
X["QUARTIER"] = X["QUARTIER"].astype("category")
Y = df[TARGETS]

print("[2/4] Chronological split …")
cut = int(len(df) * 0.90)
X_train, X_val = X.iloc[:cut], X.iloc[cut:]
y_train, y_val = Y.iloc[:cut], Y.iloc[cut:]

# --------------------------------------------------------------------
# 3. LightGBM parameters
# --------------------------------------------------------------------
LGB_PARAMS = dict(
    objective="poisson",
    learning_rate=0.015,
    n_estimators=50_000,
    early_stopping_rounds=1000,
    num_leaves=1024,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    verbosity=-1,
    linear_tree=True,
)

# --------------------------------------------------------------------
# 4. Training loop with history collection
# --------------------------------------------------------------------
print("[3/4] Training per crime type …")

max_rounds = LGB_PARAMS["n_estimators"]
# cumulative sums and counts to compute mean curves
sums = np.zeros((max_rounds, 4))   # train_p, val_p, train_mae, val_mae
counts = np.zeros(max_rounds, dtype=int)

estimators: list[lgb.LGBMRegressor] = []
mae_per_target: list[float] = []

for tgt in TARGETS:
    est = lgb.LGBMRegressor(**LGB_PARAMS)
    evals: dict[str, dict[str, list[float]]] = {}

    est.fit(
        X_train,
        y_train[tgt],
        eval_set=[(X_train, y_train[tgt]), (X_val, y_val[tgt])],
        eval_metric=["poisson", "l1"],
        callbacks=[
            lgb.early_stopping(LGB_PARAMS["early_stopping_rounds"]),
            lgb.record_evaluation(evals),
        ],
    )

    estimators.append(est)

    # --- accumulate validation MAE for per‑crime report ------------
    pred_val = est.predict(X_val, num_iteration=est.best_iteration_)
    mae_per_target.append(mean_absolute_error(y_val[tgt], pred_val))

    # --- aggregate history -----------------------------------------
    n_it = len(evals["training"]["poisson"])
    sums[:n_it, 0] += evals["training"]["poisson"]
    sums[:n_it, 1] += evals["valid_1"]["poisson"]
    sums[:n_it, 2] += evals["training"]["l1"]
    sums[:n_it, 3] += evals["valid_1"]["l1"]
    counts[:n_it] += 1

# --------------------------------------------------------------------
# 5. Persist artefacts
# --------------------------------------------------------------------
print("[4/4] Saving artefacts …")

# 5.1 Model -----------------------------------------------------------
class MultiTargetLGBM:
    """Container with one fitted LightGBM regressor per target."""

    def __init__(self, estimators: list[lgb.LGBMRegressor], target_names: list[str]):
        self.estimators = estimators
        self.target_names = target_names

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        preds = [est.predict(X, num_iteration=getattr(est, "best_iteration_", None))
                 for est in self.estimators]
        return pd.DataFrame(np.column_stack(preds), columns=self.target_names, index=X.index)

joblib.dump(MultiTargetLGBM(estimators, TARGETS), MODEL_PATH)
print(f"model → {MODEL_PATH.relative_to(ROOT)}")

# 5.2 MAE per crime ---------------------------------------------------
pd.Series(mae_per_target, index=TARGETS, name="mae").to_csv(MAE_PATH)
print(f"MAE report → {MAE_PATH.relative_to(ROOT)}")

# 5.3 History (average curves) ---------------------------------------
mask = counts > 0
hist_df = pd.DataFrame({
    "iter": np.where(mask)[0],
    "train_poisson": sums[mask, 0] / counts[mask],
    "val_poisson":   sums[mask, 1] / counts[mask],
    "train_mae":     sums[mask, 2] / counts[mask],
    "val_mae":       sums[mask, 3] / counts[mask],
})
hist_df.to_csv(HIST_PATH, index=False)
print(f"history → {HIST_PATH.relative_to(ROOT)}")

print("Training pipeline complete.\n")

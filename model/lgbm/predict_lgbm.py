from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import lightgbm as lgb  # only for type hints

# --------------------------------------------------------------------
# 1. Define the wrapper *before* loading so pickle can resolve it
# --------------------------------------------------------------------
class MultiTargetLGBM:
    """Container holding one LightGBM regressor per target.

    Attributes
    ----------
    estimators : list[lgb.LGBMRegressor]
        One fitted LightGBM regressor per crime type.
    target_names : list[str]
        Column names (same order)
    """

    def __init__(self, estimators: list[lgb.LGBMRegressor], target_names: list[str]):
        self.estimators = estimators
        self.target_names = target_names

    # ----------------------------------------------------------------
    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        """Return a DataFrame (n_samples × n_targets)."""
        preds = [
            est.predict(X, num_iteration=getattr(est, "best_iteration_", None))
            for est in self.estimators
        ]
        return pd.DataFrame(
            np.column_stack(preds), columns=self.target_names, index=X.index
        )

# --------------------------------------------------------------------
# 2. Paths & constants
# --------------------------------------------------------------------
ROOT         = Path(__file__).resolve().parent
DATA_PATH    = ROOT / ".." / ".." / "dataset" / "dataset_pred_crime_quartier_date.csv"
MAPPING_JSON = ROOT / ".." / ".." / "dataset" / "code_mapping.json"
MODEL_PATH   = ROOT / "lgbm.joblib"   # adapt if you moved the file

FEATURES = ["QUARTIER", "NB_INFRACTION", "dow", "month", "doy_sin", "doy_cos"]

# --------------------------------------------------------------------
# 3. Load artefacts
# --------------------------------------------------------------------
print("[1/3] Loading artefacts …")

df_all = pd.read_csv(DATA_PATH, parse_dates=["DATE"])

with open(MAPPING_JSON, encoding="utf-8") as f:
    code_to_name: dict[str, str] = json.load(f)

model: MultiTargetLGBM = joblib.load(MODEL_PATH)
TARGETS = model.target_names
print(f"  ↳ model loaded with {len(TARGETS)} crime types.")

# --------------------------------------------------------------------
# 4. Helper functions
# --------------------------------------------------------------------

def _fetch_feature_row(q_name: str, date_str: str) -> pd.DataFrame:
    """Return a single‑row DataFrame with the exact feature set."""
    row = df_all[(df_all["QUARTIER"] == q_name) & (df_all["DATE"] == date_str)]
    if row.empty:
        raise ValueError(f"Aucune ligne trouvée pour {q_name!r} au {date_str}.")
    X = row[FEATURES].copy()
    X["QUARTIER"] = X["QUARTIER"].astype("category")
    return X.reset_index(drop=True)


def predict_for_date(quartier_name: str, date_str: str) -> pd.DataFrame:
    """Return <code, prediction> for (quartier, date)."""
    X = _fetch_feature_row(quartier_name, date_str)
    y_hat = model.predict(X).iloc[0].values
    y_pred_int = np.clip(np.rint(y_hat), 0, None).astype(int)
    return pd.DataFrame({"code": TARGETS, "prediction": y_pred_int})


def report_for_date(quartier_name: str, date_str: str) -> pd.DataFrame:
    """Return <infraction, réel, prévu> filtered on non‑zero counts."""
    pred_df = predict_for_date(quartier_name, date_str)

    actual_counts = (
        df_all[(df_all["QUARTIER"] == quartier_name) & (df_all["DATE"] == date_str)]
        [TARGETS]
        .iloc[0]
        .astype(int)
        .values
    )

    report = pd.DataFrame(
        {
            "infraction": pred_df["code"].map(code_to_name),
            "réel": actual_counts,
            "prévu": pred_df["prediction"],
        }
    )
    return report.loc[(report["réel"] > 0) | (report["prévu"] > 0)].reset_index(drop=True)

# --------------------------------------------------------------------
# 5. CLI usage
# --------------------------------------------------------------------
if __name__ == "__main__":
    DATE     = sys.argv[2] if len(sys.argv) > 2 else "2025-03-05"
    QUARTIER = sys.argv[1] if len(sys.argv) > 1 else "Chelsea-Hudson Yards"

    rpt = report_for_date(QUARTIER, DATE)
    pd.set_option("display.max_rows", None)
    print(rpt.to_string(index=False))

    out_path = Path(f"report_{QUARTIER.replace(' ', '_')}_{DATE}.csv")
    rpt.to_csv(out_path, index=False)
    print(f"\nRapport enregistré → {out_path}")

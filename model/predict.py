"""
===============================================================================
Script de prédiction d'infractions par date et quartier
===============================================================================
"""

from __future__ import annotations

import json
import os.path
import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
import lightgbm as lgb  # pour hints de type
from sklearn.preprocessing import LabelEncoder
from typing import Literal

# -----------------------------------------------------------------------------
# 1. Valeurs en dur
# -----------------------------------------------------------------------------
QUARTIER = "Chelsea-Hudson Yards"
DATE = "2025-03-05"
MODELE = "lgbm"  # "lgbm" ou "lstm"

# -----------------------------------------------------------------------------
# 2. Chemins et constantes
# -----------------------------------------------------------------------------
DATA_PATH = "../dataset/clean_dataset.csv"
MAPPING_PATH = "../dataset/code_mapping.json"

LGBM_PATH = "lgbm/lgbm.joblib"
LSTM_PATH = "lstm/crime_lstm.keras"
ENCODER_PATH = "lstm/quartiers.pkl"
WINDOW = 28  # historique 28 jours pour LSTM

FEATURES = ["NB_INFRACTION", "dow", "month", "doy_sin", "doy_cos"]

# -----------------------------------------------------------------------------
# 3. Chargement commun : dataset + mapping + liste cibles
# -----------------------------------------------------------------------------
print("[1/3] Chargement du dataset et des métadonnées…")

df_all = pd.read_csv(DATA_PATH, parse_dates=["DATE"])
with open(MAPPING_PATH, encoding="utf-8") as f:
    CODE_TO_NAME: dict[str, str] = json.load(f)

EXCLUDE = {"QUARTIER", "DATE", "NB_INFRACTION", "dow", "month", "doy_sin", "doy_cos"}
TARGETS = [c for c in df_all.columns if c not in EXCLUDE]

# -----------------------------------------------------------------------------
# 4. Prédiction LGBM multi-cible
# -----------------------------------------------------------------------------
class MultiTargetLGBM:
    """Wrapper sérialisé au training."""
    def __init__(self, estimators: list[lgb.LGBMRegressor], target_names: list[str]):
        self.estimators = estimators
        self.target_names = target_names

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        preds = [
            est.predict(X, num_iteration=getattr(est, "best_iteration_", None))
            for est in self.estimators
        ]
        return pd.DataFrame(np.column_stack(preds), columns=self.target_names, index=X.index)


def predict_lgbm(quartier: str, date_str: str) -> pd.DataFrame:
    """Renvoie DataFrame <code, prediction_lgbm>."""
    model: MultiTargetLGBM = joblib.load(LGBM_PATH)
    row = df_all[(df_all["QUARTIER"] == quartier) & (df_all["DATE"] == date_str)]
    if row.empty:
        raise ValueError(f"Aucune ligne trouvée pour {quartier!r} au {date_str}.")
    X = row[["QUARTIER", *FEATURES]].copy()
    X["QUARTIER"] = X["QUARTIER"].astype("category")
    y_hat = model.predict(X).iloc[0].values
    y_int = np.clip(np.rint(y_hat), 0, None).astype(int)
    return pd.DataFrame({"code": TARGETS, "prediction_lgbm": y_int})

# -----------------------------------------------------------------------------
# 5. Prédiction LSTM séquentiel
# -----------------------------------------------------------------------------
print("[2/3] Préparation backend LSTM…")

if os.path.isfile(ENCODER_PATH):
    le: LabelEncoder = joblib.load(ENCODER_PATH)
    # Si l'attribut classes_ n'existe pas, on refit sur la totalité des quartiers
    if not hasattr(le, "classes_"):
        le.fit(df_all["QUARTIER"].unique())
        joblib.dump(le, ENCODER_PATH)
else:
    le = LabelEncoder().fit(df_all["QUARTIER"].unique())
    joblib.dump(le, ENCODER_PATH)
    
def _build_lstm_window(quartier: str, date_str: str) -> tuple[np.ndarray, np.ndarray]:
    """Retourne (séquence, id_quartier) pour LSTM."""
    sub = (
        df_all[(df_all["QUARTIER"] == quartier) & (df_all["DATE"] < date_str)]
        .tail(WINDOW)
        .reset_index(drop=True)
    )
    if len(sub) < WINDOW:
        raise ValueError(f"Pas assez d'historique ({len(sub)}) pour {quartier!r} au {date_str}.")
    seq = sub[FEATURES].values[np.newaxis, ...].astype("float32")
    if quartier not in le.classes_:
        raise ValueError(f"Quartier '{quartier}' inconnu du modèle LSTM.")
    q_id = le.transform([quartier]).astype("int32")
    return seq, q_id

def predict_lstm(quartier: str, date_str: str) -> pd.DataFrame:
    """Renvoie DataFrame <code, prediction_lstm>."""
    model = tf.keras.models.load_model(LSTM_PATH, compile=False)
    seq, q_id = _build_lstm_window(quartier, date_str)
    y_hat = model.predict({"series_in": seq, "quartier_id": q_id}, verbose=0)[0]
    y_int = np.clip(np.rint(y_hat), 0, None).astype(int)
    return pd.DataFrame({"code": TARGETS, "prediction_lstm": y_int})

# -----------------------------------------------------------------------------
# 6. Construction et sauvegarde du rapport
# -----------------------------------------------------------------------------
def build_report(quartier: str, date_str: str, backend: Literal["lgbm", "lstm"]) -> pd.DataFrame:
    """Construit DataFrame rapport selon backend choisi."""
    if backend == "lgbm":
        pred_df = predict_lgbm(quartier, date_str)
    elif backend == "lstm":
        pred_df = predict_lstm(quartier, date_str)
    else:
        raise ValueError("MODELE doit être 'lgbm' ou 'lstm'.")

    real_row = df_all[(df_all["QUARTIER"] == quartier) & (df_all["DATE"] == date_str)]
    if real_row.empty:
        raise ValueError(f"Pas de valeurs réelles pour {quartier!r} au {date_str}.")
    real_counts = real_row[TARGETS].iloc[0].astype(int).values

    report = pd.DataFrame({
        "infraction": [CODE_TO_NAME[c] for c in TARGETS],
        "réel": real_counts
    })
    report = report.merge(pred_df, left_on="infraction", right_on=pred_df["code"].map(CODE_TO_NAME))
    report.drop(columns=["code"], inplace=True)

    keep = report["réel"] > 0
    for col in report.columns:
        if col.startswith("prediction_"):
            keep |= report[col] > 0
    return report.loc[keep].reset_index(drop=True)

# -----------------------------------------------------------------------------
# 7. Exécution
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"[3/3] Génération du rapport pour {QUARTIER!r} le {DATE} (backend={MODELE})…")
    report_df = build_report(QUARTIER, DATE, MODELE)

    pd.set_option("display.max_rows", None)
    print(report_df.to_string(index=False))

    out_filename = f"report_{QUARTIER.replace(' ', '_')}_{DATE}_{MODELE}.csv"
    report_df.to_csv(out_filename, index=False)
    print(f"\nRapport enregistré → {out_filename}")

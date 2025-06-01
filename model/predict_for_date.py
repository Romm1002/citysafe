#!/usr/bin/env python3
"""
Crime Prediction - LSTM Prediction Script
"""
import json
import pandas as pd
import numpy as np
from tensorflow.keras.models import load_model
from sklearn.preprocessing import LabelEncoder

# ── Chemins ──────────────────────────────────────────────────────────
MODEL_PATH   = "lstm/crime_lstm.keras"
MAPPING_JSON = "../dataset/code_mapping.json"
DATA_PATH    = "../dataset/dataset_pred_crime_quartier_date.csv"
WINDOW       = 28  # nombre de jours d'historique

# ── Chargement du mapping code → libellé ───────────────────────────────
with open(MAPPING_JSON, "r", encoding="utf-8") as f:
    code_to_name = json.load(f)

# ── Pré-chargement du DataFrame complet pour encodage ──────────────────
df_all = pd.read_csv(DATA_PATH, parse_dates=["DATE"])
quartiers = df_all["QUARTIER"].unique()
le = LabelEncoder().fit(quartiers)

TARGETS = [
    c for c in df_all.columns
    if c not in ("QUARTIER", "DATE", "NB_INFRACTION", "dow", "month", "doy_sin", "doy_cos")
]
FEATURES = ["NB_INFRACTION", "dow", "month", "doy_sin", "doy_cos"]

# ── Fonctions principales ─────────────────────────────────────────────

def predict_for_date(quartier_name: str, date_str: str) -> pd.DataFrame:
    """Retourne un DataFrame <code, prediction> pour un quartier/date donnés."""
    # Chargement du modèle
    model = load_model(MODEL_PATH, compile=False)

    # Extraction de la fenêtre d'historique
    df = df_all
    sub = (
        df[(df["QUARTIER"] == quartier_name) & (df["DATE"] < date_str)]
        .tail(WINDOW)
        .reset_index(drop=True)
    )
    if len(sub) < WINDOW:
        raise ValueError(f"Pas assez d'historique ({len(sub)}) pour {quartier_name} au {date_str}.")
    seq = sub[FEATURES].values[np.newaxis, ...]

    # Encodage du quartier
    if quartier_name not in le.classes_:
        raise ValueError(f"Quartier '{quartier_name}' inconnu du modèle.")
    q_id = np.array([int(le.transform([quartier_name])[0])], dtype="int32")

    # Prédiction et arrondi
    y_hat = model.predict({"series_in": seq, "quartier_id": q_id}, verbose=0)[0]
    y_pred_int = np.clip(np.rint(y_hat), 0, None).astype(int)

    return pd.DataFrame({"code": TARGETS, "prediction": y_pred_int})


def report_for_date(quartier_name: str, date_str: str) -> pd.DataFrame:
    """Crée un rapport <infraction, réel, prévu> pour un quartier/date donnés."""
    pred_df = predict_for_date(quartier_name, date_str)

    # Trouver la ligne réelle
    row = df_all[(df_all["QUARTIER"] == quartier_name) & (df_all["DATE"] == date_str)]
    if row.empty:
        raise ValueError(f"Pas de données réelles pour {quartier_name} au {date_str}.")
    actual = row[pred_df["code"].tolist()].iloc[0].astype(int).values

    report = pd.DataFrame({
        "infraction": pred_df["code"].map(code_to_name),
        "réel": actual,
        "prévu": pred_df["prediction"]
    })
    # Filtrer zéro
    return report.loc[(report["réel"] > 0) | (report["prévu"] > 0)].reset_index(drop=True)

# ── Exécution en ligne de commande ─────────────────────────────────────
if __name__ == "__main__":
    DATE = "2025-03-05"
    QUARTIER = "Chelsea-Hudson Yards"
    rpt = report_for_date(QUARTIER, DATE)
    pd.set_option("display.max_rows", None)
    print(rpt.to_string(index=False))
    # Optionnel : sauvegarde
    rpt.to_csv(f"report_{QUARTIER.replace(' ', '_')}_{DATE}.csv", index=False)

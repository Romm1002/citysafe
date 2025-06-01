"""
===============================================================================
Prédictions d'infractions par quartier et par date
===============================================================================
Charge un modèle LightGBM multivariable (un estimateur par type d'infraction).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import lightgbm as lgb  # uniquement pour les hints de type


# =============================================================================
# 1. Définitions préalables (classe wrapper pour le modèle)
# =============================================================================
class MultiTargetLGBM:

    def __init__(self, estimators: list[lgb.LGBMRegressor], target_names: list[str]):
        self.estimators = estimators
        self.target_names = target_names

    # -------------------------------------------------------------------------
    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Retourne un DataFrame (n_samples × n_targets) avec les prédictions.

        • Utilise best_iteration_ quand disponible (early stopping).
        """
        preds = [
            est.predict(X, num_iteration=getattr(est, "best_iteration_", None))
            for est in self.estimators
        ]
        stacked = np.column_stack(preds)
        return pd.DataFrame(stacked, columns=self.target_names, index=X.index)


# =============================================================================
# 2. Chemins et constantes
# =============================================================================
ROOT = Path(__file__).resolve().parent

DATA_PATH = ROOT / ".." / ".." / "dataset" / "dataset_pred_crime_quartier_date.csv"
MAPPING_PATH = ROOT / ".." / ".." / "dataset" / "code_mapping.json"
MODEL_PATH = ROOT / "lgbm.joblib"

FEATURES = ["QUARTIER", "NB_INFRACTION", "dow", "month", "doy_sin", "doy_cos"]


# =============================================================================
# 3. Chargement des artefacts (données + modèle + mapping)
# =============================================================================
print("[1/3] Chargement des artefacts…")

# Jeu de données complet (permet de garantir la cohérence des features)
df_all = pd.read_csv(DATA_PATH, parse_dates=["DATE"])

# Mapping <code infraction> → <libellé humain>
with open(MAPPING_PATH, encoding="utf-8") as f:
    CODE_TO_NAME: dict[str, str] = json.load(f)

# Modèle multivarié
model: MultiTargetLGBM = joblib.load(MODEL_PATH)
TARGETS = model.target_names
print(f"  ↳ modèle chargé : {len(TARGETS)} types d'infractions.")


# =============================================================================
# 4. Fonctions utilitaires
# =============================================================================
def _extract_features_row(quartier: str, date_str: str) -> pd.DataFrame:
    row = df_all[(df_all["QUARTIER"] == quartier) & (df_all["DATE"] == date_str)]
    if row.empty:
        raise ValueError(
            f"Aucune observation trouvée pour {quartier!r} à la date {date_str}."
        )
    X = row[FEATURES].copy()
    X["QUARTIER"] = X["QUARTIER"].astype("category")
    return X.reset_index(drop=True)


def predict_for(quartier: str, date_str: str) -> pd.DataFrame:
    """
    Prédit toutes les infractions pour (quartier, date).
    Retourne un DataFrame
    """
    X = _extract_features_row(quartier, date_str)
    y_hat = model.predict(X).iloc[0].values
    y_int = np.clip(np.rint(y_hat), 0, None).astype(int)
    return pd.DataFrame({"code": TARGETS, "prediction": y_int})


def build_report(quartier: str, date_str: str) -> pd.DataFrame:
    preds = predict_for(quartier, date_str)

    # Comptes réels pour comparaison
    actual = (
        df_all[(df_all["QUARTIER"] == quartier) & (df_all["DATE"] == date_str)]
        [TARGETS]
        .iloc[0]
        .astype(int)
        .values
    )

    report = pd.DataFrame(
        {
            "infraction": preds["code"].map(CODE_TO_NAME),
            "réel": actual,
            "prévu": preds["prediction"],
        }
    )
    return report.loc[(report["réel"] > 0) | (report["prévu"] > 0)].reset_index(
        drop=True
    )


# =============================================================================
# 5. Exécution
# =============================================================================
if __name__ == "__main__":
    QUARTIER = "Chelsea-Hudson Yards"
    DATE = "2025-03-05"
    
    report_df = build_report(QUARTIER, DATE)

    # Affichage console (toutes lignes)
    pd.set_option("display.max_rows", None)
    print(report_df.to_string(index=False))

    # Sauvegarde CSV
    out_file = Path(f"report_{QUARTIER.replace(' ', '_')}_{DATE}.csv")
    report_df.to_csv(out_file, index=False)
    print(f"\nRapport enregistré → {out_file.resolve().relative_to(Path.cwd())}")
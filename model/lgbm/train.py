from __future__ import annotations

import numpy as np
import pandas as pd
import joblib
import lightgbm as lgb

from pathlib import Path
from sklearn.metrics import mean_absolute_error


# =============================================================================
# 1. Configuration des chemins
# =============================================================================
ROOT = Path(__file__).resolve().parent

DATA_PATH = ROOT / ".." / ".." / "dataset" / "dataset_pred_crime_quartier_date.csv"
MODEL_DIR = ROOT
MODEL_FILE = MODEL_DIR / "lgbm.joblib"
MAE_FILE = MODEL_DIR / "mae_validation.csv"
HIST_FILE = MODEL_DIR / "history_lgb.csv"

# Crée le répertoire du modèle si nécessaire
MODEL_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# 2. Chargement et préparation des données
# =============================================================================
def load_and_prepare_data(path: Path) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """
    Charge le fichier CSV, trie par QUARTIER et DATE, et prépare X (features) et Y (cibles).
    - parse_dates=["DATE"] : convertit la colonne DATE en type datetime
    - trie chronologiquement pour chaque QUARTIER
    - détermine les colonnes cibles (toutes sauf QUARTIER, DATE, NB_INFRACTION, dow, month, doy_sin, doy_cos)
    - assemble X avec les features explicites et convertit QUARTIER en catégorie
    """
    print("[1/4] Chargement des données…")
    df = pd.read_csv(path, parse_dates=["DATE"])
    df = df.sort_values(["QUARTIER", "DATE"]).reset_index(drop=True)

    # Définition des colonnes cibles et des features
    excluded = {"QUARTIER", "DATE", "NB_INFRACTION", "dow", "month", "doy_sin", "doy_cos"}
    target_cols = [col for col in df.columns if col not in excluded]
    feature_cols = ["QUARTIER", "NB_INFRACTION", "dow", "month", "doy_sin", "doy_cos"]

    # Construction de X et Y
    X = df[feature_cols].copy()
    X["QUARTIER"] = X["QUARTIER"].astype("category")
    Y = df[target_cols].copy()

    return X, Y, target_cols


def chronological_split(
    X: pd.DataFrame, Y: pd.DataFrame, train_ratio: float = 0.90
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Effectue une séparation chronologique du jeu de données selon le ratio spécifié.
    """
    print("[2/4] Séparation chronologique…")
    cutoff = int(len(X) * train_ratio)
    X_train = X.iloc[:cutoff].reset_index(drop=True)
    X_val = X.iloc[cutoff:].reset_index(drop=True)
    y_train = Y.iloc[:cutoff].reset_index(drop=True)
    y_val = Y.iloc[cutoff:].reset_index(drop=True)
    return X_train, X_val, y_train, y_val


# =============================================================================
# 3. Paramètres LightGBM
# =============================================================================
LGB_PARAMS: dict = {
    "objective": "poisson",
    "learning_rate": 0.015,
    "n_estimators": 50_000,
    "early_stopping_rounds": 1_000,
    "num_leaves": 1_024,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": 42,
    "verbosity": -1,
    "linear_tree": True,
}


# =============================================================================
# 4. Entraînement par cible et collecte de l’historique
# =============================================================================
def train_per_target(
    X_train: pd.DataFrame,
    X_val: pd.DataFrame,
    y_train: pd.DataFrame,
    y_val: pd.DataFrame,
    target_names: list[str],
    params: dict,
) -> tuple[list[lgb.LGBMRegressor], list[float], np.ndarray, np.ndarray, np.ndarray]:
    """
    Entraîne un LGBMRegressor pour chaque cible.

    Retourne :
    - la liste des modèles entraînés
    - la liste des MAE de validation pour chaque cible
    - les sommes cumulées des métriques [train_poisson, val_poisson, train_l1, val_l1]
    - le nombre d’itérations observées par cible
    - un tableau de compteurs (nombre de cibles ayant atteint chaque itération)
    """
    print("[3/4] Entraînement par type de crime…")
    max_iters = params["n_estimators"]

    # Pour accumuler les métriques moyennes sur toutes les cibles
    sums = np.zeros((max_iters, 4), dtype=float)   # colonnes : train_p, val_p, train_l1, val_l1
    counts = np.zeros(max_iters, dtype=int)

    estimators: list[lgb.LGBMRegressor] = []
    mae_list: list[float] = []

    for target in target_names:
        # Initialisation du modèle pour cette cible
        model = lgb.LGBMRegressor(**params)
        evals_result: dict[str, dict[str, list[float]]] = {}

        # Entraînement avec évaluation sur jeux train et validation
        model.fit(
            X_train,
            y_train[target],
            eval_set=[(X_train, y_train[target]), (X_val, y_val[target])],
            eval_metric=["poisson", "l1"],
            callbacks=[
                lgb.early_stopping(params["early_stopping_rounds"]),
                lgb.record_evaluation(evals_result),
            ],
        )

        estimators.append(model)

        # Calcul du MAE de validation pour cette cible
        val_pred = model.predict(X_val, num_iteration=model.best_iteration_)
        mae_val = mean_absolute_error(y_val[target], val_pred)
        mae_list.append(mae_val)

        # Agrégation de l’historique d’apprentissage
        n_iter = len(evals_result["training"]["poisson"])
        sums[:n_iter, 0] += evals_result["training"]["poisson"]
        sums[:n_iter, 1] += evals_result["valid_1"]["poisson"]
        sums[:n_iter, 2] += evals_result["training"]["l1"]
        sums[:n_iter, 3] += evals_result["valid_1"]["l1"]
        counts[:n_iter] += 1

    return estimators, mae_list, sums, counts, max_iters


# =============================================================================
# 5. Sauvegarde des artefacts : modèle, MAE, historique
# =============================================================================
class MultiTargetLGBM:
    """
    Conteneur pour prédire plusieurs cibles simultanément avec un modèle LGBM par cible.
    """

    def __init__(self, models: list[lgb.LGBMRegressor], target_names: list[str]):
        self.models = models
        self.target_names = target_names

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Pour chaque modèle entraîné, prédit la cible correspondante.
        Retourne un DataFrame dont chaque colonne correspond à une cible.
        """
        preds = []
        for model in self.models:
            iteration = getattr(model, "best_iteration_", None)
            preds.append(model.predict(X, num_iteration=iteration))
        stacked = np.column_stack(preds)
        return pd.DataFrame(stacked, columns=self.target_names, index=X.index)


def save_model(models: list[lgb.LGBMRegressor], targets: list[str], path: Path) -> None:
    """
    Sérialise l’objet MultiTargetLGBM dans un fichier .joblib.
    """
    multi = MultiTargetLGBM(models, targets)
    joblib.dump(multi, path)
    print(f"Modèle enregistré → {path.relative_to(ROOT)}")


def save_mae_report(mae_values: list[float], targets: list[str], path: Path) -> None:
    """
    Enregistre la liste des MAE de validation pour chaque cible dans un CSV.
    """
    pd.Series(mae_values, index=targets, name="mae").to_csv(path)
    print(f"Rapport MAE enregistré → {path.relative_to(ROOT)}")


def save_history(
    sums: np.ndarray, counts: np.ndarray, max_iters: int, path: Path
) -> None:
    """
    Construit un DataFrame avec les métriques moyennes par itération
    (train_poisson, val_poisson, train_mae, val_mae) et l’enregistre en CSV.
    """
    mask = counts > 0
    history_df = pd.DataFrame({
        "iter": np.arange(max_iters)[mask],
        "train_poisson": sums[mask, 0] / counts[mask],
        "val_poisson": sums[mask, 1] / counts[mask],
        "train_mae": sums[mask, 2] / counts[mask],
        "val_mae": sums[mask, 3] / counts[mask],
    })
    history_df.to_csv(path, index=False)
    print(f"Historique d’entraînement enregistré → {path.relative_to(ROOT)}")


# =============================================================================
# 6. Pipeline principale
# =============================================================================

if __name__ == "__main__":
    # Chargement et préparation
    X, Y, targets = load_and_prepare_data(DATA_PATH)

    # Séparation chronologique
    X_train, X_val, y_train, y_val = chronological_split(X, Y)

    # Entraînement et collecte des métriques
    (
        trained_models,
        mae_values,
        metric_sums,
        metric_counts,
        max_iterations,
    ) = train_per_target(X_train, X_val, y_train, y_val, targets, LGB_PARAMS)

    # Sauvegarde des resultats
    print("[4/4] Sauvegarde des resultats…")
    save_model(trained_models, targets, MODEL_FILE)
    save_mae_report(mae_values, targets, MAE_FILE)
    save_history(metric_sums, metric_counts, max_iterations, HIST_FILE)

    print("Pipeline d’entraînement terminé.\n")

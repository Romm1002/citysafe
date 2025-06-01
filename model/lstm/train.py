"""
===============================================================================
Prédiction d'infractions par LSTM
===============================================================================
"""

from __future__ import annotations

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
from pathlib import Path
from datetime import datetime

import os.path
import numpy as np
import pandas as pd
import joblib
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from tensorflow.keras import layers, models, callbacks, optimizers, losses

# -----------------------------------------------------------------------------
# 1. Paramètres globaux
# -----------------------------------------------------------------------------
DATA_PATH = "../../dataset/dataset_pred_crime_quartier_date.csv"

MODEL_FILE = "crime_lstm.keras"
SCALER_FILE = "scaler_counts.pkl"
ENCODER_FILE = "quartiers.pkl"
HISTORY_FILE = "history.csv"

WINDOW = 28                 # 4 semaines
TEST_RATIO = 0.10
BATCH_SIZE = 128
EPOCHS = 100
SEED = 42
EARLY_STOP = 20             # patience early-stopping

np.random.seed(SEED)
tf.keras.utils.set_random_seed(SEED)
AUTOTUNE = tf.data.AUTOTUNE

# -----------------------------------------------------------------------------
# 2. Chargement & préparation des données
# -----------------------------------------------------------------------------
print("\n[1/6] Chargement et préparation des données…")

df = (
    pd.read_csv(DATA_PATH, parse_dates=["DATE"])
      .sort_values(["QUARTIER", "DATE"])
      .reset_index(drop=True)
)

EXCLUDE = {"QUARTIER", "DATE", "NB_INFRACTION", "dow", "month",
           "doy_sin", "doy_cos"}
TARGETS  = [c for c in df.columns if c not in EXCLUDE]
FEATURES = ["NB_INFRACTION", "dow", "month", "doy_sin", "doy_cos"]
df = df[["QUARTIER", "DATE", *FEATURES, *TARGETS]]

# --- Encodage Quartier ---
if os.path.isfile(ENCODER_FILE):
    le: LabelEncoder = joblib.load(ENCODER_FILE)
else:
    le = LabelEncoder()
    joblib.dump(le, ENCODER_FILE)

df["quartier_id"] = le.fit_transform(df["QUARTIER"])
N_QUARTIERS = len(le.classes_)

# --- Split chronologique ---
print("[2/6] Découpage train / test…")
cut = int(len(df) * (1 - TEST_RATIO))
train_df, test_df = df.iloc[:cut].copy(), df.iloc[cut:].copy()

# --- Mise au format float32 avant scaling ---
train_df[FEATURES] = train_df[FEATURES].astype("float32")
test_df[FEATURES]  = test_df[FEATURES].astype("float32")

# --- Scaling ---
create_scaler = not os.path.isfile(SCALER_FILE)
scaler: MinMaxScaler = (
    joblib.load(SCALER_FILE) if not create_scaler else MinMaxScaler()
)
if create_scaler:
    scaler.fit(train_df[FEATURES])
    joblib.dump(scaler, SCALER_FILE)

train_df[FEATURES] = scaler.transform(train_df[FEATURES])
test_df[FEATURES]  = scaler.transform(test_df[FEATURES])

# -----------------------------------------------------------------------------
# 3. Construction des séquences glissantes
# -----------------------------------------------------------------------------
print("[3/6] Construction des fenêtres temporelles…")
N_FEATS = len(FEATURES)


def build_sequences(source: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Retourne (X_seq, quartier_id, Y) pour un DataFrame donné."""
    seqs, q_ids, tgts = [], [], []
    for q_id in source["quartier_id"].unique():
        sub = source[source["quartier_id"] == q_id].reset_index(drop=True)
        if len(sub) <= WINDOW:
            continue  # pas assez d'historique
        feats = sub[FEATURES].values.astype("float32")
        targets = sub[TARGETS].values.astype("float32")
        for t in range(WINDOW, len(sub)):
            seqs.append(feats[t - WINDOW : t])
            q_ids.append(q_id)
            tgts.append(targets[t])
    return np.asarray(seqs), np.asarray(q_ids), np.asarray(tgts)


X_tr_seq, X_tr_q, y_tr = build_sequences(train_df)
X_te_seq, X_te_q, y_te = build_sequences(test_df)

print("  → Train:", X_tr_seq.shape, "Test:", X_te_seq.shape)

# -----------------------------------------------------------------------------
# 4. Pipelines tf.data
# -----------------------------------------------------------------------------
print("[4/6] Création des jeux tf.data…")


def make_dataset(
    seq: np.ndarray, qid: np.ndarray, tgt: np.ndarray, shuffle: bool = True
) -> tf.data.Dataset:
    ds = tf.data.Dataset.from_tensor_slices(((seq, qid), tgt))
    if shuffle:
        ds = ds.shuffle(buffer_size=min(len(seq), 10_000),
                        seed=SEED, reshuffle_each_iteration=True)
    return ds.batch(BATCH_SIZE).prefetch(AUTOTUNE)


train_ds = make_dataset(X_tr_seq, X_tr_q, y_tr, shuffle=True)
valid_ds = make_dataset(X_te_seq, X_te_q, y_te, shuffle=False)

# -----------------------------------------------------------------------------
# 5. Construction ou chargement du modèle
# -----------------------------------------------------------------------------
print("[5/6] Construction / chargement du modèle…")
NEW_MODEL = not os.path.isfile(MODEL_FILE)
N_TYPES = len(TARGETS)

if NEW_MODEL:
    # -- Branche séquencielle --------------------------------------------------
    seq_in = layers.Input(shape=(WINDOW, N_FEATS), name="series_in")
    x = layers.Masking(mask_value=0.0)(seq_in)
    x = layers.Bidirectional(
        layers.LSTM(128, return_sequences=True, dropout=0.2)
    )(x)
    x = layers.MultiHeadAttention(num_heads=4, key_dim=32, dropout=0.1)(x, x)
    x = layers.LayerNormalization()(x)
    x = layers.GlobalAveragePooling1D()(x)

    # -- Branche embedding quartier -------------------------------------------
    q_in = layers.Input(shape=(), dtype="int32", name="quartier_id")
    q_emb = layers.Embedding(N_QUARTIERS, 24)(q_in)
    q_emb = layers.Flatten()(q_emb)

    # -- Tête dense ------------------------------------------------------------
    concat = layers.Concatenate()([x, q_emb])
    concat = layers.BatchNormalization()(concat)
    concat = layers.Dense(128, activation="relu")(concat)
    concat = layers.Dropout(0.3)(concat)
    concat = layers.Dense(64, activation="relu")(concat)

    out = layers.Dense(N_TYPES, activation="softplus", name="crime_counts")(concat)

    model = models.Model(inputs=[seq_in, q_in], outputs=out, name="CrimeLSTM")
else:
    model = tf.keras.models.load_model(MODEL_FILE, compile=False)

# -----------------------------------------------------------------------------
# 6. Compilation et entraînement
# -----------------------------------------------------------------------------
print("[6/6] Compilation et entraînement…")

lr_schedule = optimizers.schedules.PolynomialDecay(
    initial_learning_rate=1e-3,
    decay_steps=10_000,
    end_learning_rate=1e-6,
)

optimizer = optimizers.Nadam(learning_rate=lr_schedule, clipnorm=1.0)

model.compile(
    optimizer=optimizer,
    loss=losses.Poisson(),
    metrics=[tf.keras.metrics.MeanAbsoluteError(name="MAE")],
)

cb_list = [
    callbacks.ModelCheckpoint(
        MODEL_FILE, monitor="val_loss", mode="min",
        save_best_only=True, verbose=1
    ),
    callbacks.EarlyStopping(
        monitor="val_loss", patience=EARLY_STOP,
        min_delta=1e-4, restore_best_weights=True, verbose=1
    ),
    callbacks.CSVLogger(HISTORY_FILE, separator=";", append=False),
]

model.summary()

history = model.fit(
    train_ds,
    validation_data=valid_ds,
    epochs=EPOCHS,
    callbacks=cb_list,
    verbose=2,
)

print("\nEntraînement terminé - meilleur modèle sauvegardé →", MODEL_FILE)

#!/usr/bin/env python3
"""
Crime Prediction – LSTM
"""

# -------------------------- IMPORTS ---------------------------
import os
from datetime import datetime

import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import MinMaxScaler, LabelEncoder

import tensorflow as tf
from tensorflow.keras import layers, models, callbacks, optimizers, losses

# ---------------------- GLOBAL PARAMETERS ---------------------
DATA_PATH    = "../../dataset/dataset_pred_crime_quartier_date.csv"
MODEL_PATH   = "crime_lstm.keras"
SCALER_PATH  = "scaler_counts.pkl"
ENCODER_PATH = "quartiers.pkl"
WINDOW       = 28           # 4 semaines d'historique
TEST_SIZE    = 0.10
BATCH_SIZE   = 128
EPOCHS       = 100
SEED         = 42
EARLY_STOP_PATIENCE = 20
LR_DECAY_START = 10

np.random.seed(SEED)
tf.keras.utils.set_random_seed(SEED)
AUTOTUNE = tf.data.AUTOTUNE

# ------------------------ DATA LOADING ------------------------
print("\n[1/6] Loading & preprocessing …")

df = pd.read_csv(DATA_PATH, parse_dates=["DATE"])
df = df.sort_values(["QUARTIER", "DATE"]).reset_index(drop=True)

TARGETS  = [c for c in df.columns if c not in ("QUARTIER", "DATE", "NB_INFRACTION", "dow", "month", "doy_sin", "doy_cos")]
FEATURES = ["NB_INFRACTION", "dow", "month", "doy_sin", "doy_cos"]
ALL_USED = ["QUARTIER", "DATE"] + FEATURES + TARGETS
df = df[ALL_USED].copy()

# Quartier encoding ---------------------------------------------------------
if os.path.exists(ENCODER_PATH):
    le: LabelEncoder = joblib.load(ENCODER_PATH)
else:
    le = LabelEncoder()
    joblib.dump(le, ENCODER_PATH)

df["quartier_id"] = le.fit_transform(df["QUARTIER"])
N_QUARTIERS = len(le.classes_)

# Chronological split -------------------------------------------------------
print("[2/6] Train / test chronological split …")
cut = int(len(df) * (1 - TEST_SIZE))
train_df = df.iloc[:cut].copy()
test_df  = df.iloc[cut:].copy()

# Ensure float dtype BEFORE scaling (avoid FutureWarning) -------------------
train_df.loc[:, FEATURES] = train_df[FEATURES].astype("float32")
test_df.loc[:, FEATURES]  = test_df[FEATURES].astype("float32")

# Feature scaling -----------------------------------------------------------
create_scaler = not os.path.exists(SCALER_PATH)
scaler: MinMaxScaler = joblib.load(SCALER_PATH) if not create_scaler else MinMaxScaler()
if create_scaler:
    scaler.fit(train_df[FEATURES])
    joblib.dump(scaler, SCALER_PATH)

train_df.loc[:, FEATURES] = scaler.transform(train_df[FEATURES])
test_df.loc[:, FEATURES]  = scaler.transform(test_df[FEATURES])

# ---------------------- SEQUENCE GENERATION ------------------
print("[3/6] Building sliding windows …")

N_FEATS = len(FEATURES)

def build_sequences(source: pd.DataFrame):
    seqs, q_ids, tgts = [], [], []
    for q in source["quartier_id"].unique():
        sub = source[source["quartier_id"] == q].reset_index(drop=True)
        if len(sub) <= WINDOW:  # pas assez de pas de temps
            continue
        feats = sub[FEATURES].values.astype("float32")
        targets = sub[TARGETS].values.astype("float32")
        # Boucle python (simple, évite off‑by‑one)
        for i in range(WINDOW, len(sub)):
            seqs.append(feats[i - WINDOW : i])   # WINDOW pas de temps
            q_ids.append(q)
            tgts.append(targets[i])             # cible = pas courant
    return np.asarray(seqs), np.asarray(q_ids), np.asarray(tgts)

X_tr_seq, X_tr_q, y_tr = build_sequences(train_df)
X_te_seq, X_te_q, y_te = build_sequences(test_df)
print("  Train sequences:", X_tr_seq.shape)
print("  Test  sequences:", X_te_seq.shape)

# ---------------------- tf.data PIPELINE --------------------
print("[4/6] Creating tf.data pipelines …")

def make_dataset(seq, qid, tgt, shuffle=True):
    ds = tf.data.Dataset.from_tensor_slices(((seq, qid), tgt))
    if shuffle:
        ds = ds.shuffle(buffer_size=min(len(seq), 10_000), seed=SEED, reshuffle_each_iteration=True)
    return ds.batch(BATCH_SIZE).prefetch(AUTOTUNE)

train_ds = make_dataset(X_tr_seq, X_tr_q, y_tr, shuffle=True)
valid_ds = make_dataset(X_te_seq, X_te_q, y_te, shuffle=False)

# ------------------------ MODEL BUILD -----------------------
print("[5/6] Building / loading model …")
NEW_MODEL = not os.path.exists(MODEL_PATH)
N_TYPES   = len(TARGETS)

if NEW_MODEL:
    # Time‑series branch ---------------------------------------------------
    seq_in = layers.Input((WINDOW, N_FEATS), name="series_in")
    x = layers.Masking(mask_value=0.0)(seq_in)
    x = layers.Bidirectional(layers.LSTM(128, return_sequences=True, dropout=0.2))(x)
    x = layers.MultiHeadAttention(num_heads=4, key_dim=32, dropout=0.1)(x, x)
    x = layers.LayerNormalization()(x)
    x = layers.GlobalAveragePooling1D()(x)

    # Quartier embedding branch ------------------------------------------
    q_in = layers.Input((), dtype="int32", name="quartier_id")
    q_emb = layers.Embedding(N_QUARTIERS, 24)(q_in)
    q_emb = layers.Flatten()(q_emb)

    # Dense heads ---------------------------------------------------------
    concat = layers.Concatenate()([x, q_emb])
    concat = layers.BatchNormalization()(concat)
    concat = layers.Dense(128, activation="relu")(concat)
    concat = layers.Dropout(0.3)(concat)
    concat = layers.Dense(64, activation="relu")(concat)

    out = layers.Dense(N_TYPES, activation="softplus", name="crime_counts")(concat)

    model = models.Model(inputs=[seq_in, q_in], outputs=out, name="CrimePredictor")
else:
    model = tf.keras.models.load_model(MODEL_PATH, compile=False)

# ----------------------- COMPILE & TRAIN --------------------
print("[6/6] Compile & train …")

# lr_schedule = optimizers.schedules.CosineDecayRestarts(
#     initial_learning_rate=1e-3,
#     first_decay_steps=LR_DECAY_START,
#     t_mul=2.0,
#     m_mul=0.75,
#     alpha=1e-4,
# )

lr_schedule = tf.keras.optimizers.schedules.PolynomialDecay(
    initial_learning_rate = 1e-3,
    decay_steps           = 10000,
    end_learning_rate     = 1e-6,
    power                 = 1.0
)

# lr_schedule = optimizers.schedules.ExponentialDecay(
#     initial_learning_rate=1e-2,
#     decay_steps=250,
#     decay_rate=0.96,
#     staircase=True
# )

optimizer = optimizers.Nadam(learning_rate=lr_schedule, clipnorm=1.0)
model.compile(
    optimizer=optimizer,
    loss=losses.Poisson(),
    metrics=[tf.keras.metrics.MeanAbsoluteError(name="MAE")],
)

callbacks_list = [
    callbacks.ModelCheckpoint(MODEL_PATH, monitor="val_loss", mode="min", save_best_only=True, verbose=1),
    callbacks.EarlyStopping(monitor="val_loss", min_delta=1e-4, patience=EARLY_STOP_PATIENCE, restore_best_weights=True, verbose=1),
    callbacks.CSVLogger(filename="history.csv", separator=";", append=False),
    # lr_schedule
]

model.summary()

history = model.fit(
    train_ds,
    validation_data=valid_ds,
    epochs=EPOCHS,
    callbacks=callbacks_list,
    verbose=2
)

print("Training complete – best model stored at", MODEL_PATH)

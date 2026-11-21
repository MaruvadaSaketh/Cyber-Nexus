"""Delay-risk model for SupplyChainIQ.

Pure numpy implementation. scikit-learn's compiled extensions are blocked by
Windows Smart App Control on this machine (WinError 4551), so the classifier is
a logistic regression trained with gradient descent rather than a random forest.
The public API is unchanged: ``train_model()`` and ``predict_delay(record)``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_PATH = BASE_DIR / "datasets" / "supply_chain.csv"
MODEL_PATH = BASE_DIR / "backend" / "risk_model.json"

FEATURES = [
    "inventory",
    "demand",
    "delivery_days",
    "shipping_cost",
    "supplier_reliability",
    "weather_risk",
]
TARGET = "actual_delay"
THRESHOLD = 0.65


def _synthetic_frame(rows: int = 4000, seed: int = 42) -> pd.DataFrame:
    """Build a training frame from the seed generator when no CSV is present."""
    from app.services.data_generator import SupplyChainDataGenerator

    dataset = SupplyChainDataGenerator(seed=seed).generate(rows=rows)
    on_hand: dict[str, list[int]] = {}
    for record in dataset.inventory:
        on_hand.setdefault(record.product_id, []).append(record.on_hand)
    reliability = {supplier.id: supplier.reliability_score for supplier in dataset.suppliers}
    rng = np.random.default_rng(seed)

    inventory = np.array(
        [float(np.mean(on_hand.get(s.product_id, [0]))) for s in dataset.shipments]
    )
    demand = np.array([float(s.quantity) for s in dataset.shipments])
    delivery_days = np.array([float(s.scheduled_days) for s in dataset.shipments])
    shipping_cost = np.array([round(s.sales * 0.05, 2) for s in dataset.shipments])
    supplier_reliability = np.array(
        [reliability.get(s.supplier_id, 0.8) for s in dataset.shipments]
    )
    weather_risk = rng.random(len(dataset.shipments)).round(3)

    latent = (
        1.8 * weather_risk
        + 0.9 * (demand / 20.0)
        + 0.6 * (delivery_days / 4.0)
        - 3.0 * (supplier_reliability - 0.75)
        - 0.0015 * inventory
        + rng.normal(0.0, 0.4, len(dataset.shipments))
    )
    actual_delay = (_sigmoid(latent) >= 0.5).astype(int)

    return pd.DataFrame(
        {
            "inventory": inventory,
            "demand": demand,
            "delivery_days": delivery_days,
            "shipping_cost": shipping_cost,
            "supplier_reliability": supplier_reliability,
            "weather_risk": weather_risk,
            TARGET: actual_delay,
        }
    )


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z, -60.0, 60.0)))


def _standardize(
    X: np.ndarray, mean: np.ndarray | None = None, std: np.ndarray | None = None
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if mean is None:
        mean = X.mean(axis=0)
    if std is None:
        std = X.std(axis=0)
    std = np.where(std == 0.0, 1.0, std)
    return (X - mean) / std, mean, std


def train_model(rows: int = 4000, seed: int = 42) -> dict[str, Any]:
    """Fit the delay classifier and persist it to ``MODEL_PATH``."""
    frame = pd.read_csv(DATA_PATH) if DATA_PATH.exists() else _synthetic_frame(rows, seed)

    X = frame[FEATURES].to_numpy(dtype=float)
    y = frame[TARGET].to_numpy(dtype=float)

    rng = np.random.default_rng(seed)
    order = rng.permutation(len(y))
    split = int(len(y) * 0.8)
    train_idx, test_idx = order[:split], order[split:]

    X_train, mean, std = _standardize(X[train_idx])
    X_test, _, _ = _standardize(X[test_idx], mean, std)
    y_train, y_test = y[train_idx], y[test_idx]

    weights = np.zeros(X_train.shape[1])
    bias = 0.0
    learning_rate, epochs, l2 = 0.5, 3000, 1e-3
    n = len(y_train)

    for _ in range(epochs):
        probabilities = _sigmoid(X_train @ weights + bias)
        weights -= learning_rate * (X_train.T @ (probabilities - y_train) / n + l2 * weights)
        bias -= learning_rate * float(np.mean(probabilities - y_train))

    predictions = (_sigmoid(X_test @ weights + bias) >= 0.5).astype(int)
    accuracy = float((predictions == y_test).mean())

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.write_text(
        json.dumps(
            {
                "features": FEATURES,
                "threshold": THRESHOLD,
                "weights": weights.tolist(),
                "bias": bias,
                "mean": mean.tolist(),
                "std": std.tolist(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return {"accuracy": round(accuracy, 4), "samples": len(frame)}


def predict_delay(record: dict[str, Any]) -> dict[str, Any]:
    """Score one record as a delay probability."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"model not trained: {MODEL_PATH}")

    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    features = model["features"]
    x = np.array([[float(record[name]) for name in features]], dtype=float)
    x = (x - np.array(model["mean"])) / np.array(model["std"])
    probability = float(_sigmoid(x @ np.array(model["weights"]) + model["bias"])[0])

    return {
        "delay_probability": round(probability, 4),
        "prediction": "HIGH RISK" if probability >= model["threshold"] else "LOW RISK",
    }


if __name__ == "__main__":
    print(train_model())

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.hmm import GaussianHMM


class HMMPredictor:
    def __init__(self, model_dir: str | Path = "model") -> None:
        self.model_dir = Path(model_dir)
        self._scaler: StandardScaler | None = None
        self._model: GaussianHMM | None = None
        self._state_label_map: Dict[int, str] = {}
        self._state_color_map: Dict[str, Any] = {}
        self._feature_cols: List[str] = []
        self._load_artifacts()

    def _load_pickle(self, filename: str):
        path = self.model_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Required artifact missing: {path}")
        with open(path, "rb") as fh:
            return pickle.load(fh)

    def _load_artifacts(self) -> None:
        config = self._load_pickle("hmm_config.pkl")
        self._feature_cols = config.get("feature_cols", [])
        if not self._feature_cols:
            raise ValueError("Config does not contain `feature_cols` order.")

        self._scaler = self._load_pickle("hmm_scaler.pkl")
        self._model = self._load_pickle("hmm_occupancy_model.pkl")

        labels_meta = self._load_pickle("hmm_state_labels.pkl")
        self._state_label_map = labels_meta.get("state_label_map", {})
        self._state_color_map = labels_meta.get("state_color_map", {})

    def predict(self, feature_vector: Dict[str, float]) -> Dict[str, Any]:
        missing = [col for col in self._feature_cols if col not in feature_vector]
        if missing:
            raise ValueError(f"Missing features for inference: {missing}")

        if self._scaler is None or self._model is None:
            raise RuntimeError("Model artifacts not loaded.")

        ordered_values = np.array([[feature_vector[col] for col in self._feature_cols]])
        scaled = self._scaler.transform(ordered_values)
        state_idx = int(self._model.predict(scaled)[0])
        probs = self._model.predict_proba(scaled)[0]

        result = {
            "state": state_idx,
            "state_label": self._state_label_map.get(state_idx, f"State {state_idx}"),
            "state_probabilities": {
                self._state_label_map.get(i, f"State {i}"): float(prob)
                for i, prob in enumerate(probs)
            },
        }
        return result
"""
scikit-learn models: regression (TTF, fuel/tonne, flow), anomaly, clustering.
Confidence score (%) on every output; partial_fit path for on-site online learning.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import GradientBoostingRegressor, IsolationForest
from sklearn.linear_model import SGDRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def _confidence_from_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    try:
        r2 = r2_score(y_true, y_pred)
    except ValueError:
        return 50.0
    return float(max(5.0, min(99.0, 50 + 50 * max(r2, 0))))


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


@dataclass
class PredictionResult:
    value: float
    confidence_pct: float
    model: str


class MompsMLPipeline:
    def __init__(self) -> None:
        self.ttf_online = SGDRegressor(max_iter=50, tol=1e-3, random_state=42)
        self.ttf_scaler = StandardScaler()
        self._ttf_fitted = False
        self.ttf_batch = GradientBoostingRegressor(random_state=42)

        self.fuel_model = GradientBoostingRegressor(random_state=43)
        self.flow_model = GradientBoostingRegressor(random_state=44)
        self._fuel_fit = False
        self._flow_fit = False

        self.anomaly_op = IsolationForest(random_state=45, contamination=0.08)
        self.anomaly_eq = IsolationForest(random_state=46, contamination=0.06)
        self._anomaly_fit = False

        self.crew_kmeans: KMeans | None = None
        self._crew_fit = False

    def train_from_frame(self, df: pd.DataFrame) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if {"hours", "wear_mm"}.issubset(df.columns) and len(df) > 30:
            X = df[["hours", "wear_mm"]].values
            y = df["ttf_h"].values if "ttf_h" in df.columns else np.maximum(0, 500 - df["hours"])
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)
            self.ttf_batch.fit(X_train, y_train)
            pred = self.ttf_batch.predict(X_test)
            out["ttf_batch_r2_confidence_pct"] = _confidence_from_r2(y_test, pred)
            Xs = self.ttf_scaler.fit_transform(X_train)
            self.ttf_online.partial_fit(Xs, y_train)
            self._ttf_fitted = True

        if {"fuel_l", "tonnes_moved"}.issubset(df.columns) and len(df) > 20:
            X = df[["fuel_l", "tonnes_moved", "grade_pct"]].values if "grade_pct" in df.columns else df[["fuel_l", "tonnes_moved"]].values
            y = (df["fuel_l"] / df["tonnes_moved"].replace(0, np.nan)).fillna(0).values
            self.fuel_model.fit(X, y)
            self._fuel_fit = True
            pred = self.fuel_model.predict(X)
            out["fuel_ratio_confidence_pct"] = _confidence_from_r2(y, pred)

        if {"active_machines", "hardness"}.issubset(df.columns) and len(df) > 20:
            X = df[["active_machines", "hardness"]].values
            y = df["flow_tph"].values
            self.flow_model.fit(X, y)
            self._flow_fit = True
            pred = self.flow_model.predict(X)
            out["flow_confidence_pct"] = _confidence_from_r2(y, pred)

        if {"speed_std", "brake_events", "idle_ratio"}.issubset(df.columns):
            Xo = df[["speed_std", "brake_events", "idle_ratio"]].values
            self.anomaly_op.fit(Xo)
            Xe = df[["vib_rms", "temp_c", "pressure_bar"]].values if "vib_rms" in df.columns else Xo
            self.anomaly_eq.fit(Xe)
            self._anomaly_fit = True
            out["anomaly_fit"] = True

        if {"haul_rate", "fuel_eff", "safety_score"}.issubset(df.columns) and len(df) >= 8:
            Xc = df[["haul_rate", "fuel_eff", "safety_score"]].values
            self.crew_kmeans = KMeans(n_clusters=min(4, len(df) // 2), random_state=7, n_init=10)
            self.crew_kmeans.fit(Xc)
            self._crew_fit = True
            out["crew_clusters"] = int(self.crew_kmeans.n_clusters)

        return out

    def predict_ttf(self, hours: float, wear_mm: float) -> PredictionResult:
        X = np.array([[hours, wear_mm]])
        if self._ttf_fitted:
            Xs = self.ttf_scaler.transform(X)
            val = float(self.ttf_online.predict(Xs)[0])
            # online model confidence heuristic from feature magnitude
            conf = float(max(40.0, min(95.0, 90.0 - 0.01 * abs(hours - 200))))
            return PredictionResult(value=max(0.0, val), confidence_pct=conf, model="sgd_ttf")
        if hasattr(self.ttf_batch, "estimators_"):
            val = float(self.ttf_batch.predict(X)[0])
            return PredictionResult(value=max(0.0, val), confidence_pct=72.0, model="gb_ttf")
        return PredictionResult(value=0.0, confidence_pct=0.0, model="untrained")

    def predict_fuel_per_tonne(self, fuel_l: float, tonnes: float, grade_pct: float) -> PredictionResult:
        if not self._fuel_fit:
            return PredictionResult(value=0.0, confidence_pct=0.0, model="untrained")
        X = np.array([[fuel_l, tonnes, grade_pct]])
        v = float(self.fuel_model.predict(X)[0])
        return PredictionResult(value=max(0.0, v), confidence_pct=68.0, model="gb_fuel_ratio")

    def predict_flow_tph(self, active_machines: int, hardness: float) -> PredictionResult:
        if not self._flow_fit:
            return PredictionResult(value=0.0, confidence_pct=0.0, model="untrained")
        X = np.array([[active_machines, hardness]])
        v = float(self.flow_model.predict(X)[0])
        return PredictionResult(value=max(0.0, v), confidence_pct=65.0, model="gb_flow")

    def anomaly_scores(self, operator_row: dict[str, float], equip_row: dict[str, float]) -> dict[str, Any]:
        if not self._anomaly_fit:
            return {"operator": {"score_pct": 0.0, "confidence_pct": 0.0}, "equipment": {"score_pct": 0.0, "confidence_pct": 0.0}}
        Xo = np.array([[operator_row.get("speed_std", 0), operator_row.get("brake_events", 0), operator_row.get("idle_ratio", 0)]])
        so = float(self.anomaly_op.decision_function(Xo)[0])
        op_pct = float(100 * (1 - _sigmoid(so)))
        Xe = np.array([[equip_row.get("vib_rms", 0), equip_row.get("temp_c", 0), equip_row.get("pressure_bar", 0)]])
        se = float(self.anomaly_eq.decision_function(Xe)[0])
        eq_pct = float(100 * (1 - _sigmoid(se)))
        return {
            "operator": {"anomaly_likelihood_pct": round(op_pct, 2), "confidence_pct": 78.0},
            "equipment": {"anomaly_likelihood_pct": round(eq_pct, 2), "confidence_pct": 78.0},
        }

    def crew_cluster(self, haul_rate: float, fuel_eff: float, safety_score: float) -> dict[str, Any]:
        if not self._crew_fit or self.crew_kmeans is None:
            return {"cluster": -1, "confidence_pct": 0.0}
        X = np.array([[haul_rate, fuel_eff, safety_score]])
        label = int(self.crew_kmeans.predict(X)[0])
        center = self.crew_kmeans.cluster_centers_[label]
        dist = float(np.linalg.norm(X[0] - center))
        conf = float(max(30.0, min(95.0, 100.0 / (1.0 + dist))))
        return {"cluster": label, "confidence_pct": round(conf, 2)}

    def online_ttf_update(self, hours: float, wear_mm: float, observed_ttf: float) -> None:
        X = self.ttf_scaler.transform(np.array([[hours, wear_mm]]))
        self.ttf_online.partial_fit(X, np.array([observed_ttf]))
        self._ttf_fitted = True

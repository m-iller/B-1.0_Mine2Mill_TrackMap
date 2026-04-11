from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import require_user
from app.synthetic.generator import SyntheticMiningDataGenerator
from app.state import get_ml

router = APIRouter(prefix="/ml", tags=["ml"])


@router.post("/train/synthetic")
def train_synthetic(user: str = Depends(require_user)):
    gen = SyntheticMiningDataGenerator()
    df = gen.training_frame(500)
    pipe = get_ml()
    metrics = pipe.train_from_frame(df)
    return {"api_version": "v1", "user": user, "metrics": metrics}


@router.post("/predict/ttf")
def predict_ttf(body: dict, user: str = Depends(require_user)):
    pipe = get_ml()
    r = pipe.predict_ttf(float(body.get("hours", 0)), float(body.get("wear_mm", 0)))
    return {"api_version": "v1", "user": user, "value": r.value, "confidence_pct": r.confidence_pct, "model": r.model}


@router.post("/predict/fuel_ratio")
def predict_fuel(body: dict, user: str = Depends(require_user)):
    pipe = get_ml()
    r = pipe.predict_fuel_per_tonne(
        float(body.get("fuel_l", 0)), float(body.get("tonnes", 1)), float(body.get("grade_pct", 0))
    )
    return {"api_version": "v1", "user": user, "value": r.value, "confidence_pct": r.confidence_pct, "model": r.model}


@router.post("/anomaly")
def anomaly(body: dict, user: str = Depends(require_user)):
    pipe = get_ml()
    out = pipe.anomaly_scores(body.get("operator", {}), body.get("equipment", {}))
    return {"api_version": "v1", "user": user, **out}


@router.post("/crew")
def crew(body: dict, user: str = Depends(require_user)):
    pipe = get_ml()
    out = pipe.crew_cluster(
        float(body.get("haul_rate", 0)),
        float(body.get("fuel_eff", 0)),
        float(body.get("safety_score", 0)),
    )
    return {"api_version": "v1", "user": user, **out}

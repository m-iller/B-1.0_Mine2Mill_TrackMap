"""Process-wide singletons (prototype); replace with DI container in production."""

from __future__ import annotations

from app.ml.pipeline import MompsMLPipeline
from app.services.influx_writer import TelemetryInfluxWriter
from app.services.simulation_engine import SimulationEngine

simulation_engine: SimulationEngine | None = None
ml_pipeline: MompsMLPipeline | None = None
influx_writer: TelemetryInfluxWriter | None = None


def get_simulation() -> SimulationEngine:
    global simulation_engine
    if simulation_engine is None:
        simulation_engine = SimulationEngine()
    return simulation_engine


def get_ml() -> MompsMLPipeline:
    global ml_pipeline
    if ml_pipeline is None:
        ml_pipeline = MompsMLPipeline()
    return ml_pipeline


def get_influx() -> TelemetryInfluxWriter:
    global influx_writer
    if influx_writer is None:
        influx_writer = TelemetryInfluxWriter()
    return influx_writer

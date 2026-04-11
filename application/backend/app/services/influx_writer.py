from __future__ import annotations

from datetime import datetime
from typing import Any

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from app.config import get_settings


class TelemetryInfluxWriter:
    def __init__(self) -> None:
        s = get_settings()
        self._org = s.influx_org
        self._bucket = s.influx_bucket
        self._client: InfluxDBClient | None = None
        self._write_api = None
        if s.influx_token:
            try:
                self._client = InfluxDBClient(url=s.influx_url, token=s.influx_token, org=s.influx_org)
                self._write_api = self._client.write_api(write_options=SYNCHRONOUS)
            except Exception:
                self._client = None
                self._write_api = None

    @property
    def enabled(self) -> bool:
        return self._write_api is not None

    def write_point(self, norm: dict[str, Any]) -> None:
        if not self._write_api:
            return
        ts = norm.get("timestamp")
        if isinstance(ts, str):
            t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        else:
            t = datetime.utcnow()
        p = (
            Point("machine_telemetry")
            .tag("machine_id", norm["machine_id"])
            .field("speed_m_s", float(norm["speed_m_s"]))
            .field("fuel_l", float(norm["fuel_l"]))
            .field("payload_t", float(norm["payload_t"]))
            .field("wear_index", float(norm["wear_index"]))
            .field("x", float(norm["position"]["x"]))
            .field("y", float(norm["position"]["y"]))
            .field("z", float(norm["position"]["z"]))
            .time(t)
        )
        self._write_api.write(bucket=self._bucket, org=self._org, record=p)

    def close(self) -> None:
        if self._client:
            self._client.close()

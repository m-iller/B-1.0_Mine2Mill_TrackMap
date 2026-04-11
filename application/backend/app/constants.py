"""
Central constants aligned with common industrial / ISO-style units.
Values are defaults; runtime config overrides via DB catalog + Settings.
"""

# ISO 80000-3: length SI base meter; speeds in m/s internally where noted
UNIT_LENGTH_M = "m"
UNIT_SPEED_MS = "m/s"
UNIT_MASS_KG = "kg"
UNIT_MASS_TONNE = "t"
UNIT_VOLUME_L = "L"
UNIT_TIME_S = "s"

# Alert taxonomy (site policy maps to GOST-style severity bands externally)
ALERT_WARNING = "warning"
ALERT_CRITICAL = "critical"
ALERT_EMERGENCY = "emergency"

# Machine operational states
STATUS_IDLE = "idle"
STATUS_MOVING = "moving"
STATUS_LOADING = "loading"
STATUS_FAILURE = "failure"

# Broker topic names (versioned)
TOPIC_TELEMETRY_RAW = "momps.v1.telemetry.raw"
TOPIC_TELEMETRY_NORMALIZED = "momps.v1.telemetry.normalized"
TOPIC_SIM_STATE = "momps.v1.simulation.state"
TOPIC_SAFETY_ALERT = "momps.v1.safety.alert"
TOPIC_PLAN_UPDATE = "momps.v1.planning.update"
TOPIC_ROUTE_UPDATE = "momps.v1.routing.update"

# Extension hook event types (future: AV, 3D GIS, DEM, CV)
HOOK_AUTONOMY_TELEMETRY = "extension.v1.autonomy.telemetry"
HOOK_GIS3D_TERRAIN = "extension.v1.gis3d.terrain_patch"
HOOK_DEM_WEAR_SAMPLE = "extension.v1.dem.wear_sample"
HOOK_CV_FRAGMENTATION = "extension.v1.cv.fragmentation"

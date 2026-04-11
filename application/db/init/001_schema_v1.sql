-- MOMPS PostgreSQL + PostGIS schema v1
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
INSERT INTO schema_migrations (version) VALUES ('001_initial_v1');

CREATE TABLE machine_type_catalog (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    spec JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE machines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    machine_type_id UUID NOT NULL REFERENCES machine_type_catalog(id),
    external_id TEXT UNIQUE,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'idle',
    meta JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_machines_type ON machines(machine_type_id);

CREATE TABLE operators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    display_name TEXT NOT NULL,
    crew_id UUID,
    meta JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE production_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_date DATE NOT NULL,
    shift_code TEXT NOT NULL,
    target_tonnes NUMERIC(14, 2) NOT NULL,
    meta JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (plan_date, shift_code)
);

CREATE TABLE plan_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES production_plans(id) ON DELETE CASCADE,
    machine_id UUID REFERENCES machines(id),
    task_type TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    scheduled_start TIMESTAMPTZ,
    scheduled_end TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_plan_tasks_plan ON plan_tasks(plan_id);

CREATE TABLE hazard_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    zone_type TEXT NOT NULL,
    geom GEOMETRY(Polygon, 4326) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    meta JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_hazard_zones_geom ON hazard_zones USING GIST (geom);

CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    severity TEXT NOT NULL,
    category TEXT NOT NULL,
    machine_id UUID REFERENCES machines(id),
    operator_id UUID REFERENCES operators(id),
    detail JSONB NOT NULL DEFAULT '{}',
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);
CREATE INDEX idx_incidents_time ON incidents(occurred_at DESC);

CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    actor TEXT,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    payload JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_audit_time ON audit_logs(created_at DESC);

-- Seed machine types (config-driven in app; DB holds canonical list)
INSERT INTO machine_type_catalog (code, display_name, spec) VALUES
('haul_truck', 'Haul Truck', '{"max_speed_kmh": 55, "payload_tonnes": 240}'),
('excavator', 'Hydraulic Excavator', '{"max_reach_m": 18}'),
('dozer', 'Track Dozer', '{"blade_m3": 12}');

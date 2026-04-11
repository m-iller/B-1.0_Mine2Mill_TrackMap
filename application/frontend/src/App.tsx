import { useCallback, useEffect, useMemo, useState } from "react";

type Machine = {
  id: string;
  type: string;
  position: { x: number; y: number; z: number };
  speed_m_s: number;
  status: string;
  predicted_path: { x: number; y: number; z: number }[];
};

type SimPayload = {
  tick: number;
  machines: Machine[];
  terrain?: { width: number; height: number; cell_meters?: number };
};

const API = "";

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem("momps_token") || "");
  const [user, setUser] = useState("");
  const [pass, setPass] = useState("demo");
  const [sim, setSim] = useState<SimPayload | null>(null);
  const [alerts, setAlerts] = useState<{ level: string; code: string; detail: object }[]>([]);
  const [err, setErr] = useState("");

  const authHeaders = useMemo(
    () => ({
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    }),
    [token]
  );

  const login = async () => {
    setErr("");
    const r = await fetch(`${API}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: user || "operator", password: pass }),
    });
    if (!r.ok) {
      setErr("login failed");
      return;
    }
    const j = await r.json();
    setToken(j.access_token);
    localStorage.setItem("momps_token", j.access_token);
  };

  const loadState = useCallback(async () => {
    if (!token) return;
    const r = await fetch(`${API}/api/v1/simulation/state`, { headers: authHeaders });
    if (r.ok) setSim(await r.json());
  }, [token, authHeaders]);

  const loadProximity = useCallback(async () => {
    if (!token) return;
    const r = await fetch(`${API}/api/v1/safety/proximity`, { method: "POST", headers: authHeaders });
    if (r.ok) {
      const j = await r.json();
      setAlerts(j.alerts || []);
    }
  }, [token, authHeaders]);

  useEffect(() => {
    loadState();
  }, [loadState]);

  useEffect(() => {
    if (!token) return;
    const wsProto = window.location.protocol === "https:" ? "wss" : "ws";
    const host = window.location.hostname;
    const url = import.meta.env.DEV
      ? `ws://127.0.0.1:8000/ws/v1/stream`
      : `${wsProto}://${host}:${window.location.port}/ws/v1/stream`;
    const ws = new WebSocket(url);
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.type === "simulation") setSim(msg.payload);
      } catch {
        /* ignore */
      }
    };
    const ping = window.setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send("ping");
    }, 20000);
    return () => {
      window.clearInterval(ping);
      ws.close();
    };
  }, [token]);

  const tw = sim?.terrain?.width || 80;
  const th = sim?.terrain?.height || 80;

  return (
    <div className="layout">
      <div className="panel">
        <h2>MOMPS</h2>
        {!token ? (
          <>
            <input placeholder="username" value={user} onChange={(e) => setUser(e.target.value)} />
            <input type="password" placeholder="password" value={pass} onChange={(e) => setPass(e.target.value)} />
            <button type="button" onClick={login}>
              Login (default operator/demo)
            </button>
            {err && <p className="alert-c">{err}</p>}
          </>
        ) : (
          <>
            <div className="kpi">
              <span>tick {sim?.tick ?? "—"}</span>
              <span>machines {sim?.machines?.length ?? 0}</span>
              <button type="button" onClick={loadState}>
                Refresh
              </button>
              <button type="button" onClick={loadProximity}>
                Scan proximity
              </button>
            </div>
            <div className="map">
              {sim?.machines?.map((m, i) => (
                <div
                  key={m.id}
                  className="dot"
                  title={`${m.type} ${m.status}`}
                  style={{
                    left: `${(m.position.x / tw) * 100}%`,
                    top: `${(m.position.y / th) * 100}%`,
                    background: i === 0 ? "#58a6ff" : i === 1 ? "#3fb950" : "#d2a8ff",
                  }}
                />
              ))}
              {sim?.machines?.flatMap((m) =>
                (m.predicted_path || []).map((p, idx) => (
                  <div
                    key={`${m.id}-p-${idx}`}
                    className="dot"
                    style={{
                      left: `${(p.x / tw) * 100}%`,
                      top: `${(p.y / th) * 100}%`,
                      width: 4,
                      height: 4,
                      opacity: 0.35,
                      background: "#8b949e",
                    }}
                  />
                ))
              )}
            </div>
            <div className="legend">2D grid map · blue/green/purple = machines · gray = route samples</div>
          </>
        )}
      </div>
      <div className="side">
        <h3>Alerts</h3>
        {alerts.length === 0 && <p className="legend">Run proximity scan or wait for telemetry rules.</p>}
        {alerts.map((a, i) => (
          <div key={i} className={a.level === "emergency" ? "alert-e" : a.level === "critical" ? "alert-c" : "alert-w"}>
            <strong>{a.code}</strong> ({a.level})
            <pre style={{ fontSize: "0.7rem", overflow: "auto" }}>{JSON.stringify(a.detail, null, 2)}</pre>
          </div>
        ))}
      </div>
    </div>
  );
}

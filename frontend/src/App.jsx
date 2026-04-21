import { useState, useRef } from "react";
import * as XLSX from "xlsx";

// ─────────────────────────────────────────
//  CONFIG
// ─────────────────────────────────────────
const API_URL = "http://localhost:8000";

// ─────────────────────────────────────────
//  SAMPLE DATA
// ─────────────────────────────────────────
const SAMPLE = {
  cities: [
    { name: "Mumbai", demand: 110 }, { name: "Delhi", demand: 125 },
    { name: "Bangalore", demand: 105 }, { name: "Pune", demand: 85 },
    { name: "Hyderabad", demand: 95 }, { name: "Chennai", demand: 90 },
    { name: "Kolkata", demand: 110 }, { name: "Ahmedabad", demand: 80 },
    { name: "Jaipur", demand: 75 }, { name: "Lucknow", demand: 85 },
    { name: "Indore", demand: 70 }, { name: "Patna", demand: 75 },
    { name: "Surat", demand: 65 }, { name: "BhopalCity", demand: 60 },
    { name: "NagpurCity", demand: 65 }, { name: "RaipurCity", demand: 60 },
    { name: "Coimbatore", demand: 70 }, { name: "Varanasi", demand: 75 },
    { name: "Vadodara", demand: 60 }, { name: "Ranchi", demand: 65 },
  ],
  warehouses: [
    { name: "W1", capacity: 310 }, { name: "W2", capacity: 305 },
    { name: "W3", capacity: 285 }, { name: "W4", capacity: 265 },
    { name: "W5", capacity: 290 }, { name: "W6", capacity: 300 },
  ],
  roads: [
    { from: "Mumbai", to: "Nagpur", distance: 4 }, { from: "Pune", to: "Nagpur", distance: 3 },
    { from: "Surat", to: "Nagpur", distance: 5 }, { from: "Vadodara", to: "Nagpur", distance: 6 },
    { from: "Ahmedabad", to: "Nagpur", distance: 5 }, { from: "NagpurCity", to: "Nagpur", distance: 2 },
    { from: "Delhi", to: "Bhopal", distance: 5 }, { from: "Jaipur", to: "Bhopal", distance: 3 },
    { from: "Lucknow", to: "Bhopal", distance: 4 }, { from: "Varanasi", to: "Bhopal", distance: 6 },
    { from: "Patna", to: "Bhopal", distance: 7 }, { from: "Indore", to: "Bhopal", distance: 2 },
    { from: "BhopalCity", to: "Bhopal", distance: 1 }, { from: "Bangalore", to: "Hyderabad", distance: 3 },
    { from: "Chennai", to: "Hyderabad", distance: 2 }, { from: "Coimbatore", to: "Hyderabad", distance: 4 },
    { from: "Kolkata", to: "Raipur", distance: 4 }, { from: "Ranchi", to: "Raipur", distance: 3 },
    { from: "RaipurCity", to: "Raipur", distance: 2 }, { from: "Nagpur", to: "Bhopal", distance: 5 },
    { from: "Nagpur", to: "Hyderabad", distance: 7 }, { from: "Bhopal", to: "Hyderabad", distance: 6 },
    { from: "Raipur", to: "Nagpur", distance: 6 }, { from: "Raipur", to: "Bhopal", distance: 5 },
    { from: "Hyderabad", to: "Raipur", distance: 9 }, { from: "Nagpur", to: "W1", distance: 3 },
    { from: "Nagpur", to: "W2", distance: 6 }, { from: "Nagpur", to: "W5", distance: 8 },
    { from: "Bhopal", to: "W2", distance: 2 }, { from: "Bhopal", to: "W3", distance: 4 },
    { from: "Bhopal", to: "W4", distance: 7 }, { from: "Hyderabad", to: "W3", distance: 3 },
    { from: "Hyderabad", to: "W5", distance: 3 }, { from: "Hyderabad", to: "W6", distance: 8 },
    { from: "Raipur", to: "W4", distance: 4 }, { from: "Raipur", to: "W6", distance: 3 },
    { from: "Raipur", to: "W2", distance: 7 }, { from: "W1", to: "W2", distance: 5 },
    { from: "W3", to: "W5", distance: 4 }, { from: "W4", to: "W6", distance: 6 },
  ],
};

let idCounter = 1000;
const nid = () => ++idCounter;
const toRows = (arr) => arr.map((item) => ({ id: nid(), ...item }));

// ─────────────────────────────────────────
//  DESIGN TOKENS
// ─────────────────────────────────────────
const C = {
  bg: "#060C1A", card: "#0C1526", border: "#1A2840", hover: "#0F1E38",
  amber: "#F59E0B", amberDim: "#92600A", amberGlow: "rgba(245,158,11,0.15)",
  teal: "#10D9A8", tealDim: "rgba(16,217,168,0.15)", tealBright: "#0FFFC4",
  red: "#FF3D5A", redDim: "rgba(255,61,90,0.12)", redBright: "#FF6680",
  text: "#E8EDF5", muted: "#5C7099", dim: "#8A9DC0",
  surface: "#111D33", surface2: "#162035",
};
const F = {
  head: "'Syne', sans-serif",
  mono: "'IBM Plex Mono', monospace",
  body: "'DM Sans', sans-serif",
};

// ─────────────────────────────────────────
//  SHARED COMPONENTS
// ─────────────────────────────────────────
function Badge({ children, color = C.amber }) {
  return (
    <span style={{ background: `${color}22`, color, border: `1px solid ${color}44`, borderRadius: 4, padding: "2px 8px", fontSize: 11, fontFamily: F.mono, fontWeight: 600, letterSpacing: 1 }}>
      {children}
    </span>
  );
}

function StatCard({ label, value, sub, color = C.amber }) {
  return (
    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: "16px 20px", flex: 1, minWidth: 120 }}>
      <div style={{ color: C.muted, fontSize: 11, fontFamily: F.mono, letterSpacing: 1, textTransform: "uppercase", marginBottom: 8 }}>{label}</div>
      <div style={{ color, fontSize: 28, fontFamily: F.head, fontWeight: 700, lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ color: C.muted, fontSize: 12, marginTop: 6 }}>{sub}</div>}
    </div>
  );
}

function SectionHeader({ icon, title, badge }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
      <span style={{ fontSize: 18 }}>{icon}</span>
      <h3 style={{ margin: 0, color: C.text, fontFamily: F.head, fontSize: 15, fontWeight: 700 }}>{title}</h3>
      {badge && <Badge>{badge}</Badge>}
    </div>
  );
}

// AllocationTable — uses API costMatrix where null = unreachable
function AllocationTable({ alloc, costMatrix }) {
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: F.mono, fontSize: 12 }}>
        <thead>
          <tr>
            {["City", "Warehouse", "Units", "Cost/u", "Total"].map(h => (
              <th key={h} style={{ textAlign: h === "City" || h === "Warehouse" ? "left" : "right", color: C.muted, padding: "6px 12px", borderBottom: `1px solid ${C.border}` }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Object.entries(alloc).map(([city, whMap]) =>
            Object.entries(whMap).map(([wh, units], i) => {
              const cost = costMatrix[city]?.[wh];
              const validCost = cost != null && isFinite(cost);
              const total = validCost ? units * cost : "∞";
              return (
                <tr key={`${city}-${wh}`} style={{ background: i % 2 === 0 ? "transparent" : `${C.surface}55` }}>
                  <td style={{ padding: "6px 12px", color: C.text }}>{city}</td>
                  <td style={{ padding: "6px 12px" }}><Badge color={C.teal}>{wh}</Badge></td>
                  <td style={{ padding: "6px 12px", color: C.amber, textAlign: "right" }}>{units}</td>
                  <td style={{ padding: "6px 12px", color: C.dim, textAlign: "right" }}>{validCost ? cost : "∞"}</td>
                  <td style={{ padding: "6px 12px", color: C.text, textAlign: "right", fontWeight: 600 }}>{total}</td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}

// UtilizationBars — uses API field names: utilizationPct, overCapacity
function UtilizationBars({ wUtil }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {Object.entries(wUtil).map(([wh, d]) => {
        const pct = Math.min(d.utilizationPct, 100);
        const color = d.overCapacity ? C.red : d.utilizationPct > 80 ? C.amber : C.teal;
        return (
          <div key={wh}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <span style={{ fontFamily: F.mono, fontSize: 12, color: C.text, fontWeight: 600 }}>{wh}</span>
              <span style={{ fontFamily: F.mono, fontSize: 11, color }}>
                {d.used} / {d.capacity} ({d.utilizationPct}%) {d.overCapacity ? "⚠ OVER" : ""}
              </span>
            </div>
            <div style={{ height: 6, background: C.border, borderRadius: 99, overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${pct}%`, background: color, borderRadius: 99, transition: "width 0.5s ease" }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

// CostMatrixTable — null = unreachable (API sends null for inf)
function CostMatrixTable({ cities, warehouses, matrix }) {
  if (!matrix || !cities || !warehouses) return null;
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ borderCollapse: "collapse", fontFamily: F.mono, fontSize: 11 }}>
        <thead>
          <tr>
            <th style={{ padding: "6px 10px", color: C.muted, textAlign: "left", borderBottom: `1px solid ${C.border}`, whiteSpace: "nowrap" }}>City / WH</th>
            {warehouses.map(w => (
              <th key={w.name} style={{ padding: "6px 10px", color: C.amber, textAlign: "center", borderBottom: `1px solid ${C.border}`, whiteSpace: "nowrap" }}>{w.name}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {cities.map((city, ri) => {
            const row = matrix[city.name] || {};
            const values = warehouses.map(w => row[w.name]).filter(v => v != null && isFinite(v));
            const minVal = values.length ? Math.min(...values) : null;
            return (
              <tr key={city.name} style={{ background: ri % 2 === 0 ? "transparent" : `${C.surface}55` }}>
                <td style={{ padding: "5px 10px", color: C.text, whiteSpace: "nowrap", fontWeight: 600 }}>{city.name}</td>
                {warehouses.map(w => {
                  const v = row[w.name];
                  const valid = v != null && isFinite(v);
                  const isMin = valid && v === minVal;
                  return (
                    <td key={w.name} style={{ padding: "5px 10px", textAlign: "center", color: !valid ? C.red : isMin ? C.tealBright : C.dim, fontWeight: isMin ? 700 : 400 }}>
                      {valid ? v : "∞"}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ─────────────────────────────────────────
//  TSP ROUTES TAB
//  Adapted from File 2's TspRoutesTab.
//  API shape: tspRoutes[wh] = { cost, route, numStops }
//  "stops" derived as route.slice(1, -1)
// ─────────────────────────────────────────
function TspRoutesTab({ tspRoutes, tspTotalCost, warehouseNames, optimizedAllocation, costMatrix }) {
  const [expandedWh, setExpandedWh] = useState(null);

  const toggleWh = (wh) => setExpandedWh(prev => prev === wh ? null : wh);

  // Derive stops array from route for each warehouse
  const getTsp = (wh) => {
    const raw = tspRoutes[wh];
    if (!raw) return { cost: 0, route: [wh], stops: [] };
    const stops = raw.numStops > 0 ? raw.route.slice(1, -1) : [];
    return { cost: raw.cost, route: raw.route, stops };
  };

  const activeWarehouses = warehouseNames.filter(wh => getTsp(wh).stops.length > 0);
  const totalStops = warehouseNames.reduce((s, wh) => s + getTsp(wh).stops.length, 0);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

      {/* Summary metrics */}
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        <StatCard label="Total delivery distance" value={tspTotalCost} color={C.amber} sub="Sum of all round-trips" />
        <StatCard label="Active warehouses" value={activeWarehouses.length} color={C.teal} sub={`of ${warehouseNames.length} total`} />
        <StatCard label="Total city stops" value={totalStops} color={C.dim} sub="Splits counted per warehouse" />
      </div>

      {/* Algorithm info */}
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: "14px 20px" }}>
        <div style={{ display: "flex", gap: 20, flexWrap: "wrap", fontFamily: F.mono, fontSize: 11 }}>
          <span style={{ color: C.muted }}>Algorithm <span style={{ color: C.amber }}>Held-Karp Bitmask DP</span></span>
          <span style={{ color: C.muted }}>Time complexity <span style={{ color: C.text }}>O(n² × 2ⁿ)</span></span>
          <span style={{ color: C.muted }}>Route type <span style={{ color: C.teal }}>Round-trip (depot → cities → depot)</span></span>
          <span style={{ color: C.muted }}>Splits <span style={{ color: C.amber }}>honoured — city appears in every WH with units</span></span>
        </div>
      </div>

      {/* Per-warehouse expandable route cards */}
      {warehouseNames.map(whName => {
        const tsp = getTsp(whName);
        const hasRoute = tsp.stops.length > 0;
        const isExpanded = expandedWh === whName;

        return (
          <div key={whName} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, overflow: "hidden" }}>

            {/* Card header */}
            <div
              onClick={() => hasRoute && toggleWh(whName)}
              style={{ display: "flex", alignItems: "center", gap: 14, padding: "16px 20px", cursor: hasRoute ? "pointer" : "default", background: isExpanded ? C.hover : "transparent", transition: "background .15s" }}
            >
              <div style={{ width: 36, height: 36, borderRadius: 8, background: hasRoute ? `${C.amber}22` : C.border, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: F.mono, fontSize: 12, fontWeight: 700, color: hasRoute ? C.amber : C.muted, flexShrink: 0 }}>
                {whName}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontFamily: F.head, fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 3 }}>
                  {hasRoute ? `${tsp.stops.length} stop${tsp.stops.length !== 1 ? "s" : ""} · distance ${tsp.cost}` : "No deliveries assigned"}
                </div>
                {hasRoute && (
                  <div style={{ fontFamily: F.mono, fontSize: 11, color: C.muted, wordBreak: "break-all" }}>{tsp.route.join(" → ")}</div>
                )}
              </div>
              {hasRoute && (
                <span style={{ color: C.muted, fontSize: 16, transition: "transform .2s", transform: isExpanded ? "rotate(90deg)" : "rotate(0deg)" }}>▶</span>
              )}
            </div>

            {/* Expanded stop breakdown */}
            {isExpanded && hasRoute && (
              <div style={{ padding: "0 20px 20px", borderTop: `1px solid ${C.border}` }}>
                <div style={{ paddingTop: 14, marginBottom: 10, fontFamily: F.mono, fontSize: 11, color: C.muted }}>Delivery breakdown</div>
                <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: F.mono, fontSize: 12 }}>
                  <thead>
                    <tr>
                      {["#", "City", "Units", "Cost/unit", "Leg cost", "Split?"].map(h => (
                        <th key={h} style={{ textAlign: h === "#" || h === "City" ? "left" : "right", color: C.muted, padding: "5px 10px", borderBottom: `1px solid ${C.border}`, fontSize: 11 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {tsp.stops.map((city, idx) => {
                      const units = optimizedAllocation[city]?.[whName] ?? 0;
                      const costPerU = costMatrix[city]?.[whName];
                      const validCost = costPerU != null && isFinite(costPerU);
                      const legCost = validCost ? units * costPerU : "∞";
                      const allWhs = Object.keys(optimizedAllocation[city] || {});
                      const isSplit = allWhs.length > 1;
                      const otherWhs = allWhs.filter(w => w !== whName);
                      return (
                        <tr key={city} style={{ background: idx % 2 === 0 ? "transparent" : `${C.surface}55` }}>
                          <td style={{ padding: "6px 10px", color: C.muted }}>{idx + 1}</td>
                          <td style={{ padding: "6px 10px", color: C.text, fontWeight: 600 }}>{city}</td>
                          <td style={{ padding: "6px 10px", color: C.amber, textAlign: "right" }}>{units}</td>
                          <td style={{ padding: "6px 10px", color: C.dim, textAlign: "right" }}>{validCost ? costPerU : "∞"}</td>
                          <td style={{ padding: "6px 10px", color: C.text, textAlign: "right", fontWeight: 600 }}>{legCost}</td>
                          <td style={{ padding: "6px 10px", textAlign: "right" }}>
                            {isSplit
                              ? <span style={{ color: C.amber, fontSize: 10 }}>also {otherWhs.join(", ")}</span>
                              : <span style={{ color: C.muted, fontSize: 10 }}>—</span>}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                  <tfoot>
                    <tr>
                      <td colSpan={4} style={{ padding: "8px 10px", color: C.muted, fontFamily: F.mono, fontSize: 11, borderTop: `1px solid ${C.border}` }}>Round-trip total</td>
                      <td style={{ padding: "8px 10px", color: C.amber, textAlign: "right", fontWeight: 700, borderTop: `1px solid ${C.border}` }}>{tsp.cost}</td>
                      <td style={{ borderTop: `1px solid ${C.border}` }} />
                    </tr>
                  </tfoot>
                </table>
              </div>
            )}
          </div>
        );
      })}

      {/* Full summary table */}
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
        <SectionHeader icon="📋" title="Summary table" />
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: F.mono, fontSize: 12 }}>
            <thead>
              <tr>
                {["Warehouse", "Stops", "Route", "Distance"].map(h => (
                  <th key={h} style={{ textAlign: h === "Route" ? "left" : "center", color: C.muted, padding: "6px 12px", borderBottom: `1px solid ${C.border}` }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {warehouseNames.map((wh, i) => {
                const t = getTsp(wh);
                return (
                  <tr key={wh} style={{ background: i % 2 === 0 ? "transparent" : `${C.surface}55` }}>
                    <td style={{ padding: "7px 12px", textAlign: "center" }}><Badge color={C.teal}>{wh}</Badge></td>
                    <td style={{ padding: "7px 12px", color: C.amber, textAlign: "center" }}>{t.stops.length}</td>
                    <td style={{ padding: "7px 12px", color: C.dim, fontSize: 11, wordBreak: "break-all" }}>{t.route.join(" → ")}</td>
                    <td style={{ padding: "7px 12px", color: C.text, fontWeight: 600, textAlign: "center" }}>{t.cost}</td>
                  </tr>
                );
              })}
            </tbody>
            <tfoot>
              <tr>
                <td colSpan={3} style={{ padding: "8px 12px", color: C.muted, borderTop: `1px solid ${C.border}` }}>Total delivery distance</td>
                <td style={{ padding: "8px 12px", color: C.amber, fontWeight: 700, textAlign: "center", borderTop: `1px solid ${C.border}` }}>{tspTotalCost}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────
//  MAIN APP
// ─────────────────────────────────────────
export default function App() {
  const [cities,     setCities]     = useState(toRows(SAMPLE.cities));
  const [warehouses, setWarehouses] = useState(toRows(SAMPLE.warehouses));
  const [roads,      setRoads]      = useState(toRows(SAMPLE.roads));
  const [inputTab,   setInputTab]   = useState("cities");
  const [results,    setResults]    = useState(null);
  const [running,    setRunning]    = useState(false);
  const [resTab,     setResTab]     = useState("overview");
  const [uploadMsg,  setUploadMsg]  = useState("");
  const [drag,       setDrag]       = useState(false);
  const [apiError,   setApiError]   = useState("");
  const fileRef = useRef();

  // ── Input handlers ──
  const updateCity = (id, f, v) => setCities(p => p.map(c => c.id === id ? { ...c, [f]: v } : c));
  const addCity    = () => setCities(p => [...p, { id: nid(), name: "", demand: 0 }]);
  const removeCity = id => setCities(p => p.filter(c => c.id !== id));

  const updateWH = (id, f, v) => setWarehouses(p => p.map(w => w.id === id ? { ...w, [f]: v } : w));
  const addWH    = () => setWarehouses(p => [...p, { id: nid(), name: "", capacity: 0 }]);
  const removeWH = id => setWarehouses(p => p.filter(w => w.id !== id));

  const updateRoad = (id, f, v) => setRoads(p => p.map(r => r.id === id ? { ...r, [f]: v } : r));
  const addRoad    = () => setRoads(p => [...p, { id: nid(), from: "", to: "", distance: 0 }]);
  const removeRoad = id => setRoads(p => p.filter(r => r.id !== id));

  // ── Call Python API ──
  const handleRun = async () => {
    setRunning(true);
    setResults(null);
    setApiError("");

    const payload = {
      cities:     cities.filter(c => c.name.trim()).map(c => ({ name: c.name.trim(), demand: Number(c.demand) })),
      warehouses: warehouses.filter(w => w.name.trim()).map(w => ({ name: w.name.trim(), capacity: Number(w.capacity) })),
      roads:      roads.filter(r => r.from && r.to).map(r => ({ from: r.from.trim(), to: r.to.trim(), distance: Number(r.distance) })),
    };

    try {
      const res = await fetch(`${API_URL}/optimize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Server returned ${res.status}: ${text}`);
      }

      const data = await res.json();
      if (data.error) {
        setApiError(data.error);
      } else {
        setResults(data);
        setResTab("overview");
      }
    } catch (err) {
      setApiError(
        err.message.includes("fetch")
          ? "Cannot reach the Python API. Make sure you ran: uvicorn api:app --reload"
          : err.message
      );
    } finally {
      setRunning(false);
    }
  };

  // ── File upload ──
  const parseFile = async (file) => {
    if (!file) return;
    const ext = file.name.split(".").pop().toLowerCase();
    if (ext === "json") {
      try {
        const d = JSON.parse(await file.text());
        if (d.cities)     setCities(d.cities.map(c         => ({ id: nid(), name: c.name, demand: Number(c.demand) })));
        if (d.warehouses) setWarehouses(d.warehouses.map(w => ({ id: nid(), name: w.name, capacity: Number(w.capacity) })));
        if (d.roads)      setRoads(d.roads.map(r            => ({ id: nid(), from: r.from, to: r.to, distance: Number(r.distance) })));
        setUploadMsg(`✓ JSON loaded — ${d.cities?.length || 0} cities, ${d.warehouses?.length || 0} warehouses, ${d.roads?.length || 0} roads`);
      } catch { setUploadMsg("✗ Invalid JSON format"); }
    } else if (["xlsx", "xls", "ods"].includes(ext)) {
      const wb = XLSX.read(await file.arrayBuffer());
      const sheet = (name) => {
        const ws = wb.Sheets[name] || wb.Sheets[wb.SheetNames.find(n => n.toLowerCase() === name.toLowerCase())];
        return ws ? XLSX.utils.sheet_to_json(ws) : [];
      };
      const cd = sheet("Cities"), wd = sheet("Warehouses"), rd = sheet("Roads");
      if (cd.length) setCities(cd.map(r         => ({ id: nid(), name: r.name || r.Name || "", demand: Number(r.demand || r.Demand || 0) })));
      if (wd.length) setWarehouses(wd.map(r      => ({ id: nid(), name: r.name || r.Name || "", capacity: Number(r.capacity || r.Capacity || 0) })));
      if (rd.length) setRoads(rd.map(r           => ({ id: nid(), from: r.from || r.From || "", to: r.to || r.To || "", distance: Number(r.distance || r.Distance || 0) })));
      setUploadMsg(`✓ Excel loaded — ${cd.length} cities, ${wd.length} warehouses, ${rd.length} roads`);
    } else {
      setUploadMsg("✗ Unsupported format. Use .json, .xlsx, or .xls");
    }
  };

  const downloadTemplate = () => {
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet([{ name: "CityA", demand: 100 }]), "Cities");
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet([{ name: "W1", capacity: 300 }]), "Warehouses");
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet([{ from: "CityA", to: "W1", distance: 5 }]), "Roads");
    XLSX.writeFile(wb, "inventory_template.xlsx");
  };

  const exportResults = () => {
    if (!results) return;
    const blob = new Blob([JSON.stringify(results, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "optimization_results.json";
    a.click();
  };

  // Warehouse names derived from results for TSP tab
  const warehouseNames = results
    ? Object.keys(results.tspRoutes || {})
    : [];

  // Style helpers
  const inputTabStyle = t => ({
    padding: "8px 16px", fontSize: 12, fontFamily: F.mono, fontWeight: 600,
    cursor: "pointer", border: "none", borderRadius: 6,
    background: inputTab === t ? C.amber : "transparent",
    color: inputTab === t ? "#000" : C.muted,
    transition: "all 0.2s",
  });

  const resTabStyle = t => ({
    padding: "7px 14px", fontSize: 12, fontFamily: F.mono, cursor: "pointer",
    border: `1px solid ${resTab === t ? C.amber : C.border}`, borderRadius: 20,
    background: resTab === t ? C.amberGlow : "transparent",
    color: resTab === t ? C.amber : C.muted,
    transition: "all 0.15s",
  });

  const numInput = (value, onChange) => (
    <input type="number" value={value} onChange={e => onChange(e.target.value)}
      style={{ width: "100%", background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", color: C.text, fontFamily: F.mono, fontSize: 12, outline: "none", boxSizing: "border-box" }} />
  );
  const textInput = (value, onChange, placeholder = "") => (
    <input type="text" value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
      style={{ width: "100%", background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 10px", color: C.text, fontFamily: F.mono, fontSize: 12, outline: "none", boxSizing: "border-box" }} />
  );

  const resTabs = [
    ["overview",    "📊 Overview"],
    ["cost-matrix", "🗺 Cost Matrix"],
    ["allocation",  "📦 Allocation"],
    ["utilization", "🏭 Utilization"],
    ["tsp-routes",  "🚚 TSP Routes"],
  ];

  return (
    <div style={{ minHeight: "100vh", background: C.bg, color: C.text, fontFamily: F.body }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&family=DM+Sans:wght@400;500;600&display=swap');
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: ${C.card}; }
        ::-webkit-scrollbar-thumb { background: ${C.border}; border-radius: 3px; }
        input:focus { border-color: ${C.amber} !important; box-shadow: 0 0 0 2px ${C.amberGlow} !important; }
        input[type=number]::-webkit-inner-spin-button { opacity: 0.4; }
        .tab-pill:hover  { color: ${C.text} !important; background: ${C.hover} !important; }
        .rm-btn:hover    { color: ${C.red}  !important; background: ${C.redDim} !important; }
        .add-btn:hover   { background: ${C.hover} !important; border-color: ${C.amber}88 !important; }
        .run-btn:hover:not(:disabled) { box-shadow: 0 0 30px ${C.amberGlow}, 0 4px 20px rgba(0,0,0,0.4) !important; transform: translateY(-1px) !important; }
        .res-tab:hover   { color: ${C.text} !important; }
        @keyframes spin  { to { transform: rotate(360deg); } }
      `}</style>

      {/* ── HEADER ── */}
      <div style={{ background: `linear-gradient(180deg,#0A1428 0%,${C.bg} 100%)`, borderBottom: `1px solid ${C.border}`, padding: "0 24px" }}>
        <div style={{ maxWidth: 1600, margin: "0 auto", display: "flex", alignItems: "center", justifyContent: "space-between", height: 64 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{ width: 36, height: 36, background: C.amber, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>📦</div>
            <div>
              <div style={{ fontFamily: F.head, fontSize: 16, fontWeight: 800, color: C.text, letterSpacing: -0.5 }}>Inventory Placement Optimizer</div>
              <div style={{ fontFamily: F.mono, fontSize: 10, color: C.muted, letterSpacing: 1 }}>PYTHON BACKEND · FASTAPI · DIJKSTRA · GREEDY · KNAPSACK · TABU SEARCH · TSP HELD-KARP</div>
            </div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            {results && (
              <button onClick={exportResults} style={{ background: "transparent", border: `1px solid ${C.border}`, borderRadius: 8, padding: "8px 16px", color: C.dim, fontFamily: F.mono, fontSize: 11, cursor: "pointer", letterSpacing: 1 }}>↓ Export Results</button>
            )}
            <button onClick={downloadTemplate} style={{ background: "transparent", border: `1px solid ${C.border}`, borderRadius: 8, padding: "8px 16px", color: C.dim, fontFamily: F.mono, fontSize: 11, cursor: "pointer", letterSpacing: 1 }}>↓ Excel Template</button>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 1600, margin: "0 auto", display: "flex", minHeight: "calc(100vh - 64px)" }}>

        {/* ── LEFT: INPUT PANEL ── */}
        <div style={{ width: 420, minWidth: 380, borderRight: `1px solid ${C.border}`, display: "flex", flexDirection: "column" }}>

          {/* Upload zone */}
          <div style={{ padding: "16px 20px", borderBottom: `1px solid ${C.border}` }}>
            <div style={{ fontSize: 11, fontFamily: F.mono, color: C.muted, letterSpacing: 1, marginBottom: 10, textTransform: "uppercase" }}>Data Import</div>
            <div
              onDrop={e => { e.preventDefault(); setDrag(false); parseFile(e.dataTransfer.files[0]); }}
              onDragOver={e => { e.preventDefault(); setDrag(true); }}
              onDragLeave={() => setDrag(false)}
              onClick={() => fileRef.current.click()}
              style={{ border: `2px dashed ${drag ? C.amber : C.border}`, borderRadius: 10, padding: "14px 16px", cursor: "pointer", background: drag ? C.amberGlow : C.card, textAlign: "center", transition: "all 0.2s" }}>
              <input ref={fileRef} type="file" accept=".json,.xlsx,.xls,.ods" style={{ display: "none" }} onChange={e => parseFile(e.target.files[0])} />
              <div style={{ fontSize: 22, marginBottom: 4 }}>📂</div>
              <div style={{ fontFamily: F.mono, fontSize: 11, color: C.dim }}>Drop file or click to upload</div>
              <div style={{ fontFamily: F.mono, fontSize: 10, color: C.muted, marginTop: 2 }}>.json · .xlsx · .xls · .ods</div>
            </div>
            {uploadMsg && <div style={{ marginTop: 8, fontFamily: F.mono, fontSize: 11, color: uploadMsg.startsWith("✓") ? C.teal : C.red }}>{uploadMsg}</div>}
          </div>

          {/* Input tabs */}
          <div style={{ padding: "12px 20px 0", borderBottom: `1px solid ${C.border}` }}>
            <div style={{ display: "flex", gap: 4 }}>
              {[["cities", `Cities (${cities.length})`], ["warehouses", `Warehouses (${warehouses.length})`], ["roads", `Roads (${roads.length})`]].map(([t, label]) => (
                <button key={t} className="tab-pill" onClick={() => setInputTab(t)} style={inputTabStyle(t)}>{label}</button>
              ))}
            </div>
          </div>

          {/* Editable tables */}
          <div style={{ flex: 1, overflowY: "auto", padding: "16px 20px" }}>
            {inputTab === "cities" && (
              <>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead><tr>
                    <th style={{ textAlign: "left", color: C.muted, fontFamily: F.mono, fontSize: 10, padding: "0 0 8px", letterSpacing: 1 }}>CITY NAME</th>
                    <th style={{ textAlign: "left", color: C.muted, fontFamily: F.mono, fontSize: 10, padding: "0 0 8px 8px", letterSpacing: 1, width: 80 }}>DEMAND</th>
                    <th style={{ width: 28 }} />
                  </tr></thead>
                  <tbody>
                    {cities.map(c => (
                      <tr key={c.id}>
                        <td style={{ paddingBottom: 6, paddingRight: 6 }}>{textInput(c.name, v => updateCity(c.id, "name", v), "City name")}</td>
                        <td style={{ paddingBottom: 6, paddingRight: 6 }}>{numInput(c.demand, v => updateCity(c.id, "demand", v))}</td>
                        <td style={{ paddingBottom: 6 }}><button className="rm-btn" onClick={() => removeCity(c.id)} style={{ background: "transparent", border: "none", color: C.muted, cursor: "pointer", fontSize: 14, padding: "4px 6px", borderRadius: 4 }}>✕</button></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <button className="add-btn" onClick={addCity} style={{ width: "100%", padding: 8, background: "transparent", border: `1px dashed ${C.border}`, borderRadius: 8, color: C.muted, cursor: "pointer", fontFamily: F.mono, fontSize: 11, marginTop: 4 }}>+ Add City</button>
              </>
            )}

            {inputTab === "warehouses" && (
              <>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead><tr>
                    <th style={{ textAlign: "left", color: C.muted, fontFamily: F.mono, fontSize: 10, padding: "0 0 8px", letterSpacing: 1 }}>WAREHOUSE</th>
                    <th style={{ textAlign: "left", color: C.muted, fontFamily: F.mono, fontSize: 10, padding: "0 0 8px 8px", letterSpacing: 1, width: 90 }}>CAPACITY</th>
                    <th style={{ width: 28 }} />
                  </tr></thead>
                  <tbody>
                    {warehouses.map(w => (
                      <tr key={w.id}>
                        <td style={{ paddingBottom: 6, paddingRight: 6 }}>{textInput(w.name, v => updateWH(w.id, "name", v), "Warehouse ID")}</td>
                        <td style={{ paddingBottom: 6, paddingRight: 6 }}>{numInput(w.capacity, v => updateWH(w.id, "capacity", v))}</td>
                        <td style={{ paddingBottom: 6 }}><button className="rm-btn" onClick={() => removeWH(w.id)} style={{ background: "transparent", border: "none", color: C.muted, cursor: "pointer", fontSize: 14, padding: "4px 6px", borderRadius: 4 }}>✕</button></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <button className="add-btn" onClick={addWH} style={{ width: "100%", padding: 8, background: "transparent", border: `1px dashed ${C.border}`, borderRadius: 8, color: C.muted, cursor: "pointer", fontFamily: F.mono, fontSize: 11, marginTop: 4 }}>+ Add Warehouse</button>
              </>
            )}

            {inputTab === "roads" && (
              <>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead><tr>
                    <th style={{ textAlign: "left", color: C.muted, fontFamily: F.mono, fontSize: 10, padding: "0 0 8px", letterSpacing: 1 }}>FROM</th>
                    <th style={{ textAlign: "left", color: C.muted, fontFamily: F.mono, fontSize: 10, padding: "0 0 8px 6px", letterSpacing: 1 }}>TO</th>
                    <th style={{ textAlign: "left", color: C.muted, fontFamily: F.mono, fontSize: 10, padding: "0 0 8px 6px", letterSpacing: 1, width: 60 }}>DIST</th>
                    <th style={{ width: 28 }} />
                  </tr></thead>
                  <tbody>
                    {roads.map(r => (
                      <tr key={r.id}>
                        <td style={{ paddingBottom: 5, paddingRight: 5 }}>{textInput(r.from, v => updateRoad(r.id, "from", v), "Node A")}</td>
                        <td style={{ paddingBottom: 5, paddingRight: 5 }}>{textInput(r.to, v => updateRoad(r.id, "to", v), "Node B")}</td>
                        <td style={{ paddingBottom: 5, paddingRight: 5 }}>{numInput(r.distance, v => updateRoad(r.id, "distance", v))}</td>
                        <td style={{ paddingBottom: 5 }}><button className="rm-btn" onClick={() => removeRoad(r.id)} style={{ background: "transparent", border: "none", color: C.muted, cursor: "pointer", fontSize: 14, padding: "4px 6px", borderRadius: 4 }}>✕</button></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <button className="add-btn" onClick={addRoad} style={{ width: "100%", padding: 8, background: "transparent", border: `1px dashed ${C.border}`, borderRadius: 8, color: C.muted, cursor: "pointer", fontFamily: F.mono, fontSize: 11, marginTop: 4 }}>+ Add Road</button>
                <div style={{ marginTop: 10, padding: "8px 10px", background: C.surface, borderRadius: 8, fontFamily: F.mono, fontSize: 10, color: C.muted, lineHeight: 1.6 }}>
                  ℹ Roads are bidirectional. Hub nodes (e.g. "Nagpur") link cities to warehouses via multi-hop paths.
                </div>
              </>
            )}
          </div>

          {/* Stats + Run button */}
          <div style={{ padding: "16px 20px", borderTop: `1px solid ${C.border}` }}>
            <div style={{ display: "flex", gap: 10, marginBottom: 12, fontFamily: F.mono, fontSize: 11 }}>
              {[["Cities", cities.length], ["Warehouses", warehouses.length], ["Roads", roads.length]].map(([label, count]) => (
                <div key={label} style={{ flex: 1, background: C.surface, borderRadius: 8, padding: "8px 12px", textAlign: "center" }}>
                  <div style={{ color: C.muted }}>{label}</div>
                  <div style={{ color: C.amber, fontWeight: 700 }}>{count}</div>
                </div>
              ))}
            </div>

            {apiError && (
              <div style={{ background: C.redDim, border: `1px solid ${C.red}44`, borderRadius: 8, padding: "10px 14px", marginBottom: 10, fontFamily: F.mono, fontSize: 11, color: C.red }}>
                ✗ {apiError}
              </div>
            )}

            <button
              className="run-btn"
              onClick={handleRun}
              disabled={running || cities.length === 0 || warehouses.length === 0}
              style={{
                width: "100%", padding: 14, border: "none", borderRadius: 12,
                background: running ? C.surface : `linear-gradient(135deg,#F59E0B 0%,#D97706 100%)`,
                color: running ? C.muted : "#000",
                fontFamily: F.head, fontSize: 15, fontWeight: 800,
                cursor: running ? "default" : "pointer",
                letterSpacing: 0.5,
                boxShadow: running ? "none" : `0 4px 20px ${C.amberGlow}`,
                transition: "all 0.2s",
              }}>
              {running ? "⏳ Running Python algorithms..." : "▶ Run Optimization"}
            </button>
            <div style={{ marginTop: 8, textAlign: "center", fontFamily: F.mono, fontSize: 10, color: C.muted }}>
              Calls → {API_URL}/optimize
            </div>
          </div>
        </div>

        {/* ── RIGHT: RESULTS PANEL ── */}
        <div style={{ flex: 1, overflowY: "auto" }}>

          {!results && !running && (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", gap: 16, padding: 40 }}>
              <div style={{ fontSize: 64, opacity: 0.15 }}>🗺️</div>
              <div style={{ fontFamily: F.head, fontSize: 20, color: C.muted, fontWeight: 700 }}>Ready to Optimize</div>
              <div style={{ fontFamily: F.mono, fontSize: 12, color: C.muted, textAlign: "center", maxWidth: 360 }}>
                Configure inputs on the left, then click Run. The app calls your FastAPI server which runs the Python algorithms and returns results here.
              </div>
              <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: "12px 20px", fontFamily: F.mono, fontSize: 11, color: C.muted }}>
                Make sure Python is running:<br />
                <span style={{ color: C.amber }}>uvicorn api:app --reload</span>
              </div>
            </div>
          )}

          {running && (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", gap: 20 }}>
              <div style={{ width: 60, height: 60, border: `3px solid ${C.border}`, borderTopColor: C.amber, borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
              <div style={{ fontFamily: F.head, fontSize: 16, color: C.amber }}>Running Python Optimization Pipeline</div>
              <div style={{ fontFamily: F.mono, fontSize: 11, color: C.muted }}>Dijkstra → Greedy → Knapsack → Tabu Search → TSP</div>
            </div>
          )}

          {results && (
            <div style={{ padding: "20px 24px" }}>

              {/* Feasibility banner */}
              <div style={{ background: results.feasible ? C.tealDim : C.redDim, border: `1px solid ${results.feasible ? C.teal : C.red}44`, borderRadius: 12, padding: "12px 18px", marginBottom: 20, display: "flex", alignItems: "center", gap: 12 }}>
                <span style={{ fontSize: 20 }}>{results.feasible ? "✅" : "❌"}</span>
                <div>
                  <div style={{ fontFamily: F.mono, fontSize: 12, fontWeight: 600, color: results.feasible ? C.teal : C.red }}>
                    {results.feasible ? "FEASIBLE PROBLEM" : "INFEASIBLE — DEMAND EXCEEDS CAPACITY"}
                  </div>
                  <div style={{ fontFamily: F.mono, fontSize: 11, color: C.muted, marginTop: 2 }}>
                    Total Demand: <b style={{ color: C.text }}>{results.totalDemand}</b> &nbsp;·&nbsp;
                    Total Capacity: <b style={{ color: C.text }}>{results.totalCapacity}</b> &nbsp;·&nbsp;
                    Surplus: <b style={{ color: C.teal }}>{results.surplus}</b>
                  </div>
                </div>
              </div>

              {/* Result tabs */}
              <div style={{ display: "flex", gap: 4, marginBottom: 20, flexWrap: "wrap" }}>
                {resTabs.map(([t, label]) => (
                  <button key={t} className="res-tab" onClick={() => setResTab(t)} style={resTabStyle(t)}>{label}</button>
                ))}
              </div>

              {/* ── OVERVIEW ── */}
              {resTab === "overview" && (
                <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                  <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                    <StatCard label="Pre-Tabu Cost"       value={results.preTabuEval.totalCost}  color={C.dim}   sub="After greedy + knapsack" />
                    <StatCard label="Optimized Cost"      value={results.postTabuEval.totalCost} color={C.amber} sub="After Python Tabu Search" />
                    <StatCard label="Improvement"         value={`${results.improvementPct}%`}   color={C.teal}  sub={`Saved ${results.improvement} units cost`} />
                    <StatCard label="Total delivery dist" value={results.tspTotalCost}            color={C.dim}   sub="TSP all warehouses" />
                  </div>

                  {/* Greedy initial allocation */}
                  <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
                    <SectionHeader icon="🎯" title="Greedy Initial Allocation" badge={`${Object.keys(results.greedyAllocation).length} cities`} />
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                      {Object.entries(results.greedyAllocation).map(([city, whMap]) => {
                        const wh = Object.keys(whMap)[0];
                        const units = Object.values(whMap)[0];
                        return (
                          <div key={city} style={{ background: C.surface, borderRadius: 8, padding: "6px 12px", fontFamily: F.mono, fontSize: 11 }}>
                            <span style={{ color: C.text }}>{city}</span>
                            <span style={{ color: C.muted }}> → </span>
                            <span style={{ color: C.amber }}>{wh}</span>
                            <span style={{ color: C.muted }}> ({units}u)</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Knapsack overflow resolutions */}
                  {results.knapsackLog?.length > 0 && (
                    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
                      <SectionHeader icon="⚖️" title="Knapsack Overflow Resolutions" badge={`${results.knapsackLog.length} moves`} />
                      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                        {results.knapsackLog.map((l, i) => (
                          <div key={i} style={{ fontFamily: F.mono, fontSize: 11, color: C.dim, padding: "5px 10px", background: C.surface, borderRadius: 6 }}>
                            Moving <span style={{ color: C.amber }}>{l.units}u</span> of <span style={{ color: C.text }}>{l.city}</span>: <span style={{ color: C.red }}>{l.from}</span> → <span style={{ color: C.teal }}>{l.to}</span> <span style={{ color: C.muted }}>(Δcost: {l.penalty})</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Unreachable pairs */}
                  {results.unreachablePairs?.length > 0 && (
                    <div style={{ background: C.redDim, border: `1px solid ${C.red}44`, borderRadius: 12, padding: 20 }}>
                      <SectionHeader icon="⚠️" title="Unreachable City → Warehouse Pairs" />
                      {results.unreachablePairs.map((p, i) => (
                        <div key={i} style={{ fontFamily: F.mono, fontSize: 11, color: C.red, marginBottom: 4 }}>
                          {p.city} → {p.warehouse} (no path in road network)
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Demand satisfaction */}
                  <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
                    <SectionHeader icon="✅" title="Demand Satisfaction (Post-Tabu)" />
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                      {Object.entries(results.postTabuEval.demandDetails).map(([city, d]) => (
                        <div key={city} style={{ background: d.satisfied ? `${C.teal}18` : C.redDim, border: `1px solid ${d.satisfied ? C.teal : C.red}44`, borderRadius: 8, padding: "5px 10px", fontFamily: F.mono, fontSize: 11 }}>
                          <span style={{ color: d.satisfied ? C.teal : C.red }}>{city}</span>
                          <span style={{ color: C.muted }}> {d.allocated}/{d.demand}</span>
                          {!d.satisfied && <span style={{ color: C.red }}> {d.overAllocated ? "OVER" : "UNDER"}</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* ── COST MATRIX ── */}
              {resTab === "cost-matrix" && (
                <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
                  <SectionHeader icon="🗺" title="Shortest-Path Cost Matrix" badge="Python Dijkstra" />
                  <div style={{ marginBottom: 10, fontFamily: F.mono, fontSize: 10, color: C.muted }}>
                    <span style={{ color: C.tealBright }}>■</span> Lowest cost per city &nbsp;|&nbsp; <span style={{ color: C.red }}>∞</span> Unreachable
                  </div>
                  <CostMatrixTable
                    cities={cities.filter(c => c.name.trim()).map(c => ({ name: c.name.trim() }))}
                    warehouses={warehouses.filter(w => w.name.trim()).map(w => ({ name: w.name.trim() }))}
                    matrix={results.costMatrix}
                  />
                </div>
              )}

              {/* ── ALLOCATION ── */}
              {resTab === "allocation" && (
                <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
                  <SectionHeader icon="📦" title="Final Optimized Allocation" badge={`Cost: ${results.postTabuEval.totalCost}`} />
                  <AllocationTable alloc={results.optimizedAllocation} costMatrix={results.costMatrix} />
                  <div style={{ marginTop: 14, padding: "10px 14px", background: C.surface, borderRadius: 8, display: "flex", gap: 20, fontFamily: F.mono, fontSize: 12 }}>
                    <span>Total Cost: <b style={{ color: C.amber }}>{results.postTabuEval.totalCost}</b></span>
                    <span>Improvement: <b style={{ color: C.teal }}>{results.improvementPct}% saved</b></span>
                  </div>
                </div>
              )}

              {/* ── UTILIZATION ── */}
              {resTab === "utilization" && (
                <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                  <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
                    <SectionHeader icon="🏭" title="Warehouse Utilization (Post-Tabu)" />
                    <UtilizationBars wUtil={results.postTabuEval.warehouseUtilization} />
                    <div style={{ marginTop: 16, display: "flex", flexWrap: "wrap", gap: 10 }}>
                      {Object.entries(results.postTabuEval.warehouseUtilization).map(([wh, d]) => (
                        <div key={wh} style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, padding: "12px 16px", flex: 1, minWidth: 120 }}>
                          <div style={{ fontFamily: F.mono, fontSize: 11, color: C.muted, marginBottom: 4 }}>{wh}</div>
                          <div style={{ fontFamily: F.head, fontSize: 22, fontWeight: 700, color: d.overCapacity ? C.red : C.teal }}>{d.utilizationPct}%</div>
                          <div style={{ fontFamily: F.mono, fontSize: 10, color: C.muted }}>{d.used} / {d.capacity}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Pre vs Post Tabu comparison */}
                  <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
                    <SectionHeader icon="📊" title="Pre vs Post Tabu Comparison" />
                    <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: F.mono, fontSize: 12 }}>
                      <thead><tr>
                        {["Warehouse", "Pre-Tabu", "Post-Tabu", "Δ"].map(h => (
                          <th key={h} style={{ textAlign: h === "Warehouse" ? "left" : "right", color: C.muted, padding: "6px 10px", borderBottom: `1px solid ${C.border}` }}>{h}</th>
                        ))}
                      </tr></thead>
                      <tbody>
                        {Object.entries(results.postTabuEval.warehouseUtilization).map(([wh, post]) => {
                          const pre = results.preTabuEval.warehouseUtilization[wh] || {};
                          const delta = post.used - (pre.used || 0);
                          return (
                            <tr key={wh}>
                              <td style={{ padding: "6px 10px", color: C.text, fontWeight: 600 }}>{wh}</td>
                              <td style={{ padding: "6px 10px", textAlign: "right", color: C.dim }}>{pre.used ?? "—"} ({pre.utilizationPct ?? "—"}%)</td>
                              <td style={{ padding: "6px 10px", textAlign: "right", color: C.text }}>{post.used} ({post.utilizationPct}%)</td>
                              <td style={{ padding: "6px 10px", textAlign: "right", color: delta < 0 ? C.teal : delta > 0 ? C.amber : C.muted }}>{delta > 0 ? "+" : ""}{delta}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* ── TSP ROUTES ── */}
              {resTab === "tsp-routes" && (
                <TspRoutesTab
                  tspRoutes={results.tspRoutes}
                  tspTotalCost={results.tspTotalCost}
                  warehouseNames={warehouseNames}
                  optimizedAllocation={results.optimizedAllocation}
                  costMatrix={results.costMatrix}
                />
              )}

            </div>
          )}
        </div>
      </div>
    </div>
  );
}
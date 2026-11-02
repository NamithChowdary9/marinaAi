"use client";

import { useState, useEffect, useRef } from "react";
import { routesApi } from "@/services/api";
import {
  Navigation, Anchor, Zap, Fuel, CheckCircle, Clock3, Gauge, ShieldAlert,
  AlertTriangle, Loader2, Map as MapIcon, Sparkles, RotateCcw,
} from "lucide-react";
import { cn } from "@/utils/cn";
import { formatDistance, formatDuration } from "@/utils/formatters";
import type { RouteResult, DepartureCheck, RouteWaypoint, VoyageTwinResult, VoyageTwinScenario } from "@/types";

// ─── Ports ────────────────────────────────────────────────────────────────────

const PORTS = [
  { name: "Mumbai, India",          lat: 18.9388, lon: 72.8354 },
  { name: "Chennai, India",         lat: 13.0827, lon: 80.2707 },
  { name: "Visakhapatnam, India",   lat: 17.6868, lon: 83.2185 },
  { name: "Colombo, Sri Lanka",     lat: 6.9271,  lon: 79.8612 },
  { name: "Singapore",              lat: 1.3521,  lon: 103.8198 },
  { name: "Dubai, UAE",             lat: 25.2048, lon: 55.2708 },
  { name: "Shanghai, China",        lat: 31.2304, lon: 121.4737 },
  { name: "Rotterdam, Netherlands", lat: 51.9244, lon: 4.4777 },
  { name: "New York, USA",          lat: 40.7128, lon: -74.0059 },
  { name: "Sydney, Australia",      lat: -33.8688, lon: 151.2093 },
];

const VESSEL_TYPES = ["cargo", "tanker", "fishing", "passenger", "small_boat"];

type Tab         = "optimize" | "twin" | "departure";
type RouteKey    = "safe" | "fast" | "fuel_efficient";

// ─── Helpers ──────────────────────────────────────────────────────────────────

/** Convert plain-text markdown (**bold**, bullet •) to JSX safely */
function RichText({ text }: { text: string }) {
  const lines = text.split("\n");
  return (
    <div className="space-y-1.5">
      {lines.map((line, i) => {
        if (!line.trim()) return <div key={i} className="h-1" />;

        // Parse inline **bold**
        const parts = line.split(/(\*\*[^*]+\*\*)/g);
        const parsed = parts.map((p, j) =>
          p.startsWith("**") && p.endsWith("**")
            ? <strong key={j} className="text-ocean-100 font-semibold">{p.slice(2, -2)}</strong>
            : <span key={j}>{p}</span>
        );

        // Section headers (lines starting with emoji + **)
        if (/^[🗺🚢💡🛡⚡⛽⚠️🕐📏⏱📍🧭ℹ️]/.test(line) && line.includes("**")) {
          return (
            <p key={i} className="text-ocean-200 font-semibold text-sm leading-relaxed">
              {parsed}
            </p>
          );
        }
        // Numbered direction steps
        if (/^\s+\d+\./.test(line)) {
          return (
            <div key={i} className="flex gap-2 pl-4">
              <span className="text-ocean-500 text-xs shrink-0 pt-0.5 font-bold">
                {line.trim().match(/^(\d+)\./)?.[1]}.
              </span>
              <p className="text-xs text-ocean-300 leading-snug">
                {line.trim().replace(/^\d+\.\s*/, "")}
              </p>
            </div>
          );
        }
        // Bullet points
        if (/^\s+•/.test(line)) {
          return (
            <div key={i} className="flex gap-2 pl-4">
              <span className="text-ocean-500 text-xs shrink-0 pt-0.5">•</span>
              <p className="text-xs text-ocean-300 leading-snug">{line.trim().slice(1).trim()}</p>
            </div>
          );
        }
        // Indented sub-lines
        if (line.startsWith("  ")) {
          return (
            <p key={i} className="text-xs text-ocean-400 leading-snug pl-4">{parsed}</p>
          );
        }
        return (
          <p key={i} className="text-sm text-ocean-300 leading-relaxed">{parsed}</p>
        );
      })}
    </div>
  );
}

// ─── Route Map ────────────────────────────────────────────────────────────────

const ROUTE_COLORS: Record<RouteKey, { line: string; marker: string; label: string }> = {
  safe:           { line: "#10b981", marker: "#34d399", label: "Safe Route"  },
  fast:           { line: "#f59e0b", marker: "#fbbf24", label: "Fast Route"  },
  fuel_efficient: { line: "#3b82f6", marker: "#60a5fa", label: "Eco Route"   },
};

function RouteMap({ waypoints, routeType, overlayWaypoints }: {
  waypoints: RouteWaypoint[];
  routeType: RouteKey;
  overlayWaypoints?: RouteWaypoint[];
}) {
  const containerRef   = useRef<HTMLDivElement>(null);
  const mapRef         = useRef<any>(null);
  const routeLayersRef = useRef<any[]>([]);
  const initDoneRef    = useRef(false);
  const colors = ROUTE_COLORS[routeType];

  // ── Init map exactly once ──────────────────────────────────────────────────
  useEffect(() => {
    if (initDoneRef.current) return;
    if (!containerRef.current) return;
    initDoneRef.current = true;

    import("leaflet").then((Lmod) => {
      const L = (Lmod as any).default ?? Lmod;
      if (mapRef.current) return; // already created

      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconUrl:       "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        shadowUrl:     "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      });

      const m = L.map(containerRef.current, {
        zoomControl: true,
        attributionControl: false,
        scrollWheelZoom: true,
        center: [10, 80] as [number, number],
        zoom: 4,
      });

      L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        {
          attribution: 'Tiles &copy; <a href="https://www.esri.com/">Esri</a>',
          maxZoom: 16,
        }
      ).addTo(m);

      L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}",
        { maxZoom: 16, opacity: 0.8 }
      ).addTo(m);

      mapRef.current = m;
      setTimeout(() => m.invalidateSize(), 200);
    });
    // No cleanup — we intentionally keep the map alive
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Redraw route when waypoints / type changes ─────────────────────────────
  useEffect(() => {
    if (!waypoints || waypoints.length < 2) return;

    // If map isn't ready yet, poll until it is
    let attempts = 0;
    const tryDraw = () => {
      const map = mapRef.current;
      if (!map) {
        if (attempts++ < 20) setTimeout(tryDraw, 150);
        return;
      }
      drawRoute(map);
    };
    tryDraw();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [waypoints, routeType, overlayWaypoints]);

  function drawRoute(map: any) {
    import("leaflet").then((Lmod) => {
      const L = (Lmod as any).default ?? Lmod;

      // Remove previous route layers
      routeLayersRef.current.forEach(l => { try { map.removeLayer(l); } catch {} });
      routeLayersRef.current = [];

      if (!waypoints || waypoints.length < 2) return;

      const latlngs: [number, number][] = waypoints.map(w => [w.lat, w.lon]);

      // The grey dashed line is the original voyage when a what-if is being compared.
      if (overlayWaypoints && overlayWaypoints.length > 1) {
        const overlay = L.polyline(overlayWaypoints.map(w => [w.lat, w.lon]), {
          color: "#94a3b8", weight: 3, opacity: 0.85, dashArray: "5 8", lineCap: "round",
        }).addTo(map);
        routeLayersRef.current.push(overlay);
      }

      // Glow underneath
      const glow = L.polyline(latlngs, { color: colors.line, weight: 10, opacity: 0.15 }).addTo(map);

      // Main dashed line
      const line = L.polyline(latlngs, {
        color: colors.line, weight: 3.5, opacity: 1,
        dashArray: "12 6", lineCap: "round", lineJoin: "round",
      }).addTo(map);

      routeLayersRef.current.push(glow, line);

      // Direction arrows at segment midpoints
      for (let i = 0; i < latlngs.length - 1; i++) {
        const [la1, lo1] = latlngs[i];
        const [la2, lo2] = latlngs[i + 1];
        const midLat = (la1 + la2) / 2;
        const midLon = (lo1 + lo2) / 2;
        const angleDeg = Math.atan2(la2 - la1, lo2 - lo1) * (180 / Math.PI);

        const arrowIcon = L.divIcon({
          html: `<div style="
            width:0;height:0;
            border-left:5px solid transparent;
            border-right:5px solid transparent;
            border-bottom:10px solid ${colors.line};
            opacity:0.9;
            transform:rotate(${90 - angleDeg}deg);
            filter:drop-shadow(0 0 3px ${colors.line});
          "></div>`,
          className: "",
          iconSize: [10, 10] as [number, number],
          iconAnchor: [5, 5] as [number, number],
        });
        const arrow = L.marker([midLat, midLon] as [number, number], { icon: arrowIcon, interactive: false }).addTo(map);
        routeLayersRef.current.push(arrow);
      }

      // Waypoint markers
      waypoints.forEach((wp, i) => {
        const isOrigin = i === 0;
        const isDest   = i === waypoints.length - 1;
        const bg       = isOrigin ? "#10b981" : isDest ? "#ef4444" : colors.marker;
        const border   = isOrigin ? "#6ee7b7" : isDest ? "#fca5a5" : "#ffffff";
        const size     = isOrigin || isDest ? 20 : 13;
        const lbl      = isOrigin ? "A" : isDest ? "B" : String(i);

        const icon = L.divIcon({
          html: `<div style="
            width:${size}px;height:${size}px;border-radius:50%;
            background:${bg};border:2.5px solid ${border};
            box-shadow:0 0 8px ${bg},0 2px 6px rgba(0,0,0,0.6);
            display:flex;align-items:center;justify-content:center;
            font-size:${isOrigin || isDest ? 9 : 7}px;font-weight:900;
            color:#fff;font-family:monospace;
          ">${lbl}</div>`,
          className: "",
          iconSize:   [size, size]     as [number, number],
          iconAnchor: [size/2, size/2] as [number, number],
        });

        const popup = `<div style="background:#0f1729;color:#e2e8f0;padding:10px 12px;
          border-radius:8px;font-size:12px;min-width:170px;
          border:1px solid rgba(99,179,237,0.25);">
          <div style="font-weight:700;color:${bg};margin-bottom:5px;">
            ${isOrigin ? "🟢 Origin" : isDest ? "🔴 Destination" : `📍 Stop ${i}`}
          </div>
          <div style="color:#93c5fd;font-size:11px;margin-bottom:3px;">${wp.name}</div>
          <div style="color:#475569;font-size:10px;">
            ${Math.abs(wp.lat).toFixed(4)}°${wp.lat >= 0 ? "N" : "S"}
            &nbsp;${Math.abs(wp.lon).toFixed(4)}°${wp.lon >= 0 ? "E" : "W"}
          </div>
        </div>`;

        const marker = L.marker([wp.lat, wp.lon] as [number, number], { icon })
          .addTo(map)
          .bindPopup(popup, { maxWidth: 210 });
        routeLayersRef.current.push(marker);
      });

      // Fit bounds
      try {
        map.fitBounds(line.getBounds(), { padding: [40, 40] as [number, number], maxZoom: 7 });
      } catch {}
      setTimeout(() => map.invalidateSize(), 100);
    });
  }

  return (
    <div className="relative h-80 w-full bg-[#0d1b2a] rounded-b-xl overflow-hidden">
      <div ref={containerRef} style={{ height: "100%", width: "100%" }} />

      {/* Legend */}
      <div className="absolute bottom-3 left-3 z-[1000] bg-ocean-950/90 backdrop-blur-sm border border-ocean-700/40 rounded-lg px-3 py-2.5 pointer-events-none space-y-1.5">
        <div className="flex items-center gap-2">
          <span className="inline-block w-6 h-0.5 rounded" style={{ background: colors.line }} />
          <span className="text-xs font-semibold text-ocean-200">{colors.label}</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="w-4 h-4 rounded-full bg-emerald-500 flex items-center justify-center text-[8px] font-black text-white">A</span>
            <span className="text-[10px] text-ocean-400">Origin</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-4 h-4 rounded-full bg-red-500 flex items-center justify-center text-[8px] font-black text-white">B</span>
            <span className="text-[10px] text-ocean-400">Destination</span>
          </div>
        </div>
        <p className="text-[10px] text-ocean-500">{waypoints?.length ?? 0} waypoints · click to inspect</p>
        {overlayWaypoints && <p className="text-[10px] text-slate-400">Dashed grey: current plan</p>}
      </div>
    </div>
  );
}

// ─── Route Card ───────────────────────────────────────────────────────────────

function RouteCard({ type, route, recommended, selected, onSelect }: {
  type: RouteKey;
  route: any;
  recommended: boolean;
  selected?: boolean;
  onSelect?: () => void;
}) {
  const configs: Record<RouteKey, { icon: React.ReactNode; color: string; label: string }> = {
    safe:           { icon: <Navigation className="w-4 h-4" />, color: "text-emerald-400", label: "Safe Route"  },
    fast:           { icon: <Zap        className="w-4 h-4" />, color: "text-yellow-400",  label: "Fast Route"  },
    fuel_efficient: { icon: <Fuel       className="w-4 h-4" />, color: "text-blue-400",    label: "Eco Route"   },
  };
  const cfg       = configs[type];
  const riskScore = Number(route.risk_score?.toFixed(0) ?? 0);
  const isRisky   = riskScore > 50;

  return (
    <div
      onClick={onSelect}
      className={cn(
        "card p-4 space-y-3.5 hover:bg-ocean-700/40 transition-all cursor-pointer select-none",
        recommended && "border-ocean-500/50 shadow-ocean",
        selected    && "ring-2 ring-ocean-400/60 bg-ocean-700/30"
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className={cn("flex items-center gap-2 font-bold text-sm", cfg.color)}>
          {cfg.icon} {cfg.label}
        </div>
        <div className="flex gap-1.5 flex-wrap justify-end">
          {selected    && <span className="badge bg-ocean-400/20 border-ocean-400/40 text-ocean-200 text-xs px-2 py-0.5">🗺 On Map</span>}
          {recommended && <span className="badge bg-ocean-500/20 border-ocean-500/40 text-ocean-200 text-xs px-2 py-0.5">⭐ Recommended</span>}
        </div>
      </div>

      {/* Risk pill */}
      <div className={cn(
        "flex items-center gap-2 text-xs font-semibold px-3 py-2 rounded-lg",
        isRisky
          ? "bg-orange-900/30 border border-orange-500/30 text-orange-300"
          : "bg-emerald-900/20 border border-emerald-500/20 text-emerald-300"
      )}>
        {isRisky ? "⚠️ Moderate Risk" : "✅ Safe"} — Risk {riskScore}/100
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3">
        <StatRow label="Distance"   value={formatDistance(route.distance_nm ?? 0)} />
        <StatRow label="Duration"   value={formatDuration(route.duration_h  ?? 0)} />
        {route.fuel_savings_pct && <StatRow label="Fuel Saved"  value={`${route.fuel_savings_pct}%`} />}
        {route.waypoints?.length  && <StatRow label="Waypoints"  value={`${route.waypoints.length}`} />}
      </div>

      {/* Step-by-step directions */}
      {route.directions?.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-[10px] text-ocean-400 font-bold uppercase tracking-widest">🧭 Navigation Steps</p>
          <div className="space-y-1 max-h-32 overflow-y-auto pr-1 scrollbar-thin">
            {(route.directions as string[]).map((d, i) => (
              <div key={i} className="flex gap-2 items-start">
                <span className="shrink-0 w-4 h-4 rounded-full bg-ocean-700 border border-ocean-600 flex items-center justify-center text-[9px] font-bold text-ocean-300">
                  {i + 1}
                </span>
                <p className="text-[11px] text-ocean-300 leading-snug">{d}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {route.description && (
        <p className="text-xs text-ocean-500 leading-relaxed">{route.description}</p>
      )}
    </div>
  );
}

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] text-ocean-500 font-medium uppercase tracking-wide">{label}</p>
      <p className="text-sm text-ocean-100 font-bold">{value}</p>
    </div>
  );
}

// ─── AI Recommendation Panel ──────────────────────────────────────────────────

function AIRecommendationPanel({ text }: { text: string }) {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="card border-l-4 border-ocean-400 overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-ocean-700/20 transition-colors"
        onClick={() => setExpanded(v => !v)}
      >
        <div className="flex items-center gap-2">
          <span className="text-lg">🤖</span>
          <span className="text-sm font-bold text-ocean-200 uppercase tracking-wide">AI Recommendation</span>
          <span className="text-xs text-ocean-500 bg-ocean-800/60 px-2 py-0.5 rounded-full">Powered by MarineAI</span>
        </div>
        <button className="text-xs text-ocean-400 hover:text-ocean-200 flex items-center gap-1 transition-colors">
          {expanded ? "▲ Collapse" : "▼ Expand"}
        </button>
      </div>

      {/* Body */}
      {expanded && (
        <div className="px-4 pb-4 pt-1 border-t border-ocean-700/30">
          <RichText text={text} />
        </div>
      )}
    </div>
  );
}

const TWIN_SCENARIOS: Array<{ id: VoyageTwinScenario; label: string; description: string; icon: React.ReactNode }> = [
  { id: "depart_later", label: "Leave later", description: "Shift departure into a safer window", icon: <Clock3 className="w-4 h-4" /> },
  { id: "slow_speed", label: "Slow down", description: "Trade ETA for lower fuel use", icon: <Gauge className="w-4 h-4" /> },
  { id: "avoid_storm", label: "Avoid storm", description: "Take a safer weather corridor", icon: <ShieldAlert className="w-4 h-4" /> },
  { id: "engine_failure", label: "Engine failure", description: "Test reduced-propulsion contingency", icon: <AlertTriangle className="w-4 h-4" /> },
  { id: "ais_loss", label: "AIS loss", description: "Test manual reporting protocol", icon: <RotateCcw className="w-4 h-4" /> },
];

function TwinPlanCard({ plan, recommended, selected, onSelect }: {
  plan: VoyageTwinResult["plans"][number]; recommended: boolean; selected: boolean; onSelect: () => void;
}) {
  const risk = Number(plan.route.risk_score ?? 0);
  const riskStyle = risk >= 60 ? "text-red-300 bg-red-500/10 border-red-500/30" : risk >= 35 ? "text-amber-300 bg-amber-500/10 border-amber-500/30" : "text-emerald-300 bg-emerald-500/10 border-emerald-500/30";
  return (
    <button onClick={onSelect} className={cn("card p-4 text-left space-y-3 transition-all hover:bg-ocean-700/30", selected && "ring-2 ring-ocean-400/70", recommended && "border-emerald-400/40")}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-sm font-bold text-ocean-100">{plan.label}</p>
          <p className="text-[11px] text-ocean-500 mt-1 leading-snug">{plan.summary}</p>
        </div>
        {recommended && <span className="shrink-0 badge bg-emerald-500/15 border-emerald-400/30 text-emerald-300">Best fit</span>}
      </div>
      <div className="grid grid-cols-3 gap-2">
        <StatRow label="ETA" value={formatDuration(plan.route.duration_h ?? 0)} />
        <StatRow label="Fuel index" value={`${plan.route.fuel_index}`} />
        <StatRow label="Risk" value={`${risk}/100`} />
      </div>
      <div className={cn("rounded-lg border px-2.5 py-1.5 text-[11px] font-semibold", riskStyle)}>
        {risk >= 60 ? "High exposure — review before sailing" : risk >= 35 ? "Managed exposure" : "Lower exposure"}
      </div>
    </button>
  );
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export function RoutePlanner() {
  const [tab, setTab] = useState<Tab>("optimize");

  const [originIdx,  setOriginIdx]  = useState(0);
  const [destIdx,    setDestIdx]    = useState(3);
  const [vesselType, setVesselType] = useState("cargo");
  const [preferred,  setPreferred]  = useState<"safe" | "fast" | "fuel">("safe");

  const [routeResult,      setRouteResult]      = useState<{ route_options: RouteResult; ai_recommendation: string } | null>(null);
  const [routeLoading,     setRouteLoading]     = useState(false);
  const [routeError,       setRouteError]       = useState("");
  const [selectedRouteKey, setSelectedRouteKey] = useState<RouteKey>("safe");

  // Voyage Twin — deliberately starts with a useful, common Mumbai → Colombo example.
  const [twinOriginIdx, setTwinOriginIdx] = useState(0);
  const [twinDestIdx, setTwinDestIdx] = useState(3);
  const [twinVesselType, setTwinVesselType] = useState("cargo");
  const [twinScenario, setTwinScenario] = useState<VoyageTwinScenario>("depart_later");
  const [twinDelay, setTwinDelay] = useState(6);
  const [twinSpeed, setTwinSpeed] = useState(12);
  const [twinResult, setTwinResult] = useState<VoyageTwinResult | null>(null);
  const [twinLoading, setTwinLoading] = useState(false);
  const [twinError, setTwinError] = useState("");
  const [selectedTwinId, setSelectedTwinId] = useState("simulated");

  const [port,           setPort]           = useState("Visakhapatnam, India");
  const [portLat,        setPortLat]        = useState(17.6868);
  const [portLon,        setPortLon]        = useState(83.2185);
  const [depVesselType,  setDepVesselType]  = useState("fishing");
  const [departureTime,  setDepartureTime]  = useState("");
  const [departureResult,setDepartureResult]= useState<DepartureCheck | null>(null);
  const [depLoading,     setDepLoading]     = useState(false);

  const handleRouteOptimize = async () => {
    if (originIdx === destIdx) { setRouteError("Origin and destination must differ"); return; }
    setRouteLoading(true);
    setRouteError("");
    try {
      const origin = PORTS[originIdx];
      const dest   = PORTS[destIdx];
      const result = await routesApi.optimize({
        origin_lat:        origin.lat, origin_lon:   origin.lon, origin_name:   origin.name,
        destination_lat:   dest.lat,   destination_lon: dest.lon, destination_name: dest.name,
        vessel_type:       vesselType, preferred_route: preferred,
      });
      setRouteResult(result);
      const rec = result?.route_options?.recommended_route;
      setSelectedRouteKey((rec as RouteKey) ?? "safe");
    } catch {
      setRouteError("Route optimization failed. Ensure the backend is running.");
    } finally {
      setRouteLoading(false);
    }
  };

  const handleDepartureCheck = async () => {
    setDepLoading(true);
    try {
      const portObj = PORTS.find(p => p.name === port);
      const lat = portObj?.lat ?? portLat;
      const lon = portObj?.lon ?? portLon;
      const result = await routesApi.departureCheck(port, lat, lon, depVesselType, departureTime || undefined);
      setDepartureResult(result);
    } catch {
      setDepartureResult(null);
    } finally {
      setDepLoading(false);
    }
  };

  const handleTwinRun = async () => {
    if (twinOriginIdx === twinDestIdx) { setTwinError("Choose two different ports for the voyage."); return; }
    setTwinLoading(true); setTwinError("");
    try {
      const origin = PORTS[twinOriginIdx];
      const destination = PORTS[twinDestIdx];
      const result = await routesApi.voyageTwin({
        origin_lat: origin.lat, origin_lon: origin.lon, origin_name: origin.name,
        destination_lat: destination.lat, destination_lon: destination.lon, destination_name: destination.name,
        vessel_type: twinVesselType, preferred_route: "safe", scenario: twinScenario,
        departure_offset_h: twinDelay, speed_knots: twinSpeed,
      });
      setTwinResult(result);
      setSelectedTwinId(result.recommended_plan_id || "simulated");
    } catch {
      setTwinError("Voyage Twin could not run. Ensure the MarineAI backend is running, then try again.");
    } finally { setTwinLoading(false); }
  };

  const routes = routeResult?.route_options?.routes;
  const twinPlans = twinResult?.plans ?? [];
  const selectedTwinPlan = twinPlans.find(plan => plan.id === selectedTwinId) ?? twinPlans[0];
  const currentTwinPlan = twinPlans.find(plan => plan.id === "current");

  return (
    <div className="flex-1 min-h-0 overflow-y-auto p-6 bg-ocean-950">
      <div className="max-w-4xl mx-auto space-y-6">

        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <Navigation className="w-6 h-6 text-ocean-300" /> Route Planning
          </h1>
          <p className="text-ocean-400 text-sm mt-1">
            AI-powered maritime route optimization &amp; departure safety checks
          </p>
        </div>

        {/* Tab switch */}
        <div className="flex gap-2">
          {(["optimize", "twin", "departure"] as Tab[]).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={cn(
                "btn-secondary text-sm",
                tab === t && "bg-ocean-500/30 border-ocean-500/40 text-ocean-100"
              )}
            >
              {t === "optimize" ? "🗺️ Route Optimizer" : t === "twin" ? "✨ Voyage Twin" : "⛵ Departure Safety Check"}
            </button>
          ))}
        </div>

        {/* ── Route Optimizer ───────────────────────────────────────── */}
        {tab === "optimize" && (
          <div className="space-y-5">
            {/* Form */}
            <div className="card p-5 space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {/* Origin */}
                <div>
                  <label className="block text-sm font-semibold text-ocean-300 mb-2">Origin Port</label>
                  <select value={originIdx} onChange={e => setOriginIdx(Number(e.target.value))} className="input-field w-full text-sm h-11">
                    {PORTS.map((p, i) => <option key={p.name} value={i}>{p.name}</option>)}
                  </select>
                </div>
                {/* Destination */}
                <div>
                  <label className="block text-sm font-semibold text-ocean-300 mb-2">Destination Port</label>
                  <select value={destIdx} onChange={e => setDestIdx(Number(e.target.value))} className="input-field w-full text-sm h-11">
                    {PORTS.map((p, i) => <option key={p.name} value={i}>{p.name}</option>)}
                  </select>
                </div>
                {/* Vessel type */}
                <div>
                  <label className="block text-sm font-semibold text-ocean-300 mb-2">Vessel Type</label>
                  <select value={vesselType} onChange={e => setVesselType(e.target.value)} className="input-field w-full text-sm capitalize h-11">
                    {VESSEL_TYPES.map(t => <option key={t} value={t} className="capitalize">{t}</option>)}
                  </select>
                </div>
                {/* Route priority */}
                <div>
                  <label className="block text-sm font-semibold text-ocean-300 mb-2">Route Priority</label>
                  <div className="flex gap-2">
                    {(["safe", "fast", "fuel"] as const).map(r => (
                      <button
                        key={r}
                        onClick={() => setPreferred(r)}
                        className={cn(
                          "flex-1 py-2.5 rounded-lg text-sm font-semibold border transition-all capitalize min-h-[44px]",
                          preferred === r
                            ? "bg-ocean-500/30 border-ocean-500/50 text-ocean-100"
                            : "bg-ocean-900/40 border-ocean-700/30 text-ocean-400 hover:text-ocean-200 hover:bg-ocean-800/50"
                        )}
                      >
                        {r === "safe" ? "🛡 Safe" : r === "fast" ? "⚡ Fast" : "⛽ Fuel"}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {routeError && (
                <p className="text-red-400 text-sm bg-red-900/20 border border-red-500/30 rounded-lg px-3 py-2">
                  ⚠ {routeError}
                </p>
              )}

              <button
                onClick={handleRouteOptimize}
                disabled={routeLoading}
                className="btn-primary w-full flex items-center justify-center gap-2 text-base font-semibold"
              >
                {routeLoading
                  ? <><Loader2 className="w-4 h-4 animate-spin" /> Calculating optimal route…</>
                  : <><Navigation className="w-4 h-4" /> Optimize Route</>
                }
              </button>
            </div>

            {/* Results */}
            {routeResult && routes && (
              <div className="space-y-5 animate-fade-in">

                {/* ── Map ─────────────────────────────────────────── */}
                <div className="card p-0 overflow-hidden">
                  {/* Map header with route switcher */}
                  <div className="flex items-center gap-2 px-4 py-3 border-b border-ocean-700/40">
                    <MapIcon className="w-4 h-4 text-ocean-300 shrink-0" />
                    <span className="text-sm font-bold text-ocean-200">Route Map</span>
                    <span className="text-xs text-ocean-500 ml-1">
                      {PORTS[originIdx]?.name.split(",")[0]} → {PORTS[destIdx]?.name.split(",")[0]}
                    </span>
                    <div className="flex gap-1.5 ml-auto">
                      {(["safe", "fast", "fuel_efficient"] as RouteKey[]).map(k => {
                        const active = selectedRouteKey === k;
                        const colorMap = { safe: "emerald", fast: "yellow", fuel_efficient: "blue" } as const;
                        const c = colorMap[k];
                        return (
                          <button
                            key={k}
                            onClick={() => setSelectedRouteKey(k)}
                            className={cn(
                              "px-2.5 py-1 rounded-md text-xs font-semibold border transition-all",
                              active
                                ? c === "emerald" ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-300"
                                : c === "yellow"  ? "bg-yellow-500/20  border-yellow-500/40  text-yellow-300"
                                :                   "bg-blue-500/20    border-blue-500/40    text-blue-300"
                                : "bg-ocean-800/40 border-ocean-700/30 text-ocean-400 hover:text-ocean-200"
                            )}
                          >
                            {k === "safe" ? "🛡 Safe" : k === "fast" ? "⚡ Fast" : "⛽ Eco"}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <RouteMap
                    waypoints={routes[selectedRouteKey]?.waypoints ?? []}
                    routeType={selectedRouteKey}
                  />
                </div>

                {/* ── AI Recommendation ───────────────────────────── */}
                {routeResult.ai_recommendation && (
                  <AIRecommendationPanel text={routeResult.ai_recommendation} />
                )}

                {/* ── Route Cards ─────────────────────────────────── */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {(["safe", "fast", "fuel_efficient"] as RouteKey[]).map(key => (
                    routes[key] && (
                      <RouteCard
                        key={key}
                        type={key}
                        route={routes[key]}
                        recommended={routeResult.route_options.recommended_route === key}
                        selected={selectedRouteKey === key}
                        onSelect={() => setSelectedRouteKey(key)}
                      />
                    )
                  ))}
                </div>

              </div>
            )}
          </div>
        )}

        {/* ── What-if Voyage Twin ─────────────────────────────────── */}
        {tab === "twin" && (
          <div className="space-y-5 animate-fade-in">
            <div className="card-glow p-5">
              <div className="flex items-start gap-3 mb-5">
                <div className="w-10 h-10 rounded-xl bg-violet-500/15 border border-violet-400/25 flex items-center justify-center shrink-0">
                  <Sparkles className="w-5 h-5 text-violet-300" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white">What-if Voyage Twin</h2>
                  <p className="text-sm text-ocean-400 mt-0.5">Change one condition. Compare the operational impact before you sail.</p>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
                <div><label className="block text-xs font-semibold text-ocean-300 mb-2">From</label><select value={twinOriginIdx} onChange={e => setTwinOriginIdx(Number(e.target.value))} className="input-field h-11">{PORTS.map((p, i) => <option key={p.name} value={i}>{p.name}</option>)}</select></div>
                <div><label className="block text-xs font-semibold text-ocean-300 mb-2">To</label><select value={twinDestIdx} onChange={e => setTwinDestIdx(Number(e.target.value))} className="input-field h-11">{PORTS.map((p, i) => <option key={p.name} value={i}>{p.name}</option>)}</select></div>
                <div><label className="block text-xs font-semibold text-ocean-300 mb-2">Vessel type</label><select value={twinVesselType} onChange={e => setTwinVesselType(e.target.value)} className="input-field h-11 capitalize">{VESSEL_TYPES.map(t => <option key={t} value={t}>{t}</option>)}</select></div>
              </div>
              <p className="section-title mb-2">What changes?</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2">
                {TWIN_SCENARIOS.map(item => <button key={item.id} onClick={() => setTwinScenario(item.id)} className={cn("min-h-[88px] rounded-xl border p-3 text-left transition-all", twinScenario === item.id ? "bg-violet-500/15 border-violet-400/45 text-violet-100" : "bg-ocean-900/40 border-ocean-700/35 text-ocean-400 hover:bg-ocean-800/60")}><span className={cn("mb-2 block", twinScenario === item.id ? "text-violet-300" : "text-ocean-500")}>{item.icon}</span><span className="block text-xs font-bold">{item.label}</span><span className="block text-[10px] leading-snug mt-1 opacity-75">{item.description}</span></button>)}
              </div>
              {(twinScenario === "depart_later" || twinScenario === "slow_speed") && <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-5 bg-ocean-950/45 border border-ocean-700/30 rounded-xl p-4">
                {twinScenario === "depart_later" && <label className="text-xs text-ocean-300 font-semibold">Delay departure: <span className="text-violet-300">{twinDelay} hours</span><input aria-label="Departure delay" type="range" min="1" max="24" value={twinDelay} onChange={e => setTwinDelay(Number(e.target.value))} className="w-full mt-2 accent-violet-400" /></label>}
                {twinScenario === "slow_speed" && <label className="text-xs text-ocean-300 font-semibold">Target speed: <span className="text-violet-300">{twinSpeed} knots</span><input aria-label="Target speed" type="range" min="8" max="18" value={twinSpeed} onChange={e => setTwinSpeed(Number(e.target.value))} className="w-full mt-2 accent-violet-400" /></label>}
              </div>}
              {twinError && <p className="mt-4 text-sm text-red-300 bg-red-500/10 border border-red-500/25 rounded-lg px-3 py-2">⚠ {twinError}</p>}
              <button onClick={handleTwinRun} disabled={twinLoading} className="btn-primary w-full mt-5 text-base py-3">{twinLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> Simulating voyage…</> : <><Sparkles className="w-4 h-4" /> Run Voyage Twin</>}</button>
            </div>
            {twinResult && selectedTwinPlan && <div className="space-y-5 animate-slide-up">
              <div className="card border-l-4 border-emerald-400 p-4"><p className="section-title text-emerald-400 mb-1">MarineAI recommendation</p><p className="text-sm text-ocean-100 leading-relaxed">{twinResult.recommendation}</p></div>
              <div className="card overflow-hidden"><div className="flex items-center gap-2 px-4 py-3 border-b border-ocean-700/40"><MapIcon className="w-4 h-4 text-violet-300" /><span className="text-sm font-bold text-ocean-200">Original vs. simulated route</span><span className="ml-auto text-[10px] text-ocean-500">Select a plan below to inspect it</span></div><RouteMap waypoints={selectedTwinPlan.route.waypoints} overlayWaypoints={selectedTwinPlan.id === "current" ? undefined : currentTwinPlan?.route.waypoints} routeType={selectedTwinPlan.id === "eco" ? "fuel_efficient" : "safe"} /></div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">{twinPlans.map(plan => <TwinPlanCard key={plan.id} plan={plan} recommended={plan.id === twinResult.recommended_plan_id} selected={plan.id === selectedTwinId} onSelect={() => setSelectedTwinId(plan.id)} />)}</div>
              {twinResult.hazards.length > 0 && <div className="card p-4"><p className="section-title mb-2">Conditions to monitor</p><div className="flex flex-wrap gap-2">{twinResult.hazards.map(h => <span key={h} className="text-xs text-amber-200 bg-amber-500/10 border border-amber-500/20 rounded-full px-3 py-1">⚠ {h}</span>)}</div><p className="text-[11px] text-ocean-500 mt-3">{twinResult.data_note}</p></div>}
            </div>}
          </div>
        )}

        {/* ── Departure Safety Check ──────────────────────────────── */}
        {tab === "departure" && (
          <div className="space-y-4">
            <div className="card p-5 space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-semibold text-ocean-300 mb-2">Departure Port</label>
                  <select
                    value={port}
                    onChange={e => {
                      setPort(e.target.value);
                      const p = PORTS.find(pt => pt.name === e.target.value);
                      if (p) { setPortLat(p.lat); setPortLon(p.lon); }
                    }}
                    className="input-field w-full text-sm h-11"
                  >
                    {PORTS.map(p => <option key={p.name} value={p.name}>{p.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-ocean-300 mb-2">Vessel Type</label>
                  <select value={depVesselType} onChange={e => setDepVesselType(e.target.value)} className="input-field w-full text-sm capitalize h-11">
                    {VESSEL_TYPES.map(t => <option key={t} value={t} className="capitalize">{t}</option>)}
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-semibold text-ocean-300 mb-2">
                    Planned Departure <span className="text-ocean-500 font-normal">(optional)</span>
                  </label>
                  <input
                    type="datetime-local"
                    value={departureTime}
                    onChange={e => setDepartureTime(e.target.value)}
                    className="input-field w-full text-sm h-11"
                  />
                </div>
              </div>

              <button
                onClick={handleDepartureCheck}
                disabled={depLoading}
                className="btn-primary w-full flex items-center justify-center gap-2 text-base font-semibold"
              >
                {depLoading
                  ? <><Loader2 className="w-4 h-4 animate-spin" /> Checking conditions…</>
                  : <><Anchor className="w-4 h-4" /> Check Departure Safety</>
                }
              </button>
            </div>

            {departureResult && (
              <div className={cn(
                "card p-5 border-l-4 animate-fade-in",
                departureResult.is_safe_to_depart ? "border-emerald-500" : "border-red-500"
              )}>
                <div className="flex items-center gap-3 mb-4">
                  {departureResult.is_safe_to_depart
                    ? <CheckCircle  className="w-7 h-7 text-emerald-400 shrink-0" />
                    : <AlertTriangle className="w-7 h-7 text-red-400 shrink-0" />}
                  <div>
                    <h3 className={cn(
                      "font-bold text-lg",
                      departureResult.is_safe_to_depart ? "text-emerald-300" : "text-red-300"
                    )}>
                      {departureResult.safety_verdict}
                    </h3>
                    <p className="text-ocean-400 text-sm mt-0.5">
                      Risk score: <span className="font-semibold text-ocean-200">{departureResult.risk_score.toFixed(0)}/100</span>
                      {" "}· Port: {departureResult.port}
                    </p>
                  </div>
                </div>
                <div className="bg-ocean-800/50 rounded-xl p-4 text-sm text-ocean-200 leading-relaxed">
                  {departureResult.ai_explanation}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

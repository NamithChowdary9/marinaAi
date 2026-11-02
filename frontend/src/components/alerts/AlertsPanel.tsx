"use client";

import { useQuery } from "@tanstack/react-query";
import { alertsApi } from "@/services/api";
import {
  Bell, AlertTriangle, Waves, Wind,
  TriangleAlert, MapPin, RefreshCw, ShieldCheck,
} from "lucide-react";
import { cn } from "@/utils/cn";
import type { Alert, DangerZone } from "@/types";

const CARD: React.CSSProperties = {
  background: "rgba(255,255,255,0.03)",
  border: "1px solid rgba(255,255,255,0.07)",
  borderRadius: "16px",
};

const SEV_CONFIG: Record<string, { bg: string; border: string; text: string; accent: string }> = {
  extreme:  { bg: "rgba(239,68,68,0.07)",    border: "rgba(239,68,68,0.25)",    text: "#f87171", accent: "#ef4444" },
  critical: { bg: "rgba(239,68,68,0.07)",    border: "rgba(239,68,68,0.25)",    text: "#f87171", accent: "#ef4444" },
  warning:  { bg: "rgba(249,115,22,0.07)",   border: "rgba(249,115,22,0.25)",   text: "#fb923c", accent: "#f97316" },
  high:     { bg: "rgba(249,115,22,0.07)",   border: "rgba(249,115,22,0.25)",   text: "#fb923c", accent: "#f97316" },
  medium:   { bg: "rgba(234,179,8,0.07)",    border: "rgba(234,179,8,0.22)",    text: "#fbbf24", accent: "#eab308" },
  low:      { bg: "rgba(16,185,129,0.06)",   border: "rgba(16,185,129,0.2)",    text: "#34d399", accent: "#10b981" },
};

const SEV_ORDER: Record<string, number> = {
  extreme: 0, critical: 0, warning: 1, high: 1, medium: 2, low: 3,
};

export function AlertsPanel() {
  const { data: alertsData, isLoading: aLoading, refetch } = useQuery({
    queryKey: ["alerts"],
    queryFn: alertsApi.getActive,
    refetchInterval: 30_000,
  });

  const { data: zonesData, isLoading: zLoading } = useQuery({
    queryKey: ["danger-zones"],
    queryFn: alertsApi.getDangerZones,
    refetchInterval: 60_000,
  });

  const alerts = alertsData?.alerts ?? [];
  const zones  = zonesData?.danger_zones ?? [];

  const criticals = alerts.filter(a => a.severity === "critical" || a.severity === "extreme").length;

  return (
    <div
      className="flex-1 min-h-0 overflow-y-auto"
      style={{ background: "linear-gradient(180deg, #040d1c 0%, #030b18 100%)" }}
    >
      <div className="max-w-4xl mx-auto px-6 py-6 space-y-6">

        {/* Header */}
        <div className="flex items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2.5">
              <div
                className="w-8 h-8 rounded-xl flex items-center justify-center"
                style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)" }}
              >
                <Bell className="w-4 h-4 text-red-400" />
              </div>
              Maritime Alerts
            </h1>
            <p className="text-sm mt-1" style={{ color: "rgba(255,255,255,0.3)" }}>
              AI-generated real-time alerts for storm, wave, and emergency events
            </p>
          </div>
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 px-3.5 h-9 rounded-xl text-xs font-semibold transition-all text-white/50 hover:text-white/80"
            style={{
              background: "rgba(255,255,255,0.05)",
              border: "1px solid rgba(255,255,255,0.08)",
            }}
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>

        {/* Summary strip */}
        <div className="grid grid-cols-3 gap-3">
          <SummaryCard
            icon={<AlertTriangle className="w-5 h-5 text-red-400" />}
            label="Active Alerts"
            value={alerts.length}
            accent="#ef4444"
          />
          <SummaryCard
            icon={<TriangleAlert className="w-5 h-5 text-orange-400" />}
            label="Danger Zones"
            value={zones.length}
            accent="#f97316"
          />
          <SummaryCard
            icon={<Waves className="w-5 h-5 text-red-300" />}
            label="Critical"
            value={criticals}
            accent="#ef4444"
          />
        </div>

        {/* Active alerts */}
        <div className="p-5 space-y-4" style={CARD}>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              Active Alerts
            </h2>
            {alerts.length > 0 && (
              <span
                className="text-[10px] px-2 py-0.5 rounded-full font-bold"
                style={{ background: "rgba(239,68,68,0.15)", border: "1px solid rgba(239,68,68,0.25)", color: "#f87171" }}
              >
                {alerts.length}
              </span>
            )}
          </div>

          {aLoading ? (
            <div className="space-y-2.5">
              {[0,1,2].map(i => (
                <div key={i} className="h-20 rounded-xl animate-shimmer" style={{ background: "rgba(255,255,255,0.03)" }} />
              ))}
            </div>
          ) : alerts.length === 0 ? (
            <div className="py-12 text-center space-y-3">
              <div
                className="w-14 h-14 rounded-2xl mx-auto flex items-center justify-center"
                style={{ background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.18)" }}
              >
                <ShieldCheck className="w-7 h-7 text-emerald-400" />
              </div>
              <p className="text-base font-semibold" style={{ color: "#34d399" }}>All Clear</p>
              <p className="text-sm" style={{ color: "rgba(255,255,255,0.3)" }}>No active alerts — ocean conditions are calm</p>
            </div>
          ) : (
            <div className="space-y-2.5">
              {[...alerts]
                .sort((a, b) => (SEV_ORDER[a.severity] ?? 4) - (SEV_ORDER[b.severity] ?? 4))
                .map((alert, i) => <AlertCard key={i} alert={alert} />)}
            </div>
          )}
        </div>

        {/* Danger zones */}
        <div className="p-5 space-y-4" style={CARD}>
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <MapPin className="w-4 h-4 text-orange-400" />
            Ocean Danger Zones
          </h2>

          {zLoading ? (
            <div className="space-y-2.5">
              {[0,1,2].map(i => (
                <div key={i} className="h-14 rounded-xl animate-shimmer" style={{ background: "rgba(255,255,255,0.03)" }} />
              ))}
            </div>
          ) : zones.length === 0 ? (
            <div className="py-10 text-center space-y-2">
              <MapPin className="w-8 h-8 mx-auto" style={{ color: "rgba(255,255,255,0.1)" }} />
              <p className="text-sm" style={{ color: "rgba(255,255,255,0.25)" }}>No danger zones detected</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {zones.map((zone, i) => <ZoneCard key={i} zone={zone} />)}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

// ─── Alert card ───────────────────────────────────────────────────────────────

function AlertCard({ alert }: { alert: Alert }) {
  const cfg = SEV_CONFIG[alert.severity] ?? SEV_CONFIG.low;

  const ICONS: Record<string, React.ReactNode> = {
    storm:     <Wind className="w-4 h-4" />,
    wave:      <Waves className="w-4 h-4" />,
    cyclone:   <Wind className="w-4 h-4" />,
    collision: <TriangleAlert className="w-4 h-4" />,
    sos:       <AlertTriangle className="w-4 h-4" />,
  };

  return (
    <div
      className="flex gap-3 p-4 rounded-xl transition-all hover:scale-[1.005]"
      style={{
        background: cfg.bg,
        border: `1px solid ${cfg.border}`,
        borderLeft: `3px solid ${cfg.accent}`,
      }}
    >
      {/* Icon */}
      <div
        className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
        style={{ background: `${cfg.accent}18`, color: cfg.text }}
      >
        {ICONS[alert.type] ?? <Bell className="w-4 h-4" />}
      </div>

      {/* Body */}
      <div className="flex-1 min-w-0 space-y-1.5">
        <div className="flex items-center gap-2 flex-wrap">
          <h3 className="text-sm font-bold text-white">{alert.title}</h3>
          <span
            className="text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wide"
            style={{
              background: `${cfg.accent}18`,
              border: `1px solid ${cfg.border}`,
              color: cfg.text,
            }}
          >
            {alert.severity}
          </span>
        </div>
        <p className="text-xs leading-relaxed" style={{ color: "rgba(255,255,255,0.55)" }}>{alert.description}</p>
        {alert.region && (
          <p className="text-[10px] flex items-center gap-1" style={{ color: "rgba(255,255,255,0.3)" }}>
            <MapPin className="w-2.5 h-2.5" /> {alert.region}
          </p>
        )}
      </div>
    </div>
  );
}

// ─── Zone card ────────────────────────────────────────────────────────────────

function ZoneCard({ zone }: { zone: DangerZone }) {
  const colors = {
    red:    { bg: "rgba(239,68,68,0.07)",  border: "rgba(239,68,68,0.22)",  accent: "#ef4444", text: "#f87171" },
    orange: { bg: "rgba(249,115,22,0.07)", border: "rgba(249,115,22,0.22)", accent: "#f97316", text: "#fb923c" },
    yellow: { bg: "rgba(234,179,8,0.06)",  border: "rgba(234,179,8,0.2)",   accent: "#eab308", text: "#fbbf24" },
  };
  const c = colors[zone.color as keyof typeof colors] ?? colors.yellow;

  return (
    <div
      className="p-4 rounded-xl transition-all hover:scale-[1.01]"
      style={{ background: c.bg, border: `1px solid ${c.border}`, borderLeft: `3px solid ${c.accent}` }}
    >
      <div className="flex items-center justify-between mb-2.5">
        <p className="text-sm font-bold text-white">{zone.region}</p>
        <span
          className="text-[10px] px-2 py-0.5 rounded-full font-bold uppercase"
          style={{ background: `${c.accent}18`, color: c.text }}
        >
          {zone.danger_level.replace("_", " ")}
        </span>
      </div>
      <div className="flex flex-wrap gap-3 text-[10px]" style={{ color: "rgba(255,255,255,0.4)" }}>
        <span>Threat: {zone.primary_threat.replace("_", " ")}</span>
        {zone.wave_height_m != null && <span>Waves: {zone.wave_height_m.toFixed(1)} m</span>}
        {zone.wind_speed_kmh != null && <span>Wind: {zone.wind_speed_kmh.toFixed(0)} km/h</span>}
      </div>
    </div>
  );
}

// ─── Summary card ─────────────────────────────────────────────────────────────

function SummaryCard({ icon, label, value, accent }: {
  icon: React.ReactNode; label: string; value: number; accent: string;
}) {
  return (
    <div
      className="p-4 rounded-2xl relative overflow-hidden"
      style={{
        background: "rgba(255,255,255,0.03)",
        border: "1px solid rgba(255,255,255,0.07)",
      }}
    >
      <div
        className="absolute -top-4 -right-4 w-16 h-16 rounded-full opacity-[0.07] pointer-events-none"
        style={{ background: accent, filter: "blur(12px)" }}
      />
      <div className="flex items-center gap-2.5 mb-3">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
          style={{ background: `${accent}14` }}
        >
          {icon}
        </div>
        <p className="text-[10px] font-semibold uppercase tracking-[0.12em]" style={{ color: "rgba(255,255,255,0.28)" }}>
          {label}
        </p>
      </div>
      <p
        className="text-3xl font-bold font-mono leading-none"
        style={{ color: value > 0 ? accent : "#34d399" }}
      >
        {value}
      </p>
      <div
        className="absolute bottom-0 left-0 right-0 h-[2px] opacity-25"
        style={{ background: `linear-gradient(90deg, ${accent}, transparent)` }}
      />
    </div>
  );
}

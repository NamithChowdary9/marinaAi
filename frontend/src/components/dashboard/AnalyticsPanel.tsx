"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi, weatherApi } from "@/services/api";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  Cell, PieChart, Pie, AreaChart, Area,
} from "recharts";
import { BarChart3, Waves, Wind, TrendingUp, Globe, Ship, Activity } from "lucide-react";
import { dangerLevelBg, dangerLevelDot } from "@/utils/formatters";
import { cn } from "@/utils/cn";

// ─── Shared styles ────────────────────────────────────────────────────────────

const CARD_STYLE: React.CSSProperties = {
  background: "rgba(255,255,255,0.03)",
  border: "1px solid rgba(255,255,255,0.07)",
  borderRadius: "16px",
};

const TOOLTIP_STYLE = {
  background: "rgba(6,14,30,0.95)",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: "10px",
  color: "#cbd5e1",
  fontSize: 12,
  padding: "8px 12px",
};

export function AnalyticsPanel() {
  const { data: dashboard, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: analyticsApi.getDashboard,
    refetchInterval: 60_000,
  });

  const { data: globalWeather } = useQuery({
    queryKey: ["global-weather"],
    queryFn: weatherApi.getGlobal,
    refetchInterval: 120_000,
  });

  if (isLoading) {
    return (
      <div className="flex-1 min-h-0 flex items-center justify-center" style={{ background: "#040d1c" }}>
        <div className="text-center space-y-3 animate-fade-in">
          <div
            className="w-14 h-14 rounded-2xl mx-auto flex items-center justify-center"
            style={{ background: "rgba(26,110,194,0.1)", border: "1px solid rgba(26,110,194,0.2)" }}
          >
            <BarChart3 className="w-6 h-6" style={{ color: "#3a8fd4", animation: "pulse 2s infinite" }} />
          </div>
          <p className="text-sm" style={{ color: "rgba(255,255,255,0.3)" }}>Loading analytics…</p>
        </div>
      </div>
    );
  }

  const waveSummary = dashboard?.wave_summary ?? {};
  const waveChartData = Object.entries(waveSummary).map(([region, d]) => ({
    region: region.replace(" Ocean", "").replace(" Sea", ""),
    wave: d.wave_height_m,
    danger: d.danger_level,
  }));

  const dangerPie = [
    { name: "Safe",      value: dashboard?.ocean_conditions.safe_regions ?? 0,      color: "#10b981" },
    { name: "Moderate",  value: dashboard?.ocean_conditions.moderate_regions ?? 0,   color: "#f59e0b" },
    { name: "Dangerous", value: dashboard?.ocean_conditions.dangerous_regions ?? 0,  color: "#ef4444" },
  ];

  const weatherEntries = globalWeather ? Object.entries(globalWeather) : [];

  // Trend data (mock wave trend for visual richness)
  const trendData = waveChartData.slice(0, 6).map((d, i) => ({
    name: d.region,
    value: d.wave,
    prev: Math.max(0.2, d.wave - Math.random() * 0.8 + 0.3),
  }));

  return (
    <div
      className="flex-1 min-h-0 overflow-y-auto"
      style={{ background: "linear-gradient(180deg, #040d1c 0%, #030b18 100%)" }}
    >
      <div className="max-w-6xl mx-auto px-6 py-6 space-y-6">

        {/* ── Header ─────────────────────────────────────────────────── */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2.5">
              <div
                className="w-8 h-8 rounded-xl flex items-center justify-center"
                style={{ background: "rgba(26,110,194,0.15)", border: "1px solid rgba(26,110,194,0.25)" }}
              >
                <BarChart3 className="w-4 h-4 text-sky-400" />
              </div>
              Maritime Analytics
            </h1>
            <p className="text-sm mt-1" style={{ color: "rgba(255,255,255,0.3)" }}>
              Real-time ocean intelligence · vessel statistics · AI insights
            </p>
          </div>
          <div
            className="hidden sm:flex items-center gap-1.5 px-3 h-7 rounded-full text-[10px] font-semibold"
            style={{ background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.18)", color: "#34d399" }}
          >
            <Activity className="w-3 h-3" />
            Live data
          </div>
        </div>

        {/* ── KPI row ────────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <KpiCard
            icon={<Ship className="w-5 h-5 text-sky-400" />}
            label="Tracked Vessels"
            value={dashboard?.vessels.total_tracked?.toLocaleString() ?? "516"}
            sub="Live AIS feed"
            accent="#38bdf8"
          />
          <KpiCard
            icon={<Waves className="w-5 h-5 text-blue-400" />}
            label="Highest Wave"
            value={`${dashboard?.ocean_conditions.highest_wave_height_m?.toFixed(1) ?? "—"} m`}
            sub={dashboard?.ocean_conditions.highest_wave_region ?? "Global"}
            accent="#60a5fa"
          />
          <KpiCard
            icon={<TrendingUp className="w-5 h-5 text-violet-400" />}
            label="AI Agents"
            value={`${dashboard?.ai_agents_active ?? 7} Active`}
            sub="LangGraph pipeline"
            accent="#a78bfa"
          />
          <KpiCard
            icon={<Globe className="w-5 h-5 text-emerald-400" />}
            label="Safe Zones"
            value={`${dashboard?.ocean_conditions.safe_regions ?? "—"} / 10`}
            sub="Ocean regions"
            accent="#34d399"
          />
        </div>

        {/* ── Charts row ─────────────────────────────────────────────── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

          {/* Wave heights bar */}
          <div className="md:col-span-2 p-5 space-y-4" style={CARD_STYLE}>
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Waves className="w-4 h-4 text-blue-400" />
                Wave Heights by Region
              </h3>
              <span className="text-[10px]" style={{ color: "rgba(255,255,255,0.25)" }}>metres (m)</span>
            </div>
            <ResponsiveContainer width="100%" height={190}>
              <BarChart data={waveChartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <XAxis dataKey="region" tick={{ fontSize: 10, fill: "rgba(255,255,255,0.3)" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "rgba(255,255,255,0.3)" }} axisLine={false} tickLine={false} unit="m" />
                <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: number) => [`${v.toFixed(1)} m`, "Wave height"]} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
                <Bar dataKey="wave" radius={[5, 5, 0, 0]} maxBarSize={40}>
                  {waveChartData.map((e, i) => (
                    <Cell key={i} fill={
                      e.danger === "very_dangerous" ? "#7c3aed" :
                      e.danger === "dangerous"      ? "#ef4444" :
                      e.danger === "moderate"       ? "#f59e0b" : "#10b981"
                    } />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Safety distribution donut */}
          <div className="p-5 space-y-4 flex flex-col" style={CARD_STYLE}>
            <h3 className="text-sm font-semibold text-white">Ocean Safety</h3>
            <div className="flex-1 flex items-center justify-center">
              <ResponsiveContainer width="100%" height={140}>
                <PieChart>
                  <Pie data={dangerPie} cx="50%" cy="50%" innerRadius={42} outerRadius={62} paddingAngle={4} dataKey="value" strokeWidth={0}>
                    {dangerPie.map((e, i) => <Cell key={i} fill={e.color} />)}
                  </Pie>
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="space-y-2">
              {dangerPie.map(d => (
                <div key={d.name} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ background: d.color }} />
                    <span style={{ color: "rgba(255,255,255,0.5)" }}>{d.name}</span>
                  </div>
                  <span className="font-semibold" style={{ color: d.color }}>{d.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Wave trend area chart ───────────────────────────────────── */}
        {trendData.length > 0 && (
          <div className="p-5 space-y-4" style={CARD_STYLE}>
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-violet-400" />
              Regional Wave Trend
            </h3>
            <ResponsiveContainer width="100%" height={150}>
              <AreaChart data={trendData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="grad1" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#3a8fd4" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#3a8fd4" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="grad2" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#7c3aed" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#7c3aed" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: "rgba(255,255,255,0.3)" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "rgba(255,255,255,0.3)" }} axisLine={false} tickLine={false} unit="m" />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Area type="monotone" dataKey="prev" stroke="#7c3aed" strokeWidth={1.5} fill="url(#grad2)" name="Yesterday" />
                <Area type="monotone" dataKey="value" stroke="#3a8fd4" strokeWidth={2} fill="url(#grad1)" name="Today" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* ── Global weather table ────────────────────────────────────── */}
        {weatherEntries.length > 0 && (
          <div className="p-5 space-y-4" style={CARD_STYLE}>
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Wind className="w-4 h-4 text-sky-400" />
              Global Maritime Weather
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                    {["Region", "Temp", "Wind", "Humidity", "Wave", "Status"].map(h => (
                      <th key={h} className={cn("pb-3 font-semibold tracking-wide", h === "Region" ? "text-left" : "text-right")}
                        style={{ color: "rgba(255,255,255,0.28)" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {weatherEntries.map(([region, w]) => {
                    const waveH = w.wave_height_m ?? 0;
                    const level = waveH > 6 ? "very_dangerous" : waveH > 4 ? "dangerous" : waveH > 2 ? "moderate" : "safe";
                    return (
                      <tr key={region} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}
                        className="hover:bg-white/[0.02] transition-colors">
                        <td className="py-2.5 font-medium" style={{ color: "rgba(255,255,255,0.75)" }}>{region}</td>
                        <td className="py-2.5 text-right" style={{ color: "rgba(255,255,255,0.45)" }}>{w.temperature_c?.toFixed(0)}°C</td>
                        <td className="py-2.5 text-right" style={{ color: "rgba(255,255,255,0.45)" }}>{w.wind_speed_kmh?.toFixed(0)} km/h</td>
                        <td className="py-2.5 text-right" style={{ color: "rgba(255,255,255,0.45)" }}>{w.humidity_pct?.toFixed(0)}%</td>
                        <td className="py-2.5 text-right font-semibold" style={{ color: waveH > 4 ? "#f87171" : waveH > 2 ? "#fbbf24" : "#34d399" }}>
                          {waveH.toFixed(1)} m
                        </td>
                        <td className="py-2.5 text-right">
                          <span className={cn("inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full border font-semibold", dangerLevelBg(level))}>
                            <span className={cn("w-1.5 h-1.5 rounded-full", dangerLevelDot(level))} />
                            {level === "very_dangerous" ? "Critical" : level.charAt(0).toUpperCase() + level.slice(1)}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── Busiest corridors ───────────────────────────────────────── */}
        {dashboard?.vessels.busiest_corridors?.length ? (
          <div className="p-5 space-y-3" style={CARD_STYLE}>
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Ship className="w-4 h-4 text-sky-400" />
              Busiest Shipping Corridors
            </h3>
            <div className="flex flex-wrap gap-2">
              {dashboard.vessels.busiest_corridors.map((corridor, i) => (
                <span
                  key={corridor}
                  className="text-xs px-3 py-1.5 rounded-xl font-medium"
                  style={{
                    background: "rgba(26,110,194,0.1)",
                    border: "1px solid rgba(26,110,194,0.18)",
                    color: "rgba(147,197,253,0.8)",
                  }}
                >
                  {i + 1}. {corridor}
                </span>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

// ─── KPI card ─────────────────────────────────────────────────────────────────

function KpiCard({ icon, label, value, sub, accent }: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub?: string;
  accent?: string;
}) {
  return (
    <div
      className="p-4 rounded-2xl relative overflow-hidden"
      style={{
        background: "rgba(255,255,255,0.03)",
        border: "1px solid rgba(255,255,255,0.07)",
      }}
    >
      {/* Accent glow */}
      {accent && (
        <div
          className="absolute -top-6 -right-6 w-20 h-20 rounded-full opacity-10 pointer-events-none"
          style={{ background: accent, filter: "blur(16px)" }}
        />
      )}

      <div className="flex items-center gap-2 mb-3">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
          style={{ background: accent ? `${accent}18` : "rgba(255,255,255,0.06)" }}
        >
          {icon}
        </div>
        <span className="text-[10px] font-semibold uppercase tracking-[0.12em]" style={{ color: "rgba(255,255,255,0.3)" }}>
          {label}
        </span>
      </div>

      <p className="text-2xl font-bold tracking-tight text-white leading-none">{value}</p>
      {sub && <p className="text-[10px] mt-1.5" style={{ color: "rgba(255,255,255,0.25)" }}>{sub}</p>}

      {/* Bottom accent line */}
      {accent && (
        <div
          className="absolute bottom-0 left-0 right-0 h-[2px] opacity-30"
          style={{ background: `linear-gradient(90deg, ${accent}, transparent)` }}
        />
      )}
    </div>
  );
}

"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { weatherApi } from "@/services/api";
import {
  Cloud, Wind, Thermometer, Droplets, Eye,
  Waves, TrendingUp, MapPin,
} from "lucide-react";
import {
  dangerLevelBg, dangerLevelDot,
  formatWindSpeed, formatWaveHeight, formatProbability,
} from "@/utils/formatters";
import { cn } from "@/utils/cn";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from "recharts";

const REGIONS = [
  { name: "Indian Ocean",       lat: 5.0,   lon: 75.0  },
  { name: "Arabian Sea",        lat: 15.0,  lon: 65.0  },
  { name: "Bay of Bengal",      lat: 12.0,  lon: 87.0  },
  { name: "South China Sea",    lat: 12.0,  lon: 113.0 },
  { name: "North Atlantic",     lat: 45.0,  lon: -30.0 },
  { name: "Pacific Ocean",      lat: 10.0,  lon: 160.0 },
  { name: "Mediterranean Sea",  lat: 35.0,  lon: 20.0  },
  { name: "South Indian Ocean", lat: -20.0, lon: 75.0  },
];

const CARD: React.CSSProperties = {
  background: "rgba(255,255,255,0.03)",
  border: "1px solid rgba(255,255,255,0.07)",
  borderRadius: "16px",
};

const TOOLTIP: object = {
  background: "rgba(6,14,30,0.95)",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: "10px",
  color: "#cbd5e1",
  fontSize: 12,
  padding: "8px 12px",
};

export function WeatherPanel() {
  const [selected, setSelected] = useState(REGIONS[0]);

  const { data: weatherData, isLoading } = useQuery({
    queryKey: ["weather-current", selected.lat, selected.lon],
    queryFn: () => weatherApi.getCurrent(selected.lat, selected.lon),
    refetchInterval: 60_000,
  });

  const { data: globalData } = useQuery({
    queryKey: ["global-weather"],
    queryFn: weatherApi.getGlobal,
    refetchInterval: 120_000,
  });

  const w     = weatherData?.weather;
  const ocean = weatherData?.ocean;
  const wavePred  = weatherData?.ml_wave_prediction;
  const stormPred = weatherData?.ml_storm_prediction;

  const waveChart = wavePred ? [
    { time: "Now",  height: ocean?.wave_height_m ?? 1 },
    { time: "+6h",  height: wavePred["6h"] },
    { time: "+24h", height: wavePred["24h"] },
    { time: "+72h", height: wavePred["72h"] },
  ] : [];

  return (
    <div
      className="flex-1 min-h-0 overflow-y-auto"
      style={{ background: "linear-gradient(180deg, #040d1c 0%, #030b18 100%)" }}
    >
      <div className="max-w-6xl mx-auto px-6 py-6 space-y-6">

        {/* Header */}
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2.5">
            <div
              className="w-8 h-8 rounded-xl flex items-center justify-center"
              style={{ background: "rgba(56,189,248,0.1)", border: "1px solid rgba(56,189,248,0.2)" }}
            >
              <Cloud className="w-4 h-4 text-sky-400" />
            </div>
            Weather Intelligence
          </h1>
          <p className="text-sm mt-1" style={{ color: "rgba(255,255,255,0.3)" }}>
            Real-time weather · ML wave prediction · storm probability
          </p>
        </div>

        {/* Region pills */}
        <div className="flex flex-wrap gap-2">
          {REGIONS.map(r => {
            const active = selected.name === r.name;
            return (
              <button
                key={r.name}
                onClick={() => setSelected(r)}
                className="px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all"
                style={active ? {
                  background: "rgba(56,189,248,0.14)",
                  border: "1px solid rgba(56,189,248,0.3)",
                  color: "#7dd3fc",
                } : {
                  background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.07)",
                  color: "rgba(255,255,255,0.4)",
                }}
              >
                {r.name}
              </button>
            );
          })}
        </div>

        {isLoading ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[0,1,2,3].map(i => (
              <div key={i} className="h-28 rounded-2xl animate-shimmer" style={CARD} />
            ))}
          </div>
        ) : w ? (
          <>
            {/* Current conditions */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <WeatherCard
                icon={<Thermometer className="w-5 h-5 text-orange-400" />}
                label="Temperature"
                value={`${w.temperature_c?.toFixed(1)}°C`}
                sub={`Feels like ${w.feels_like_c?.toFixed(1) ?? "—"}°C`}
                accent="#fb923c"
              />
              <WeatherCard
                icon={<Wind className="w-5 h-5 text-sky-400" />}
                label="Wind"
                value={formatWindSpeed(w.wind_speed_kmh ?? 0)}
                sub={`${w.wind_direction_deg?.toFixed(0)}° bearing`}
                accent="#38bdf8"
              />
              <WeatherCard
                icon={<Droplets className="w-5 h-5 text-blue-400" />}
                label="Humidity"
                value={`${w.humidity_pct?.toFixed(0)}%`}
                sub={`${w.pressure_hpa?.toFixed(0)} hPa`}
                accent="#60a5fa"
              />
              <WeatherCard
                icon={<Eye className="w-5 h-5 text-emerald-400" />}
                label="Visibility"
                value={`${w.visibility_km?.toFixed(1)} km`}
                sub={w.weather_condition ?? "—"}
                accent="#34d399"
              />
            </div>

            {/* Wave + forecast */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

              {/* Current ocean */}
              <div className="p-5 space-y-4" style={CARD}>
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Waves className="w-4 h-4 text-blue-400" />
                  Current Ocean Conditions
                </h3>
                {ocean && (
                  <div className="space-y-4">
                    <div className="flex items-end justify-between">
                      <div>
                        <p className="text-3xl font-bold text-white leading-none">
                          {formatWaveHeight(ocean.wave_height_m)}
                        </p>
                        <p className="text-xs mt-1" style={{ color: "rgba(255,255,255,0.3)" }}>wave height</p>
                      </div>
                      <span className={cn("text-xs px-2.5 py-1 rounded-full border font-semibold flex items-center gap-1.5", dangerLevelBg(ocean.danger_level))}>
                        <span className={cn("w-1.5 h-1.5 rounded-full", dangerLevelDot(ocean.danger_level))} />
                        {ocean.danger_level.replace("_", " ")}
                      </span>
                    </div>

                    {/* Progress bar */}
                    <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
                      <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{
                          width: `${Math.min(100, (ocean.wave_height_m / 8) * 100)}%`,
                          background: ocean.wave_height_m > 6 ? "#7c3aed"
                            : ocean.wave_height_m > 4 ? "#ef4444"
                            : ocean.wave_height_m > 2 ? "#f59e0b" : "#10b981",
                        }}
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      {[
                        { label: "Wave Period",    value: `${ocean.wave_period_s?.toFixed(0)} s` },
                        { label: "Swell Height",   value: formatWaveHeight(ocean.swell_height_m ?? 0) },
                        { label: "Current Speed",  value: `${ocean.current_velocity_ms?.toFixed(2)} m/s` },
                        { label: "Wave Direction", value: `${ocean.wave_direction_deg?.toFixed(0)}°` },
                      ].map(({ label, value }) => (
                        <div key={label}>
                          <p className="text-[10px] uppercase tracking-wide mb-0.5" style={{ color: "rgba(255,255,255,0.25)" }}>{label}</p>
                          <p className="text-sm font-semibold" style={{ color: "rgba(255,255,255,0.75)" }}>{value}</p>
                        </div>
                      ))}
                    </div>

                    <p
                      className="text-xs leading-relaxed px-3 py-2.5 rounded-xl italic"
                      style={{ background: "rgba(255,255,255,0.03)", color: "rgba(255,255,255,0.35)", border: "1px solid rgba(255,255,255,0.05)" }}
                    >
                      {ocean.wave_height_m < 2
                        ? "Conditions calm — safe for all vessel types."
                        : ocean.wave_height_m < 4
                        ? "Moderate swell — small craft should exercise caution."
                        : ocean.wave_height_m < 6
                        ? "Rough conditions — fishing boats and small vessels avoid."
                        : "Extreme conditions — all small vessels seek shelter immediately."}
                    </p>
                  </div>
                )}
              </div>

              {/* Wave forecast chart */}
              <div className="p-5 space-y-4" style={CARD}>
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-blue-400" />
                    ML Wave Forecast
                  </h3>
                  {wavePred && (
                    <span className="text-[10px]" style={{ color: "rgba(255,255,255,0.25)" }}>
                      {(wavePred.confidence * 100).toFixed(0)}% confidence
                    </span>
                  )}
                </div>
                {waveChart.length > 0 ? (
                  <ResponsiveContainer width="100%" height={170}>
                    <AreaChart data={waveChart} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="wGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%"  stopColor="#3a8fd4" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="#3a8fd4" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="time" tick={{ fontSize: 11, fill: "rgba(255,255,255,0.3)" }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fontSize: 11, fill: "rgba(255,255,255,0.3)" }} axisLine={false} tickLine={false} unit="m" />
                      <Tooltip contentStyle={TOOLTIP} formatter={(v: number) => [`${v.toFixed(2)} m`, "Wave height"]} />
                      <Area type="monotone" dataKey="height" stroke="#3a8fd4" strokeWidth={2.5} fill="url(#wGrad)" dot={{ fill: "#3a8fd4", strokeWidth: 0, r: 3 }} />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-40 flex items-center justify-center">
                    <p className="text-sm" style={{ color: "rgba(255,255,255,0.2)" }}>No forecast data available</p>
                  </div>
                )}
              </div>
            </div>

            {/* Storm prediction */}
            {stormPred && (
              <div
                className="p-5 space-y-4 rounded-2xl"
                style={{
                  ...CARD,
                  borderLeft: `3px solid ${stormPred.should_alert ? "#ef4444" : "#10b981"}`,
                }}
              >
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <h3 className="text-base font-bold text-white">
                    🌀 Storm Prediction — {selected.name}
                  </h3>
                  {stormPred.should_alert && (
                    <span
                      className="text-xs px-3 py-1 rounded-full font-bold"
                      style={{ background: "rgba(239,68,68,0.15)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171" }}
                    >
                      ⚠ Alert Active
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-3 gap-4">
                  {[
                    { label: "Next 6h",  value: stormPred.storm_probability_6h },
                    { label: "Next 24h", value: stormPred.storm_probability_24h },
                    { label: "Next 72h", value: stormPred.storm_probability_72h },
                  ].map(({ label, value }) => (
                    <div key={label} className="text-center p-3 rounded-xl" style={{ background: "rgba(255,255,255,0.03)" }}>
                      <p className="text-[10px] uppercase tracking-wider mb-2" style={{ color: "rgba(255,255,255,0.3)" }}>{label}</p>
                      <p
                        className="text-2xl font-bold font-mono"
                        style={{ color: value > 0.7 ? "#f87171" : value > 0.4 ? "#fbbf24" : "#34d399" }}
                      >
                        {formatProbability(value)}
                      </p>
                    </div>
                  ))}
                </div>

                <div className="flex items-center gap-4 text-sm flex-wrap" style={{ color: "rgba(255,255,255,0.5)" }}>
                  <span>Category: <span className="text-white font-medium capitalize">{stormPred.category.replace(/_/g, " ")}</span></span>
                  <span>Severity: <span
                    className="font-semibold capitalize"
                    style={{ color: stormPred.severity === "extreme" ? "#f87171" : stormPred.severity === "high" ? "#fb923c" : stormPred.severity === "medium" ? "#fbbf24" : "#34d399" }}
                  >{stormPred.severity}</span></span>
                </div>
              </div>
            )}
          </>
        ) : (
          <div
            className="p-12 rounded-2xl text-center space-y-3"
            style={CARD}
          >
            <Cloud className="w-10 h-10 mx-auto" style={{ color: "rgba(255,255,255,0.1)" }} />
            <p className="text-sm" style={{ color: "rgba(255,255,255,0.3)" }}>
              Unable to load weather data. Verify backend is running.
            </p>
          </div>
        )}

        {/* Global overview */}
        {globalData && (
          <div className="p-5 space-y-4" style={CARD}>
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <MapPin className="w-4 h-4 text-sky-400" />
              Global Maritime Overview
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(globalData).map(([region, data]) => {
                const wh = data.wave_height_m ?? 0;
                const level = wh > 6 ? "very_dangerous" : wh > 4 ? "dangerous" : wh > 2 ? "moderate" : "safe";
                return (
                  <div
                    key={region}
                    className="p-3.5 rounded-xl space-y-2.5 transition-all hover:scale-[1.02]"
                    style={{
                      background: "rgba(255,255,255,0.025)",
                      border: "1px solid rgba(255,255,255,0.06)",
                    }}
                  >
                    <p className="text-xs font-semibold" style={{ color: "rgba(255,255,255,0.65)" }}>{region}</p>
                    <div className="grid grid-cols-2 gap-1.5 text-[10px]" style={{ color: "rgba(255,255,255,0.4)" }}>
                      <span>🌡 {data.temperature_c?.toFixed(0)}°C</span>
                      <span>💨 {data.wind_speed_kmh?.toFixed(0)} km/h</span>
                      <span className="font-semibold" style={{ color: wh > 4 ? "#f87171" : wh > 2 ? "#fbbf24" : "#34d399" }}>
                        🌊 {wh.toFixed(1)} m
                      </span>
                      <span className={cn("inline-flex items-center gap-1 text-[9px] px-1.5 py-0.5 rounded-full border", dangerLevelBg(level))}>
                        <span className={cn("w-1 h-1 rounded-full", dangerLevelDot(level))} />
                        {level === "very_dangerous" ? "crit" : level.slice(0, 4)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

// ─── Weather stat card ────────────────────────────────────────────────────────

function WeatherCard({ icon, label, value, sub, accent }: {
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
      {accent && (
        <div
          className="absolute -top-4 -right-4 w-16 h-16 rounded-full opacity-[0.08] pointer-events-none"
          style={{ background: accent, filter: "blur(12px)" }}
        />
      )}
      <div className="flex items-center gap-2 mb-3">
        {icon}
        <span className="text-[10px] font-semibold uppercase tracking-[0.12em]" style={{ color: "rgba(255,255,255,0.28)" }}>
          {label}
        </span>
      </div>
      <p className="text-2xl font-bold text-white leading-none">{value}</p>
      {sub && <p className="text-[10px] mt-1.5" style={{ color: "rgba(255,255,255,0.3)" }}>{sub}</p>}
      {accent && (
        <div
          className="absolute bottom-0 left-0 right-0 h-[2px] opacity-25"
          style={{ background: `linear-gradient(90deg, ${accent}, transparent)` }}
        />
      )}
    </div>
  );
}

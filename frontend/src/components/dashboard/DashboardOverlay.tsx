"use client";

import { useStore } from "@/store/useStore";
import { Ship, Waves, TriangleAlert, Bot } from "lucide-react";
import { MOCK_VESSELS } from "@/data/mockVessels";

export function DashboardOverlay() {
  const { dashboardStats, vessels, activeAlertCount } = useStore();
  const stats = dashboardStats;

  const vesselCount =
    stats?.vessels.total_tracked ??
    (vessels.length > 0 ? vessels.length : MOCK_VESSELS.length);

  const waveH      = stats?.ocean_conditions.highest_wave_height_m;
  const waveRegion = stats?.ocean_conditions.highest_wave_region;

  const chips = [
    {
      icon: <Ship className="w-3.5 h-3.5" />,
      iconColor: "#38bdf8",
      label: "VESSELS LIVE",
      value: vesselCount.toLocaleString(),
      valueColor: "#fff",
      accent: "#38bdf8",
    },
    {
      icon: <Waves className="w-3.5 h-3.5" />,
      iconColor: "#60a5fa",
      label: "HIGHEST WAVES",
      value: waveH ? `${waveH.toFixed(1)} m` : "—",
      sub: waveRegion,
      valueColor: waveH
        ? waveH > 4 ? "#f87171" : waveH > 2 ? "#fbbf24" : "#34d399"
        : "#94a3b8",
      accent: "#60a5fa",
    },
    {
      icon: <TriangleAlert className="w-3.5 h-3.5" />,
      iconColor: activeAlertCount > 0 ? "#f87171" : "#34d399",
      label: "ACTIVE ALERTS",
      value: activeAlertCount.toString(),
      valueColor: activeAlertCount > 0 ? "#f87171" : "#34d399",
      accent: activeAlertCount > 0 ? "#ef4444" : "#10b981",
    },
    {
      icon: <Bot className="w-3.5 h-3.5" />,
      iconColor: "#c084fc",
      label: "AI AGENTS",
      value: `${stats?.ai_agents_active ?? 7} Active`,
      valueColor: "#c084fc",
      accent: "#a855f7",
    },
  ];

  return (
    <div className="absolute top-4 right-4 flex flex-col gap-2 z-10 pointer-events-none">
      {chips.map(chip => (
        <Chip key={chip.label} {...chip} />
      ))}
    </div>
  );
}

function Chip({
  icon, iconColor, label, value, sub, valueColor, accent,
}: {
  icon: React.ReactNode;
  iconColor: string;
  label: string;
  value: string;
  sub?: string;
  valueColor?: string;
  accent?: string;
}) {
  const rgb = accent ? hexToRgb(accent) : "255,255,255";

  return (
    <div
      className="min-w-[158px] rounded-xl px-3.5 py-2.5"
      style={{
        background: "rgba(4,12,28,0.88)",
        backdropFilter: "blur(16px)",
        WebkitBackdropFilter: "blur(16px)",
        border: "1px solid rgba(255,255,255,0.06)",
        boxShadow: `0 4px 20px rgba(0,0,0,0.45), 0 0 0 1px rgba(${rgb},0.04)`,
      }}
    >
      {/* Label row */}
      <div className="flex items-center gap-1.5 mb-1.5">
        <span style={{ color: iconColor }}>{icon}</span>
        <span
          className="text-[9px] font-bold tracking-[0.16em] uppercase"
          style={{ color: "rgba(255,255,255,0.28)" }}
        >
          {label}
        </span>
      </div>

      {/* Value */}
      <p
        className="text-[15px] font-black leading-none font-mono"
        style={{ color: valueColor }}
      >
        {value}
      </p>

      {/* Sub */}
      {sub && (
        <p className="text-[9px] mt-1 truncate max-w-[130px]" style={{ color: "rgba(255,255,255,0.2)" }}>
          {sub}
        </p>
      )}

      {/* Accent line */}
      <div
        className="mt-2 h-[1.5px] rounded-full opacity-30"
        style={{ background: accent ? `linear-gradient(90deg, ${accent}, transparent)` : "rgba(255,255,255,0.1)" }}
      />
    </div>
  );
}

function hexToRgb(hex: string): string {
  const n = parseInt(hex.replace("#", ""), 16);
  return `${(n >> 16) & 255},${(n >> 8) & 255},${n & 255}`;
}

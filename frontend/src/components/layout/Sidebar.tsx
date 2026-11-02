"use client";

import { useState } from "react";
import { useStore } from "@/store/useStore";
import { cn } from "@/utils/cn";
import {
  Ship, Waves, Cloud, TriangleAlert, Eye, EyeOff,
  Layers, ChevronRight, ChevronLeft, Activity,
  Bot, Globe2, BarChart3,
} from "lucide-react";
import { dangerLevelBg, dangerLevelDot, vesselTypeIcon } from "@/utils/formatters";
import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/services/api";

interface SidebarProps { open: boolean; onToggle: () => void; }

// ─── Icon rail items ──────────────────────────────────────────────────────────
const RAIL_ITEMS = [
  { id: "layers",     icon: <Layers   className="w-5 h-5" />, label: "Map Layers"  },
  { id: "fleet",      icon: <Ship     className="w-5 h-5" />, label: "Fleet"       },
  { id: "agents",     icon: <Bot      className="w-5 h-5" />, label: "AI Agents"   },
  { id: "regions",    icon: <Globe2   className="w-5 h-5" />, label: "Regions"     },
  { id: "conditions", icon: <Waves    className="w-5 h-5" />, label: "Ocean Data"  },
] as const;

type PanelId = typeof RAIL_ITEMS[number]["id"] | null;

export function Sidebar({ open, onToggle }: SidebarProps) {
  const [activePanel, setActivePanel] = useState<PanelId>("layers");
  const { map, setMapLayer, vessels, activeAlertCount, dashboardStats } = useStore();

  const { data: dashboard } = useQuery({
    queryKey: ["dashboard"],
    queryFn: analyticsApi.getDashboard,
    refetchInterval: 60_000,
  });

  const stats = dashboard || dashboardStats;

  const vesselTypeCounts = vessels.reduce<Record<string, number>>((acc, v) => {
    const t = v.vessel_type || "Unknown";
    acc[t] = (acc[t] || 0) + 1;
    return acc;
  }, {});

  const handleRailClick = (id: PanelId) => {
    setActivePanel(prev => prev === id ? null : id);
  };

  // ── Collapsed: just the icon rail ──────────────────────────────────────────
  if (!open) {
    return (
      <div className="flex shrink-0 z-20">
        {/* Icon rail */}
        <div className="w-14 bg-ocean-900/95 border-r border-ocean-700/40 flex flex-col items-center py-3 gap-1">
          {RAIL_ITEMS.map(item => (
            <button
              key={item.id}
              onClick={() => { onToggle(); handleRailClick(item.id); }}
              title={item.label}
              className="w-10 h-10 rounded-xl flex items-center justify-center
                         text-ocean-400 hover:text-white hover:bg-ocean-700/60 transition-all"
            >
              {item.icon}
            </button>
          ))}
        </div>
      </div>
    );
  }

  // ── Open: icon rail + panel ───────────────────────────────────────────────
  return (
    <div className="flex shrink-0 z-20">
      {/* Icon rail */}
      <div className="w-14 bg-ocean-900/95 border-r border-ocean-700/30 flex flex-col items-center py-3 gap-1">
        {RAIL_ITEMS.map(item => (
          <button
            key={item.id}
            onClick={() => handleRailClick(item.id)}
            title={item.label}
            className={cn(
              "w-10 h-10 rounded-xl flex items-center justify-center transition-all",
              activePanel === item.id
                ? "bg-ocean-500/30 text-ocean-200 ring-1 ring-ocean-500/50"
                : "text-ocean-400 hover:text-white hover:bg-ocean-700/60"
            )}
          >
            {item.icon}
          </button>
        ))}

        {/* Collapse button at bottom */}
        <div className="flex-1" />
        <button
          onClick={onToggle}
          title="Collapse sidebar"
          className="w-10 h-10 rounded-xl flex items-center justify-center
                     text-ocean-500 hover:text-white hover:bg-ocean-700/60 transition-all"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
      </div>

      {/* Slide-in panel */}
      {activePanel && (
        <div className="w-60 bg-ocean-900/95 border-r border-ocean-700/40
                        flex flex-col min-h-0 overflow-y-auto">

          {/* Panel header */}
          <div className="px-4 py-3 border-b border-ocean-700/40 flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-widest text-ocean-300">
              {RAIL_ITEMS.find(i => i.id === activePanel)?.label}
            </span>
            <button
              onClick={() => setActivePanel(null)}
              className="text-ocean-500 hover:text-ocean-300 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <div className="p-3 space-y-3 flex-1">
            {/* ── MAP LAYERS ─────────────────────────────────────────── */}
            {activePanel === "layers" && (
              <div className="space-y-2">
                {[
                  { key: "showShips",        label: "Live Ships",      icon: <Ship           className="w-4 h-4" />, color: "text-blue-400"    },
                  { key: "showWaveHeatmap",  label: "Wave Heatmap",    icon: <Waves          className="w-4 h-4" />, color: "text-cyan-400"    },
                  { key: "showWeatherLayer", label: "Weather",         icon: <Cloud          className="w-4 h-4" />, color: "text-sky-400"     },
                  { key: "showDangerZones",  label: "Danger Zones",    icon: <TriangleAlert  className="w-4 h-4" />, color: "text-orange-400"  },
                ].map(layer => (
                  <LayerToggle
                    key={layer.key}
                    icon={<span className={layer.color}>{layer.icon}</span>}
                    label={layer.label}
                    active={map[layer.key as keyof typeof map] as boolean}
                    onToggle={() => setMapLayer(layer.key as any, !map[layer.key as keyof typeof map])}
                  />
                ))}
              </div>
            )}

            {/* ── FLEET STATS ─────────────────────────────────────────── */}
            {activePanel === "fleet" && (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-2">
                  <MiniStat label="Vessels" value={stats?.vessels.total_tracked?.toLocaleString() ?? vessels.length.toString()} color="text-ocean-200" />
                  <MiniStat label="Alerts"  value={activeAlertCount.toString()} color={activeAlertCount > 0 ? "text-red-400" : "text-emerald-400"} />
                  <MiniStat label="Safe"    value={stats?.ocean_conditions.safe_regions?.toString() ?? "--"}    color="text-emerald-400" />
                  <MiniStat label="Danger"  value={stats?.ocean_conditions.dangerous_regions?.toString() ?? "--"} color="text-orange-400" />
                </div>
                {Object.keys(vesselTypeCounts).length > 0 && (
                  <div className="space-y-1.5 pt-1">
                    <p className="text-[10px] text-ocean-500 uppercase tracking-wider font-bold">By Type</p>
                    {Object.entries(vesselTypeCounts).sort(([,a],[,b])=>b-a).slice(0,5).map(([type, count]) => (
                      <div key={type} className="flex items-center justify-between py-1 px-2 rounded-lg bg-ocean-800/50">
                        <span className="text-xs text-ocean-300 flex items-center gap-1.5">
                          <span>{vesselTypeIcon(type)}</span>{type}
                        </span>
                        <span className="text-xs font-bold text-ocean-200 font-mono">{count}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* ── AI AGENTS ───────────────────────────────────────────── */}
            {activePanel === "agents" && (
              <div className="space-y-1.5">
                {[
                  { name: "Weather Agent", color: "bg-sky-400",     status: "Active" },
                  { name: "Wave Agent",    color: "bg-blue-400",    status: "Active" },
                  { name: "Ship Agent",    color: "bg-violet-400",  status: "Active" },
                  { name: "Route Agent",   color: "bg-emerald-400", status: "Active" },
                  { name: "Risk Agent",    color: "bg-orange-400",  status: "Active" },
                  { name: "Maritime GPT",  color: "bg-pink-400",    status: "Active" },
                  { name: "Orchestrator",  color: "bg-yellow-400",  status: "Active" },
                ].map(a => (
                  <div key={a.name}
                    className="flex items-center justify-between px-3 py-2 rounded-lg bg-ocean-800/50 border border-ocean-700/30">
                    <div className="flex items-center gap-2">
                      <span className={cn("w-2 h-2 rounded-full shrink-0 animate-pulse", a.color)} />
                      <span className="text-xs text-ocean-200">{a.name}</span>
                    </div>
                    <span className="text-[10px] font-bold text-emerald-400">{a.status}</span>
                  </div>
                ))}
              </div>
            )}

            {/* ── QUICK REGIONS ────────────────────────────────────────── */}
            {activePanel === "regions" && (
              <div className="space-y-1">
                {[
                  { name: "Global View",       lat: 10.0,  lng: 60.0,  zoom: 3 },
                  { name: "Indian Ocean",       lat: 10.0,  lng: 75.0,  zoom: 5 },
                  { name: "Arabian Sea",        lat: 18.0,  lng: 63.0,  zoom: 5 },
                  { name: "Bay of Bengal",      lat: 13.0,  lng: 86.0,  zoom: 5 },
                  { name: "South China Sea",    lat: 12.0,  lng: 113.0, zoom: 5 },
                  { name: "Mediterranean Sea",  lat: 35.0,  lng: 20.0,  zoom: 5 },
                  { name: "North Atlantic",     lat: 45.0,  lng: -35.0, zoom: 4 },
                  { name: "Malacca Strait",     lat: 3.0,   lng: 101.0, zoom: 6 },
                  { name: "Persian Gulf",       lat: 26.0,  lng: 53.0,  zoom: 6 },
                  { name: "Red Sea",            lat: 20.0,  lng: 37.0,  zoom: 5 },
                ].map(r => (
                  <button
                    key={r.name}
                    onClick={() => {
                      const maps = (window as any)._leaflet_maps;
                      if (maps) Object.values(maps).forEach((m: any) => {
                        try { m.flyTo([r.lat, r.lng], r.zoom, { duration: 1.2 }); } catch {}
                      });
                    }}
                    className="w-full text-left px-3 py-2 rounded-lg text-xs text-ocean-300
                               hover:text-white hover:bg-ocean-700/60 transition-all flex items-center gap-2"
                  >
                    <Globe2 className="w-3 h-3 text-ocean-500 shrink-0" />
                    {r.name}
                  </button>
                ))}
              </div>
            )}

            {/* ── OCEAN CONDITIONS ─────────────────────────────────────── */}
            {activePanel === "conditions" && (
              <div className="space-y-1.5">
                {stats && Object.entries(stats.wave_summary || {}).slice(0, 10).map(([region, data]) => (
                  <div key={region}
                    className="flex items-center justify-between px-2 py-1.5 rounded-lg bg-ocean-800/40">
                    <span className="text-xs text-ocean-300 truncate max-w-[110px]">{region}</span>
                    <span className={cn(
                      "flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full border",
                      dangerLevelBg(data.danger_level)
                    )}>
                      <span className={cn("w-1.5 h-1.5 rounded-full", dangerLevelDot(data.danger_level))} />
                      {data.wave_height_m?.toFixed(1)}m
                    </span>
                  </div>
                ))}
                {(!stats || !Object.keys(stats.wave_summary || {}).length) && (
                  <p className="text-xs text-ocean-500 text-center py-4">Loading conditions…</p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function LayerToggle({ icon, label, active, onToggle }: {
  icon: React.ReactNode; label: string; active: boolean; onToggle: () => void;
}) {
  return (
    <button
      onClick={onToggle}
      className={cn(
        "w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs font-medium transition-all border",
        active
          ? "bg-ocean-500/20 border-ocean-500/40 text-ocean-100"
          : "bg-ocean-800/40 border-ocean-700/30 text-ocean-400 hover:text-ocean-200 hover:bg-ocean-800/70"
      )}
    >
      {icon}
      <span className="flex-1 text-left">{label}</span>
      {active
        ? <Eye className="w-3.5 h-3.5 text-ocean-300" />
        : <EyeOff className="w-3.5 h-3.5 text-ocean-600" />}
    </button>
  );
}

function MiniStat({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="bg-ocean-800/60 border border-ocean-700/30 rounded-xl p-3 text-center">
      <p className="text-[10px] text-ocean-500 uppercase tracking-wide font-bold mb-1">{label}</p>
      <p className={cn("text-xl font-black font-mono", color)}>{value}</p>
    </div>
  );
}

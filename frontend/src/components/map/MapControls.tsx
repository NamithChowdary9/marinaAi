"use client";

import {
  ChevronDown, Globe2, RefreshCw, RotateCcw, Settings2,
  Ship, Waves, Cloud, TriangleAlert,
} from "lucide-react";
import { useState } from "react";
import { cn } from "@/utils/cn";
import { useStore } from "@/store/useStore";

interface Props {
  onRefresh: () => void;
}

const QUICK_REGIONS = [
  { name: "Global", lat: 20.0, lng: 60.0, zoom: 2 },
  { name: "Indian Ocean", lat: 10.0, lng: 75.0, zoom: 5 },
  { name: "Arabian Sea", lat: 18.0, lng: 63.0, zoom: 5 },
  { name: "Bay of Bengal", lat: 13.0, lng: 86.0, zoom: 5 },
  { name: "South China", lat: 12.0, lng: 113.0, zoom: 5 },
  { name: "Atlantic", lat: 45.0, lng: -35.0, zoom: 4 },
];

type LayerKey = "showShips" | "showWaveHeatmap" | "showWeatherLayer" | "showDangerZones";

const LAYERS: Array<{ key: LayerKey; label: string; icon: typeof Ship; color: string }> = [
  { key: "showShips", label: "Ships", icon: Ship, color: "text-sky-300" },
  { key: "showWaveHeatmap", label: "Waves", icon: Waves, color: "text-cyan-300" },
  { key: "showWeatherLayer", label: "Weather", icon: Cloud, color: "text-blue-300" },
  { key: "showDangerZones", label: "Alerts", icon: TriangleAlert, color: "text-orange-300" },
];

function flyTo(lat: number, lng: number, zoom: number) {
  const maps = (window as Window & { _leaflet_maps?: Record<string, { flyTo: Function }> })._leaflet_maps;
  Object.values(maps || {}).forEach(map => map.flyTo([lat, lng], zoom, { duration: 0.9 }));
}

export function MapControls({ onRefresh }: Props) {
  const [refreshing, setRefreshing] = useState(false);
  const [open, setOpen] = useState(true);
  const [regionsOpen, setRegionsOpen] = useState(false);
  const { map, setMapLayer, setMapCenter } = useStore();

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await onRefresh();
    } finally {
      window.setTimeout(() => setRefreshing(false), 500);
    }
  };

  return (
    <div className="absolute top-4 left-4 z-[1000] max-w-[calc(100vw-2rem)]">
      <section className={cn(
        "overflow-hidden rounded-2xl border border-white/10 bg-ocean-950/90 shadow-2xl shadow-black/40 backdrop-blur-xl transition-[width] duration-200",
        open ? "w-[276px]" : "w-auto"
      )} aria-label="Map tools">
        <div className="flex items-center gap-2 px-3 py-2.5 bg-gradient-to-r from-ocean-800/90 to-ocean-900/40">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-ocean-500/20 text-ocean-200 ring-1 ring-ocean-400/30">
            <Settings2 className="h-4 w-4" />
          </div>
          {open && <div className="min-w-0 flex-1">
            <p className="text-xs font-bold text-white">Map tools</p>
            <p className="text-[10px] text-ocean-400">Choose what you want to see</p>
          </div>}
          <button onClick={() => setOpen(value => !value)} className="rounded-lg p-1.5 text-ocean-300 hover:bg-white/10 hover:text-white"
            aria-label={open ? "Collapse map tools" : "Expand map tools"} title={open ? "Collapse map tools" : "Expand map tools"}>
            <ChevronDown className={cn("h-4 w-4 transition-transform", !open && "-rotate-90")} />
          </button>
        </div>

        {open && <div className="space-y-3 p-3 animate-fade-in">
          <div className="grid grid-cols-2 gap-2" aria-label="Map layers">
            {LAYERS.map(layer => {
              const Icon = layer.icon;
              const enabled = map[layer.key];
              return <button key={layer.key} onClick={() => setMapLayer(layer.key, !enabled)} aria-pressed={enabled}
                title={`${enabled ? "Hide" : "Show"} ${layer.label}`}
                className={cn("rounded-xl border p-2.5 text-left transition-all", enabled
                  ? "border-ocean-400/40 bg-ocean-500/20 text-white shadow-[inset_0_1px_0_rgba(255,255,255,.08)]"
                  : "border-white/8 bg-ocean-900/50 text-ocean-400 hover:border-ocean-500/35 hover:bg-ocean-800/70")}>
                <span className="mb-2 flex items-center justify-between">
                  <Icon className={cn("h-4 w-4", enabled ? layer.color : "text-ocean-600")} />
                  <span className={cn("h-2 w-2 rounded-full", enabled ? "bg-emerald-400 shadow-[0_0_8px_#34d399]" : "bg-ocean-700")} />
                </span>
                <span className="block text-xs font-semibold">{layer.label}</span>
                <span className="mt-0.5 block text-[9px] leading-tight text-ocean-500">{enabled ? "Visible" : "Hidden"}</span>
              </button>;
            })}
          </div>

          <div className="border-t border-white/8 pt-3">
            <button onClick={() => setRegionsOpen(value => !value)} className="flex w-full items-center gap-2 rounded-xl bg-ocean-800/55 px-3 py-2 text-left text-xs font-semibold text-ocean-200 hover:bg-ocean-700/70 hover:text-white" aria-expanded={regionsOpen}>
              <Globe2 className="h-4 w-4 text-ocean-400" /> Jump to a region
              <ChevronDown className={cn("ml-auto h-3.5 w-3.5 transition-transform", regionsOpen && "rotate-180")} />
            </button>
            {regionsOpen && <div className="mt-2 grid grid-cols-2 gap-1 animate-fade-in">
              {QUICK_REGIONS.map(region => <button key={region.name} onClick={() => { flyTo(region.lat, region.lng, region.zoom); setRegionsOpen(false); }} className="rounded-lg px-2 py-1.5 text-left text-[10px] text-ocean-300 hover:bg-ocean-700/70 hover:text-white">{region.name}</button>)}
            </div>}
          </div>

          <div className="grid grid-cols-2 gap-2">
            <button onClick={handleRefresh} className="btn-secondary !px-2.5 !py-2" title="Refresh live data"><RefreshCw className={cn("h-3.5 w-3.5", refreshing && "animate-spin")} />Refresh</button>
            <button onClick={() => { setMapCenter([60, 20], 2); flyTo(20, 60, 2); }} className="btn-secondary !px-2.5 !py-2" title="Return to global map view"><RotateCcw className="h-3.5 w-3.5" />Reset view</button>
          </div>
        </div>}
      </section>
    </div>
  );
}

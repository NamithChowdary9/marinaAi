"use client";

import { useEffect, useRef, useState } from "react";
import { useStore } from "@/store/useStore";
import { useQuery } from "@tanstack/react-query";
import { shipsApi, weatherApi } from "@/services/api";
import { cn } from "@/utils/cn";
import { MapControls } from "./MapControls";
import { MapLegend } from "./MapLegend";
import { DashboardOverlay } from "../dashboard/DashboardOverlay";
import { WeatherPanel } from "../weather/WeatherPanel";
import { RoutePlanner } from "./RoutePlanner";
import { AnalyticsPanel } from "../dashboard/AnalyticsPanel";
import { AlertsPanel } from "../alerts/AlertsPanel";
import type { Vessel } from "@/types";
import { vesselTypeIcon } from "@/utils/formatters";
import { MOCK_VESSELS } from "@/data/mockVessels";

const VESSEL_COLORS: Record<string, string> = {
  Cargo: "#3a8fd4", Tanker: "#f59e0b", Fishing: "#10b981",
  Passenger: "#a78bfa", Naval: "#ef4444", Sailing: "#34d399", default: "#94a3b8",
};

export default function MarineMap() {
  const mapDivRef = useRef<HTMLDivElement>(null);
  const mapRef    = useRef<any>(null);
  const leafletRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const circlesRef = useRef<any[]>([]);
  const heatmapMarkersRef = useRef<any[]>([]);
  const [mapReady, setMapReady] = useState(false);

  const { map: mapState, setMapCenter, setSelectedVessel, vessels, dangerZones, activeTab } = useStore();

  const { data: vesselsData, refetch } = useQuery({
    queryKey: ["vessels"],
    queryFn: () => shipsApi.getAll({ limit: 500 }),
    refetchInterval: 60_000,
  });

  const { data: heatmapData } = useQuery({
    queryKey: ["wave-heatmap"],
    queryFn: weatherApi.getWaveHeatmap,
    refetchInterval: 120_000,
    enabled: mapReady,
  });

  // ─── Init map once on mount ───────────────────────────────────────────────
  useEffect(() => {
    if (mapRef.current || !mapDivRef.current) return;

    let cancelled = false;

    import("leaflet").then((L) => {
      if (cancelled || !mapDivRef.current) return;

      leafletRef.current = L;

      // Clear any stale Leaflet ID so re-init works
      if ((mapDivRef.current as any)._leaflet_id) {
        delete (mapDivRef.current as any)._leaflet_id;
      }

      const map = L.map(mapDivRef.current!, {
        center: [20.0, 60.0],
        zoom: 2,
        zoomControl: false,
        attributionControl: true,
        minZoom: 2,
      });

      L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        {
          attribution: 'Tiles &copy; <a href="https://www.esri.com/">Esri</a>',
          maxZoom: 16,
        }
      ).addTo(map);

      // Labels layer on top
      L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}",
        { maxZoom: 16, opacity: 0.8 }
      ).addTo(map);

      L.control.zoom({ position: "bottomright" }).addTo(map);

      map.on("moveend", () => {
        const c = map.getCenter();
        setMapCenter([c.lng, c.lat], map.getZoom());
      });

      mapRef.current = map;
      setMapReady(true);

      requestAnimationFrame(() => map.invalidateSize());
    });

    return () => {
      cancelled = true;
      markersRef.current.forEach(m => m.remove());
      circlesRef.current.forEach(c => c.remove());
      heatmapMarkersRef.current.forEach(m => m.remove());
      markersRef.current = [];
      circlesRef.current = [];
      heatmapMarkersRef.current = [];

      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
      setMapReady(false);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ─── Invalidate map size when tab returns to map ──────────────────────────
  useEffect(() => {
    if (activeTab === "map" && mapRef.current) {
      requestAnimationFrame(() => {
        mapRef.current?.invalidateSize({ pan: false });
        setTimeout(() => mapRef.current?.invalidateSize({ pan: false }), 150);
      });
    }
  }, [activeTab]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady || typeof ResizeObserver === "undefined" || !mapDivRef.current) return;

    const observer = new ResizeObserver(() => {
      requestAnimationFrame(() => map.invalidateSize({ pan: false }));
    });
    observer.observe(mapDivRef.current);

    return () => observer.disconnect();
  }, [mapReady]);

  // ─── Vessel markers ───────────────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    const L = leafletRef.current;
    if (!map || !L || !mapReady) return;

    markersRef.current.forEach(m => m.remove());
    markersRef.current = [];

    if (!mapState.showShips) return;

    const list: Vessel[] =
      (vesselsData?.vessels?.length ?? 0) > 0
        ? vesselsData!.vessels
        : vessels.length > 0
        ? vessels
        : MOCK_VESSELS;

    list.forEach((v) => {
      if (!v.latitude || !v.longitude) return;
      const color = VESSEL_COLORS[v.vessel_type] || VESSEL_COLORS.default;

      // Glow ring color by risk level
      const glowColor =
        v.risk_level === "critical" ? "#ef4444" :
        v.risk_level === "high"     ? "#f97316" :
        v.risk_level === "medium"   ? "#f59e0b" : color;

      const svg = `<svg width="26" height="26" viewBox="0 0 26 26" xmlns="http://www.w3.org/2000/svg">
        <circle cx="13" cy="13" r="12" fill="${glowColor}" fill-opacity="0.18" stroke="${glowColor}" stroke-width="1" stroke-opacity="0.5"/>
        <circle cx="13" cy="13" r="8" fill="${color}" fill-opacity="0.95" stroke="white" stroke-width="1.8"/>
        <polygon points="13,4 10,14 13,12 16,14" fill="white" fill-opacity="0.95"
          transform="rotate(${v.course || 0},13,13)"/>
      </svg>`;

      const icon = L.divIcon({ html: svg, iconSize: [26, 26], iconAnchor: [13, 13], className: "" });
      const marker = L.marker([v.latitude, v.longitude], { icon })
        .addTo(map)
        .bindPopup(buildPopup(v), { maxWidth: 280 })
        .on("click", () => setSelectedVessel(v));

      markersRef.current.push(marker);
    });
  }, [mapReady, mapState.showShips, vesselsData, vessels, setSelectedVessel]);

  // ─── Danger zones ─────────────────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    const L = leafletRef.current;
    if (!map || !L || !mapReady) return;

    circlesRef.current.forEach(c => c.remove());
    circlesRef.current = [];

    if (!mapState.showDangerZones) return;

    dangerZones.filter(z => z.latitude != null && z.longitude != null).forEach(z => {
      const border = z.color === "red" ? "#ef4444" : z.color === "orange" ? "#f97316" : "#f59e0b";
      const fill   = z.color === "red" ? "rgba(239,68,68,0.2)" : z.color === "orange" ? "rgba(249,115,22,0.2)" : "rgba(245,158,11,0.15)";
      const c = L.circle([z.latitude!, z.longitude!], {
        radius: 180_000,
        fillColor: fill, fillOpacity: 1,
        color: border, weight: 2, opacity: 0.8,
      }).addTo(map).bindPopup(
        `<b style="color:#e2e8f0">⚠️ ${z.region}</b><br>
         <span style="color:#94a3b8">${z.primary_threat.replace("_", " ")}</span>
         ${z.wave_height_m ? `<br><span style="color:#94a3b8">Wave: ${z.wave_height_m.toFixed(1)}m</span>` : ""}`
      );
      circlesRef.current.push(c);
    });
  }, [mapReady, mapState.showDangerZones, dangerZones]);

  // ─── Wave heatmap ─────────────────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    const L = leafletRef.current;
    if (!map || !L || !mapReady) return;

    heatmapMarkersRef.current.forEach(m => m.remove());
    heatmapMarkersRef.current = [];

    if (!mapState.showWaveHeatmap || !heatmapData?.heatmap_points) return;

    heatmapData.heatmap_points.filter(p => p.lat && p.lon).forEach(p => {
      const h = p.wave_height_m || 0;
      const color = h > 6 ? "#7c3aed" : h > 4 ? "#ef4444" : h > 2 ? "#f59e0b" : "#10b981";
      const r = Math.min(30, 10 + h * 3);
      const icon = L.divIcon({
        html: `<div style="width:${r*2}px;height:${r*2}px;border-radius:50%;background:${color};opacity:0.45;"></div>`,
        iconSize: [r*2, r*2], iconAnchor: [r, r], className: "",
      });
      const marker = L.marker([p.lat, p.lon], { icon }).addTo(map)
        .bindTooltip(`${p.region}: ${h.toFixed(1)}m`, { permanent: false });
      heatmapMarkersRef.current.push(marker);
    });
  }, [mapReady, mapState.showWaveHeatmap, heatmapData]);

  // ─── Tab routing ──────────────────────────────────────────────────────────
  // Keep map mounted but hidden — fixes blank map on tab return
  return (
    <>
      <div
        className={cn(
          "absolute inset-0 min-h-0 w-full h-full transition-opacity duration-150",
          activeTab === "map"
            ? "z-0 opacity-100 pointer-events-auto"
            : "z-0 opacity-0 pointer-events-none"
        )}
        aria-hidden={activeTab !== "map"}
      >
        <div ref={mapDivRef} className="absolute inset-0 w-full h-full z-0" />
        {mapReady && (
          <>
            <MapControls onRefresh={() => refetch()} />
            <MapLegend />
            <DashboardOverlay />
          </>
        )}
      </div>

      {/* Other tab panels */}
      <div
        className={cn(
          "relative z-10 flex flex-col flex-1 min-h-0 overflow-hidden",
          activeTab === "map" && "hidden"
        )}
      >
        {activeTab === "weather"   && <WeatherPanel />}
        {activeTab === "routes"    && <RoutePlanner />}
        {activeTab === "analytics" && <AnalyticsPanel />}
        {activeTab === "alerts"    && <AlertsPanel />}
      </div>
    </>
  );
}

function buildPopup(v: Vessel): string {
  const rc: Record<string, string> = {
    safe: "#10b981", low: "#34d399", medium: "#f59e0b", high: "#f97316", critical: "#ef4444",
  };
  const color = rc[v.risk_level || "safe"] || "#94a3b8";
  return `<div style="font-family:Inter,sans-serif;min-width:200px;color:#e2e8f0">
    <div style="font-weight:700;font-size:14px;margin-bottom:8px;color:#fff">
      ${vesselTypeIcon(v.vessel_type)} ${v.name || "Unknown"}
    </div>
    <table style="width:100%;font-size:12px">
      <tr><td style="color:#94a3b8;padding:1px 4px">MMSI</td><td style="color:#cbd5e1">${v.mmsi}</td></tr>
      <tr><td style="color:#94a3b8;padding:1px 4px">Type</td><td style="color:#cbd5e1">${v.vessel_type || "—"}</td></tr>
      <tr><td style="color:#94a3b8;padding:1px 4px">Flag</td><td style="color:#cbd5e1">${v.flag || "—"}</td></tr>
      <tr><td style="color:#94a3b8;padding:1px 4px">Speed</td><td style="color:#cbd5e1">${v.speed?.toFixed(1) || "0"} kts</td></tr>
      <tr><td style="color:#94a3b8;padding:1px 4px">Course</td><td style="color:#cbd5e1">${v.course?.toFixed(0) || "0"}°</td></tr>
      <tr><td style="color:#94a3b8;padding:1px 4px">Dest</td><td style="color:#cbd5e1">${v.destination || "—"}</td></tr>
      <tr><td style="color:#94a3b8;padding:1px 4px">Risk</td>
        <td style="color:${color};font-weight:600;font-size:11px;text-transform:uppercase">
          ${v.risk_level || "safe"}
        </td>
      </tr>
    </table>
  </div>`;
}

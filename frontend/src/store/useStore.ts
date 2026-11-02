/**
 * Global Zustand store — app-wide state.
 */

import { create } from "zustand";
import type { Vessel, Alert, DangerZone, DashboardStats } from "@/types";

interface MapState {
  center: [number, number];  // [lng, lat]
  zoom: number;
  showShips: boolean;
  showWaveHeatmap: boolean;
  showWeatherLayer: boolean;
  showDangerZones: boolean;
  showRoutes: boolean;
}

interface AppStore {
  // Map
  map: MapState;
  setMapCenter: (center: [number, number], zoom?: number) => void;
  setMapLayer: (key: keyof Pick<MapState, "showShips" | "showWaveHeatmap" | "showWeatherLayer" | "showDangerZones" | "showRoutes">, value: boolean) => void;

  // Selected vessel
  selectedVessel: Vessel | null;
  setSelectedVessel: (vessel: Vessel | null) => void;

  // Vessels
  vessels: Vessel[];
  setVessels: (vessels: Vessel[]) => void;

  // Alerts
  alerts: Alert[];
  setAlerts: (alerts: Alert[]) => void;
  activeAlertCount: number;

  // Danger zones
  dangerZones: DangerZone[];
  setDangerZones: (zones: DangerZone[]) => void;

  // Dashboard stats
  dashboardStats: DashboardStats | null;
  setDashboardStats: (stats: DashboardStats) => void;

  // UI
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  activeTab: "map" | "weather" | "chat" | "routes" | "analytics" | "alerts";
  setActiveTab: (tab: AppStore["activeTab"]) => void;

  // Chat panel
  chatOpen: boolean;
  setChatOpen: (open: boolean) => void;

  // Connection status
  wsConnected: boolean;
  setWsConnected: (connected: boolean) => void;
  backendOnline: boolean;
  setBackendOnline: (online: boolean) => void;
}

export const useStore = create<AppStore>((set, get) => ({
  // Map defaults — centered on Indian Ocean
  map: {
    center: [60.0, 20.0],   // [lng, lat] — centered on world ocean belt
    zoom: 2,
    showShips: true,
    showWaveHeatmap: true,
    showWeatherLayer: false,
    showDangerZones: true,
    showRoutes: false,
  },

  setMapCenter: (center, zoom) =>
    set(s => ({ map: { ...s.map, center, zoom: zoom ?? s.map.zoom } })),

  setMapLayer: (key, value) =>
    set(s => ({ map: { ...s.map, [key]: value } })),

  // Vessel state
  selectedVessel: null,
  setSelectedVessel: vessel => set({ selectedVessel: vessel }),

  vessels: [],
  setVessels: vessels => set({ vessels }),

  // Alert state
  alerts: [],
  setAlerts: alerts => set({ alerts, activeAlertCount: alerts.length }),
  activeAlertCount: 0,

  // Danger zones
  dangerZones: [],
  setDangerZones: dangerZones => set({ dangerZones }),

  // Dashboard
  dashboardStats: null,
  setDashboardStats: dashboardStats => set({ dashboardStats }),

  // UI
  sidebarOpen: false,   // start collapsed — map fills full width like MarineTraffic
  setSidebarOpen: sidebarOpen => set({ sidebarOpen }),

  activeTab: "map",
  setActiveTab: activeTab => set({ activeTab }),

  chatOpen: false,
  setChatOpen: chatOpen => set({ chatOpen }),

  // Connection
  wsConnected: false,
  setWsConnected: wsConnected => set({ wsConnected }),
  backendOnline: false,
  setBackendOnline: backendOnline => set({ backendOnline }),
}));

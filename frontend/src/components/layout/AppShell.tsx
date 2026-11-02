"use client";

import { useEffect } from "react";
import { Navbar } from "./Navbar";
import { Sidebar } from "./Sidebar";
import { useStore } from "@/store/useStore";
import { alertsApi, analyticsApi, shipsApi } from "@/services/api";
import { useQuery } from "@tanstack/react-query";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { VesselDetailPanel } from "@/components/map/VesselDetailPanel";
import { MOCK_VESSELS } from "@/data/mockVessels";

interface Props {
  children: React.ReactNode;
}

export function AppShell({ children }: Props) {
  const {
    sidebarOpen, setSidebarOpen,
    setAlerts, setDangerZones, setDashboardStats, setVessels, setBackendOnline,
    chatOpen, selectedVessel,
  } = useStore();

  const { data: dashboard } = useQuery({
    queryKey: ["dashboard"],
    queryFn: analyticsApi.getDashboard,
    refetchInterval: 60_000,
  });
  const { data: alertsData } = useQuery({
    queryKey: ["alerts"],
    queryFn: alertsApi.getActive,
    refetchInterval: 30_000,
  });
  const { data: zonesData } = useQuery({
    queryKey: ["danger-zones"],
    queryFn: alertsApi.getDangerZones,
    refetchInterval: 60_000,
  });
  const { data: vesselsData } = useQuery({
    queryKey: ["vessels"],
    queryFn: () => shipsApi.getAll({ limit: 500 }),
    refetchInterval: 60_000,
  });

  useEffect(() => {
    if (dashboard) { setDashboardStats(dashboard); setBackendOnline(true); }
  }, [dashboard, setDashboardStats, setBackendOnline]);

  useEffect(() => {
    if (alertsData?.alerts) setAlerts(alertsData.alerts);
  }, [alertsData, setAlerts]);

  useEffect(() => {
    if (zonesData?.danger_zones) setDangerZones(zonesData.danger_zones);
  }, [zonesData, setDangerZones]);

  // Inject vessels — real API data when available, mock fallback when backend is offline
  useEffect(() => {
    if (vesselsData?.vessels && vesselsData.vessels.length > 0) {
      setVessels(vesselsData.vessels);
    } else {
      setVessels(MOCK_VESSELS);
    }
  }, [vesselsData, setVessels]);

  return (
    /*
     * Root shell: full viewport, never scroll at document level.
     * h-screen + overflow-hidden pins everything inside.
     */
    <div className="flex flex-col h-screen overflow-hidden bg-ocean-950" style={{ background: "#030d1a" }}>

      {/* Fixed-height top nav */}
      <Navbar />

      {/*
       * Content row: flex-1 so it fills the remaining height after the navbar.
       * overflow-hidden here is intentional — each child manages its own scroll.
       */}
      <div className="flex flex-1 min-h-0 overflow-hidden relative">

        {/* Sidebar — scrolls internally via overflow-y-auto */}
        <Sidebar open={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />

        {/*
         * Main area:
         *  - For the map tab: position absolute children fill it (overflow-hidden is fine)
         *  - For panel tabs (Weather, Analytics, etc.): they render as
         *    flex-1 overflow-y-auto children and need min-h-0 to work inside a flex parent
         */}
        <main className="flex flex-col flex-1 min-h-0 overflow-hidden relative">
          {children}
        </main>

        {/*
         * Chat panel — slides in from the right.
         * absolute + inset-y-0 gives it the full content-row height.
         * The inner ChatPanel is flex-col h-full so its message list can scroll.
         */}
        {chatOpen && (
          <div className="absolute right-0 top-0 bottom-0 w-96 z-30 flex flex-col">
            <ChatPanel />
          </div>
        )}

        {/* Vessel detail card — floats over the map (map tab only) */}
        {selectedVessel && !chatOpen && (
          <div className="absolute right-4 bottom-4 w-96 z-20">
            <VesselDetailPanel />
          </div>
        )}
      </div>
    </div>
  );
}

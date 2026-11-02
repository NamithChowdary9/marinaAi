"use client";

import { useStore } from "@/store/useStore";
import {
  Anchor, MessageSquare, Bell,
  Map, Cloud, Navigation, BarChart2, AlertTriangle, Radio,
} from "lucide-react";
import { cn } from "@/utils/cn";
import { useQuery } from "@tanstack/react-query";
import { healthApi } from "@/services/api";

const TABS = [
  { id: "map",       label: "Live Map",   icon: Map           },
  { id: "weather",   label: "Weather",    icon: Cloud         },
  { id: "routes",    label: "Routes",     icon: Navigation    },
  { id: "analytics", label: "Analytics",  icon: BarChart2     },
  { id: "alerts",    label: "Alerts",     icon: AlertTriangle },
] as const;

export function Navbar() {
  const {
    activeTab, setActiveTab, chatOpen, setChatOpen,
    activeAlertCount, sidebarOpen, setSidebarOpen,
  } = useStore();

  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: healthApi.check,
    refetchInterval: 30_000,
    retry: 1,
  });

  const isOnline = !!health;

  return (
    <nav
      className="h-14 shrink-0 flex items-center px-4 gap-3 z-50 select-none"
      style={{
        background: "linear-gradient(180deg, rgba(6,14,30,0.98) 0%, rgba(4,10,22,0.98) 100%)",
        borderBottom: "1px solid rgba(255,255,255,0.055)",
        boxShadow: "0 1px 0 rgba(26,110,194,0.08), 0 8px 32px rgba(0,0,0,0.6)",
      }}
    >
      {/* ── Logo ──────────────────────────────────────────────────────── */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="flex items-center gap-2.5 mr-1 group shrink-0"
        aria-label="Toggle sidebar"
      >
        <div
          className="w-8 h-8 rounded-xl flex items-center justify-center transition-transform group-hover:scale-105"
          style={{
            background: "linear-gradient(135deg, #1d7ad4 0%, #0f4080 100%)",
            boxShadow: "0 0 16px rgba(26,110,194,0.45), inset 0 1px 0 rgba(255,255,255,0.15)",
          }}
        >
          <Anchor className="w-4 h-4 text-white" />
        </div>
        <div className="hidden sm:block">
          <p className="text-sm font-extrabold text-white leading-none tracking-tight">MarineAI</p>
          <p className="text-[9px] font-semibold tracking-[0.2em] uppercase mt-0.5" style={{ color: "rgba(58,143,212,0.75)" }}>
            Maritime Intel
          </p>
        </div>
      </button>

      <div className="w-px h-5 shrink-0" style={{ background: "rgba(255,255,255,0.07)" }} />

      {/* ── Tabs ──────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-0.5 flex-1 overflow-x-auto" style={{ scrollbarWidth: "none" }}>
        {TABS.map(tab => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "relative flex items-center gap-1.5 px-3 h-9 rounded-xl text-xs font-semibold whitespace-nowrap shrink-0 transition-all duration-150",
                active ? "text-white" : "text-white/38 hover:text-white/70 hover:bg-white/[0.05]"
              )}
              style={active ? {
                background: "rgba(26,110,194,0.16)",
                boxShadow: "inset 0 0 0 1px rgba(26,110,194,0.28)",
              } : {}}
            >
              <Icon className="w-3.5 h-3.5 shrink-0" />
              <span className="hidden sm:block">{tab.label}</span>

              {/* Active underline */}
              {active && (
                <span
                  className="absolute bottom-0.5 left-3 right-3 h-[2px] rounded-full"
                  style={{ background: "linear-gradient(90deg, #3a8fd4, rgba(58,143,212,0.3))" }}
                />
              )}

              {/* Alert badge */}
              {tab.id === "alerts" && activeAlertCount > 0 && (
                <span
                  className="min-w-[16px] h-4 px-1 rounded-full text-[9px] font-bold flex items-center justify-center text-white"
                  style={{ background: "linear-gradient(135deg, #ef4444, #b91c1c)" }}
                >
                  {activeAlertCount > 9 ? "9+" : activeAlertCount}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* ── Right controls ─────────────────────────────────────────────── */}
      <div className="flex items-center gap-1.5 shrink-0">

        {/* Status */}
        <div
          className="hidden sm:flex items-center gap-1.5 px-2.5 h-7 rounded-full text-[10px] font-semibold"
          style={isOnline ? {
            background: "rgba(16,185,129,0.08)",
            border: "1px solid rgba(16,185,129,0.2)",
            color: "#34d399",
          } : {
            background: "rgba(239,68,68,0.08)",
            border: "1px solid rgba(239,68,68,0.2)",
            color: "#f87171",
          }}
        >
          <span
            className="w-1.5 h-1.5 rounded-full shrink-0"
            style={isOnline
              ? { background: "#10b981", boxShadow: "0 0 5px #10b981", animation: "pulse 2s infinite" }
              : { background: "#ef4444" }}
          />
          {isOnline ? "Live" : "Offline"}
        </div>

        {/* Agents */}
        <div
          className="hidden lg:flex items-center gap-1.5 px-2.5 h-7 rounded-full text-[10px] font-semibold"
          style={{
            background: "rgba(124,58,237,0.08)",
            border: "1px solid rgba(124,58,237,0.2)",
            color: "#c4b5fd",
          }}
        >
          <Radio className="w-3 h-3" style={{ color: "#a78bfa" }} />
          7 Agents
        </div>

        {/* Bell */}
        <button
          onClick={() => setActiveTab("alerts")}
          className="relative w-8 h-8 rounded-xl flex items-center justify-center text-white/35 hover:text-white/75 hover:bg-white/[0.07] transition-all"
          aria-label="Alerts"
        >
          <Bell className="w-4 h-4" />
          {activeAlertCount > 0 && (
            <span
              className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full"
              style={{ background: "#ef4444", boxShadow: "0 0 5px #ef4444" }}
            />
          )}
        </button>

        {/* AI Chat */}
        <button
          onClick={() => setChatOpen(!chatOpen)}
          className={cn(
            "flex items-center gap-1.5 px-3 h-8 rounded-xl text-xs font-bold transition-all",
            chatOpen ? "text-white" : "text-white/55 hover:text-white"
          )}
          style={chatOpen ? {
            background: "linear-gradient(135deg, #1a6ec2, #7c3aed)",
            boxShadow: "0 0 18px rgba(26,110,194,0.35)",
          } : {
            background: "rgba(255,255,255,0.06)",
            border: "1px solid rgba(255,255,255,0.09)",
          }}
        >
          <MessageSquare className="w-3.5 h-3.5 shrink-0" />
          <span>AI Chat</span>
        </button>
      </div>
    </nav>
  );
}

"use client";

import { useStore } from "@/store/useStore";
import { X, Anchor, Navigation, Wind, Waves, AlertTriangle, ExternalLink } from "lucide-react";
import { cn } from "@/utils/cn";
import { dangerLevelBg, vesselTypeIcon, formatKnots, compassDirection } from "@/utils/formatters";
import { useQuery } from "@tanstack/react-query";
import { shipsApi } from "@/services/api";

export function VesselDetailPanel() {
  const { selectedVessel, setSelectedVessel } = useStore();

  const { data: riskData, isLoading } = useQuery({
    queryKey: ["vessel-risk", selectedVessel?.mmsi],
    queryFn: () => shipsApi.getRisk(selectedVessel!.mmsi),
    enabled: !!selectedVessel,
  });

  if (!selectedVessel) return null;

  const risk = riskData?.risk_assessment;
  const riskScore = risk?.overall_risk_score ?? 0;
  const riskLevel = risk?.risk_level ?? selectedVessel.risk_level ?? "safe";

  return (
    <div className="card-glow animate-slide-up overflow-hidden">
      {/* Header */}
      <div className="flex items-start justify-between p-4 border-b border-ocean-700/30">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-ocean-700/50 flex items-center justify-center text-lg">
            {vesselTypeIcon(selectedVessel.vessel_type)}
          </div>
          <div>
            <h3 className="font-semibold text-white text-sm leading-tight">
              {selectedVessel.name || "Unknown Vessel"}
            </h3>
            <p className="text-ocean-400 text-xs mt-0.5">MMSI: {selectedVessel.mmsi}</p>
          </div>
        </div>
        <button
          onClick={() => setSelectedVessel(null)}
          className="p-1.5 rounded-lg text-ocean-400 hover:text-white hover:bg-ocean-700/50 transition-all"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Details grid */}
      <div className="p-4 space-y-3">
        <div className="grid grid-cols-2 gap-2 text-xs">
          {[
            { icon: <Anchor className="w-3 h-3" />, label: "Type",    value: selectedVessel.vessel_type || "—" },
            { icon: <span className="text-sm">🏳</span>,  label: "Flag",    value: selectedVessel.flag || "—" },
            { icon: <Navigation className="w-3 h-3" />, label: "Speed",  value: formatKnots(selectedVessel.speed || 0) },
            { icon: <span className="text-sm">🧭</span>, label: "Course", value: `${selectedVessel.course?.toFixed(0) || "0"}° ${compassDirection(selectedVessel.course || 0)}` },
            { icon: <span className="text-sm">📍</span>, label: "Lat",    value: selectedVessel.latitude?.toFixed(3) || "—" },
            { icon: <span className="text-sm">📍</span>, label: "Lon",    value: selectedVessel.longitude?.toFixed(3) || "—" },
          ].map(({ icon, label, value }) => (
            <div key={label} className="flex items-center gap-1.5 text-ocean-300">
              <span className="text-ocean-500 shrink-0">{icon}</span>
              <span className="text-ocean-500">{label}:</span>
              <span className="text-ocean-200 font-medium truncate">{value}</span>
            </div>
          ))}
        </div>

        {selectedVessel.destination && (
          <div className="flex items-center gap-2 text-xs text-ocean-300">
            <span>→ Destination:</span>
            <span className="text-white font-medium">{selectedVessel.destination}</span>
          </div>
        )}

        {/* Risk assessment */}
        <div className="border-t border-ocean-700/30 pt-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-ocean-400 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" /> AI Risk Score
            </span>
            {isLoading
              ? <span className="text-xs text-ocean-500 animate-pulse">Analyzing...</span>
              : (
                <span className={cn("badge text-xs", dangerLevelBg(riskLevel))}>
                  {riskScore.toFixed(0)}/100 — {riskLevel.toUpperCase()}
                </span>
              )
            }
          </div>

          {/* Risk bar */}
          <div className="h-1.5 bg-ocean-800 rounded-full overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all duration-500",
                riskScore > 75 ? "bg-red-500" :
                riskScore > 50 ? "bg-orange-500" :
                riskScore > 25 ? "bg-yellow-500" : "bg-emerald-500"
              )}
              style={{ width: `${riskScore}%` }}
            />
          </div>
        </div>

        {/* AI recommendation */}
        {riskData?.ai_summary && (
          <div className="bg-ocean-800/60 rounded-lg p-3 text-xs text-ocean-300 border border-ocean-700/30">
            <span className="text-ocean-400 font-medium">🤖 AI:</span>{" "}
            {riskData.ai_summary.substring(0, 200)}
            {riskData.ai_summary.length > 200 && "..."}
          </div>
        )}
      </div>
    </div>
  );
}

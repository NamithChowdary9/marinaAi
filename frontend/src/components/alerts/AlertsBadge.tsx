"use client";

import { useStore } from "@/store/useStore";
import { cn } from "@/utils/cn";

export function AlertsBadge() {
  const { alerts } = useStore();

  if (!alerts.length) return null;

  const topAlerts = alerts.slice(0, 3);

  return (
    <div className="space-y-1.5">
      {topAlerts.map((alert, i) => (
        <div
          key={i}
          className={cn(
            "px-2.5 py-2 rounded-lg border text-xs",
            alert.severity === "critical" || alert.severity === "extreme"
              ? "bg-red-500/10 border-red-500/20 text-red-300"
              : alert.severity === "warning" || alert.severity === "high"
              ? "bg-orange-500/10 border-orange-500/20 text-orange-300"
              : "bg-yellow-500/10 border-yellow-500/20 text-yellow-300"
          )}
        >
          <p className="font-medium truncate">{alert.title}</p>
          <p className="text-[10px] opacity-70 mt-0.5 truncate">{alert.description.substring(0, 60)}...</p>
        </div>
      ))}
    </div>
  );
}

"use client";

import dynamic from "next/dynamic";
import { AppShell } from "@/components/layout/AppShell";

// Dynamic import for map (no SSR — browser-only Mapbox)
const MarineMap = dynamic(() => import("@/components/map/MarineMap"), {
  ssr: false,
  loading: () => (
    <div className="flex-1 flex items-center justify-center bg-ocean-950">
      <div className="text-center space-y-4 animate-fade-in">
        <div className="text-6xl animate-wave">🌊</div>
        <p className="text-ocean-300 text-lg font-medium">Loading MarineAI...</p>
        <div className="flex gap-2 justify-center">
          {[0, 1, 2].map(i => (
            <div
              key={i}
              className="w-2 h-2 rounded-full bg-ocean-400"
              style={{ animation: `blink 1.4s ${i * 0.2}s infinite` }}
            />
          ))}
        </div>
      </div>
    </div>
  ),
});

export default function Home() {
  return (
    <AppShell>
      <MarineMap />
    </AppShell>
  );
}

"use client";

const WAVE_ITEMS = [
  { color: "#10b981", glow: "rgba(16,185,129,0.4)",  label: "Safe",     sub: "< 2 m"  },
  { color: "#f59e0b", glow: "rgba(245,158,11,0.4)",  label: "Moderate", sub: "2 – 4 m" },
  { color: "#ef4444", glow: "rgba(239,68,68,0.4)",   label: "Danger",   sub: "> 4 m"  },
  { color: "#7c3aed", glow: "rgba(124,58,237,0.4)",  label: "Critical", sub: "> 6 m"  },
];

const VESSEL_ITEMS = [
  { color: "#3a8fd4", label: "Cargo"     },
  { color: "#f59e0b", label: "Tanker"    },
  { color: "#10b981", label: "Fishing"   },
  { color: "#a78bfa", label: "Passenger" },
  { color: "#ef4444", label: "Naval"     },
];

export function MapLegend() {
  return (
    <div
      className="absolute bottom-16 left-4 z-10 rounded-2xl px-4 py-3.5 min-w-[195px]"
      style={{
        background: "rgba(4,14,31,0.82)",
        backdropFilter: "blur(14px)",
        WebkitBackdropFilter: "blur(14px)",
        border: "1px solid rgba(255,255,255,0.07)",
        boxShadow: "0 8px 32px rgba(0,0,0,0.5),inset 0 1px 0 rgba(255,255,255,0.05)",
      }}
    >
      {/* Wave height */}
      <p className="text-[9px] font-bold tracking-[0.18em] uppercase mb-2.5" style={{ color: "rgba(255,255,255,0.3)" }}>
        Wave Height
      </p>
      <div className="space-y-1.5 mb-3">
        {WAVE_ITEMS.map(item => (
          <div key={item.label} className="flex items-center gap-2.5">
            <span
              className="w-3 h-3 rounded-sm shrink-0"
              style={{ background: item.color, boxShadow: `0 0 6px ${item.glow}` }}
            />
            <span className="text-xs font-medium flex-1" style={{ color: "rgba(255,255,255,0.65)" }}>
              {item.label}
            </span>
            <span className="text-[10px]" style={{ color: "rgba(255,255,255,0.28)" }}>
              {item.sub}
            </span>
          </div>
        ))}
      </div>

      <div className="mb-3" style={{ height: 1, background: "rgba(255,255,255,0.07)" }} />

      {/* Vessels */}
      <p className="text-[9px] font-bold tracking-[0.18em] uppercase mb-2.5" style={{ color: "rgba(255,255,255,0.3)" }}>
        Vessels
      </p>
      <div className="space-y-1.5">
        {VESSEL_ITEMS.map(item => (
          <div key={item.label} className="flex items-center gap-2.5">
            {/* Mini vessel SVG matching the actual map marker */}
            <svg width="14" height="14" viewBox="0 0 26 26" className="shrink-0">
              <circle cx="13" cy="13" r="12" fill={item.color} fillOpacity="0.18" stroke={item.color} strokeWidth="1" strokeOpacity="0.45" />
              <circle cx="13" cy="13" r="8"  fill={item.color} fillOpacity="0.95" stroke="white"     strokeWidth="1.8" />
              <polygon points="13,4 10,14 13,12 16,14" fill="white" fillOpacity="0.9" />
            </svg>
            <span className="text-xs font-medium" style={{ color: "rgba(255,255,255,0.65)" }}>
              {item.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

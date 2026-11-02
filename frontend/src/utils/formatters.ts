import { DangerLevel } from "@/types";

export function formatWaveHeight(h: number): string {
  return `${h.toFixed(1)}m`;
}

export function formatWindSpeed(kmh: number): string {
  return `${kmh.toFixed(0)} km/h`;
}

export function formatKnots(knots: number): string {
  return `${knots.toFixed(1)} kts`;
}

export function formatDistance(nm: number): string {
  if (nm >= 1000) return `${(nm / 1000).toFixed(1)}k nm`;
  return `${nm.toFixed(0)} nm`;
}

export function formatDuration(hours: number): string {
  const h = Math.floor(hours);
  const m = Math.round((hours - h) * 60);
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

export function formatProbability(p: number): string {
  return `${(p * 100).toFixed(0)}%`;
}

export function dangerLevelColor(level: DangerLevel | string): string {
  switch (level) {
    case "safe":           return "text-emerald-400";
    case "moderate":       return "text-yellow-400";
    case "dangerous":      return "text-orange-400";
    case "very_dangerous": return "text-red-400";
    default:               return "text-gray-400";
  }
}

export function dangerLevelBg(level: DangerLevel | string): string {
  switch (level) {
    case "safe":           return "bg-emerald-500/20 border-emerald-500/40 text-emerald-300";
    case "moderate":       return "bg-yellow-500/20 border-yellow-500/40 text-yellow-300";
    case "dangerous":      return "bg-orange-500/20 border-orange-500/40 text-orange-300";
    case "very_dangerous": return "bg-red-500/20 border-red-500/40 text-red-300";
    default:               return "bg-gray-500/20 border-gray-500/40 text-gray-300";
  }
}

export function dangerLevelDot(level: DangerLevel | string): string {
  switch (level) {
    case "safe":           return "bg-emerald-400";
    case "moderate":       return "bg-yellow-400";
    case "dangerous":      return "bg-orange-400";
    case "very_dangerous": return "bg-red-400";
    default:               return "bg-gray-400";
  }
}

export function dangerEmoji(level: DangerLevel | string): string {
  switch (level) {
    case "safe":           return "🟢";
    case "moderate":       return "🟡";
    case "dangerous":      return "🟠";
    case "very_dangerous": return "🔴";
    default:               return "⚪";
  }
}

export function severityColor(severity: string): string {
  switch (severity) {
    case "extreme":
    case "critical": return "text-red-400";
    case "warning":
    case "high":     return "text-orange-400";
    case "medium":   return "text-yellow-400";
    case "low":      return "text-emerald-400";
    default:         return "text-gray-400";
  }
}

export function vesselTypeIcon(type: string): string {
  switch (type?.toLowerCase()) {
    case "cargo":     return "🚢";
    case "tanker":    return "🛢️";
    case "fishing":   return "🎣";
    case "passenger": return "🛳";
    case "naval":     return "⚓";
    case "sailing":   return "⛵";
    default:          return "🚤";
  }
}

export function compassDirection(deg: number): string {
  const dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"];
  return dirs[Math.round(deg / 22.5) % 16];
}

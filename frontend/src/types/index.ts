// ─── Vessel / Ship Types ─────────────────────────────────────────────────────

export interface Vessel {
  mmsi: string;
  name: string;
  vessel_type: string;
  flag: string;
  latitude: number;
  longitude: number;
  speed: number;
  course: number;
  heading?: number;
  status?: string;
  destination?: string;
  draught?: number;
  length?: number;
  risk_score?: number;
  risk_level?: "safe" | "low" | "medium" | "high" | "critical";
  ai_alert?: string;
  last_seen?: string;
}

export interface VesselDetail extends Vessel {
  callsign?: string;
  imo?: string;
  width?: number;
  eta?: string;
}

export interface VesselsResponse {
  total: number;
  vessels: Vessel[];
  stats: string[];
}

// ─── Weather Types ────────────────────────────────────────────────────────────

export interface WeatherData {
  temperature_c: number;
  feels_like_c?: number;
  humidity_pct: number;
  pressure_hpa: number;
  wind_speed_kmh: number;
  wind_direction_deg: number;
  visibility_km: number;
  weather_condition: string;
  weather_description?: string;
  precipitation_mm?: number;
  wave_height_m: number;
  wave_direction_deg?: number;
  wave_period_s?: number;
  wave_forecast_6h?: number;
  wave_forecast_24h?: number;
  wave_forecast_72h?: number;
}

export interface GlobalWeatherResponse {
  [region: string]: WeatherData;
}

// ─── Ocean / Wave Types ───────────────────────────────────────────────────────

export type DangerLevel = "safe" | "moderate" | "dangerous" | "very_dangerous";

export interface WaveData {
  latitude: number;
  longitude: number;
  wave_height_m: number;
  wave_direction_deg: number;
  wave_period_s: number;
  swell_height_m?: number;
  current_velocity_ms?: number;
  current_direction_deg?: number;
  danger_level: DangerLevel;
  wave_forecast: {
    "6h": number;
    "12h": number;
    "24h": number;
    "48h": number;
    "72h": number;
  };
}

export interface HeatmapPoint {
  lat: number;
  lon: number;
  wave_height_m: number;
  danger_level: DangerLevel;
  region: string;
}

// ─── Alert Types ──────────────────────────────────────────────────────────────

export type AlertSeverity = "low" | "medium" | "warning" | "high" | "critical" | "extreme";
export type AlertType = "storm" | "wave" | "collision" | "sos" | "cyclone";

export interface Alert {
  type: AlertType;
  severity: AlertSeverity;
  title: string;
  description: string;
  region?: string;
  latitude?: number;
  longitude?: number;
  wave_height_m?: number;
  storm_data?: Record<string, unknown>;
}

export interface AlertsResponse {
  total: number;
  alerts: Alert[];
}

export interface DangerZone {
  region: string;
  latitude?: number;
  longitude?: number;
  danger_level: DangerLevel;
  primary_threat: string;
  wave_height_m?: number;
  wind_speed_kmh?: number;
  color: "red" | "yellow" | "orange";
}

// ─── ML Prediction Types ──────────────────────────────────────────────────────

export interface WavePrediction {
  "6h": number;
  "24h": number;
  "72h": number;
  confidence: number;
  model: string;
}

export interface StormPrediction {
  storm_probability_6h: number;
  storm_probability_24h: number;
  storm_probability_72h: number;
  category: string;
  severity: string;
  wind_speed_kmh: number;
  pressure_hpa: number;
  should_alert: boolean;
}

export interface WeatherWithPredictions {
  location: { lat: number; lon: number };
  weather: WeatherData;
  ocean: WaveData;
  ml_wave_prediction: WavePrediction;
  ml_storm_prediction: StormPrediction;
  danger_level: DangerLevel;
}

// ─── Route Types ──────────────────────────────────────────────────────────────

export interface RouteWaypoint {
  lat: number;
  lon: number;
  name: string;
}

export interface RouteOption {
  waypoints: RouteWaypoint[];
  distance_nm: number;
  duration_h: number;
  risk_score: number;
  description: string;
  fuel_savings_pct?: number;
  directions?: string[];
}

export interface RouteResult {
  routes: {
    safe: RouteOption;
    fast: RouteOption;
    fuel_efficient: RouteOption;
  };
  recommended_route: "safe" | "fast" | "fuel_efficient";
  reasoning: string;
  hazards_on_path: string[];
  departure_advice: string;
  agent_recommendation: string;
}

export interface DepartureCheck {
  port: string;
  vessel_type: string;
  departure_time?: string;
  is_safe_to_depart: boolean;
  safety_verdict: string;
  risk_score: number;
  ai_explanation: string;
  weather: Record<string, unknown>;
  wave: Record<string, unknown>;
  agents_used: string[];
}

export type VoyageTwinScenario = "depart_later" | "slow_speed" | "avoid_storm" | "engine_failure" | "ais_loss";

export interface VoyageTwinPlan {
  id: "current" | "simulated" | "eco";
  label: string;
  route: RouteOption & { fuel_index: number };
  summary: string;
  why: string;
}

export interface VoyageTwinResult {
  voyage: { origin: string; destination: string; vessel_type?: string };
  scenario: VoyageTwinScenario;
  plans: VoyageTwinPlan[];
  recommended_plan_id: string;
  recommendation: string;
  hazards: string[];
  data_note: string;
}

// ─── Chat Types ───────────────────────────────────────────────────────────────

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp?: Date;
  agents_used?: string[];
  weather_data?: Record<string, unknown>;
  wave_data?: Record<string, unknown>;
  risk_assessment?: Record<string, unknown>;
}

export interface ChatResponse {
  answer: string;
  agents_used: string[];
  weather_data?: Record<string, unknown>;
  wave_data?: Record<string, unknown>;
  risk_assessment?: Record<string, unknown>;
  route_data?: Record<string, unknown>;
}

// ─── Analytics / Dashboard Types ─────────────────────────────────────────────

export interface DashboardStats {
  vessels: {
    total_tracked: number;
    busiest_corridors: string[];
  };
  ocean_conditions: {
    safe_regions: number;
    moderate_regions: number;
    dangerous_regions: number;
    highest_wave_region: string;
    highest_wave_height_m: number;
  };
  wave_summary: Record<string, {
    wave_height_m: number;
    danger_level: DangerLevel;
    lat: number;
    lon: number;
  }>;
  ai_agents_active: number;
  system_status: string;
}

// ─── Agent Types ──────────────────────────────────────────────────────────────

export interface AgentStatus {
  name: string;
  status: "active" | "idle" | "error";
  description: string;
}

export interface AgentResponse {
  answer: string;
  weather_data?: Record<string, unknown>;
  wave_data?: Record<string, unknown>;
  ship_data?: Record<string, unknown>;
  route_data?: Record<string, unknown>;
  risk_assessment?: Record<string, unknown>;
  agents_used: string[];
}

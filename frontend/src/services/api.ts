/**
 * API service — all communication with the MarineAI backend.
 */

import axios from "axios";
import type {
  Vessel, VesselsResponse, WeatherData, WeatherWithPredictions,
  GlobalWeatherResponse, WaveData, HeatmapPoint, AlertsResponse,
  DangerZone, DashboardStats, ChatResponse, ChatMessage,
  RouteResult, DepartureCheck, AgentResponse, AgentStatus, VoyageTwinResult, VoyageTwinScenario,
} from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { "Content-Type": "application/json" },
});

// ─── Ships ───────────────────────────────────────────────────────────────────

export const shipsApi = {
  getAll: (params?: {
    lat_min?: number; lat_max?: number;
    lon_min?: number; lon_max?: number;
    vessel_type?: string; limit?: number;
  }) =>
    api.get<VesselsResponse>("/api/ships/", { params }).then(r => r.data),

  getOne: (mmsi: string) =>
    api.get<Vessel>(`/api/ships/${mmsi}`).then(r => r.data),

  getRisk: (mmsi: string) =>
    api.get(`/api/ships/${mmsi}/risk`).then(r => r.data),

  searchArea: (lat: number, lon: number, radius = 100) =>
    api.get(`/api/ships/area/search`, { params: { lat, lon, radius } }).then(r => r.data),

  getCollisionRisks: (lat: number, lon: number, radius = 50) =>
    api.get(`/api/ships/collision/risks`, { params: { lat, lon, radius } }).then(r => r.data),
};

// ─── Weather ─────────────────────────────────────────────────────────────────

export const weatherApi = {
  getCurrent: (lat: number, lon: number) =>
    api.get<WeatherWithPredictions>("/api/weather/current", { params: { lat, lon } }).then(r => r.data),

  getGlobal: () =>
    api.get<GlobalWeatherResponse>("/api/weather/global").then(r => r.data),

  getWavesGlobal: () =>
    api.get<Record<string, WaveData>>("/api/weather/waves/global").then(r => r.data),

  getWaveHeatmap: () =>
    api.get<{ heatmap_points: HeatmapPoint[]; total: number }>("/api/weather/waves/heatmap").then(r => r.data),

  getStormForecast: (lat: number, lon: number) =>
    api.get("/api/weather/storm/forecast", { params: { lat, lon } }).then(r => r.data),
};

// ─── Alerts ───────────────────────────────────────────────────────────────────

export const alertsApi = {
  getActive: () =>
    api.get<AlertsResponse>("/api/alerts/active").then(r => r.data),

  getDangerZones: () =>
    api.get<{ total: number; danger_zones: DangerZone[] }>("/api/alerts/danger-zones").then(r => r.data),
};

// ─── Routes ───────────────────────────────────────────────────────────────────

export const routesApi = {
  optimize: (body: {
    origin_lat: number; origin_lon: number; origin_name: string;
    destination_lat: number; destination_lon: number; destination_name: string;
    vessel_type?: string; preferred_route?: string;
  }) =>
    api.post("/api/routes/optimize", body).then(r => r.data),

  departureCheck: (port: string, lat: number, lon: number, vessel_type = "fishing", departure_time?: string) =>
    api.get<DepartureCheck>("/api/routes/departure-check", {
      params: { port, lat, lon, vessel_type, departure_time },
    }).then(r => r.data),

  voyageTwin: (body: {
    origin_lat: number; origin_lon: number; origin_name: string;
    destination_lat: number; destination_lon: number; destination_name: string;
    vessel_type?: string; preferred_route?: string;
    scenario: VoyageTwinScenario; departure_offset_h?: number; speed_knots?: number;
  }) => api.post<VoyageTwinResult>("/api/routes/voyage-twin", body).then(r => r.data),
};

// ─── Chat ─────────────────────────────────────────────────────────────────────

export const chatApi = {
  send: (body: {
    message: string;
    history?: Array<{ role: string; content: string }>;
    location?: { lat: number; lon: number; name?: string };
    vessel_mmsi?: string;
    use_agents?: boolean;
  }) =>
    api.post<ChatResponse>("/api/chat/", body).then(r => r.data),

  quick: (message: string) =>
    api.post<{ answer: string }>("/api/chat/quick", { message }).then(r => r.data),
};

// ─── Analytics ───────────────────────────────────────────────────────────────

export const analyticsApi = {
  getDashboard: () =>
    api.get<DashboardStats>("/api/analytics/dashboard").then(r => r.data),

  getOceanRegions: () =>
    api.get<Record<string, WaveData>>("/api/analytics/ocean-regions").then(r => r.data),
};

// ─── Agents ───────────────────────────────────────────────────────────────────

export const agentsApi = {
  run: (query: string, location?: { lat: number; lon: number }, vessel_mmsi?: string) =>
    api.post<AgentResponse>("/api/agents/run", { query, location, vessel_mmsi }).then(r => r.data),

  getStatus: () =>
    api.get<{ agents: AgentStatus[]; total_agents: number; framework: string; llm: string }>
      ("/api/agents/status").then(r => r.data),
};

// ─── Health ───────────────────────────────────────────────────────────────────

export const healthApi = {
  check: () => api.get("/health").then(r => r.data),
};

export default api;

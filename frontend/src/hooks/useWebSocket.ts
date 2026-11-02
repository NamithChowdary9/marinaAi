"use client";

import { useEffect, useRef, useCallback } from "react";
import { useStore } from "@/store/useStore";
import type { Vessel } from "@/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

interface WSMessage {
  type: "snapshot" | "position_update" | "heartbeat" | "alert";
  vessels?: Vessel[];
  mmsi?: string;
  latitude?: number;
  longitude?: number;
  speed?: number;
  course?: number;
}

/**
 * Hook to maintain a live WebSocket connection to the backend
 * for real-time vessel position updates.
 */
export function useVesselWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMountedRef = useRef(true);
  const reconnectAttemptsRef = useRef(0);
  const { setVessels, setWsConnected } = useStore();

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(`${WS_URL}/api/ships/ws/live`);
      wsRef.current = ws;

      ws.onopen = () => {
        reconnectAttemptsRef.current = 0;
        setWsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const msg: WSMessage = JSON.parse(event.data);

          if (msg.type === "snapshot" && msg.vessels) {
            setVessels(msg.vessels);
          } else if (msg.type === "position_update" && msg.mmsi) {
            // Update a single vessel position in store
            setVessels(
              useStore.getState().vessels.map(v =>
                v.mmsi === msg.mmsi
                  ? {
                      ...v,
                      latitude: msg.latitude ?? v.latitude,
                      longitude: msg.longitude ?? v.longitude,
                      speed: msg.speed ?? v.speed,
                      course: msg.course ?? v.course,
                    }
                  : v
              )
            );
          }
        } catch {
          // Ignore parse errors
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
        if (!isMountedRef.current) return;
        const delay = Math.min(30_000, 1_000 * 2 ** reconnectAttemptsRef.current++);
        reconnectTimerRef.current = setTimeout(connect, delay);
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      // WebSocket not available — polling fallback will handle data
    }
  }, [setVessels, setWsConnected]);

  useEffect(() => {
    isMountedRef.current = true;
    connect();
    return () => {
      isMountedRef.current = false;
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
}

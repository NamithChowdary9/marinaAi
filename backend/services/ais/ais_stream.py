"""
AIS WebSocket Stream — connects to aisstream.io for live vessel updates.
Falls back to simulating movement across the full 500-vessel fleet.
Pushes live position updates to subscribed WebSocket clients every 10 seconds.
"""

import asyncio
import json
import math
import random
from loguru import logger
from typing import Set, Callable

from config.settings import settings


class AISStreamService:
    """
    Maintains a live connection to aisstream.io (or mock simulation)
    and fans out vessel position updates to subscribed frontend clients.
    """

    WS_URL = "wss://stream.aisstream.io/v0/stream"

    def __init__(self):
        self._running    = False
        self._task       = None
        self._subscribers: Set[Callable] = set()
        self._vessel_cache: dict = {}          # mmsi → vessel dict

    # ── Pub/sub ───────────────────────────────────────────────────────────────

    def subscribe(self, callback: Callable):
        self._subscribers.add(callback)

    def unsubscribe(self, callback: Callable):
        self._subscribers.discard(callback)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._stream_loop())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    # ── Main loop ─────────────────────────────────────────────────────────────

    async def _stream_loop(self):
        """Try real AIS stream; fall back to simulated fleet updates."""
        if settings.aisstream_api_key:
            try:
                await self._connect_and_stream()
            except Exception as e:
                logger.warning(f"AIS stream unavailable ({type(e).__name__}) — switching to simulation")
            # Always run simulation after real stream ends/fails
        logger.info("Running simulated fleet (500+ vessels, 10s tick)")
        await self._simulated_stream()

    # ── Real AIS stream ───────────────────────────────────────────────────────

    async def _connect_and_stream(self):
        try:
            import websockets
        except ImportError:
            logger.warning("websockets package not installed — falling back to simulation")
            await self._simulated_stream()
            return

        subscribe_msg = {
            "APIKey": settings.aisstream_api_key,
            "BoundingBoxes": [[[-90, -180], [90, 180]]],
            "FilterMessageTypes": ["PositionReport", "ShipStaticData"],
        }

        async with websockets.connect(self.WS_URL, ping_interval=20) as ws:
            await ws.send(json.dumps(subscribe_msg))
            logger.info("✅ AIS stream connected (live)")

            async for raw in ws:
                if not self._running:
                    break
                try:
                    msg = json.loads(raw)
                    await self._process_message(msg)
                except Exception as e:
                    logger.debug(f"AIS parse error: {e}")

    async def _process_message(self, message: dict):
        msg_type = message.get("MessageType")

        if msg_type == "ShipStaticData":
            # Seed vessel into cache with full metadata
            static = message.get("Message", {}).get("ShipStaticData", {})
            mmsi   = str(static.get("UserID", ""))
            if mmsi:
                self._vessel_cache.setdefault(mmsi, {}).update({
                    "mmsi":        mmsi,
                    "name":        static.get("Name", "Unknown").strip(),
                    "vessel_type": self._decode_type(static.get("Type", 0)),
                    "flag":        static.get("Destination", "")[:2] or "XX",
                    "destination": static.get("Destination", ""),
                    "draught":     static.get("Draught", 0),
                    "length":      static.get("DimensionA", 0) + static.get("DimensionB", 0),
                })

        elif msg_type == "PositionReport":
            report = message.get("Message", {}).get("PositionReport", {})
            mmsi   = str(report.get("UserID", ""))
            if mmsi:
                self._vessel_cache.setdefault(mmsi, {"mmsi": mmsi}).update({
                    "latitude":  report.get("Latitude"),
                    "longitude": report.get("Longitude"),
                    "speed":     report.get("Sog"),
                    "course":    report.get("Cog"),
                    "heading":   report.get("TrueHeading"),
                })
                update = {"type": "position_update", **self._vessel_cache[mmsi]}
                await self._broadcast(update)

    def _decode_type(self, type_code: int) -> str:
        m = {30:"Fishing",36:"Sailing",37:"Pleasure Craft",
             60:"Passenger",70:"Cargo",80:"Tanker",90:"Other"}
        for k, v in m.items():
            if type_code == k or (type_code // 10) * 10 == k:
                return v
        return "Cargo"

    # ── Simulated stream (500+ vessel fleet) ──────────────────────────────────

    async def _simulated_stream(self):
        """
        Simulate realistic vessel movement across the full fleet.
        Every 10 seconds:
          - move every vessel along its course at its speed
          - randomly nudge course ±1° to simulate drift
          - broadcast position_update for a random 20% subset (realistic churn)
        Also broadcasts a full snapshot every 60 seconds.
        """
        from services.ais.ais_service import _get_fleet

        # Seed the cache from the global fleet
        fleet = _get_fleet()
        for v in fleet:
            self._vessel_cache[v["mmsi"]] = dict(v)

        logger.info(f"Simulated stream: {len(fleet)} vessels loaded into cache")

        tick     = 0
        interval = 10          # seconds per tick
        dt_h     = interval / 3600.0   # hours per tick

        while self._running:
            await asyncio.sleep(interval)
            tick += 1

            # Every 60s send a full snapshot to all subscribers
            if tick % 6 == 0:
                vessels = list(self._vessel_cache.values())
                await self._broadcast({"type": "snapshot", "vessels": vessels})
                continue

            # Move vessels and broadcast 20% sample as position_updates
            mmsi_list = list(self._vessel_cache.keys())
            sample    = random.sample(mmsi_list, max(1, len(mmsi_list) // 5))

            for mmsi in sample:
                v = self._vessel_cache[mmsi]
                if v.get("latitude") is None:
                    continue

                lat    = v["latitude"]
                lon    = v["longitude"]
                speed  = v.get("speed", 10)          # knots
                course = v.get("course", 0)

                # Advance position (great-circle approximation for short steps)
                dist_nm = speed * dt_h
                d_lat   = dist_nm * math.cos(math.radians(course)) / 60.0
                d_lon   = dist_nm * math.sin(math.radians(course)) / (
                    60.0 * max(0.01, math.cos(math.radians(lat)))
                )

                new_lat = lat + d_lat
                new_lon = lon + d_lon

                # Wrap longitude, clamp latitude
                new_lon = ((new_lon + 180) % 360) - 180
                new_lat = max(-80.0, min(80.0, new_lat))

                # Small course drift
                new_course = (course + random.gauss(0, 1.0)) % 360

                v["latitude"]  = round(new_lat, 5)
                v["longitude"] = round(new_lon, 5)
                v["course"]    = round(new_course, 1)

                await self._broadcast({
                    "type":      "position_update",
                    "mmsi":      mmsi,
                    "latitude":  v["latitude"],
                    "longitude": v["longitude"],
                    "speed":     v.get("speed"),
                    "course":    v["course"],
                })

    # ── Broadcast ─────────────────────────────────────────────────────────────

    async def _broadcast(self, message: dict):
        dead = set()
        for cb in self._subscribers:
            try:
                await cb(message)
            except Exception:
                dead.add(cb)
        self._subscribers -= dead

    # ── Accessors ─────────────────────────────────────────────────────────────

    def get_cached_vessels(self) -> list:
        return list(self._vessel_cache.values())

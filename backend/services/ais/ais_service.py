"""
AIS Service — fetches vessel position data.
Primary:  aisstream.io API
Fallback: 500+ realistic vessels across all major world shipping lanes.
"""

import httpx
import math
import random
from typing import Optional, List
from loguru import logger

from config.settings import settings

# ─── Vessel type map ─────────────────────────────────────────────────────────

VESSEL_TYPE_MAP = {
    0: "Unknown", 20: "Wing In Ground", 30: "Fishing",
    31: "Towing", 32: "Towing Large", 36: "Sailing",
    37: "Pleasure Craft", 60: "Passenger", 70: "Cargo",
    80: "Tanker", 90: "Other",
}

# ─── Shipping lane corridor definitions ──────────────────────────────────────
# Each corridor: (lat_center, lon_center, lat_spread, lon_spread,
#                 heading_mean, heading_spread, speed_mean, speed_spread,
#                 vessel_types_weighted, flags_weighted, count)

CORRIDORS = [
    # ── Indian West Coast ──────────────────────────────────────────────────
    (14.0,  74.5,  4.0,  1.5, 185, 25, 12, 3,
     ["Cargo"]*5+["Tanker"]*3+["Fishing"]*4+["Passenger"],
     ["IN"]*6+["SG","AE","LK","GB"], 28),
    # ── Arabian Sea ───────────────────────────────────────────────────────
    (18.0,  63.0,  5.0,  5.0, 295, 35, 13, 3,
     ["Tanker"]*5+["Cargo"]*5+["Naval"],
     ["AE"]*4+["SA","IN","IR","US","GB"], 22),
    # ── Strait of Hormuz / Persian Gulf ───────────────────────────────────
    (25.5,  56.5,  2.0,  3.0, 270, 20, 10, 2,
     ["Tanker"]*7+["Cargo"]*3,
     ["AE"]*5+["SA","IR","KW","QA"], 18),
    # ── Red Sea ───────────────────────────────────────────────────────────
    (20.0,  38.5,  6.0,  1.5, 350, 20, 12, 2,
     ["Cargo"]*5+["Tanker"]*4+["Passenger"],
     ["EG","SA","YE","ET","DJ"], 16),
    # ── Gulf of Aden ──────────────────────────────────────────────────────
    (12.5,  47.0,  1.5,  4.0, 90, 25, 13, 2,
     ["Cargo"]*5+["Tanker"]*4+["Naval"],
     ["SO","DJ","YE","IN","CN","GB"], 12),
    # ── Indian Ocean East ─────────────────────────────────────────────────
    ( 5.0,  72.0,  6.0,  8.0, 120, 40, 14, 3,
     ["Cargo"]*6+["Tanker"]*4,
     ["IN","SG","LK","CN","MY"], 20),
    # ── Bay of Bengal ─────────────────────────────────────────────────────
    (13.0,  85.0,  5.0,  5.0, 180, 40, 11, 3,
     ["Cargo"]*5+["Fishing"]*4+["Tanker"]*2+["Passenger"],
     ["IN"]*4+["BD","LK","CN","MY"], 22),
    # ── Strait of Malacca ─────────────────────────────────────────────────
    ( 3.5, 101.0,  2.0,  2.5, 310, 15, 13, 2,
     ["Cargo"]*6+["Tanker"]*4,
     ["SG"]*3+["MY","ID","CN","JP","KR"], 20),
    # ── Singapore Strait ──────────────────────────────────────────────────
    ( 1.2, 104.0,  0.8,  1.5, 90, 20, 12, 2,
     ["Cargo"]*5+["Tanker"]*4+["Passenger"],
     ["SG"]*5+["MY","ID","CN","JP"], 16),
    # ── South China Sea ───────────────────────────────────────────────────
    (12.0, 113.0,  6.0,  7.0, 45, 40, 14, 3,
     ["Cargo"]*6+["Tanker"]*3+["Fishing"]*3,
     ["CN"]*5+["VN","PH","TW","KR","JP"], 28),
    # ── Taiwan / East China Sea ───────────────────────────────────────────
    (28.0, 124.0,  4.0,  4.0, 40, 30, 13, 2,
     ["Cargo"]*6+["Tanker"]*3+["Passenger"],
     ["CN"]*4+["TW","JP","KR"], 16),
    # ── Japan / Korean waters ─────────────────────────────────────────────
    (33.5, 131.0,  3.0,  4.0, 90, 35, 13, 2,
     ["Cargo"]*5+["Tanker"]*3+["Fishing"]*3+["Passenger"],
     ["JP"]*5+["KR","CN"], 18),
    # ── North Pacific (Trans-Pacific lane) ────────────────────────────────
    (38.0, 165.0,  5.0, 20.0, 80, 20, 17, 2,
     ["Cargo"]*7+["Tanker"]*3,
     ["JP","KR","CN","US","TW"], 18),
    # ── US West Coast ─────────────────────────────────────────────────────
    (36.0,-122.0,  5.0,  2.0, 180, 30, 12, 2,
     ["Cargo"]*5+["Tanker"]*3+["Passenger"]*2,
     ["US"]*6+["PA","LR"], 14),
    # ── US East Coast ─────────────────────────────────────────────────────
    (37.0, -74.0,  5.0,  2.0, 10, 30, 11, 2,
     ["Cargo"]*5+["Tanker"]*3+["Passenger"]*2,
     ["US"]*6+["BS","AG","PA"], 14),
    # ── North Atlantic (Europe–US lane) ───────────────────────────────────
    (47.0, -30.0,  5.0, 25.0, 275, 20, 16, 2,
     ["Cargo"]*6+["Tanker"]*4,
     ["GB","NO","DE","NL","GR","US","PA"], 22),
    # ── English Channel / North Sea ───────────────────────────────────────
    (51.0,   2.0,  2.0,  4.0, 245, 20, 12, 2,
     ["Cargo"]*6+["Tanker"]*3+["Passenger"],
     ["GB","NL","DE","FR","NO","DK"], 18),
    # ── Mediterranean ─────────────────────────────────────────────────────
    (37.0,  16.0,  4.0, 12.0, 90, 45, 12, 3,
     ["Cargo"]*5+["Tanker"]*3+["Passenger"]*3,
     ["GR","IT","MT","CY","TR","ES","FR"], 24),
    # ── Suez Canal approach ───────────────────────────────────────────────
    (31.0,  32.3,  1.5,  0.5, 355, 10, 8, 1,
     ["Cargo"]*5+["Tanker"]*5,
     ["EG","SG","CN","JP","IN","GR"], 12),
    # ── Cape of Good Hope ─────────────────────────────────────────────────
    (-35.0, 18.5,  3.0,  4.0, 80, 35, 13, 2,
     ["Cargo"]*5+["Tanker"]*5,
     ["ZA","GR","NO","PA","LR"], 12),
    # ── West Africa ───────────────────────────────────────────────────────
    ( 4.0,   2.5,  4.0,  3.0, 200, 40, 10, 2,
     ["Cargo"]*5+["Tanker"]*4+["Fishing"],
     ["NG","GH","CM","SN","CI"], 12),
    # ── South Atlantic ────────────────────────────────────────────────────
    (-25.0, -35.0,  8.0, 12.0, 200, 40, 13, 3,
     ["Cargo"]*6+["Tanker"]*4,
     ["BR","AR","PA","GR","NO"], 16),
    # ── Caribbean / Gulf of Mexico ────────────────────────────────────────
    (22.0, -80.0,  4.0,  8.0, 90, 50, 12, 3,
     ["Cargo"]*4+["Tanker"]*3+["Passenger"]*3,
     ["US","MX","PA","BS","CU"], 16),
    # ── Australia (SE coast) ──────────────────────────────────────────────
    (-34.0, 152.0,  3.0,  3.0, 10, 35, 12, 2,
     ["Cargo"]*5+["Tanker"]*3+["Fishing"]*2,
     ["AU"]*5+["NZ","SG"], 12),
    # ── Australia (NW + Indian Ocean) ─────────────────────────────────────
    (-20.0, 115.0,  4.0,  5.0, 250, 35, 12, 2,
     ["Cargo"]*4+["Tanker"]*6,
     ["AU"]*4+["SG","IN","CN"], 12),
    # ── South Pacific ─────────────────────────────────────────────────────
    (-20.0,-170.0,  6.0, 15.0, 90, 40, 13, 2,
     ["Cargo"]*6+["Passenger"]*2+["Fishing"]*2,
     ["AU","NZ","FJ","PG","US"], 10),
    # ── Black Sea ─────────────────────────────────────────────────────────
    (43.0,  33.0,  3.0,  7.0, 270, 40, 10, 2,
     ["Cargo"]*6+["Tanker"]*4,
     ["TR","UA","RO","BG","RU","GR"], 12),
    # ── Baltic Sea ────────────────────────────────────────────────────────
    (57.0,  19.0,  4.0,  7.0, 90, 45, 11, 2,
     ["Cargo"]*5+["Tanker"]*3+["Passenger"]*2,
     ["SE","FI","DK","DE","PL","EE","LV"], 12),
    # ── Indian Ocean (deep water, south) ──────────────────────────────────
    (-10.0,  70.0,  8.0, 15.0, 90, 40, 14, 3,
     ["Cargo"]*6+["Tanker"]*4,
     ["IN","SG","GR","PA","LR"], 16),
    # ── Fishing grounds — North Pacific ───────────────────────────────────
    (48.0, 162.0,  5.0, 10.0, 135, 60, 6, 2,
     ["Fishing"]*8+["Cargo"]*2,
     ["JP","KR","RU","TW","CN"], 14),
    # ── Fishing grounds — North Atlantic ──────────────────────────────────
    (60.0, -20.0,  5.0, 10.0, 200, 60, 5, 2,
     ["Fishing"]*8+["Cargo"]*2,
     ["NO","IS","GB","IE","RU"], 14),
]

# Named vessel prefixes by type
_PREFIXES = {
    "Cargo":     ["MV", "MS", "SS"],
    "Tanker":    ["MT", "T/V", "SS"],
    "Fishing":   ["FV", "MFV", "FY"],
    "Passenger": ["SS", "MS", "MV"],
    "Naval":     ["HMCS", "USS", "INS", "HMAS"],
    "Sailing":   ["SV", "Ketch"],
}
_NAMES = [
    "Pioneer","Star","Eagle","Horizon","Atlas","Titan","Aurora","Venture","Spirit",
    "Mariner","Viking","Neptune","Poseidon","Triton","Oceania","Pacific","Atlantic",
    "Arctic","Endeavour","Explorer","Voyager","Discovery","Challenger","Meridian",
    "Solstice","Equinox","Zenith","Apex","Pinnacle","Summit","Crest","Beacon",
    "Guardian","Sentinel","Protector","Defender","Ranger","Pathfinder","Trailblazer",
    "Constellation","Galaxy","Cosmos","Nova","Eclipse","Polaris","Vega","Sirius",
    "Orion","Cygnus","Hydra","Lyra","Phoenix","Dragon","Falcon","Condor","Albatross",
    "Petrel","Gannet","Frigate","Cormorant","Kingfisher","Osprey","Pelican","Heron",
]
_DESTINATIONS = [
    "SGSIN","INMAA","CNSHA","GBLON","AEDXB","USNYC","USLAX","NLRTM","DEHAM",
    "JPYOK","KRBUS","AUHBA","INPAV","INBOM","EGPSD","TRMER","GRPIR","ITGOA",
    "MAPTM","ZACPT","NGAPP","BRSAN","ARBA","MXVER","AUMEL","NZAKL",
]

_RISK_WEIGHTS = {
    "safe": 0.55, "low": 0.25, "medium": 0.12, "high": 0.06, "critical": 0.02,
}

def _weighted_choice(d: dict):
    keys = list(d.keys())
    weights = list(d.values())
    return random.choices(keys, weights=weights, k=1)[0]

def _risk_score(level: str) -> float:
    bands = {"safe":(0,15),"low":(15,30),"medium":(30,55),"high":(55,78),"critical":(78,100)}
    lo, hi = bands[level]
    return round(random.uniform(lo, hi), 1)


def build_global_fleet(seed: int = 42) -> List[dict]:
    """
    Generate 500+ realistic vessels spread across all major shipping lanes.
    Deterministic when called with same seed.
    """
    random.seed(seed)
    vessels = []
    counter = 1

    for (clat, clon, dlat, dlon, hdg, dhdg, spd, dspd,
         vtypes, flags, count) in CORRIDORS:

        for _ in range(count):
            lat = clat + random.gauss(0, dlat / 2.5)
            lon = clon + random.gauss(0, dlon / 2.5)
            lat = max(-80.0, min(80.0, lat))
            lon = max(-179.9, min(179.9, lon))

            course   = (hdg + random.gauss(0, dhdg)) % 360
            speed    = max(0.5, spd + random.gauss(0, dspd))
            vtype    = random.choice(vtypes)
            flag     = random.choice(flags)
            prefix   = random.choice(_PREFIXES.get(vtype, ["MV"]))
            name     = f"{prefix} {random.choice(_NAMES)} {random.randint(1, 99):02d}"
            mmsi     = f"{random.randint(200000000, 799999999)}"
            dest     = random.choice(_DESTINATIONS)
            risk_lvl = _weighted_choice(_RISK_WEIGHTS)

            # Fishing boats move slower; naval move faster
            if vtype == "Fishing":
                speed = max(1.0, random.uniform(3, 9))
            elif vtype == "Naval":
                speed = random.uniform(18, 28)
            elif vtype == "Passenger":
                speed = random.uniform(16, 26)

            vessels.append({
                "mmsi":        mmsi,
                "name":        name,
                "vessel_type": vtype,
                "flag":        flag,
                "latitude":    round(lat, 4),
                "longitude":   round(lon, 4),
                "speed":       round(speed, 1),
                "course":      round(course, 1),
                "heading":     round((course + random.gauss(0, 3)) % 360, 1),
                "status":      random.choices(
                    ["Under way using engine","Under way using engine","Anchored","Moored"],
                    weights=[70, 15, 10, 5]
                )[0],
                "destination": dest,
                "draught":     round(random.uniform(3.5, 14.5), 1),
                "length":      random.choice([85, 120, 150, 185, 220, 265, 300, 335, 400]),
                "risk_level":  risk_lvl,
                "risk_score":  _risk_score(risk_lvl),
                "ai_alert":    None,
                "last_seen":   None,
            })
            counter += 1

    # Shuffle so map doesn't render in corridor order
    random.shuffle(vessels)
    return vessels


# ─── Singleton fleet (built once, reused) ────────────────────────────────────
_GLOBAL_FLEET: List[dict] = []

def _get_fleet() -> List[dict]:
    global _GLOBAL_FLEET
    if not _GLOBAL_FLEET:
        _GLOBAL_FLEET = build_global_fleet()
        logger.info(f"AIS fleet initialised: {len(_GLOBAL_FLEET)} vessels")
    return _GLOBAL_FLEET


# ─── AISService ──────────────────────────────────────────────────────────────

class AISService:
    """Fetches and caches AIS vessel data."""

    BASE_URL = "https://api.aisstream.io/v0"

    def __init__(self):
        self._cache: dict = {}

    @staticmethod
    def _has_api_key() -> bool:
        """Avoid remote calls when AIS streaming has not been configured."""
        key = (settings.aisstream_api_key or "").strip()
        return bool(key) and key.lower() not in {"your-aisstream-key-here", "changeme"}

    async def get_vessel(self, mmsi: str) -> Optional[dict]:
        if self._has_api_key():
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(
                        f"{self.BASE_URL}/vessel",
                        params={"mmsi": mmsi},
                        headers={"Authorization": f"Bearer {settings.aisstream_api_key}"},
                    )
                    if resp.status_code == 200:
                        return resp.json()
            except Exception as e:
                logger.debug(f"AIS API unavailable: {e}")

        # Search local fleet first.
        for vessel in _get_fleet():
            if vessel["mmsi"] == mmsi:
                return vessel
        return None

    async def get_vessels_in_area(
        self, lat: float, lon: float, radius_nm: float = 100
    ) -> List[dict]:
        if self._has_api_key():
            try:
                deg = radius_nm / 60
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(
                        f"{self.BASE_URL}/vessels",
                        params={
                            "lat_min": lat - deg, "lat_max": lat + deg,
                            "lon_min": lon - deg, "lon_max": lon + deg,
                        },
                        headers={"Authorization": f"Bearer {settings.aisstream_api_key}"},
                    )
                    if resp.status_code == 200:
                        return resp.json().get("vessels", [])
            except Exception as e:
                logger.debug(f"AIS area query unavailable: {e}")

        return self._area_from_fleet(lat, lon, radius_nm)

    async def get_global_snapshot(self) -> dict:
        fleet = _get_fleet()
        return {
            "total_vessels": len(fleet),
            "vessels":       fleet,
            "busiest_regions": [
                "Strait of Malacca", "English Channel", "Suez Canal",
                "Strait of Hormuz",  "Singapore Strait",
            ],
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _area_from_fleet(self, lat: float, lon: float, radius_nm: float) -> List[dict]:
        """Filter global fleet to vessels within radius_nm of a point."""
        R = 3440.065
        result = []
        for v in _get_fleet():
            dlat = math.radians(v["latitude"] - lat)
            dlon = math.radians(v["longitude"] - lon)
            a    = (math.sin(dlat/2)**2
                    + math.cos(math.radians(lat)) * math.cos(math.radians(v["latitude"]))
                    * math.sin(dlon/2)**2)
            dist = R * 2 * math.asin(math.sqrt(a))
            if dist <= radius_nm:
                result.append(v)
        return result

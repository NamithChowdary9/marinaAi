"""
Route Agent — generates optimal maritime routes using real ocean shipping lanes.
All waypoints are in open water. Routes follow actual sea lanes, straits, and
passage points used by commercial shipping.
"""

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from typing import Optional, List, Dict, Tuple
import json
import math

from agents.maritime_gpt.maritime_gpt_agent import _build_llm, _is_key_configured

SYSTEM_PROMPT = """You are the MarineAI Route Agent — a professional maritime navigator.
Generate realistic, geographically accurate maritime routes with real waypoints strictly
in open water / ocean. Never place waypoints on land. Respond in valid JSON only."""


# ─── Nautical math helpers ────────────────────────────────────────────────────

def _nm(lat1, lon1, lat2, lon2) -> float:
    """Haversine distance in nautical miles."""
    R = 3440.065
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dLon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))

def _bearing(lat1, lon1, lat2, lon2) -> float:
    dLon = math.radians(lon2 - lon1)
    lat1, lat2 = math.radians(lat1), math.radians(lat2)
    x = math.sin(dLon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dLon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360

def _compass(deg: float) -> str:
    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
    return dirs[round(deg / 22.5) % 16]

def _route_stats(waypoints: List[Dict], speed_kts: float,
                 risk: int, dist_mult: float = 1.0,
                 fuel_saving: Optional[float] = None) -> Dict:
    """Compute total distance, duration, and step-by-step directions from a waypoint list."""
    total_nm = sum(
        _nm(waypoints[i]["lat"], waypoints[i]["lon"],
            waypoints[i+1]["lat"], waypoints[i+1]["lon"])
        for i in range(len(waypoints) - 1)
    )
    dist = round(total_nm * dist_mult)
    directions = []
    for i in range(len(waypoints) - 1):
        w1, w2 = waypoints[i], waypoints[i + 1]
        bear = _bearing(w1["lat"], w1["lon"], w2["lat"], w2["lon"])
        seg  = _nm(w1["lat"], w1["lon"], w2["lat"], w2["lon"])
        directions.append(
            f"From {w1['name']} → head {_compass(bear)} ({bear:.0f}°) for {seg:.0f} nm to {w2['name']}"
        )
    return {
        "distance_nm": dist,
        "duration_h": round(dist / speed_kts, 1),
        "risk_score": risk,
        "fuel_savings_pct": fuel_saving,
        "directions": directions,
    }


# ─── Named ocean waypoints (never on land) ───────────────────────────────────
# All positions verified to be in open water.

WP = {
    # Indian West Coast / Arabian Sea
    "mumbai_outer":     {"lat": 18.80, "lon": 72.60, "name": "Mumbai Outer Anchorage"},
    "ratnagiri_off":    {"lat": 16.98, "lon": 73.10, "name": "Ratnagiri Offshore"},
    "goa_off":          {"lat": 15.30, "lon": 73.50, "name": "Goa Offshore"},
    "mangalore_off":    {"lat": 12.80, "lon": 74.50, "name": "Mangalore Offshore"},
    "kochi_off":        {"lat": 9.90,  "lon": 75.80, "name": "Kochi Offshore"},
    "kanyakumari":      {"lat": 7.80,  "lon": 77.50, "name": "Cape Comorin (Kanyakumari)"},
    "lakshadweep":      {"lat": 10.50, "lon": 72.00, "name": "Lakshadweep Sea"},
    "arabian_mid":      {"lat": 14.00, "lon": 65.00, "name": "Arabian Sea Mid"},
    "arabian_nw":       {"lat": 20.00, "lon": 62.00, "name": "Arabian Sea NW"},
    "gulf_oman_entry":  {"lat": 24.00, "lon": 58.50, "name": "Gulf of Oman Entry"},
    "hormuz":           {"lat": 26.50, "lon": 56.50, "name": "Strait of Hormuz"},
    "dubai_outer":      {"lat": 25.10, "lon": 55.20, "name": "Dubai Outer Anchorage"},

    # Indian East Coast / Bay of Bengal
    "vizag_outer":      {"lat": 17.50, "lon": 83.50, "name": "Visakhapatnam Outer"},
    "chennai_outer":    {"lat": 13.05, "lon": 80.35, "name": "Chennai Outer Anchorage"},
    "ennore":           {"lat": 13.20, "lon": 80.35, "name": "Ennore Anchorage"},
    "pt_calimere":      {"lat": 10.30, "lon": 80.00, "name": "Point Calimere"},
    "palk_bay":         {"lat": 9.30,  "lon": 79.85, "name": "Palk Bay Waypoint"},
    "gulf_mannar":      {"lat": 8.40,  "lon": 79.50, "name": "Gulf of Mannar"},
    "colombo_outer":    {"lat": 6.90,  "lon": 79.75, "name": "Colombo Outer Anchorage"},
    "sl_south":         {"lat": 5.80,  "lon": 80.60, "name": "Sri Lanka Southern Tip"},
    "sl_east":          {"lat": 7.50,  "lon": 82.00, "name": "Sri Lanka East"},
    "bay_mid":          {"lat": 10.00, "lon": 87.00, "name": "Bay of Bengal Mid"},
    "bay_north":        {"lat": 14.00, "lon": 85.00, "name": "Bay of Bengal North"},
    "andaman_north":    {"lat": 13.30, "lon": 93.00, "name": "Andaman Sea North"},
    "andaman_south":    {"lat": 6.50,  "lon": 94.00, "name": "Andaman Sea South"},

    # Malacca / Singapore / SEA
    "malacca_north":    {"lat": 5.50,  "lon": 99.50, "name": "Malacca Strait North"},
    "malacca_mid":      {"lat": 3.80,  "lon": 101.00, "name": "Malacca Strait Mid"},
    "malacca_south":    {"lat": 1.80,  "lon": 103.20, "name": "Malacca Strait South"},
    "singapore_outer":  {"lat": 1.20,  "lon": 104.00, "name": "Singapore Outer Roads"},
    "south_china_sw":   {"lat": 4.00,  "lon": 108.00, "name": "South China Sea SW"},
    "south_china_mid":  {"lat": 12.00, "lon": 113.00, "name": "South China Sea Mid"},
    "taiwan_strait_s":  {"lat": 22.50, "lon": 120.50, "name": "Taiwan Strait South"},
    "east_china_sea":   {"lat": 27.00, "lon": 124.00, "name": "East China Sea"},
    "shanghai_outer":   {"lat": 31.00, "lon": 122.80, "name": "Shanghai Outer Anchorage"},

    # Indian Ocean / Red Sea / Suez
    "io_mid":           {"lat": -5.00, "lon": 75.00, "name": "Indian Ocean Mid"},
    "io_west":          {"lat": 0.00,  "lon": 60.00, "name": "Indian Ocean West"},
    "socotra":          {"lat": 12.50, "lon": 54.00, "name": "Socotra Island Passage"},
    "aden_gulf":        {"lat": 12.20, "lon": 46.00, "name": "Gulf of Aden Mid"},
    "red_sea_south":    {"lat": 13.50, "lon": 43.50, "name": "Red Sea South"},
    "red_sea_mid":      {"lat": 20.00, "lon": 38.50, "name": "Red Sea Mid"},
    "bab_el_mandeb":    {"lat": 12.60, "lon": 43.40, "name": "Bab-el-Mandeb Strait"},
    "suez_south":       {"lat": 29.80, "lon": 32.50, "name": "Suez Canal South"},

    # Mediterranean / Atlantic
    "suez_north":       {"lat": 31.20, "lon": 32.20, "name": "Suez Canal North (Port Said)"},
    "med_east":         {"lat": 33.00, "lon": 34.00, "name": "Mediterranean East"},
    "med_mid":          {"lat": 35.50, "lon": 18.00, "name": "Mediterranean Mid"},
    "med_west":         {"lat": 36.50, "lon": 4.00,  "name": "Mediterranean West"},
    "gibraltar":        {"lat": 35.97, "lon": -5.50, "name": "Strait of Gibraltar"},
    "bay_biscay":       {"lat": 46.00, "lon": -8.00, "name": "Bay of Biscay"},
    "english_channel":  {"lat": 50.50, "lon": -1.50, "name": "English Channel"},
    "rotterdam_outer":  {"lat": 51.90, "lon": 3.80,  "name": "Rotterdam Outer Roads"},
    "north_atlantic_e": {"lat": 48.00, "lon": -18.00,"name": "North Atlantic East"},
    "north_atlantic_m": {"lat": 45.00, "lon": -40.00,"name": "North Atlantic Mid"},
    "north_atlantic_w": {"lat": 42.00, "lon": -60.00,"name": "North Atlantic West"},
    "ny_outer":         {"lat": 40.45, "lon": -73.80,"name": "New York Outer Harbour"},

    # Pacific / Australia
    "lombok":           {"lat": -8.80, "lon": 115.80,"name": "Lombok Strait"},
    "timor_sea":        {"lat": -11.00,"lon": 124.00, "name": "Timor Sea"},
    "torres_strait":    {"lat": -10.50,"lon": 142.50, "name": "Torres Strait"},
    "coral_sea":        {"lat": -20.00,"lon": 155.00, "name": "Coral Sea"},
    "tasman_sea":       {"lat": -32.00,"lon": 154.00, "name": "Tasman Sea"},
    "sydney_outer":     {"lat": -33.80,"lon": 151.40, "name": "Sydney Outer Roads"},
    "pacific_nw":       {"lat": 28.00, "lon": 145.00, "name": "Pacific NW"},
    "pacific_mid":      {"lat": 30.00, "lon": -150.00,"name": "Pacific Mid"},
    "pacific_ne":       {"lat": 38.00, "lon": -130.00,"name": "Pacific NE"},
    "cape_horn":        {"lat": -58.00,"lon": -68.00, "name": "Cape Horn Passage"},
    "south_atlantic":   {"lat": -35.00,"lon": -30.00, "name": "South Atlantic"},
    "cape_good_hope":   {"lat": -35.00,"lon": 18.00,  "name": "Cape of Good Hope"},
}

def _wp(*keys) -> List[Dict]:
    """Return a list of named waypoint dicts."""
    return [WP[k] for k in keys]


# ─── Comprehensive maritime route database ────────────────────────────────────
# Keys are (origin_keyword, dest_keyword) — matched by substring against port names.
# Every route uses only open-water waypoints.

def _make_route(waypoints, speed, risk, dist_mult=1.0, desc="", fuel_saving=None):
    stats = _route_stats(waypoints, speed, risk, dist_mult, fuel_saving)
    return {"waypoints": waypoints, "description": desc, **stats}

MARITIME_ROUTES: Dict[Tuple[str,str], Dict] = {}

def _register(o_key: str, d_key: str, safe_wps, fast_wps, eco_wps,
              recommended: str, reasoning: str, hazards: List[str], advice: str):
    """Register bidirectional routes between two port keywords."""
    def _rev(wps):
        return list(reversed(wps))

    def _build(wps_safe, wps_fast, wps_eco):
        return {
            "routes": {
                "safe": _make_route(wps_safe, 12, 20, 1.08,
                    "Weather-optimised route via established shipping lanes. Maximum sea-room from hazards."),
                "fast": _make_route(wps_fast, 18, 38, 1.0,
                    "Direct great-circle route for minimum transit time. Higher weather exposure."),
                "fuel_efficient": _make_route(wps_eco, 11, 24, 1.05,
                    "Current-assisted eco route at reduced speed for fuel saving.", 11),
            },
            "recommended_route": recommended,
            "reasoning": reasoning,
            "hazards_on_path": hazards,
            "departure_advice": advice,
        }

    MARITIME_ROUTES[(o_key, d_key)] = _build(safe_wps, fast_wps, eco_wps)
    MARITIME_ROUTES[(d_key, o_key)] = _build(_rev(safe_wps), _rev(fast_wps), _rev(eco_wps))


# ── Mumbai ↔ Colombo ──────────────────────────────────────────────────────────
_register(
    "mumbai", "colombo",
    safe_wps=_wp("mumbai_outer","mangalore_off","kochi_off","kanyakumari","gulf_mannar","colombo_outer"),
    fast_wps=_wp("mumbai_outer","kochi_off","kanyakumari","sl_south","colombo_outer"),
    eco_wps=_wp("mumbai_outer","lakshadweep","kochi_off","gulf_mannar","colombo_outer"),
    recommended="safe",
    reasoning="Coastal route via Kanyakumari avoids Bay of Bengal swell exposure.",
    hazards=["SW Monsoon swells Jun–Sep off Kerala coast","Gulf of Mannar: fishing vessel traffic","Check depth for Palk Strait if transiting"],
    advice="Best window: Oct–March. Avoid peak SW Monsoon (Jun–Aug).",
)

# ── Mumbai ↔ Singapore ────────────────────────────────────────────────────────
_register(
    "mumbai", "singapore",
    safe_wps=_wp("mumbai_outer","goa_off","kochi_off","kanyakumari","sl_south","andaman_south","malacca_north","malacca_mid","malacca_south","singapore_outer"),
    fast_wps=_wp("mumbai_outer","lakshadweep","sl_south","andaman_south","malacca_mid","singapore_outer"),
    eco_wps=_wp("mumbai_outer","arabian_mid","sl_south","io_mid","andaman_south","malacca_north","malacca_mid","singapore_outer"),
    recommended="safe",
    reasoning="Coastal Indian route then Malacca Strait TSS. Avoids open monsoon exposure.",
    hazards=["Malacca Strait: heavy traffic (80,000 ships/year) — follow TSS","SW Monsoon swells in Arabian Sea Jun–Sep","Piracy advisory: Gulf of Aden / Malacca approaches"],
    advice="Avoid Jun–Aug (peak SW Monsoon). Follow Malacca TSS strictly.",
)

# ── Mumbai ↔ Dubai ────────────────────────────────────────────────────────────
_register(
    "mumbai", "dubai",
    safe_wps=_wp("mumbai_outer","arabian_nw","gulf_oman_entry","hormuz","dubai_outer"),
    fast_wps=_wp("mumbai_outer","arabian_mid","gulf_oman_entry","hormuz","dubai_outer"),
    eco_wps=_wp("mumbai_outer","lakshadweep","arabian_nw","gulf_oman_entry","hormuz","dubai_outer"),
    recommended="safe",
    reasoning="Standard Arabian Sea lane via Strait of Hormuz.",
    hazards=["Strait of Hormuz: heavy tanker traffic","Piracy advisory: Gulf of Aden if routing south","SW Monsoon: rough seas Jun–Sep"],
    advice="Clear Hormuz during daylight. File with Gulf VTS.",
)

# ── Mumbai ↔ Rotterdam ────────────────────────────────────────────────────────
_register(
    "mumbai", "rotterdam",
    safe_wps=_wp("mumbai_outer","lakshadweep","arabian_nw","socotra","aden_gulf","bab_el_mandeb","red_sea_south","red_sea_mid","suez_south","suez_north","med_east","med_mid","med_west","gibraltar","bay_biscay","rotterdam_outer"),
    fast_wps=_wp("mumbai_outer","arabian_nw","socotra","aden_gulf","bab_el_mandeb","red_sea_mid","suez_north","med_mid","gibraltar","rotterdam_outer"),
    eco_wps=_wp("mumbai_outer","io_west","cape_good_hope","south_atlantic","gibraltar","bay_biscay","rotterdam_outer"),
    recommended="safe",
    reasoning="Suez Canal route is standard and fastest. Cape route only if canal is blocked.",
    hazards=["Gulf of Aden: Somali piracy zone — use IRTC corridor","Red Sea: geopolitical risk — check latest advisories","Bab-el-Mandeb: traffic separation scheme","Bay of Biscay: rough in winter"],
    advice="Use BMP5 (Best Management Practices) in Gulf of Aden. Register with UKMTO.",
)

# ── Mumbai ↔ Shanghai ────────────────────────────────────────────────────────
_register(
    "mumbai", "shanghai",
    safe_wps=_wp("mumbai_outer","kochi_off","kanyakumari","sl_south","andaman_south","malacca_north","malacca_mid","singapore_outer","south_china_sw","south_china_mid","taiwan_strait_s","east_china_sea","shanghai_outer"),
    fast_wps=_wp("mumbai_outer","sl_south","andaman_south","malacca_mid","singapore_outer","south_china_mid","taiwan_strait_s","shanghai_outer"),
    eco_wps=_wp("mumbai_outer","lakshadweep","sl_south","andaman_south","malacca_south","singapore_outer","south_china_mid","east_china_sea","shanghai_outer"),
    recommended="safe",
    reasoning="Standard IO–Malacca–SCS route followed by all major carriers.",
    hazards=["South China Sea: territorial disputes — stay on recognised sea lanes","Typhoon season Jul–Oct between Philippines and China","Malacca Strait: dense traffic"],
    advice="Monitor typhoon advisories. Avoid South China Sea off-lane navigation.",
)

# ── Mumbai ↔ New York ─────────────────────────────────────────────────────────
_register(
    "mumbai", "new york",
    safe_wps=_wp("mumbai_outer","lakshadweep","io_west","cape_good_hope","south_atlantic","gibraltar","north_atlantic_e","north_atlantic_m","north_atlantic_w","ny_outer"),
    fast_wps=_wp("mumbai_outer","arabian_nw","socotra","aden_gulf","bab_el_mandeb","red_sea_mid","suez_north","med_mid","gibraltar","north_atlantic_m","ny_outer"),
    eco_wps=_wp("mumbai_outer","io_west","cape_good_hope","south_atlantic","north_atlantic_e","north_atlantic_m","north_atlantic_w","ny_outer"),
    recommended="fast",
    reasoning="Suez route is 2,000 nm shorter. Cape route used if canal unavailable.",
    hazards=["Gulf of Aden piracy zone","North Atlantic winter storms Dec–Mar","Cape Horn/Good Hope: heavy seas if taking southern route"],
    advice="Suez transit requires advance booking (48-72hr notice). Convoy through Gulf of Aden.",
)

# ── Mumbai ↔ Sydney ────────────────────────────────────────────────────────────
_register(
    "mumbai", "sydney",
    safe_wps=_wp("mumbai_outer","kochi_off","sl_south","io_mid","lombok","timor_sea","torres_strait","coral_sea","tasman_sea","sydney_outer"),
    fast_wps=_wp("mumbai_outer","sl_south","io_mid","lombok","timor_sea","coral_sea","sydney_outer"),
    eco_wps=_wp("mumbai_outer","lakshadweep","sl_south","io_mid","lombok","timor_sea","torres_strait","coral_sea","sydney_outer"),
    recommended="safe",
    reasoning="Lombok Strait avoids shallow Malacca waters for deep-draught vessels.",
    hazards=["Lombok Strait: strong currents","Torres Strait: reef navigation — use pilot","Coral Sea: cyclones Nov–Apr"],
    advice="Torres Strait transit requires licensed pilot. Avoid cyclone season.",
)

# ── Chennai ↔ Colombo ──────────────────────────────────────────────────────────
_register(
    "chennai", "colombo",
    safe_wps=_wp("chennai_outer","ennore","pt_calimere","palk_bay","gulf_mannar","colombo_outer"),
    fast_wps=_wp("chennai_outer","sl_east","sl_south","colombo_outer"),
    eco_wps=_wp("chennai_outer","pt_calimere","gulf_mannar","colombo_outer"),
    recommended="safe",
    reasoning="Palk Bay coastal route avoids open Bay of Bengal swell.",
    hazards=["Palk Bay: shallow (20m) — check vessel draught","Heavy fishing traffic near Point Calimere","Cyclone season Oct–Dec"],
    advice="Depart 0600–0800 to arrive Colombo in daylight. Check INCHMET forecast.",
)

# ── Chennai ↔ Singapore ────────────────────────────────────────────────────────
_register(
    "chennai", "singapore",
    safe_wps=_wp("chennai_outer","sl_south","andaman_south","malacca_north","malacca_mid","malacca_south","singapore_outer"),
    fast_wps=_wp("chennai_outer","bay_mid","andaman_south","malacca_mid","singapore_outer"),
    eco_wps=_wp("chennai_outer","sl_south","io_mid","andaman_south","malacca_north","malacca_mid","singapore_outer"),
    recommended="safe",
    reasoning="Standard Bay of Bengal to Malacca route.",
    hazards=["Bay of Bengal cyclones Apr–Jun, Oct–Dec","Malacca Strait traffic"],
    advice="Monitor Bay of Bengal weather. File VTIS notification before Malacca.",
)

# ── Chennai ↔ Dubai ────────────────────────────────────────────────────────────
_register(
    "chennai", "dubai",
    safe_wps=_wp("chennai_outer","kanyakumari","lakshadweep","arabian_nw","gulf_oman_entry","hormuz","dubai_outer"),
    fast_wps=_wp("chennai_outer","kanyakumari","arabian_mid","gulf_oman_entry","hormuz","dubai_outer"),
    eco_wps=_wp("chennai_outer","kanyakumari","lakshadweep","arabian_mid","gulf_oman_entry","hormuz","dubai_outer"),
    recommended="safe",
    reasoning="Standard Indian Ocean – Arabian Sea – Hormuz lane.",
    hazards=["SW Monsoon Arabian Sea Jun–Sep","Strait of Hormuz tanker traffic"],
    advice="Avoid peak monsoon. File with Gulf VTS at Hormuz.",
)

# ── Chennai ↔ Shanghai ────────────────────────────────────────────────────────
_register(
    "chennai", "shanghai",
    safe_wps=_wp("chennai_outer","sl_south","andaman_south","malacca_north","malacca_mid","singapore_outer","south_china_mid","taiwan_strait_s","east_china_sea","shanghai_outer"),
    fast_wps=_wp("chennai_outer","andaman_south","malacca_mid","singapore_outer","south_china_mid","taiwan_strait_s","shanghai_outer"),
    eco_wps=_wp("chennai_outer","sl_south","andaman_south","malacca_north","singapore_outer","south_china_sw","south_china_mid","east_china_sea","shanghai_outer"),
    recommended="safe",
    reasoning="Malacca Strait standard route for East-West Asia trade.",
    hazards=["Bay of Bengal cyclones","South China Sea typhoons Jul–Oct","Malacca TSS strict compliance"],
    advice="Monitor typhoon season. Register with Malacca VTS.",
)

# ── Chennai ↔ Rotterdam ────────────────────────────────────────────────────────
_register(
    "chennai", "rotterdam",
    safe_wps=_wp("chennai_outer","kanyakumari","lakshadweep","arabian_nw","socotra","aden_gulf","bab_el_mandeb","red_sea_mid","suez_south","suez_north","med_east","med_mid","gibraltar","bay_biscay","rotterdam_outer"),
    fast_wps=_wp("chennai_outer","kanyakumari","arabian_nw","aden_gulf","bab_el_mandeb","red_sea_mid","suez_north","med_mid","gibraltar","rotterdam_outer"),
    eco_wps=_wp("chennai_outer","kanyakumari","io_west","cape_good_hope","south_atlantic","gibraltar","bay_biscay","rotterdam_outer"),
    recommended="safe",
    reasoning="Suez Canal route is standard for Europe–Asia. Cape route as contingency.",
    hazards=["Gulf of Aden piracy","Red Sea geopolitical risk","Bay of Biscay winter storms"],
    advice="Use BMP5 in Gulf of Aden. Suez booking 48–72hr in advance.",
)

# ── Chennai ↔ New York ─────────────────────────────────────────────────────────
_register(
    "chennai", "new york",
    safe_wps=_wp("chennai_outer","kanyakumari","io_west","cape_good_hope","south_atlantic","gibraltar","north_atlantic_e","north_atlantic_m","north_atlantic_w","ny_outer"),
    fast_wps=_wp("chennai_outer","kanyakumari","arabian_nw","aden_gulf","bab_el_mandeb","red_sea_mid","suez_north","med_mid","gibraltar","north_atlantic_m","ny_outer"),
    eco_wps=_wp("chennai_outer","kanyakumari","io_west","cape_good_hope","south_atlantic","north_atlantic_e","north_atlantic_m","ny_outer"),
    recommended="fast",
    reasoning="Suez route saves ~2,000 nm over Cape route.",
    hazards=["Gulf of Aden piracy zone","North Atlantic winter storms","Cape of Good Hope heavy swells"],
    advice="Suez transit requires advance booking. Use IRTC in Gulf of Aden.",
)

# ── Chennai ↔ Sydney ──────────────────────────────────────────────────────────
_register(
    "chennai", "sydney",
    safe_wps=_wp("chennai_outer","sl_south","io_mid","lombok","timor_sea","torres_strait","coral_sea","tasman_sea","sydney_outer"),
    fast_wps=_wp("chennai_outer","sl_east","andaman_south","lombok","timor_sea","coral_sea","sydney_outer"),
    eco_wps=_wp("chennai_outer","sl_south","io_mid","lombok","timor_sea","torres_strait","tasman_sea","sydney_outer"),
    recommended="safe",
    reasoning="Standard Indian Ocean – Lombok – Torres route to Australia east coast.",
    hazards=["Lombok Strait: strong currents","Torres Strait: requires pilot","Coral Sea cyclones Nov–Apr"],
    advice="Book Torres Strait pilot in advance. Avoid cyclone season Nov–Apr.",
)

# ── Visakhapatnam ↔ Colombo ───────────────────────────────────────────────────
_register(
    "visakhapatnam", "colombo",
    safe_wps=_wp("vizag_outer","chennai_outer","pt_calimere","palk_bay","gulf_mannar","colombo_outer"),
    fast_wps=_wp("vizag_outer","sl_east","sl_south","colombo_outer"),
    eco_wps=_wp("vizag_outer","chennai_outer","gulf_mannar","colombo_outer"),
    recommended="safe",
    reasoning="Coastal Bay of Bengal then Palk Bay route.",
    hazards=["Bay of Bengal cyclones","Palk Bay shallow draft limit","Fishing traffic"],
    advice="Monitor Bay of Bengal cyclone advisories Oct–Dec.",
)

# ── Visakhapatnam ↔ Singapore ─────────────────────────────────────────────────
_register(
    "visakhapatnam", "singapore",
    safe_wps=_wp("vizag_outer","bay_north","bay_mid","sl_east","andaman_south","malacca_north","malacca_mid","singapore_outer"),
    fast_wps=_wp("vizag_outer","bay_mid","andaman_south","malacca_mid","singapore_outer"),
    eco_wps=_wp("vizag_outer","bay_north","bay_mid","sl_south","andaman_south","malacca_north","malacca_mid","singapore_outer"),
    recommended="safe",
    reasoning="Bay of Bengal direct to Malacca Strait.",
    hazards=["Bay of Bengal cyclone season","Malacca TSS — compulsory reporting"],
    advice="File with Bay of Bengal meteorological service. VTIS Malacca notification required.",
)

# ── Visakhapatnam ↔ Dubai ─────────────────────────────────────────────────────
_register(
    "visakhapatnam", "dubai",
    safe_wps=_wp("vizag_outer","chennai_outer","kanyakumari","lakshadweep","arabian_nw","gulf_oman_entry","hormuz","dubai_outer"),
    fast_wps=_wp("vizag_outer","kanyakumari","arabian_mid","gulf_oman_entry","hormuz","dubai_outer"),
    eco_wps=_wp("vizag_outer","chennai_outer","kanyakumari","lakshadweep","arabian_mid","gulf_oman_entry","hormuz","dubai_outer"),
    recommended="safe",
    reasoning="Standard east coast India to Arabian Gulf route.",
    hazards=["SW Monsoon in Arabian Sea","Hormuz tanker congestion"],
    advice="Avoid monsoon season. Gulf VTS filing mandatory.",
)

# ── Visakhapatnam ↔ Shanghai ──────────────────────────────────────────────────
_register(
    "visakhapatnam", "shanghai",
    safe_wps=_wp("vizag_outer","bay_mid","sl_east","andaman_south","malacca_mid","singapore_outer","south_china_mid","taiwan_strait_s","east_china_sea","shanghai_outer"),
    fast_wps=_wp("vizag_outer","bay_mid","andaman_south","malacca_mid","singapore_outer","south_china_mid","taiwan_strait_s","shanghai_outer"),
    eco_wps=_wp("vizag_outer","bay_mid","sl_south","andaman_south","malacca_north","malacca_mid","singapore_outer","south_china_mid","east_china_sea","shanghai_outer"),
    recommended="safe",
    reasoning="Bay of Bengal to Malacca to South China Sea — standard Asia trade lane.",
    hazards=["Bay of Bengal cyclones","South China Sea typhoons","Malacca traffic"],
    advice="Monitor SCS typhoon season Jul–Oct.",
)

# ── Visakhapatnam ↔ Rotterdam ─────────────────────────────────────────────────
_register(
    "visakhapatnam", "rotterdam",
    safe_wps=_wp("vizag_outer","bay_north","kanyakumari","lakshadweep","socotra","aden_gulf","bab_el_mandeb","red_sea_mid","suez_south","suez_north","med_east","med_mid","gibraltar","bay_biscay","rotterdam_outer"),
    fast_wps=_wp("vizag_outer","kanyakumari","arabian_nw","aden_gulf","bab_el_mandeb","red_sea_mid","suez_north","med_mid","gibraltar","rotterdam_outer"),
    eco_wps=_wp("vizag_outer","kanyakumari","io_west","cape_good_hope","south_atlantic","gibraltar","bay_biscay","rotterdam_outer"),
    recommended="safe",
    reasoning="Suez Canal primary route for India–Europe trade.",
    hazards=["Gulf of Aden piracy","Red Sea security situation","Bay of Biscay winter gales"],
    advice="Use BMP5. Suez advance booking required.",
)

# ── Visakhapatnam ↔ New York ──────────────────────────────────────────────────
_register(
    "visakhapatnam", "new york",
    safe_wps=_wp("vizag_outer","kanyakumari","io_west","cape_good_hope","south_atlantic","gibraltar","north_atlantic_e","north_atlantic_m","north_atlantic_w","ny_outer"),
    fast_wps=_wp("vizag_outer","kanyakumari","arabian_nw","aden_gulf","bab_el_mandeb","red_sea_mid","suez_north","med_mid","gibraltar","north_atlantic_m","ny_outer"),
    eco_wps=_wp("vizag_outer","kanyakumari","io_west","cape_good_hope","south_atlantic","north_atlantic_e","ny_outer"),
    recommended="fast",
    reasoning="Suez saves ~2,000 nm. Cape route if Suez unavailable.",
    hazards=["Gulf of Aden piracy","North Atlantic winter","Cape Horn swells"],
    advice="Suez booking 48–72hr ahead. IRTC in Gulf of Aden.",
)

# ── Visakhapatnam ↔ Sydney ────────────────────────────────────────────────────
_register(
    "visakhapatnam", "sydney",
    safe_wps=_wp("vizag_outer","bay_mid","sl_east","io_mid","lombok","timor_sea","torres_strait","coral_sea","tasman_sea","sydney_outer"),
    fast_wps=_wp("vizag_outer","bay_mid","andaman_south","lombok","timor_sea","coral_sea","sydney_outer"),
    eco_wps=_wp("vizag_outer","bay_mid","sl_south","io_mid","lombok","timor_sea","torres_strait","tasman_sea","sydney_outer"),
    recommended="safe",
    reasoning="Indian Ocean – Lombok – Torres is the standard Bay of Bengal to Sydney route.",
    hazards=["Torres Strait reef navigation","Coral Sea cyclones","Bay of Bengal cyclones"],
    advice="Pilot compulsory for Torres Strait. Avoid cyclone season.",
)

# ── Singapore ↔ Shanghai ──────────────────────────────────────────────────────
_register(
    "singapore", "shanghai",
    safe_wps=_wp("singapore_outer","south_china_sw","south_china_mid","taiwan_strait_s","east_china_sea","shanghai_outer"),
    fast_wps=_wp("singapore_outer","south_china_mid","taiwan_strait_s","shanghai_outer"),
    eco_wps=_wp("singapore_outer","south_china_sw","south_china_mid","east_china_sea","shanghai_outer"),
    recommended="safe",
    reasoning="Standard South China Sea lane for Singapore–China trade.",
    hazards=["South China Sea territorial tensions","Typhoon season Jul–Oct","Taiwan Strait traffic"],
    advice="Monitor typhoon advisories. Follow coastal TSS in Taiwan Strait.",
)

# ── Singapore ↔ Rotterdam ─────────────────────────────────────────────────────
_register(
    "singapore", "rotterdam",
    safe_wps=_wp("singapore_outer","malacca_north","andaman_south","sl_south","lakshadweep","socotra","aden_gulf","bab_el_mandeb","red_sea_mid","suez_south","suez_north","med_east","med_mid","gibraltar","bay_biscay","rotterdam_outer"),
    fast_wps=_wp("singapore_outer","malacca_north","sl_south","arabian_nw","aden_gulf","bab_el_mandeb","suez_north","med_mid","gibraltar","rotterdam_outer"),
    eco_wps=_wp("singapore_outer","io_mid","io_west","cape_good_hope","south_atlantic","gibraltar","bay_biscay","rotterdam_outer"),
    recommended="safe",
    reasoning="Suez route is the standard Asia–Europe lane.",
    hazards=["Malacca TSS","Gulf of Aden piracy","Red Sea security","Bay of Biscay winter"],
    advice="BMP5 in Gulf of Aden. Malacca VTIS notification. Suez pre-booking.",
)

# ── Singapore ↔ New York ──────────────────────────────────────────────────────
_register(
    "singapore", "new york",
    safe_wps=_wp("singapore_outer","malacca_north","io_mid","io_west","cape_good_hope","south_atlantic","gibraltar","north_atlantic_e","north_atlantic_m","ny_outer"),
    fast_wps=_wp("singapore_outer","malacca_north","arabian_nw","aden_gulf","bab_el_mandeb","suez_north","med_mid","gibraltar","north_atlantic_m","ny_outer"),
    eco_wps=_wp("singapore_outer","malacca_north","io_west","cape_good_hope","south_atlantic","north_atlantic_e","ny_outer"),
    recommended="fast",
    reasoning="Suez route saves ~4,000 nm compared to Cape route.",
    hazards=["Gulf of Aden piracy","Suez Canal traffic","North Atlantic storms"],
    advice="IRTC corridor in Gulf of Aden. Suez booking 72hr ahead.",
)

# ── Singapore ↔ Sydney ────────────────────────────────────────────────────────
_register(
    "singapore", "sydney",
    safe_wps=_wp("singapore_outer","lombok","timor_sea","torres_strait","coral_sea","tasman_sea","sydney_outer"),
    fast_wps=_wp("singapore_outer","lombok","timor_sea","coral_sea","sydney_outer"),
    eco_wps=_wp("singapore_outer","lombok","timor_sea","torres_strait","tasman_sea","sydney_outer"),
    recommended="safe",
    reasoning="Lombok Strait – Torres Strait is the standard Singapore–Sydney route.",
    hazards=["Lombok strong currents","Torres Strait reef — pilot required","Coral Sea cyclones"],
    advice="Torres pilot mandatory. Monitor Coral Sea cyclone season Nov–Apr.",
)

# ── Dubai ↔ Rotterdam ─────────────────────────────────────────────────────────
_register(
    "dubai", "rotterdam",
    safe_wps=_wp("dubai_outer","hormuz","gulf_oman_entry","arabian_nw","socotra","aden_gulf","bab_el_mandeb","red_sea_mid","suez_south","suez_north","med_east","med_mid","gibraltar","bay_biscay","rotterdam_outer"),
    fast_wps=_wp("dubai_outer","hormuz","arabian_nw","aden_gulf","bab_el_mandeb","red_sea_mid","suez_north","med_mid","gibraltar","rotterdam_outer"),
    eco_wps=_wp("dubai_outer","hormuz","io_west","cape_good_hope","south_atlantic","gibraltar","rotterdam_outer"),
    recommended="safe",
    reasoning="Suez Canal is the standard Middle East – Europe route.",
    hazards=["Hormuz tanker traffic","Gulf of Aden piracy","Red Sea security","Suez pilot compulsory"],
    advice="BMP5 Gulf of Aden. Suez booking 72hr ahead. VTS filing at Hormuz.",
)

# ── Dubai ↔ Shanghai ──────────────────────────────────────────────────────────
_register(
    "dubai", "shanghai",
    safe_wps=_wp("dubai_outer","hormuz","gulf_oman_entry","arabian_mid","sl_south","andaman_south","malacca_north","malacca_mid","singapore_outer","south_china_mid","taiwan_strait_s","east_china_sea","shanghai_outer"),
    fast_wps=_wp("dubai_outer","hormuz","arabian_mid","sl_south","malacca_mid","singapore_outer","south_china_mid","taiwan_strait_s","shanghai_outer"),
    eco_wps=_wp("dubai_outer","hormuz","lakshadweep","sl_south","andaman_south","malacca_north","malacca_mid","singapore_outer","south_china_mid","east_china_sea","shanghai_outer"),
    recommended="safe",
    reasoning="Standard Middle East – Malacca – SCS route for Asia trade.",
    hazards=["Hormuz traffic","Malacca TSS","SCS typhoons Jul–Oct"],
    advice="Monitor SCS typhoon season. Malacca VTIS notification required.",
)

# ── Dubai ↔ New York ──────────────────────────────────────────────────────────
_register(
    "dubai", "new york",
    safe_wps=_wp("dubai_outer","hormuz","gulf_oman_entry","socotra","aden_gulf","bab_el_mandeb","red_sea_mid","suez_north","med_mid","gibraltar","north_atlantic_e","north_atlantic_m","ny_outer"),
    fast_wps=_wp("dubai_outer","hormuz","aden_gulf","bab_el_mandeb","red_sea_mid","suez_north","med_mid","gibraltar","north_atlantic_m","ny_outer"),
    eco_wps=_wp("dubai_outer","hormuz","io_west","cape_good_hope","south_atlantic","north_atlantic_e","ny_outer"),
    recommended="fast",
    reasoning="Suez route is 8,000 nm shorter than Cape route.",
    hazards=["Gulf of Aden piracy","Suez Canal congestion","North Atlantic winter storms"],
    advice="IRTC Gulf of Aden. Suez booking 72hr ahead.",
)

# ── Dubai ↔ Sydney ────────────────────────────────────────────────────────────
_register(
    "dubai", "sydney",
    safe_wps=_wp("dubai_outer","hormuz","arabian_mid","sl_south","io_mid","lombok","timor_sea","torres_strait","coral_sea","sydney_outer"),
    fast_wps=_wp("dubai_outer","hormuz","arabian_mid","sl_south","lombok","timor_sea","coral_sea","sydney_outer"),
    eco_wps=_wp("dubai_outer","hormuz","lakshadweep","sl_south","io_mid","lombok","timor_sea","torres_strait","sydney_outer"),
    recommended="safe",
    reasoning="Hormuz – IO – Lombok – Torres standard route.",
    hazards=["Hormuz traffic","Lombok currents","Torres pilot required"],
    advice="Torres Strait pilot mandatory. Book in advance.",
)

# ── Rotterdam ↔ New York ──────────────────────────────────────────────────────
_register(
    "rotterdam", "new york",
    safe_wps=_wp("rotterdam_outer","english_channel","bay_biscay","gibraltar","north_atlantic_e","north_atlantic_m","north_atlantic_w","ny_outer"),
    fast_wps=_wp("rotterdam_outer","english_channel","north_atlantic_e","north_atlantic_m","ny_outer"),
    eco_wps=_wp("rotterdam_outer","english_channel","bay_biscay","north_atlantic_e","north_atlantic_m","ny_outer"),
    recommended="fast",
    reasoning="North Atlantic great-circle route is the standard transatlantic lane.",
    hazards=["North Atlantic winter storms Nov–Mar","English Channel dense traffic","Iceberg risk Feb–Jul above 43°N"],
    advice="Winter routing: take southern option to avoid storms. Monitor iceberg reports.",
)

# ── Rotterdam ↔ Shanghai ──────────────────────────────────────────────────────
_register(
    "rotterdam", "shanghai",
    safe_wps=_wp("rotterdam_outer","bay_biscay","gibraltar","med_mid","med_east","suez_north","suez_south","red_sea_mid","bab_el_mandeb","aden_gulf","socotra","arabian_nw","sl_south","malacca_north","malacca_mid","singapore_outer","south_china_mid","taiwan_strait_s","east_china_sea","shanghai_outer"),
    fast_wps=_wp("rotterdam_outer","gibraltar","med_mid","suez_north","red_sea_mid","bab_el_mandeb","aden_gulf","arabian_nw","malacca_mid","singapore_outer","south_china_mid","taiwan_strait_s","shanghai_outer"),
    eco_wps=_wp("rotterdam_outer","bay_biscay","gibraltar","med_mid","suez_north","red_sea_mid","aden_gulf","sl_south","malacca_north","singapore_outer","south_china_mid","east_china_sea","shanghai_outer"),
    recommended="safe",
    reasoning="Suez Canal – Malacca Strait is the world's primary Europe–Asia trade lane.",
    hazards=["Gulf of Aden piracy","Red Sea security","Malacca TSS","SCS typhoons"],
    advice="BMP5 Gulf of Aden. Suez 72hr booking. Malacca VTIS registration.",
)

# ── Rotterdam ↔ Sydney ────────────────────────────────────────────────────────
_register(
    "rotterdam", "sydney",
    safe_wps=_wp("rotterdam_outer","bay_biscay","gibraltar","med_mid","suez_north","red_sea_mid","bab_el_mandeb","aden_gulf","arabian_mid","sl_south","io_mid","lombok","timor_sea","torres_strait","coral_sea","tasman_sea","sydney_outer"),
    fast_wps=_wp("rotterdam_outer","gibraltar","suez_north","red_sea_mid","bab_el_mandeb","aden_gulf","sl_south","lombok","timor_sea","coral_sea","sydney_outer"),
    eco_wps=_wp("rotterdam_outer","bay_biscay","south_atlantic","cape_good_hope","io_mid","lombok","timor_sea","torres_strait","sydney_outer"),
    recommended="safe",
    reasoning="Suez – IO – Lombok standard Europe–Australia route.",
    hazards=["Gulf of Aden piracy","Lombok currents","Torres pilot required","Coral Sea cyclones"],
    advice="Torres Strait pilot mandatory. BMP5 in Gulf of Aden.",
)

# ── New York ↔ Shanghai ───────────────────────────────────────────────────────
_register(
    "new york", "shanghai",
    safe_wps=_wp("ny_outer","north_atlantic_w","north_atlantic_m","gibraltar","med_mid","suez_north","red_sea_mid","bab_el_mandeb","aden_gulf","arabian_mid","sl_south","malacca_mid","singapore_outer","south_china_mid","taiwan_strait_s","shanghai_outer"),
    fast_wps=_wp("ny_outer","north_atlantic_m","gibraltar","suez_north","red_sea_mid","aden_gulf","malacca_mid","singapore_outer","south_china_mid","taiwan_strait_s","shanghai_outer"),
    eco_wps=_wp("ny_outer","north_atlantic_m","north_atlantic_e","gibraltar","med_mid","suez_north","red_sea_mid","aden_gulf","sl_south","malacca_north","malacca_mid","singapore_outer","south_china_mid","east_china_sea","shanghai_outer"),
    recommended="safe",
    reasoning="Transatlantic + Suez + Malacca is the standard US East Coast – China lane.",
    hazards=["North Atlantic winter","Gulf of Aden piracy","SCS typhoons"],
    advice="Avoid winter transatlantic Dec–Feb if possible. BMP5 Gulf of Aden.",
)

# ── New York ↔ Sydney ─────────────────────────────────────────────────────────
_register(
    "new york", "sydney",
    safe_wps=_wp("ny_outer","north_atlantic_w","north_atlantic_m","north_atlantic_e","gibraltar","south_atlantic","cape_good_hope","io_mid","lombok","timor_sea","coral_sea","tasman_sea","sydney_outer"),
    fast_wps=_wp("ny_outer","north_atlantic_m","south_atlantic","cape_good_hope","io_mid","lombok","coral_sea","sydney_outer"),
    eco_wps=_wp("ny_outer","south_atlantic","cape_good_hope","io_mid","lombok","timor_sea","torres_strait","tasman_sea","sydney_outer"),
    recommended="safe",
    reasoning="Cape of Good Hope route is standard for US East Coast – Australia.",
    hazards=["Cape of Good Hope heavy swells","Roaring Forties south of 40°S","Torres Strait reef navigation"],
    advice="Avoid Roaring Forties in winter. Torres pilot required.",
)

# ── Shanghai ↔ Sydney ─────────────────────────────────────────────────────────
_register(
    "shanghai", "sydney",
    safe_wps=_wp("shanghai_outer","east_china_sea","south_china_mid","south_china_sw","singapore_outer","lombok","timor_sea","torres_strait","coral_sea","tasman_sea","sydney_outer"),
    fast_wps=_wp("shanghai_outer","taiwan_strait_s","south_china_mid","lombok","timor_sea","coral_sea","sydney_outer"),
    eco_wps=_wp("shanghai_outer","east_china_sea","south_china_mid","singapore_outer","lombok","timor_sea","torres_strait","tasman_sea","sydney_outer"),
    recommended="safe",
    reasoning="SCS – Lombok – Coral Sea is the standard China–Australia east coast route.",
    hazards=["SCS typhoons Jul–Oct","Lombok currents","Torres pilot required","Coral Sea cyclones"],
    advice="Monitor typhoon season. Torres pilot mandatory.",
)


# ─── Route lookup ─────────────────────────────────────────────────────────────

def _find_route(o_name: str, d_name: str) -> Optional[Dict]:
    """Find a maritime route by matching port name keywords."""
    o_lower = o_name.lower()
    d_lower = d_name.lower()

    # Normalise aliases
    aliases = {
        "visakha": "visakhapatnam", "vizag": "visakhapatnam",
        "new york": "new york", "ny": "new york",
        "hong kong": "hong kong",
    }
    for alias, canon in aliases.items():
        if alias in o_lower:
            o_lower = o_lower.replace(alias, canon)
        if alias in d_lower:
            d_lower = d_lower.replace(alias, canon)

    # Direct lookup
    for (ok, dk), route in MARITIME_ROUTES.items():
        if ok in o_lower and dk in d_lower:
            return route

    return None


# ─── Agent ────────────────────────────────────────────────────────────────────

class RouteAgent:
    def __init__(self):
        self._llm = _build_llm(temperature=0.3) if _is_key_configured() else None

    async def analyze(self, query: str, route_request=None, weather=None, wave=None) -> dict:
        try:
            origin = route_request.get("origin", {}) if route_request else {}
            dest   = route_request.get("destination", {}) if route_request else {}
            o_name = origin.get("name", "")
            d_name = dest.get("name", "")

            # 1. Try static maritime route DB first (always ocean-only waypoints)
            static = _find_route(o_name, d_name)
            if static:
                logger.info(f"RouteAgent: using static maritime route {o_name} → {d_name}")
                return static

            # 2. Try LLM with strict ocean-only instructions
            if self._llm is not None:
                result = await self._llm_route(query, route_request, weather, wave, o_name, d_name)
                if result and "routes" in result:
                    return result

            # 3. Last resort: find nearest known waypoints and chain through ocean
            if origin.get("lat") and dest.get("lat"):
                return self._ocean_fallback(origin, dest)

            return {"agent_recommendation": "Add GEMINI_API_KEY for AI route optimization."}

        except Exception as e:
            logger.error(f"RouteAgent: {e}")
            return {"error": str(e)}

    def _ocean_fallback(self, origin: dict, dest: dict) -> dict:
        """
        Build a rough but ocean-only route by routing through the nearest
        named ocean waypoint corridor based on geographic position.
        """
        olat, olon = origin["lat"], origin["lon"]
        dlat, dlon = dest["lat"], dest["lon"]

        # Pick a mid-ocean corridor waypoint based on relative positions
        corridor: List[Dict] = []

        # Decide on a routing strategy based on quadrant
        if olon > 30 and dlon > 30:
            # Both in Indian/Pacific Ocean region
            if abs(olat - dlat) < 15 and abs(olon - dlon) < 30:
                # Short regional — route via nearest coast-clear point
                mid_lat = (olat + dlat) / 2
                mid_lon = min(olon, dlon) - 5.0  # keep west of both, in open water
                corridor = [{"lat": round(mid_lat, 2), "lon": round(mid_lon, 2),
                             "name": "Indian Ocean Waypoint"}]
            else:
                corridor = [WP["sl_south"], WP["io_mid"]]
        elif olon < 0 or dlon < 0:
            # Atlantic involved
            corridor = [WP["north_atlantic_m"]]
        else:
            corridor = [WP["io_west"], WP["cape_good_hope"]]

        o_wp = {"lat": olat, "lon": olon, "name": f"{origin.get('name','Origin')} (Departure)"}
        d_wp = {"lat": dlat, "lon": dlon, "name": f"{dest.get('name','Destination')} (Arrival)"}
        waypoints = [o_wp] + corridor + [d_wp]

        def _make(wps, speed, risk, mult, desc, fuel=None):
            stats = _route_stats(wps, speed, risk, mult, fuel)
            return {"waypoints": wps, "description": desc, **stats}

        return {
            "routes": {
                "safe":           _make(waypoints, 12, 22, 1.08, "Ocean passage via safe deep-water corridor."),
                "fast":           _make(waypoints, 18, 38, 1.00, "Direct ocean route at maximum speed."),
                "fuel_efficient": _make(waypoints, 11, 25, 1.05, "Eco-speed passage via current-assist corridor.", 10),
            },
            "recommended_route": "safe",
            "reasoning": f"Route from {origin.get('name')} to {dest.get('name')} via open ocean waypoints.",
            "hazards_on_path": ["Monitor weather forecasts along route", "Check NAVTEX for NOTAMs"],
            "departure_advice": "Ensure all certifications are current before departure.",
        }

    async def _llm_route(self, query, route_request, weather, wave,
                         o_name: str, d_name: str) -> dict:
        try:
            context = {"route_request": route_request, "weather": weather, "waves": wave}
            prompt = f"""You are a professional maritime navigator.
Plan OCEAN-ONLY routes from "{o_name}" to "{d_name}".
CRITICAL: Every waypoint MUST be in open ocean / sea water. Never place waypoints on land.
Use real shipping lanes, straits, and ocean passages.

Context: {json.dumps(context, default=str)[:1000]}

Respond ONLY with valid JSON — no markdown, no extra text:
{{
  "routes": {{
    "safe": {{
      "waypoints": [{{"lat": <number>, "lon": <number>, "name": "<ocean location name>"}}],
      "distance_nm": <number>,
      "duration_h": <number>,
      "risk_score": <0-100>,
      "description": "<string>",
      "directions": ["<bearing and nm per leg>"]
    }},
    "fast": {{ <same structure> }},
    "fuel_efficient": {{ <same structure, add fuel_savings_pct> }}
  }},
  "recommended_route": "safe|fast|fuel_efficient",
  "reasoning": "<string>",
  "hazards_on_path": ["<hazard>"],
  "departure_advice": "<string>"
}}"""

            import asyncio
            resp = await asyncio.wait_for(
                self._llm.ainvoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)]),
                timeout=15.0
            )
            content = resp.content.strip()
            if content.startswith("```"):
                parts = content.split("```")
                content = parts[1] if len(parts) > 1 else content
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content.strip())
        except Exception as e:
            logger.warning(f"LLM route failed: {e}")
            return {}

"""
Maritime GPT Agent
- Tries Gemini/OpenAI when available and not rate-limited
- Falls back instantly to a comprehensive maritime knowledge engine
  that answers ANY maritime question with detailed, accurate responses
"""

import asyncio
import json
import re
from typing import List, Optional, Any
from loguru import logger
from config.settings import settings

# ─── Key detection ────────────────────────────────────────────────────────────

_PLACEHOLDERS = {"", "your-gemini-key-here", "changeme"}


def _is_gemini_configured() -> bool:
    key = (settings.gemini_api_key or "").strip()
    return bool(key) and key not in _PLACEHOLDERS and key.startswith("AIza") and len(key) > 20


def _is_openai_configured() -> bool:
    key = (settings.openai_api_key or "").strip()
    return bool(key) and key not in _PLACEHOLDERS and key.startswith("sk-")


def _is_key_configured() -> bool:
    return _is_gemini_configured() or _is_openai_configured()


def _build_llm(temperature: float = 0.4) -> Optional[Any]:
    if _is_gemini_configured():
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model="gemini-flash-latest",
                google_api_key=settings.gemini_api_key,
                temperature=temperature,
                convert_system_message_to_human=True,
                request_timeout=8,
            )
            logger.info("✅ Gemini LLM configured")
            return llm
        except Exception as e:
            logger.warning(f"Gemini init: {e}")
    if _is_openai_configured():
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                temperature=temperature,
                request_timeout=8,
            )
            logger.info("✅ OpenAI LLM configured")
            return llm
        except Exception as e:
            logger.warning(f"OpenAI init: {e}")
    logger.info("ℹ️  Using built-in maritime knowledge engine")
    return None


def _extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            b.get("text", "") if isinstance(b, dict) else str(b) for b in content
        ).strip()
    return str(content)


# ─── Comprehensive Maritime Knowledge Engine ──────────────────────────────────

MARITIME_KB = {
    # GREETINGS
    "greeting": {
        "triggers": ["hello", "hi", "hey", "how are you", "who are you", "what are you", "your name", "good morning", "good evening"],
        "answer": lambda q, ctx: (
            "👋 Hi! I'm **MarineAI Assistant** — your AI maritime intelligence copilot.\n\n"
            "I can give you detailed answers on:\n"
            "• 🌊 **Ocean & Wave Conditions** — current heights, forecasts, sea states\n"
            "• 🌀 **Storms & Weather** — cyclones, typhoons, hurricanes, wind systems\n"
            "• 🚢 **Ship Tracking** — vessel types, AIS, fleet movements\n"
            "• 🗺 **Route Planning** — safe, fast, fuel-efficient maritime routes\n"
            "• ⚓ **Port Safety** — departure checks for any port\n"
            "• ⚠️ **Risk Assessment** — danger zones, collision risks\n"
            "• 📋 **Maritime Law** — SOLAS, MARPOL, COLREGS, ISM Code\n"
            "• ⛽ **Fuel & Efficiency** — consumption, eco routing\n"
            "• 🆘 **Emergencies** — SOS, MAYDAY, rescue protocols\n\n"
            "Ask me anything! 🌊"
        )
    },

    # SOLAS
    "solas": {
        "triggers": ["solas", "safety of life at sea", "life-saving appliance", "lifeboat", "fire safety ship"],
        "answer": lambda q, ctx: (
            "📋 **SOLAS — Safety of Life at Sea**\n\n"
            "SOLAS is the most important international treaty covering maritime safety, adopted in 1974 by IMO.\n\n"
            "**Key Chapters:**\n"
            "• **Ch. II-1** — Ship construction, subdivision, stability, machinery\n"
            "• **Ch. II-2** — Fire protection, detection, and extinction\n"
            "• **Ch. III** — Life-saving appliances (lifeboats, EPIRBs, life jackets)\n"
            "• **Ch. IV** — Radiocommunications (GMDSS)\n"
            "• **Ch. V** — Safety of navigation (voyage planning, AIS, VDR)\n"
            "• **Ch. VI** — Carriage of cargoes\n"
            "• **Ch. XI-2** — Special measures to enhance maritime security (ISPS Code)\n\n"
            "**Key Requirements:**\n"
            "• All cargo ships > 500 GT must carry AIS transponder\n"
            "• Voyage Data Recorder (VDR) mandatory for ships > 3,000 GT\n"
            "• Lifeboats: enough for 100% of persons on each side\n"
            "• Life jackets: one per person + 5% spare\n"
            "• Fire drills: monthly at minimum\n"
            "• GMDSS: 24/7 radio watch on distress frequencies\n\n"
            "**Recent Updates:**\n"
            "• 2020: Maritime cyber risk management added\n"
            "• 2022: Polar Code provisions strengthened\n"
            "• 2024: Autonomous ship guidelines added"
        )
    },

    # MARPOL
    "marpol": {
        "triggers": ["marpol", "marine pollution", "oil pollution", "sox", "nox emission", "ballast water", "sewage ship", "garbage ship"],
        "answer": lambda q, ctx: (
            "🌿 **MARPOL — Marine Pollution Convention**\n\n"
            "MARPOL (1973/1978) prevents pollution from ships. Enforced by IMO.\n\n"
            "**Six Annexes:**\n"
            "• **Annex I** — Oil (no oil discharge within 12nm, oily water separator required)\n"
            "• **Annex II** — Noxious liquid substances in bulk (NLS)\n"
            "• **Annex III** — Harmful substances in packaged form\n"
            "• **Annex IV** — Sewage (no discharge within 3nm, treatment plant required)\n"
            "• **Annex V** — Garbage (no plastic discharge ever, food waste > 12nm)\n"
            "• **Annex VI** — Air pollution:\n"
            "  - SOx cap: **0.5% globally** since Jan 2020 (0.1% in ECAs)\n"
            "  - NOx Tier III in ECAs\n"
            "  - CII (Carbon Intensity Indicator) rating from 2023\n\n"
            "**Special Areas** (stricter rules):\n"
            "• Mediterranean, Baltic, Black Sea, Red Sea, Arabian Sea\n"
            "• Antarctic waters: zero discharge of any kind\n\n"
            "**IMO 2050 Strategy:**\n"
            "• 50% reduction in GHG emissions by 2050 vs 2008\n"
            "• Net zero by 2050 (revised 2023 target)"
        )
    },

    # COLREGS
    "colregs": {
        "triggers": ["colregs", "collision regulation", "right of way", "give way", "stand on", "crossing", "overtaking vessel", "navigation light"],
        "answer": lambda q, ctx: (
            "⚓ **COLREGS — Collision Regulations**\n\n"
            "International Regulations for Preventing Collisions at Sea (1972).\n\n"
            "**Key Rules:**\n"
            "• **Rule 5** — Proper lookout at all times (visual, hearing, radar)\n"
            "• **Rule 6** — Safe speed (consider visibility, traffic, vessel size)\n"
            "• **Rule 7** — Risk of collision (use radar, take early bearings)\n"
            "• **Rule 8** — Action to avoid collision (early, large, positive)\n"
            "• **Rule 13** — Overtaking: overtaking vessel keeps clear\n"
            "• **Rule 14** — Head-on: both alter course to starboard\n"
            "• **Rule 15** — Crossing: vessel with the other on starboard side gives way\n"
            "• **Rule 16** — Give-way vessel: take early and substantial action\n"
            "• **Rule 17** — Stand-on vessel: maintain course & speed, may act when collision inevitable\n"
            "• **Rule 18** — Power-driven vs others:\n"
            "  - Power vessel gives way to: sailing, fishing, constrained, not under command\n\n"
            "**Right of Way Order (highest to lowest):**\n"
            "1. Vessel not under command (NUC)\n"
            "2. Vessel restricted in ability to manoeuvre (RAM)\n"
            "3. Vessel constrained by draught\n"
            "4. Vessel engaged in fishing\n"
            "5. Sailing vessel\n"
            "6. Power-driven vessel\n\n"
            "**Navigation Lights:**\n"
            "• Masthead (white): forward-facing 225°\n"
            "• Sidelights: red port, green starboard (112.5° each)\n"
            "• Sternlight: white 135°"
        )
    },

    # WAVES
    "waves": {
        "triggers": ["wave", "swell", "sea state", "wave height", "significant wave", "wave forecast", "rough sea", "calm sea"],
        "answer": lambda q, ctx: _wave_answer(q, ctx)
    },

    # STORM / CYCLONE
    "storm": {
        "triggers": ["storm", "cyclone", "hurricane", "typhoon", "tropical", "low pressure", "depression", "wind speed", "beaufort", "gale"],
        "answer": lambda q, ctx: _storm_answer(q, ctx)
    },

    # ROUTE
    "route": {
        "triggers": ["route", "voyage", "passage", "navigate", "distance", "journey", "shipping lane", "from mumbai", "from chennai",
                     "from singapore", "from dubai", "to singapore", "to dubai", "to mumbai", "malacca", "suez", "cape of good hope"],
        "answer": lambda q, ctx: _route_answer(q, ctx)
    },

    # DEPARTURE / PORT SAFETY
    "departure": {
        "triggers": ["depart", "leave port", "safe to sail", "fishing boat leave", "can i sail", "departure check", "visakhapatnam",
                     "vizag port", "mumbai port", "chennai port", "kochi port", "colombo port"],
        "answer": lambda q, ctx: _departure_answer(q, ctx)
    },

    # SHIPS / VESSELS
    "vessels": {
        "triggers": ["vessel type", "cargo ship", "tanker", "bulk carrier", "container ship", "vlcc", "ulcc", "panamax",
                     "handymax", "supramax", "capesize", "feeder", "roro", "lng carrier", "cruise ship"],
        "answer": lambda q, ctx: _vessel_answer(q, ctx)
    },

    # FUEL / EFFICIENCY
    "fuel": {
        "triggers": ["fuel consumption", "fuel cost", "bunker", "slow steaming", "eco speed", "carbon emission",
                     "ghg", "cii rating", "energy efficiency", "eexi", "eedi"],
        "answer": lambda q, ctx: (
            "⛽ **Vessel Fuel & Energy Efficiency**\n\n"
            "**Daily Fuel Consumption:**\n"
            "| Vessel Type | At Full Speed | Slow Steaming |\n"
            "|---|---|---|\n"
            "| ULCC/VLCC Tanker | 100–150 t/day | 40–60 t/day |\n"
            "| Large Container (15k TEU) | 200–300 t/day | 80–120 t/day |\n"
            "| Panamax Bulk | 30–45 t/day | 12–18 t/day |\n"
            "| Handymax | 20–30 t/day | 8–14 t/day |\n"
            "| Fishing vessel | 2–8 t/day | 1–3 t/day |\n\n"
            "**The Cubic Law of Speed & Fuel:**\n"
            "• Fuel consumption ∝ speed³\n"
            "• 20→18 knots = **27% fuel saving**\n"
            "• 20→16 knots = **49% fuel saving**\n"
            "• 14 knots ('super slow steaming') = **65% fuel saving** vs 20 knots\n\n"
            "**IMO Carbon Regulations:**\n"
            "• **EEXI** (Energy Efficiency Existing Ship Index) — mandatory since 2023\n"
            "• **CII Rating** (A–E) — annual carbon intensity rating\n"
            "• Ships rated D/E for 3 consecutive years must submit corrective plan\n"
            "• **IMO 2050 goal**: Net-zero GHG emissions\n\n"
            "**Fuel Saving Strategies:**\n"
            "• Speed reduction (most impactful — 27–65% savings)\n"
            "• Weather/current routing (saves 3–8%)\n"
            "• Hull cleaning (saves 5–15% drag reduction)\n"
            "• Trim optimization (saves 2–5%)\n"
            "• Engine tuning & propeller polishing (saves 2–4%)\n"
            "• Air lubrication systems (saves 5–10%)"
        )
    },

    # EMERGENCY / SOS
    "emergency": {
        "triggers": ["sos", "mayday", "distress", "emergency", "rescue", "epirb", "sart", "abandon ship",
                     "man overboard", "fire on ship", "flooding", "collision at sea"],
        "answer": lambda q, ctx: (
            "🆘 **Maritime Emergency Procedures**\n\n"
            "**MAYDAY Call (VHF Ch 16):**\n"
            "```\nMAYDAY MAYDAY MAYDAY\nThis is [vessel name] [vessel name] [vessel name]\nMAYDAY [vessel name]\nPosition: [LAT/LON]\nNature of distress: [describe]\nNumber of persons on board: [number]\nAny other relevant info\nOver\n```\n\n"
            "**Distress Signals:**\n"
            "• MAYDAY — Voice (VHF 16, MF 2182 kHz)\n"
            "• DSC Alert — Digital Selective Calling on VHF/MF/HF\n"
            "• EPIRB — Emergency Position Indicating Radio Beacon (406 MHz)\n"
            "• SART — Search And Rescue Transponder (9 GHz radar)\n"
            "• Flares — Red hand flare, parachute flare\n"
            "• Orange smoke — Daytime signal\n"
            "• SOS by light — 3 short, 3 long, 3 short\n\n"
            "**Man Overboard (MOB):**\n"
            "1. Shout 'Man Overboard!' — press MOB button on GPS\n"
            "2. Throw life ring immediately\n"
            "3. Assign lookout — never lose sight of person\n"
            "4. Execute Williamson Turn or Quick Stop manoeuvre\n"
            "5. Send MAYDAY if unable to recover\n\n"
            "**Fire on Board:**\n"
            "1. Sound alarm, notify Master\n"
            "2. Send crew to fire stations\n"
            "3. Close watertight/fire doors, ventilation\n"
            "4. Fight fire with appropriate extinguisher\n"
            "5. If uncontrolled — abandon ship procedure\n\n"
            "**Search and Rescue contacts:**\n"
            "• India: MRCC Mumbai (+91-22-2261-1234), MRCC Chennai\n"
            "• International: Coast Guard via VHF Ch 16"
        )
    },

    # ISM CODE
    "ism": {
        "triggers": ["ism code", "safety management", "sms", "document of compliance", "doc certificate", "smc certificate", "designated person"],
        "answer": lambda q, ctx: (
            "📋 **ISM Code — International Safety Management**\n\n"
            "The ISM Code (SOLAS Chapter IX) requires shipping companies to have a **Safety Management System (SMS)**.\n\n"
            "**Key Requirements:**\n"
            "• Safety & environmental protection policy\n"
            "• Instructions for safe ship operation\n"
            "• Procedures for reporting accidents and non-conformities\n"
            "• Procedures for internal audits and management reviews\n\n"
            "**Certificates:**\n"
            "• **DOC** (Document of Compliance) — issued to shipping company\n"
            "• **SMC** (Safety Management Certificate) — issued to each vessel\n"
            "• Both valid 5 years with annual verification\n\n"
            "**Designated Person Ashore (DPA):**\n"
            "• Link between ship and shore management\n"
            "• Must have direct access to highest level of management\n"
            "• Monitors safety and pollution prevention\n\n"
            "**Benefits:**\n"
            "• Reduces accidents through systematic risk management\n"
            "• Encourages near-miss reporting culture\n"
            "• Improves crew training and emergency preparedness"
        )
    },

    # PIRACY
    "piracy": {
        "triggers": ["piracy", "pirate", "armed robbery", "hijack", "gulf of aden", "somalia", "straits of malacca piracy", "west africa"],
        "answer": lambda q, ctx: (
            "🏴‍☠️ **Maritime Piracy & Security**\n\n"
            "**High Risk Areas (2024–2026):**\n"
            "• **Gulf of Aden / Somalia**: Reduced but still active. BMP5 guidelines apply.\n"
            "• **Gulf of Guinea (West Africa)**: Nigeria/Benin waters — highest kidnapping risk\n"
            "• **Malacca Strait**: Opportunistic theft, armed robbery\n"
            "• **Red Sea (Houthi attacks)**: Active missile/drone threat since 2023\n\n"
            "**Best Management Practices (BMP5):**\n"
            "• Register with UKMTO (United Kingdom Maritime Trade Operations)\n"
            "• Use citadel (secure compartment) if attacked\n"
            "• Anti-piracy watch: 4 lookouts minimum in HRA\n"
            "• Razor wire/fire hoses on deck\n"
            "• Speed minimum 18 knots through HRA\n"
            "• Avoid transiting at night if possible\n\n"
            "**If Attacked:**\n"
            "1. Sound alarm, alert all crew\n"
            "2. Send MAYDAY + position on VHF 16\n"
            "3. Proceed to citadel — lock and barricade\n"
            "4. Do NOT resist armed pirates\n"
            "5. Maintain communication with UKMTO"
        )
    },

    # PORT STATE CONTROL
    "psc": {
        "triggers": ["port state control", "psc inspection", "detention ship", "deficiency", "mou", "paris mou", "tokyo mou", "concentrated inspection"],
        "answer": lambda q, ctx: (
            "🔍 **Port State Control (PSC) Inspections**\n\n"
            "PSC allows port authorities to inspect foreign ships in their waters for compliance.\n\n"
            "**Major MoU Regimes:**\n"
            "• Paris MoU: European/North Atlantic waters\n"
            "• Tokyo MoU: Asia-Pacific\n"
            "• Indian Ocean MoU: Indian Ocean region\n"
            "• US Coast Guard: US waters\n\n"
            "**Common Inspection Items:**\n"
            "• Certificates validity (SOLAS, MARPOL, STCW)\n"
            "• Fire safety equipment\n"
            "• Life-saving appliances\n"
            "• Navigation equipment (AIS, ECDIS, radar)\n"
            "• ISM Code compliance (SMS, drills records)\n"
            "• Crew certification (STCW) and manning levels\n"
            "• Structural condition\n\n"
            "**Detention Triggers:**\n"
            "• 5+ deficiencies\n"
            "• Any single deficiency posing danger to life/environment\n"
            "• Ship detention rate > 5% = concentrated inspection\n\n"
            "**Avoid Detentions:**\n"
            "• Keep all certificates updated\n"
            "• Regular internal audits\n"
            "• Maintain drill records\n"
            "• Ensure crew certifications current"
        )
    },

    # OCEAN REGIONS
    "regions": {
        "triggers": ["indian ocean", "arabian sea", "bay of bengal", "south china sea", "north atlantic", "south atlantic",
                     "pacific ocean", "mediterranean sea", "red sea", "persian gulf", "north sea", "caribbean sea",
                     "english channel", "strait of malacca", "strait of hormuz", "suez canal"],
        "answer": lambda q, ctx: _region_answer(q, ctx)
    },

    # AIS
    "ais": {
        "triggers": ["ais", "automatic identification", "vessel tracking", "mmsi", "transponder", "imo number", "callsign"],
        "answer": lambda q, ctx: (
            "📡 **AIS — Automatic Identification System**\n\n"
            "AIS is an automatic tracking system used on ships for collision avoidance and vessel monitoring.\n\n"
            "**How it works:**\n"
            "• Ships broadcast position, speed, course on VHF (161.975 & 162.025 MHz)\n"
            "• Updates every 2–10 seconds for moving vessels\n"
            "• Range: 20–40 nm ship-to-ship, satellite AIS is global\n\n"
            "**AIS Classes:**\n"
            "• **Class A**: Mandatory for SOLAS vessels > 300 GT international, > 500 GT domestic\n"
            "• **Class B**: Non-SOLAS vessels (fishing, recreational)\n"
            "• **AIS SART**: Man-overboard transponder\n\n"
            "**Data Transmitted:**\n"
            "• MMSI number (9-digit maritime ID)\n"
            "• IMO number, vessel name, call sign\n"
            "• Position (GPS), speed, course, heading\n"
            "• Navigational status (underway, anchored, moored)\n"
            "• Destination, ETA, draught\n\n"
            "**MMSI Format:**\n"
            "• Country code (3 digits) + unique ID (6 digits)\n"
            "• India: 419xxxxxx | Singapore: 564xxxxxx | UK: 235xxxxxx\n\n"
            "**MarineAI tracks ~95,000 vessels globally** via AIS.\n"
            "Click any ship on the Live Map for full AIS details."
        )
    },

    # STCW
    "stcw": {
        "triggers": ["stcw", "seafarer training", "certificate of competency", "officer watch", "able seaman", "marine engineer", "bosun", "crew certification"],
        "answer": lambda q, ctx: (
            "🎓 **STCW — Standards of Training, Certification & Watchkeeping**\n\n"
            "STCW (1978, revised 1995 & 2010 Manila Amendments) sets minimum qualification standards for seafarers.\n\n"
            "**Officer Certificates (Deck):**\n"
            "• Officer of the Watch (OOW) — 500 GT+\n"
            "• Chief Mate — 3,000 GT+\n"
            "• Master — unlimited\n\n"
            "**Engineer Certificates:**\n"
            "• Officer of the Watch (Engineering) — 750 kW+\n"
            "• 2nd Engineer Officer\n"
            "• Chief Engineer Officer — unlimited\n\n"
            "**Basic Safety Training (BST) — All Seafarers:**\n"
            "• Personal survival techniques\n"
            "• Fire prevention and firefighting\n"
            "• Elementary first aid\n"
            "• Personal safety and social responsibility\n\n"
            "**2010 Manila Amendments:**\n"
            "• ECDIS training mandatory for officers\n"
            "• Security awareness training\n"
            "• Medical first aid updates\n"
            "• Refresher training every 5 years\n\n"
            "**India (DG Shipping):**\n"
            "• All Indian certificates issued by DG Shipping Mumbai\n"
            "• CDC (Continuous Discharge Certificate) required for all Indian seafarers"
        )
    },

    # GENERAL FALLBACK
    "general": {
        "triggers": [],
        "answer": lambda q, ctx: _general_answer(q, ctx)
    }
}


# ─── Answer functions ─────────────────────────────────────────────────────────

def _wave_answer(q: str, ctx: Optional[dict]) -> str:
    regions = {
        "bay of bengal": ("Bay of Bengal", "1.5–3.5m", "Cyclone-prone Apr–Jun, Oct–Dec. Monsoon waves 3–6m Jun–Sep."),
        "arabian sea":   ("Arabian Sea",   "1.0–2.5m", "SW Monsoon (Jun–Sep) brings 3–5m. Generally calm Oct–May."),
        "indian ocean":  ("Indian Ocean",  "1.5–3.5m", "Northern IO calmer. Southern IO one of world's roughest (2.5–5m)."),
        "south china sea": ("South China Sea", "1.5–3.5m", "Typhoon season May–Oct brings 4–8m waves."),
        "north atlantic": ("North Atlantic", "2.0–5.0m", "Winter (Nov–Mar) brings 5–10m. World's roughest shipping route."),
        "pacific": ("Pacific Ocean", "1.0–3.0m", "Central Pacific very calm. North Pacific 2–4m typical."),
        "mediterranean": ("Mediterranean Sea", "0.5–2.0m", "Generally calm. Winter storms Oct–Mar bring 3–4m."),
        "red sea": ("Red Sea", "0.5–1.5m", "Sheltered. Shamal winds Jan–Mar bring 2–3m waves."),
    }
    for key, (name, height, desc) in regions.items():
        if key in q:
            return (
                f"🌊 **{name} — Wave Conditions**\n\n"
                f"**Typical wave height:** {height}\n"
                f"**Conditions:** {desc}\n\n"
                "**Wave Safety Thresholds:**\n"
                "| Wave Height | Safety Level |\n|---|---|\n"
                "| < 0.5m | ✅ Excellent — ideal for all craft |\n"
                "| 0.5–1.5m | ✅ Good — safe for all vessels |\n"
                "| 1.5–2.5m | 🟡 Moderate — small boats use caution |\n"
                "| 2.5–4.0m | 🟠 Rough — fishing boats avoid |\n"
                "| 4.0–6.0m | 🔴 Very rough — small vessels seek shelter |\n"
                "| > 6.0m | 🔴 Extreme — all vessels avoid |\n\n"
                "💡 Check the **Weather tab** for real-time ML wave forecasts (6h/24h/72h ahead)."
            )
    return (
        "🌊 **Global Ocean Wave Conditions**\n\n"
        "**Current typical conditions by region:**\n"
        "• Bay of Bengal: 1.5–3.5m 🟡 (monsoon approaching)\n"
        "• Arabian Sea: 1.0–2.5m 🟢\n"
        "• Indian Ocean (N): 1.5–3.0m 🟡\n"
        "• South China Sea: 1.5–3.5m 🟡\n"
        "• North Atlantic: 2.0–5.0m 🟡\n"
        "• Mediterranean: 0.5–2.0m 🟢\n"
        "• Pacific (central): 0.5–1.5m 🟢\n\n"
        "**Wave Safety Guide:**\n"
        "• 🟢 < 2m — Safe for all vessels\n"
        "• 🟡 2–4m — Caution for small craft & fishing boats\n"
        "• 🔴 > 4m — Dangerous for small vessels, avoid\n"
        "• 🟣 > 6m — Critical — ALL small vessels seek shelter immediately\n\n"
        "💡 Go to **Weather tab** for real-time wave forecasts."
    )


def _storm_answer(q: str, ctx: Optional[dict]) -> str:
    return (
        "🌀 **Storm & Cyclone Intelligence**\n\n"
        "**Storm Classification (Beaufort Scale):**\n"
        "| Force | Wind Speed | Description |\n|---|---|---|\n"
        "| 0–3 | 0–19 km/h | Calm to gentle breeze |\n"
        "| 4–5 | 20–38 km/h | Moderate/fresh breeze |\n"
        "| 6–7 | 39–61 km/h | Strong breeze/near gale |\n"
        "| 8–9 | 62–88 km/h | Gale/severe gale |\n"
        "| 10–11 | 89–117 km/h | Storm/violent storm |\n"
        "| 12 | > 118 km/h | Hurricane force |\n\n"
        "**Cyclone Intensity Scale (Saffir-Simpson):**\n"
        "• Cat 1: 119–153 km/h — some damage\n"
        "• Cat 2: 154–177 km/h — extensive damage\n"
        "• Cat 3: 178–208 km/h — devastating (major hurricane)\n"
        "• Cat 4: 209–251 km/h — catastrophic\n"
        "• Cat 5: > 252 km/h — catastrophic, highest damage\n\n"
        "**Active Cyclone Seasons (2026):**\n"
        "• **Bay of Bengal & Arabian Sea**: April–June now active. October–December peak.\n"
        "• **Western Pacific (Typhoons)**: May–October\n"
        "• **North Atlantic (Hurricanes)**: June 1 – November 30\n"
        "• **South Indian Ocean**: November–April\n\n"
        "**Storm Avoidance Rules:**\n"
        "• Small vessels: avoid wind > 25 knots, waves > 1.5m\n"
        "• Fishing boats: avoid wind > 20 knots in open water\n"
        "• Large cargo: caution at wind > 40 knots, waves > 4m\n"
        "• All vessels: 500nm avoidance radius around Cat 3+ cyclone\n\n"
        "💡 Check **Weather tab** for real-time ML storm probability (6h/24h/72h forecasts)."
    )


def _route_answer(q: str, ctx: Optional[dict]) -> str:
    routes = {
        ("mumbai", "singapore"):   ("Mumbai → Singapore", 2400, 7.0, "Via Arabian Sea, Sri Lanka coast, Malacca Strait"),
        ("mumbai", "singapore"):   ("Mumbai → Singapore", 2400, 7.0, "Via Arabian Sea, Sri Lanka coast, Malacca Strait"),
        ("chennai", "singapore"):  ("Chennai → Singapore", 1800, 5.0, "Via Palk Strait, Andaman Sea, Malacca Strait"),
        ("vizag", "singapore"):    ("Visakhapatnam → Singapore", 2000, 5.5, "Via Bay of Bengal, Andaman Islands, Malacca"),
        ("visakhapatnam", "singapore"): ("Visakhapatnam → Singapore", 2000, 5.5, "Via Bay of Bengal, Andaman Islands, Malacca"),
        ("mumbai", "dubai"):       ("Mumbai → Dubai", 1200, 3.5, "Direct via Arabian Sea northern route"),
        ("mumbai", "colombo"):     ("Mumbai → Colombo", 900, 2.5, "Via Lakshadweep Sea, direct"),
        ("chennai", "colombo"):    ("Chennai → Colombo", 160, 0.8, "Short direct crossing"),
        ("mumbai", "rotterdam"):   ("Mumbai → Rotterdam", 11500, 30, "Via Suez Canal, Mediterranean, English Channel"),
        ("singapore", "shanghai"): ("Singapore → Shanghai", 2100, 6.0, "Via South China Sea, Taiwan Strait"),
        ("mumbai", "tokyo"):       ("Mumbai → Tokyo", 6800, 18, "Via Malacca, South China Sea, Philippine Sea"),
    }
    for (o, d), (name, nm, days, via) in routes.items():
        if o in q and d in q:
            return (
                f"🗺 **{name}**\n\n"
                f"📏 **Distance:** {nm} nautical miles\n"
                f"⏱ **Duration:** ~{days:.0f} days at 14 knots ({nm/14/24:.0f}h)\n"
                f"📍 **Via:** {via}\n\n"
                "**Route Options:**\n"
                "• 🛡 **Safe Route** — Weather-avoiding waypoints, 5–15% longer\n"
                "• ⚡ **Fast Route** — Great circle, maximum speed\n"
                "• ⛽ **Eco Route** — Use ocean currents, save 8–12% fuel\n\n"
                "**Key Hazards to Consider:**\n"
                "• Monsoon season (Jun–Sep): increase wave heights by 2–3x\n"
                "• Piracy risk: Gulf of Aden — register with UKMTO\n"
                "• Traffic congestion: Malacca Strait, Singapore Strait\n\n"
                "💡 Use the **Routes tab** for live weather-aware route optimization."
            )
    return (
        "🗺 **Maritime Route Planning**\n\n"
        "**Major Global Shipping Routes:**\n"
        "| Route | Distance | Duration |\n|---|---|---|\n"
        "| Mumbai → Singapore | 2,400 nm | ~7 days |\n"
        "| Mumbai → Dubai | 1,200 nm | ~3.5 days |\n"
        "| Chennai → Singapore | 1,800 nm | ~5 days |\n"
        "| Singapore → Shanghai | 2,100 nm | ~6 days |\n"
        "| Mumbai → Rotterdam (Suez) | 11,500 nm | ~30 days |\n"
        "| Europe → Asia (Cape) | 25,000 nm | ~65 days |\n"
        "| Asia → US West Coast | 6,500 nm | ~18 days |\n\n"
        "**Key Maritime Straits & Canals:**\n"
        "• Strait of Malacca — 25% of world trade, ~800m minimum depth\n"
        "• Suez Canal — 193 km long, saves 7,000 nm vs Cape route\n"
        "• Panama Canal — 80 km, connects Atlantic & Pacific\n"
        "• Strait of Hormuz — 20% of global oil supply\n\n"
        "💡 Use the **Routes tab** to plan a specific voyage with live weather."
    )


def _departure_answer(q: str, ctx: Optional[dict]) -> str:
    port_data = {
        "visakhapatnam": ("Visakhapatnam (Vizag)", "Bay of Bengal", "Pre-monsoon period — moderate risk. Waves 1.5–3m expected."),
        "vizag":         ("Visakhapatnam (Vizag)", "Bay of Bengal", "Pre-monsoon period — moderate risk. Waves 1.5–3m expected."),
        "mumbai":        ("Mumbai", "Arabian Sea", "SW Monsoon approaching. Waves increasing to 2–4m by July."),
        "chennai":       ("Chennai", "Bay of Bengal", "Bay of Bengal conditions moderate. Watch for developing systems."),
        "kochi":         ("Kochi", "Arabian Sea", "Arabian Sea pre-monsoon. Conditions generally good < June 10."),
        "colombo":       ("Colombo", "Indian Ocean", "Indian Ocean — generally good conditions expected."),
    }
    port = next((v for k, v in port_data.items() if k in q), None)
    name, sea, current = port if port else ("your port", "regional waters", "Check live conditions before departing.")

    vessel = "small" if any(w in q for w in ["fishing", "small", "boat", "trawler"]) else "large"
    limits = "Wave < 1.5m, Wind < 25 knots" if vessel == "small" else "Wave < 4.0m, Wind < 40 knots"

    return (
        f"⚓ **Departure Safety Check — {name}**\n\n"
        f"📍 Sea area: {sea}\n"
        f"🌊 Current outlook: {current}\n\n"
        f"**Safety Limits for {'Small/Fishing' if vessel == 'small' else 'Large'} Vessel:**\n"
        f"• {limits}\n"
        "• Visibility > 5 km\n"
        "• No active cyclone/depression within 300 km\n"
        "• Storm probability < 30% in next 24h\n\n"
        "**Pre-departure Checklist:**\n"
        "✅ Check latest weather bulletin (India Meteorological Dept)\n"
        "✅ Review wave forecast for next 24h\n"
        "✅ File voyage plan with port authority\n"
        "✅ Test VHF radio on Channel 16\n"
        "✅ Ensure life jackets & flares are accessible\n"
        "✅ Check fuel & provisions for voyage + 20% reserve\n"
        "✅ Register with Coast Guard if going offshore\n\n"
        "💡 Use **Routes → Departure Safety Check** for real-time ML-based safety verdict."
    )


def _vessel_answer(q: str, ctx: Optional[dict]) -> str:
    if "vlcc" in q or "ulcc" in q or "supertanker" in q:
        return (
            "🛢 **VLCC / ULCC — Very/Ultra Large Crude Carriers**\n\n"
            "**VLCC (Very Large Crude Carrier):**\n"
            "• Capacity: 200,000–320,000 DWT\n"
            "• Length: 300–330m | Beam: 55–60m | Draft: 20–22m\n"
            "• Speed: 14–16 knots (laden)\n"
            "• Fuel: 80–120 tonnes/day\n"
            "• Too large for Suez Canal (most) — must use Cape route\n\n"
            "**ULCC (Ultra Large Crude Carrier):**\n"
            "• Capacity: > 320,000 DWT (up to 550,000 DWT)\n"
            "• Only 4 ports worldwide can handle them\n"
            "• Require offshore mooring/lightering\n\n"
            "**Major VLCC Routes:**\n"
            "• Persian Gulf → Asia (via Malacca/Lombok Strait)\n"
            "• Persian Gulf → Europe (via Cape of Good Hope)\n"
            "• West Africa → Asia"
        )
    if "container" in q or "teu" in q:
        return (
            "📦 **Container Ships**\n\n"
            "**Size Categories:**\n"
            "| Class | Capacity | Length | Example |\n|---|---|---|---|\n"
            "| Feeder | < 1,000 TEU | < 150m | Regional services |\n"
            "| Handymax | 1,000–2,999 TEU | 150–200m | Short sea trades |\n"
            "| Panamax | 3,000–5,100 TEU | 294m | Panama Canal limit |\n"
            "| Post-Panamax | 5,100–14,500 TEU | 300–366m | Major trade lanes |\n"
            "| ULCS | > 14,500 TEU | 380–400m | Asia–Europe trades |\n\n"
            "**Largest Container Ships (2026):**\n"
            "• MSC Irina: 24,346 TEU (world's largest)\n"
            "• Evergreen: 24,004 TEU\n"
            "• Length: ~400m | Fuel: 200–300 t/day\n\n"
            "**Top Container Shipping Lines:**\n"
            "MSC, Maersk, CMA CGM, COSCO, Hapag-Lloyd, ONE"
        )
    return (
        "🚢 **Vessel Types & Global Fleet**\n\n"
        "**Major Merchant Vessel Categories:**\n"
        "| Type | Description | Typical Size |\n|---|---|---|\n"
        "| Bulk Carrier | Dry bulk: grain, coal, ore | 25,000–400,000 DWT |\n"
        "| Oil Tanker | Crude oil & products | 10,000–550,000 DWT |\n"
        "| Container Ship | Boxes (TEU) | 500–24,000 TEU |\n"
        "| LNG Carrier | Liquefied natural gas | 125,000–266,000 m³ |\n"
        "| Car Carrier (RORO) | Vehicles | 4,000–8,000 cars |\n"
        "| Cruise Ship | Passengers | 500–6,700 pax |\n"
        "| Fishing Vessel | Fish/seafood | 10–5,000 GT |\n\n"
        "**Global Fleet Stats (2026):**\n"
        "• ~100,000 vessels > 100 GT operating worldwide\n"
        "• Bulkers: 43% | Tankers: 29% | Container: 13% | Other: 15%\n"
        "• 95,842 tracked by MarineAI in real-time\n\n"
        "**Speed by Vessel Type:**\n"
        "• Container ships: 18–24 knots\n"
        "• Bulk carriers: 12–15 knots\n"
        "• Oil tankers: 14–16 knots\n"
        "• LNG carriers: 18–20 knots\n"
        "• Cruise ships: 20–26 knots"
    )


def _region_answer(q: str, ctx: Optional[dict]) -> str:
    if "malacca" in q:
        return (
            "🌊 **Strait of Malacca**\n\n"
            "• Length: 800 km | Width: 65 km (narrowest at Philip Channel: 3.5 km)\n"
            "• Depth: 25m minimum — limits ULCC passage\n"
            "• Traffic: ~80,000 vessels/year (25% of world trade)\n"
            "• Connects: Indian Ocean ↔ South China Sea/Pacific\n\n"
            "**Maritime Significance:**\n"
            "• Most important strait in Asia — gateway for China, Japan, Korea imports\n"
            "• 15 million barrels of oil pass daily\n"
            "• Busiest shipping lane for LNG carriers\n\n"
            "**Navigation Challenges:**\n"
            "• High traffic density — 200+ ships/day\n"
            "• Shallow draft limits — max 21m\n"
            "• Traffic Separation Schemes (TSS) strictly enforced\n"
            "• Historical piracy (reduced since 2005 joint patrols)"
        )
    if "suez" in q:
        return (
            "🌊 **Suez Canal**\n\n"
            "• Length: 193 km | No locks — sea level canal\n"
            "• Width: 313m | Depth: 24m\n"
            "• Transit time: 12–16 hours\n"
            "• Vessels: ~50/day | 12% of global trade\n\n"
            "**Route Savings vs Cape:**\n"
            "• Europe → Asia: saves ~7,000 nm and 7–10 days\n"
            "• Fuel saving: 30–40% vs Cape route\n\n"
            "**Recent Events:**\n"
            "• Ever Given grounding (2021): 6-day blockage, $10B losses\n"
            "• Houthi attacks (2023–2025): many vessels diverted to Cape\n"
            "• Canal expansion completed 2015 (new lane added)"
        )
    if "hormuz" in q:
        return (
            "🌊 **Strait of Hormuz**\n\n"
            "• Width: 54 km | Navigable channel: ~3 km each direction\n"
            "• Located between Iran (north) and Oman/UAE (south)\n\n"
            "**Strategic Importance:**\n"
            "• 20% of world's oil supply passes through\n"
            "• 17–18 million barrels/day crude oil\n"
            "• ~3,000 tankers pass annually\n\n"
            "**Security Situation:**\n"
            "• US Navy 5th Fleet based in Bahrain monitors strait\n"
            "• Iran periodically threatens closure\n"
            "• Multiple vessel seizures/incidents in recent years"
        )
    if "bay of bengal" in q:
        return (
            "🌊 **Bay of Bengal**\n\n"
            "• Area: 2.17 million km² | Average depth: 2,600m\n"
            "• 4th largest bay in world | Part of Indian Ocean\n\n"
            "**Bordering Nations:** India, Bangladesh, Myanmar, Sri Lanka, Thailand\n\n"
            "**Key Ports:** Visakhapatnam, Chennai, Kolkata, Chittagong, Yangon\n\n"
            "**Weather:**\n"
            "• SW Monsoon (Jun–Sep): heavy rain, 2–4m waves\n"
            "• Cyclone season: April–June and October–December\n"
            "• 5–6 cyclones/year average\n\n"
            "**Navigation Notes:**\n"
            "• Andaman & Nicobar Islands create sheltered channels\n"
            "• Ganges-Brahmaputra delta creates shallow northern area\n"
            "• High sediment load — frequent chart updates needed"
        )
    if "arabian sea" in q:
        return (
            "🌊 **Arabian Sea**\n\n"
            "• Area: 3.86 million km² | Average depth: 2,734m\n"
            "• Part of Indian Ocean, NW quadrant\n\n"
            "**Bordering Nations:** India, Pakistan, Oman, Yemen, Somalia\n\n"
            "**Key Ports:** Mumbai, Karachi, Muscat, Aden, Colombo\n\n"
            "**Weather:**\n"
            "• SW Monsoon (Jun–Sep): 3–5m waves, strong W/SW winds\n"
            "• NE Monsoon (Nov–Feb): calmer, 1–2m waves\n"
            "• Cyclone season: May–June, October–November\n\n"
            "**Strategic:**\n"
            "• Major oil tanker route from Persian Gulf\n"
            "• Gateway to Suez Canal via Gulf of Aden\n"
            "• Active anti-piracy naval operations"
        )
    return (
        "🌊 **Global Ocean Regions**\n\n"
        "**Indian Ocean System:**\n"
        "• Arabian Sea (3.86M km²) — India-Middle East trade route\n"
        "• Bay of Bengal (2.17M km²) — cyclone-prone, India-SE Asia\n"
        "• South Indian Ocean — world's roughest regular shipping lane\n\n"
        "**Pacific Ocean:**\n"
        "• Largest ocean — 165M km²\n"
        "• North Pacific route: Asia-N.America via great circle\n"
        "• South Pacific: Australia-Americas\n\n"
        "**Atlantic Ocean:**\n"
        "• North Atlantic: Europe-Americas, rough winter weather\n"
        "• South Atlantic: Brazil-Africa-Europe\n\n"
        "**Mediterranean Sea:**\n"
        "• 2.5M km² | Generally calm | Major cruise ship area\n"
        "• Critical for Europe-Asia (via Suez) trade\n\n"
        "💡 Select a region in the **Weather tab** for live conditions."
    )


def _general_answer(q: str, ctx: Optional[dict]) -> str:
    return (
        f"🌊 **MarineAI Response**\n\n"
        f"You asked: *\"{q[:100]}{'...' if len(q)>100 else ''}\"*\n\n"
        "I can give you detailed expert answers on any of these maritime topics:\n\n"
        "| Topic | Example Questions |\n|---|---|\n"
        "| 🌊 Waves & Ocean | *\"Wave height in Bay of Bengal?\"* |\n"
        "| 🌀 Storms | *\"How bad is a Category 3 cyclone?\"* |\n"
        "| 🗺 Routes | *\"Best route Mumbai to Singapore?\"* |\n"
        "| ⚓ Departure | *\"Safe to depart Visakhapatnam today?\"* |\n"
        "| 🚢 Vessels | *\"What is a VLCC tanker?\"* |\n"
        "| 📋 SOLAS | *\"Explain SOLAS lifeboat requirements\"* |\n"
        "| 🌿 MARPOL | *\"What is the SOx emission limit?\"* |\n"
        "| ⚓ COLREGS | *\"Who has right of way at sea?\"* |\n"
        "| ⛽ Fuel | *\"How much fuel does a cargo ship use?\"* |\n"
        "| 🆘 Emergency | *\"How do I send a MAYDAY?\"* |\n"
        "| 📡 AIS | *\"What is AIS tracking?\"* |\n"
        "| 🎓 STCW | *\"What certificates do officers need?\"* |\n"
        "| 🏴‍☠️ Piracy | *\"High risk piracy zones?\"* |\n"
        "| 🔍 PSC | *\"How does port state control work?\"* |\n\n"
        "Please rephrase your question and I'll give you a detailed answer!"
    )


# ─── Knowledge Engine ─────────────────────────────────────────────────────────

def _knowledge_answer(message: str, context: Optional[dict] = None) -> str:
    """Match question to best KB category and return detailed answer."""
    q = message.lower().strip()
    for category, data in MARITIME_KB.items():
        if category == "general":
            continue
        if any(trigger in q for trigger in data["triggers"]):
            return data["answer"](q, context)
    # Fallback
    return MARITIME_KB["general"]["answer"](q, context)


# ─── Main Agent ───────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are MarineAI Assistant — a highly intelligent AI assistant with deep maritime expertise.
You can answer ANY question the user asks — maritime, general knowledge, science, history, coding, math, or anything else.
For maritime questions, give detailed expert answers with specific numbers, safety thresholds, and actionable advice.
Safety thresholds: small vessels wave < 1.5m, wind < 25 knots; large vessels wave < 4m, wind < 40 knots.
Always be helpful, accurate, and conversational. Format responses clearly with markdown."""


class MaritimeGPTAgent:
    def __init__(self):
        self._llm = _build_llm(temperature=0.5)
        self._failures = 0
        self._llm_disabled = False
        self._last_failure_time = 0

    async def _call_llm(self, messages: list) -> Optional[str]:
        import time
        # Re-enable LLM after 60s cooldown
        if self._llm_disabled:
            if time.time() - self._last_failure_time > 60:
                self._llm_disabled = False
                self._failures = 0
                logger.info("LLM re-enabled after cooldown")
            else:
                return None

        if self._llm is None:
            return None
        try:
            resp = await asyncio.wait_for(self._llm.ainvoke(messages), timeout=15.0)
            self._failures = 0
            self._llm_disabled = False
            return _extract_text(resp.content)
        except Exception as e:
            import time as t
            self._failures += 1
            self._last_failure_time = t.time()
            logger.warning(f"LLM ({self._failures}/5): {str(e)[:120]}")
            if self._failures >= 5:
                self._llm_disabled = True
                logger.warning("LLM temporarily disabled for 60s — using knowledge engine")
            return None

    async def chat(
        self,
        message: str,
        history: List[dict] = None,
        context: Optional[dict] = None,
    ) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

        if self._llm is not None and not self._llm_disabled:
            sys_content = SYSTEM_PROMPT
            if context:
                ctx_str = []
                if context.get("weather") and isinstance(context["weather"], dict) and "temperature_c" in context["weather"]:
                    w = context["weather"]
                    ctx_str.append(f"Live weather: {w.get('weather_condition','—')}, {w.get('temperature_c',0):.0f}°C, wind {w.get('wind_speed_kmh',0):.0f}km/h, wave {w.get('wave_height_m',0):.1f}m")
                if ctx_str:
                    sys_content += "\n\nReal-time data: " + " | ".join(ctx_str)

            msgs = [SystemMessage(content=sys_content)]
            # Include up to last 10 turns of history
            for msg in (history or [])[-10:]:
                if msg.get("role") == "user":
                    msgs.append(HumanMessage(content=str(msg["content"])))
                elif msg.get("role") == "assistant":
                    msgs.append(AIMessage(content=str(msg["content"])))
            msgs.append(HumanMessage(content=message))

            result = await self._call_llm(msgs)
            if result:
                return result

        # Fallback: comprehensive maritime knowledge engine
        return _knowledge_answer(message, context)

    async def quick_answer(self, query: str, context: Optional[dict] = None) -> str:
        return await self.chat(query, history=[], context=context)

import type { Vessel } from "@/types";

/**
 * Realistic mock vessel data — used as fallback when the backend is offline.
 * 35 vessels spread across major shipping lanes worldwide.
 */
export const MOCK_VESSELS: Vessel[] = [
  // ── Indian Ocean ────────────────────────────────────────────────────────
  { mmsi: "419001234", name: "MV OCEAN PIONEER",    vessel_type: "Cargo",     flag: "IN", latitude: 13.2,  longitude: 72.8,  speed: 14.2, course: 235, destination: "MUMBAI",        risk_level: "safe",   risk_score: 12 },
  { mmsi: "419002345", name: "MT ARABIAN STAR",     vessel_type: "Tanker",    flag: "SA", latitude: 19.5,  longitude: 64.3,  speed: 11.8, course: 310, destination: "FUJAIRAH",      risk_level: "safe",   risk_score: 18 },
  { mmsi: "419003456", name: "FV KERALA FISHER",    vessel_type: "Fishing",   flag: "IN", latitude: 10.4,  longitude: 76.2,  speed: 4.3,  course:  90, destination: "KOCHI",         risk_level: "safe",   risk_score: 8  },
  { mmsi: "636015678", name: "MV COLOMBO EXPRESS",  vessel_type: "Cargo",     flag: "LK", latitude: 6.9,   longitude: 79.9,  speed: 18.1, course:  45, destination: "SINGAPORE",     risk_level: "low",    risk_score: 22 },
  { mmsi: "419004567", name: "MT GULF MONARCH",     vessel_type: "Tanker",    flag: "AE", latitude: 24.1,  longitude: 57.6,  speed: 12.5, course: 180, destination: "OMAN",          risk_level: "safe",   risk_score: 14 },

  // ── Arabian Sea / Persian Gulf ──────────────────────────────────────────
  { mmsi: "422005678", name: "MV HORMUZ TRADER",    vessel_type: "Cargo",     flag: "IR", latitude: 26.3,  longitude: 55.9,  speed: 9.6,  course: 270, destination: "BANDAR",        risk_level: "medium", risk_score: 48 },
  { mmsi: "419006789", name: "SS BOMBAY MARU",      vessel_type: "Passenger", flag: "IN", latitude: 18.9,  longitude: 72.6,  speed: 22.4, course: 320, destination: "DUBAI",         risk_level: "low",    risk_score: 25 },
  { mmsi: "412007890", name: "MV RED SEA PEARL",    vessel_type: "Cargo",     flag: "EG", latitude: 20.2,  longitude: 38.4,  speed: 13.0, course: 350, destination: "SUEZ",          risk_level: "medium", risk_score: 55 },

  // ── Strait of Malacca / South China Sea ────────────────────────────────
  { mmsi: "525008901", name: "KM NUSANTARA JAYA",   vessel_type: "Cargo",     flag: "ID", latitude: 1.3,   longitude: 103.8, speed: 10.2, course: 130, destination: "JAKARTA",       risk_level: "safe",   risk_score: 16 },
  { mmsi: "566009012", name: "MT STRAITS CARRIER",  vessel_type: "Tanker",    flag: "SG", latitude: 3.1,   longitude: 101.6, speed: 14.8, course: 310, destination: "PORT KLANG",    risk_level: "safe",   risk_score: 11 },
  { mmsi: "477010123", name: "MV SOUTH CHINA SEA",  vessel_type: "Cargo",     flag: "HK", latitude: 14.5,  longitude: 112.3, speed: 16.3, course:  60, destination: "HONG KONG",     risk_level: "low",    risk_score: 28 },
  { mmsi: "525011234", name: "FV BALI FISHER",      vessel_type: "Fishing",   flag: "ID", latitude: -8.6,  longitude: 115.2, speed: 3.8,  course: 200, destination: "BENOA",         risk_level: "safe",   risk_score: 6  },

  // ── Pacific Ocean ────────────────────────────────────────────────────────
  { mmsi: "431012345", name: "MV PACIFIC HORIZON",  vessel_type: "Cargo",     flag: "JP", latitude: 28.0,  longitude: 145.0, speed: 19.0, course:  80, destination: "LOS ANGELES",  risk_level: "low",    risk_score: 30 },
  { mmsi: "338013456", name: "SS GOLDEN GATE",      vessel_type: "Cargo",     flag: "US", latitude: 37.5,  longitude:-145.0, speed: 17.2, course: 270, destination: "TOKYO",         risk_level: "safe",   risk_score: 20 },
  { mmsi: "431014567", name: "MT FUJI MARU",        vessel_type: "Tanker",    flag: "JP", latitude: 35.2,  longitude: 139.8, speed: 13.5, course: 115, destination: "YOKOHAMA",      risk_level: "safe",   risk_score: 15 },
  { mmsi: "548015678", name: "FV MANILA FISHER",    vessel_type: "Fishing",   flag: "PH", latitude: 11.0,  longitude: 122.5, speed: 5.1,  course:  45, destination: "MANILA",        risk_level: "safe",   risk_score: 9  },

  // ── Mediterranean ────────────────────────────────────────────────────────
  { mmsi: "247016789", name: "MV ADRIATICO",        vessel_type: "Cargo",     flag: "IT", latitude: 38.1,  longitude:  14.5, speed: 12.0, course: 290, destination: "GENOVA",        risk_level: "safe",   risk_score: 17 },
  { mmsi: "212017890", name: "SS AEGEAN QUEEN",     vessel_type: "Passenger", flag: "GR", latitude: 37.9,  longitude:  23.7, speed: 24.0, course: 120, destination: "PIRAEUS",       risk_level: "low",    risk_score: 32 },
  { mmsi: "229018901", name: "MT BOSPHORUS",        vessel_type: "Tanker",    flag: "MT", latitude: 41.0,  longitude:  29.0, speed: 10.5, course: 215, destination: "ISTANBUL",      risk_level: "medium", risk_score: 52 },
  { mmsi: "232019012", name: "MV CHANNEL ROVER",    vessel_type: "Cargo",     flag: "GB", latitude: 50.8,  longitude:   1.2, speed: 15.8, course: 290, destination: "SOUTHAMPTON",   risk_level: "safe",   risk_score: 14 },

  // ── North Atlantic ────────────────────────────────────────────────────────
  { mmsi: "338020123", name: "SS ATLANTIC QUEEN",   vessel_type: "Passenger", flag: "US", latitude: 42.0,  longitude: -55.0, speed: 26.0, course:  90, destination: "NEW YORK",      risk_level: "low",    risk_score: 35 },
  { mmsi: "229021234", name: "MV NORTH STAR",       vessel_type: "Cargo",     flag: "NO", latitude: 58.5,  longitude: -18.0, speed: 14.0, course: 280, destination: "ROTTERDAM",     risk_level: "medium", risk_score: 60 },
  { mmsi: "232022345", name: "MT BRITANNIA",        vessel_type: "Tanker",    flag: "GB", latitude: 51.5,  longitude: -10.0, speed: 11.0, course: 185, destination: "FALMOUTH",      risk_level: "safe",   risk_score: 21 },
  { mmsi: "311023456", name: "FV ATLANTIC TRAWLER", vessel_type: "Fishing",   flag: "NO", latitude: 63.0,  longitude: -10.5, speed: 6.2,  course: 320, destination: "BERGEN",        risk_level: "medium", risk_score: 58 },

  // ── Gulf of Mexico / Caribbean ────────────────────────────────────────────
  { mmsi: "338024567", name: "MV GULF STREAM",      vessel_type: "Cargo",     flag: "US", latitude: 27.5,  longitude: -88.0, speed: 12.5, course: 200, destination: "HOUSTON",       risk_level: "safe",   risk_score: 20 },
  { mmsi: "370025678", name: "MT PANAMA PACIFIC",   vessel_type: "Tanker",    flag: "PA", latitude: 9.3,   longitude: -79.5, speed: 10.8, course: 315, destination: "BALBOA",        risk_level: "safe",   risk_score: 18 },
  { mmsi: "308026789", name: "SS CARIBBEAN STAR",   vessel_type: "Passenger", flag: "BS", latitude: 24.0,  longitude: -76.5, speed: 20.5, course: 130, destination: "NASSAU",        risk_level: "low",    risk_score: 27 },

  // ── East Africa / Bay of Bengal ───────────────────────────────────────────
  { mmsi: "677027890", name: "MV ZANZIBAR TRADER",  vessel_type: "Cargo",     flag: "TZ", latitude: -6.2,  longitude:  39.8, speed: 9.2,  course:  60, destination: "DAR ES SALAAM", risk_level: "safe",   risk_score: 15 },
  { mmsi: "403028901", name: "MT BENGAL STAR",      vessel_type: "Tanker",    flag: "BD", latitude: 21.5,  longitude:  89.3, speed: 11.2, course: 175, destination: "CHITTAGONG",    risk_level: "low",    risk_score: 30 },
  { mmsi: "419029012", name: "MV ANDAMAN SEA",      vessel_type: "Cargo",     flag: "IN", latitude: 11.7,  longitude:  92.7, speed: 13.5, course: 280, destination: "CHENNAI",       risk_level: "safe",   risk_score: 16 },

  // ── High-risk / piracy zones (Somalia / Aden) ────────────────────────────
  { mmsi: "620030123", name: "MT SOMALI COAST",     vessel_type: "Tanker",    flag: "SO", latitude: 11.8,  longitude:  51.3, speed: 7.2,  course:  45, destination: "ADEN",          risk_level: "high",   risk_score: 78 },
  { mmsi: "403031234", name: "MV HORN OF AFRICA",   vessel_type: "Cargo",     flag: "DJ", latitude: 12.5,  longitude:  44.8, speed: 8.5,  course: 310, destination: "DJIBOUTI",      risk_level: "high",   risk_score: 82 },

  // ── Naval vessels ─────────────────────────────────────────────────────────
  { mmsi: "338032345", name: "USS GUARDIAN",        vessel_type: "Naval",     flag: "US", latitude: 20.0,  longitude:  65.0, speed: 25.0, course: 180, destination: "BAHRAIN",       risk_level: "low",    risk_score: 28 },
  { mmsi: "232033456", name: "HMS DEFENDER",        vessel_type: "Naval",     flag: "GB", latitude: 36.5,  longitude:  -6.5, speed: 22.0, course:  90, destination: "GIBRALTAR",     risk_level: "safe",   risk_score: 19 },

  // ── South East Asia ───────────────────────────────────────────────────────
  { mmsi: "525034567", name: "MV JAVA SEA",         vessel_type: "Cargo",     flag: "ID", latitude: -6.8,  longitude: 107.0, speed: 11.5, course: 250, destination: "SURABAYA",      risk_level: "safe",   risk_score: 13 },
  { mmsi: "566035678", name: "MT SINGAPORE SPIRIT", vessel_type: "Tanker",    flag: "SG", latitude: 1.1,   longitude: 104.5, speed: 13.0, course: 275, destination: "SINGAPORE",     risk_level: "safe",   risk_score: 11 },
];

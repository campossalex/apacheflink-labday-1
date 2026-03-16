#!/usr/bin/env python3
"""
ANA Portugal Flight Data Generator
Generates realistic flight data payloads at random intervals of 3–6 minutes
and publishes each event to a Kafka topic.

Usage:
    python3 flight_data_generator.py \\
        --broker localhost:9092 \\
        --topic flights.events

    # Multiple brokers:
    python3 flight_data_generator.py \\
        --broker broker1:9092,broker2:9092 \\
        --topic flights.events \\
        --interval-min 3 \\
        --interval-max 6

Dependencies:
    pip install kafka-python
"""

import argparse
import json
import sys
import uuid
import random
import time
import logging
from datetime import datetime, timezone, timedelta

try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError, NoBrokersAvailable
except ImportError:
    print(
        "ERROR: kafka-python is not installed.\n"
        "       Run:  pip install kafka-python",
        file=sys.stderr,
    )
    sys.exit(1)

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("flight-gen")

# ─────────────────────────────────────────────
# ANA Portugal Airports
# ─────────────────────────────────────────────
ANA_AIRPORTS = [
    {"iata": "LIS", "icao": "LPPT", "name": "Lisbon Humberto Delgado"},
    {"iata": "OPO", "icao": "LPPR", "name": "Porto Francisco Sá Carneiro"},
    {"iata": "FAO", "icao": "LPFR", "name": "Faro Gago Coutinho"},
    {"iata": "BYJ", "icao": "LPBJ", "name": "Beja Civilian Terminal"},
    {"iata": "FNC", "icao": "LPMA", "name": "Madeira Airport"},
    {"iata": "PXO", "icao": "LPPS", "name": "Porto Santo Airport"},
    {"iata": "PDL", "icao": "LPPD", "name": "Ponta Delgada João Paulo II"},
    {"iata": "HOR", "icao": "LPHR", "name": "Horta Airport"},
    {"iata": "SMA", "icao": "LPAZ", "name": "Santa Maria Airport"},
]

# ─────────────────────────────────────────────
# Other European / World Airports (non-ANA)
# ─────────────────────────────────────────────
OTHER_AIRPORTS = [
    {"iata": "LHR", "icao": "EGLL"},  # London Heathrow
    {"iata": "CDG", "icao": "LFPG"},  # Paris CDG
    {"iata": "AMS", "icao": "EHAM"},  # Amsterdam
    {"iata": "FRA", "icao": "EDDF"},  # Frankfurt
    {"iata": "MAD", "icao": "LEMD"},  # Madrid
    {"iata": "BCN", "icao": "LEBL"},  # Barcelona
    {"iata": "FCO", "icao": "LIRF"},  # Rome Fiumicino
    {"iata": "VIE", "icao": "LOWW"},  # Vienna
    {"iata": "ZRH", "icao": "LSZH"},  # Zurich
    {"iata": "MUC", "icao": "EDDM"},  # Munich
    {"iata": "BRU", "icao": "EBBR"},  # Brussels
    {"iata": "DUB", "icao": "EIDW"},  # Dublin
    {"iata": "CPH", "icao": "EKCH"},  # Copenhagen
    {"iata": "ARN", "icao": "ESSA"},  # Stockholm
    {"iata": "OSL", "icao": "ENGM"},  # Oslo
    {"iata": "HEL", "icao": "EFHK"},  # Helsinki
    {"iata": "JFK", "icao": "KJFK"},  # New York JFK
    {"iata": "BOS", "icao": "KBOS"},  # Boston
    {"iata": "MIA", "icao": "KMIA"},  # Miami
    {"iata": "GRU", "icao": "SBGR"},  # São Paulo
    {"iata": "EZE", "icao": "SAEZ"},  # Buenos Aires
    {"iata": "GIG", "icao": "SBGL"},  # Rio de Janeiro
    {"iata": "RAK", "icao": "GMMX"},  # Marrakech
    {"iata": "CMN", "icao": "GMMN"},  # Casablanca
    {"iata": "DXB", "icao": "OMDB"},  # Dubai
    {"iata": "NBO", "icao": "HKJK"},  # Nairobi
]

# ─────────────────────────────────────────────
# Airlines operating in Portugal
# ─────────────────────────────────────────────
AIRLINES = [
    {"icao": "TAP", "iata": "TP", "name": "TAP Air Portugal"},
    {"icao": "RYR", "iata": "FR", "name": "Ryanair"},
    {"icao": "EZY", "iata": "U2", "name": "easyJet"},
    {"icao": "WZZ", "iata": "W6", "name": "Wizz Air"},
    {"icao": "BAW", "iata": "BA", "name": "British Airways"},
    {"icao": "DLH", "iata": "LH", "name": "Lufthansa"},
    {"icao": "AFR", "iata": "AF", "name": "Air France"},
    {"icao": "IBE", "iata": "IB", "name": "Iberia"},
    {"icao": "KLM", "iata": "KL", "name": "KLM"},
    {"icao": "VLG", "iata": "VY", "name": "Vueling"},
    {"icao": "AEA", "iata": "UX", "name": "Air Europa"},
    {"icao": "UAE", "iata": "EK", "name": "Emirates"},
    {"icao": "TUI", "iata": "BY", "name": "TUI Airways"},
    {"icao": "NOS", "iata": "8X", "name": "Neos"},
    {"icao": "PGA", "iata": "NI", "name": "Portugália"},
    {"icao": "AMX", "iata": "AM", "name": "Aeromexico"},
    {"icao": "TAM", "iata": "JJ", "name": "LATAM Brasil"},
]

# ─────────────────────────────────────────────
# Aircraft types (IATA → ICAO)
# ─────────────────────────────────────────────
AIRCRAFT_TYPES = [
    {"iata": "320", "icao": "A320", "seats": (150, 186), "wtc": "M"},
    {"iata": "321", "icao": "A321", "seats": (180, 220), "wtc": "M"},
    {"iata": "319", "icao": "A319", "seats": (120, 156), "wtc": "M"},
    {"iata": "332", "icao": "A332", "seats": (250, 300), "wtc": "H"},
    {"iata": "333", "icao": "A333", "seats": (280, 335), "wtc": "H"},
    {"iata": "359", "icao": "A359", "seats": (300, 369), "wtc": "H"},
    {"iata": "73H", "icao": "B737", "seats": (162, 189), "wtc": "M"},
    {"iata": "738", "icao": "B738", "seats": (160, 189), "wtc": "M"},
    {"iata": "788", "icao": "B788", "seats": (242, 296), "wtc": "H"},
    {"iata": "789", "icao": "B789", "seats": (280, 330), "wtc": "H"},
    {"iata": "E90", "icao": "E190", "seats": (96, 114),  "wtc": "M"},
    {"iata": "E95", "icao": "E195", "seats": (118, 130), "wtc": "M"},
    {"iata": "AT7", "icao": "AT72", "seats": (66, 78),   "wtc": "M"},
    {"iata": "DH4", "icao": "DH8D", "seats": (74, 86),   "wtc": "M"},
]

# ─────────────────────────────────────────────
# Reference / static tables
# ─────────────────────────────────────────────
OPERATIONAL_STATUSES = ["OPERATIONAL", "NON_OPERATIONAL", "SCHEDULED", "CANCELLED"]
OPERATIONAL_STATUS_WEIGHTS = [60, 5, 30, 5]

CLASSIFICATIONS = {
    # Intra-Portugal (ANA ↔ ANA) → LOCAL
    "local":         "LOCAL",
    # Intra-Schengen → SCHENGEN
    "schengen":      "SCHENGEN",
    # UK / long-haul Europe outside Schengen → NON_SCHENGEN
    "non_schengen":  "NON_SCHENGEN",
    # Intercontinental → INTERNATIONAL
    "international": "INTERNATIONAL",
}

# Airports outside Schengen (for classification logic)
NON_SCHENGEN_IATA = {"LHR", "LGW", "STN", "MAN", "EDI", "GLA", "JFK", "BOS",
                     "MIA", "GRU", "EZE", "GIG", "NBO", "DXB"}

SERVICE_TYPES = ["J", "C", "F", "W", "S", "B"]         # SSIM service types
REMARKS       = ["Boarding", "Gate Open", "Departed", "Landed", "On Time",
                 "Delayed", "Cancelled", "Check-in Open", "Final Call"]
HANDLERS      = ["PTW", "SPDH", "GROUNDFORCE", "PORTWAY", "SWISSPORT"]
MOVEMENT_TYPES = ["ARRIVAL", "DEPARTURE", "TURNAROUND"]
MOVEMENT_WEIGHTS = [45, 45, 10]
FLIGHT_RULES  = ["IFR", "VFR"]
SUFFIXES       = ["O", "S", "N"]                        # Operational / Schedule / Non-op
MATCH_CODES    = ["OK", "FIRST_WARNING", "SECOND_WARNING"]
TERMINALS      = ["T1", "T2"]
DELAY_CODES    = ["11", "14", "21", "41", "51", "61", "71", "81", "93"]

SIDS  = ["IXIDA2N", "BUSEN4B", "OBIDI3C", "TULKA2L", "KOLEM2C"]
STARS = ["XAMAX9C", "LUNIP5C", "RIDSU4C", "MAXIR5C", "RIPTU5C"]

RUNWAY_CODES   = ["03", "21", "35", "17", "24R", "06L", "07C"]
RUNWAY_EXITS   = ["U5", "H1", "A3", "G7", "N2"]
RUNWAY_INTERS  = ["HS", "N1", "A5", "G6"]
STAND_CODES    = [str(i) for i in range(1, 200)]

GATE_STATUSES  = ["Gate Open", "Boarding", "Final Call", "Gate Closed", "Gate Change"]
BELT_STATUSES  = ["Assigned", "First Bag", "Last Bag", "Closed"]
CHECKIN_STATUSES = ["Check-in Open", "Check-in Closed"]
CHUTE_STATUSES = ["Chute Open", "Chute Closed", "Chute Assigned"]


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def rand_dt(base: datetime, delta_min: int = -120, delta_max: int = 120) -> str:
    """Return a random datetime around *base* within the given minute range."""
    offset = random.randint(delta_min * 60, delta_max * 60)
    return iso(base + timedelta(seconds=offset))


def rand_reg() -> str:
    prefix = random.choice(["CS", "EC", "G", "D", "F", "OE", "PH", "SE"])
    suffix = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=3))
    return f"{prefix}-{suffix}"


def classify(dep_iata: str, arr_iata: str, ana_iatas: set) -> str:
    both_ana = dep_iata in ana_iatas and arr_iata in ana_iatas
    if both_ana:
        return "LOCAL"
    other = arr_iata if dep_iata in ana_iatas else dep_iata
    if other in NON_SCHENGEN_IATA:
        # Intercontinental capitals → INTERNATIONAL
        if other in {"JFK", "BOS", "MIA", "GRU", "EZE", "GIG", "NBO", "DXB"}:
            return "INTERNATIONAL"
        return "NON_SCHENGEN"
    return "SCHENGEN"


# ─────────────────────────────────────────────
# Core generator
# ─────────────────────────────────────────────
def generate_flight() -> dict:
    base_time  = now_utc()
    ana_iatas  = {a["iata"] for a in ANA_AIRPORTS}

    movement   = random.choices(MOVEMENT_TYPES, weights=MOVEMENT_WEIGHTS, k=1)[0]
    ana_airport = random.choice(ANA_AIRPORTS)
    airline    = random.choice(AIRLINES)
    aircraft   = random.choice(AIRCRAFT_TYPES)
    seat_cap   = random.randint(*aircraft["seats"])
    flight_num = random.randint(100, 9999)
    suffix     = random.choice(SUFFIXES)
    op_status  = random.choices(OPERATIONAL_STATUSES, weights=OPERATIONAL_STATUS_WEIGHTS, k=1)[0]

    # Determine departure / arrival airports based on movement type
    if movement == "DEPARTURE":
        dep_airport = ana_airport
        arr_airport = random.choice(OTHER_AIRPORTS + [a for a in ANA_AIRPORTS if a["iata"] != ana_airport["iata"]])
    elif movement == "ARRIVAL":
        arr_airport = ana_airport
        dep_airport = random.choice(OTHER_AIRPORTS + [a for a in ANA_AIRPORTS if a["iata"] != ana_airport["iata"]])
    else:  # TURNAROUND
        dep_airport = ana_airport
        arr_airport = ana_airport

    classification = classify(dep_airport["iata"], arr_airport["iata"], ana_iatas)

    public_code    = f"{airline['iata']}{flight_num}{suffix}"[:8]
    call_sign      = f"{airline['icao']}{flight_num}"
    aodb_ref       = str(random.randint(1_000_000, 9_999_999))
    fub_ref        = str(random.randint(1_000_000, 9_999_999))
    assoc_flight_id = str(uuid.uuid4())

    # Passengers
    total_pax      = random.randint(0, seat_cap)
    transfer_pax   = random.randint(0, total_pax // 3)
    local_pax      = total_pax - transfer_pax
    web_checkin    = random.randint(0, total_pax)
    onsite_checkin = total_pax - web_checkin
    prm_total      = random.randint(0, max(1, total_pax // 20))
    prm_notif      = random.randint(0, prm_total)

    handler     = random.choice(HANDLERS)
    terminal    = random.choice(TERMINALS)
    gate_code   = str(random.randint(1, 60))
    belt_code   = str(random.randint(1, 20)).zfill(2)
    counter_pos = str(random.randint(100, 180))
    chute_code  = str(random.randint(10, 50)).zfill(3)

    # Time anchors
    sched_time = rand_dt(base_time, -180, 180)
    gate_open  = rand_dt(base_time, -60, -30)
    gate_close = rand_dt(base_time, -10, 10)
    belt_first = rand_dt(base_time, -5, 20)
    belt_last  = rand_dt(base_time, 20, 60)
    ci_open    = rand_dt(base_time, -180, -90)
    ci_close   = rand_dt(base_time, -40, -20)

    # Random delay codes (0–3 entries)
    delay_entries = {}
    for _ in range(random.randint(0, 3)):
        code = random.choice(DELAY_CODES)
        delay_entries[code] = str(random.randint(5, 180))

    flight = {
        # ── Identifiers ──────────────────────────────
        "id":                       str(uuid.uuid4()),
        "airportIataCode":          ana_airport["iata"],
        "airportIcaoCode":          ana_airport["icao"],
        "movementType":             movement,
        "sourceUpdated":            iso(base_time),

        # ── Airline / flight identification ──────────
        "airlineIcaoCode":          airline["icao"],
        "airlineIataCode":          airline["iata"],
        "flightNumber":             flight_num,
        "flightOperationalSuffix":  suffix,
        "operatingAirlineCode":     airline["icao"],
        "publicFlightCode":         public_code,
        "callSign":                 call_sign,
        "coordinated":              random.choice([True, False]),

        # ── System fields ─────────────────────────────
        "initialSchedule":          sched_time,
        "initialOperationalSuffix": suffix,
        "created":                  iso(base_time - timedelta(days=random.randint(1, 30))),
        "createdBy":                "flight-gen@ana.pt",
        "updated":                  iso(base_time),
        "updatedBy":                "flight-gen@ana.pt",

        # ── References ────────────────────────────────
        "references": {
            "AODB": aodb_ref,
            "FUB":  fub_ref,
        },

        # ── Associated flight ─────────────────────────
        "associatedFlight": {
            "sequence":                random.choice(["BEFORE", "AFTER"]),
            "id":                      assoc_flight_id,
            "airlineIcaoCode":         airline["icao"],
            "airlineIataCode":         airline["iata"],
            "flightNumber":            flight_num,
            "flightOperationalSuffix": suffix,
            "publicFlightCode":        public_code,
            "schedule":                sched_time,
            "references": {"AODB": aodb_ref, "FUB": fub_ref},
        },

        # ── Status & remarks ──────────────────────────
        "operationalStatus": op_status,
        "remark":            random.choice(REMARKS),

        # ── Route ─────────────────────────────────────
        "departureAirportIataCode": dep_airport["iata"],
        "departureAirportIcaoCode": dep_airport["icao"],
        "arrivalAirportIataCode":   arr_airport["iata"],
        "arrivalAirportIcaoCode":   arr_airport["icao"],

        # ── Service / classification ──────────────────
        "serviceType":    random.choice(SERVICE_TYPES),
        "nature":         random.choice([111, 112, 121, 122]),
        "operationType":  random.choice([1, 2, 3]),
        "classification": classification,

        # ── Aircraft ──────────────────────────────────
        "aircraftTypeIata":        aircraft["iata"],
        "aircraftTypeIcao":        aircraft["icao"],
        "registration":            rand_reg(),
        "seatCapacity":            seat_cap,
        "wakeTurbulenceCategory":  aircraft["wtc"],

        # ── Flight plan ───────────────────────────────
        "standardInstrumentDeparture": random.choice(SIDS),
        "standardArrivalRoute":        random.choice(STARS),
        "flightRules":                 random.choice(FLIGHT_RULES),
        "matchCode":                   random.choice(MATCH_CODES),

        # ── Operation times ───────────────────────────
        "scheduledTimeOfArrival":    rand_dt(base_time, -30,  0),
        "scheduledTimeOfDeparture":  rand_dt(base_time,   0, 30),
        "estimatedTimeOfDeparture":  rand_dt(base_time,  -5, 15),
        "actualOffBlockOfDeparture": rand_dt(base_time,  -3,  3),
        "actualTakeOffOfDeparture":  rand_dt(base_time,  10, 20),
        "targetLanding":             rand_dt(base_time, -10,  5),
        "estimatedLanding":          rand_dt(base_time,  -5, 10),
        "tenMilesOut":               rand_dt(base_time, -15, -5),
        "actualLanding":             rand_dt(base_time,  -5,  5),
        "scheduledInBlock":          rand_dt(base_time,  -5, 10),
        "estimatedInBlock": {
            "AIRLINE": rand_dt(base_time,  -5, 10),
            "ACDM":    rand_dt(base_time,  -5, 10),
        },
        "actualInBlock":             rand_dt(base_time,   0,  5),
        "scheduledOffBlock":         rand_dt(base_time,  -5,  5),
        "estimatedOffBlock": {
            "AIRLINE":          rand_dt(base_time,  0, 10),
            "NETWORK_MANAGER":  rand_dt(base_time,  0, 10),
            "ATC":              rand_dt(base_time,  2, 12),
            "AODB":             rand_dt(base_time, -2,  8),
        },
        "actualOffBlock":            rand_dt(base_time,  0,  5),
        "targetOffBlock":            rand_dt(base_time, -5,  5),
        "calculatedOffBlock":        rand_dt(base_time, -5,  5),
        "targetStartupApproval":     rand_dt(base_time, -15, -5),
        "actualStartup":             rand_dt(base_time, -10, -2),
        "actualStartupStatus":       random.choice(["CONFIRMED", "CANCELLED"]),
        "estimatedTakeOff":          rand_dt(base_time,  10, 20),
        "targetTakeOff":             rand_dt(base_time,  10, 20),
        "calculatedTakeOff":         rand_dt(base_time,  10, 20),
        "actualTakeOff":             rand_dt(base_time,  12, 22),
        "actualGroundHandlingCommence": rand_dt(base_time, -20, -10),
        "actualStartupRequest":      rand_dt(base_time, -12, -5),
        "actualReady":               rand_dt(base_time,  -5,  0),
        "estimatedTaxiIn":           str(random.randint(5, 20)),
        "estimatedTaxiOut":          str(random.randint(5, 25)),

        # ── Passengers ────────────────────────────────
        "totalPassengersCount":     total_pax,
        "transferPassengersCount":  transfer_pax,
        "localPassengersCount":     local_pax,
        "webCheckInCount":          web_checkin,
        "onSiteCheckInCount":       onsite_checkin,
        "prmAssistancesTotal":          prm_total,
        "prmAssistancesTotalNotified":  prm_notif,
        "prmAssistancesTotalNonNotified": prm_total - prm_notif,
        "securityQueuePaxEntryTotal":   random.randint(0, total_pax),
        "securityQueuePaxExitTotal":    random.randint(0, total_pax),

        # ── Crew passage ──────────────────────────────
        "firstCrewMemberPassage": rand_dt(base_time, -90, -60),
        "lastCrewMemberPassage":  rand_dt(base_time, -60, -40),

        # ── Delay codes ───────────────────────────────
        "irregularityDelays": delay_entries if delay_entries else None,

        # ── Runway ────────────────────────────────────
        "runwayCode":         random.choice(RUNWAY_CODES),
        "runwayExit":         random.choice(RUNWAY_EXITS),
        "runwayIntersection": random.choice(RUNWAY_INTERS),

        # ── Stand ─────────────────────────────────────
        "standCode":    random.choice(STAND_CODES),
        "standHandler": handler,

        # ── Terminal ──────────────────────────────────
        "terminals": {terminal: ""},

        # ── Gate ──────────────────────────────────────
        "gates": {
            gate_code: {
                "terminal":     terminal,
                "handler":      handler,
                "gateAt":       rand_dt(base_time, -30, -15),
                "goToGate":     rand_dt(base_time, -40, -20),
                "gateOpen":     gate_open,
                "boarding":     rand_dt(base_time, -25, -10),
                "finalCall":    rand_dt(base_time, -10,  -2),
                "gateClosed":   gate_close,
                "publicGate":   gate_code,
                "status":       random.choice(GATE_STATUSES),
                "boardingAlarms": random.choice(["NOT_STARTED", "NOT_COMPLETED"]),
            }
        },

        # ── Baggage claim belts ───────────────────────
        "baggageClaimBelts": {
            belt_code: {
                "terminal":   terminal,
                "handler":    handler,
                "firstBag":   belt_first,
                "lastBag":    belt_last,
                "firstBagAt": belt_first,
                "status":     random.choice(BELT_STATUSES),
            }
        },

        # ── Check-in counters ─────────────────────────
        "checkinCounters": {
            counter_pos: {
                "terminal": terminal,
                "handler":  handler,
                "open":     ci_open,
                "close":    ci_close,
                "status":   random.choice(CHECKIN_STATUSES),
            }
        },

        # ── Chutes ────────────────────────────────────
        "chutes": {
            chute_code: {
                "terminal": terminal,
                "handler":  handler,
                "open":     rand_dt(base_time, -60, -40),
                "close":    rand_dt(base_time,  10,  40),
                "status":   random.choice(CHUTE_STATUSES),
            }
        },

        # ── Intermediate stops (optional, ~20% chance) ─
        **({"intermediateStops": {
            "1": {
                "airportIataCode": random.choice(ANA_AIRPORTS)["iata"],
                "airportIcaoCode": random.choice(ANA_AIRPORTS)["icao"],
            }
        }} if random.random() < 0.2 else {}),

        # ── Code shares (optional, ~30% chance) ───────
        **({"codeShares": {
            "1": {
                "airlineIcaoCode":          random.choice(AIRLINES)["icao"],
                "airlineIataCode":          random.choice(AIRLINES)["iata"],
                "flightNumber":             random.randint(100, 9999),
                "flightOperationalSuffix":  random.choice(SUFFIXES),
                "publicFlightCode":         public_code,
            }
        }} if random.random() < 0.3 else {}),
    }

    # Remove None values to keep the payload clean
    return {k: v for k, v in flight.items() if v is not None}


def build_payload(flight: dict) -> dict:
    return flight


# ─────────────────────────────────────────────
# CLI arguments
# ─────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ANA Portugal Flight Data Generator — publishes events to Kafka.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--broker", "-b",
        required=True,
        metavar="HOST:PORT[,HOST:PORT,...]",
        help="Kafka bootstrap broker(s), comma-separated. E.g. localhost:9092",
    )
    parser.add_argument(
        "--topic", "-t",
        required=True,
        metavar="TOPIC",
        help="Kafka topic to publish flight events to.",
    )
    parser.add_argument(
        "--interval-min",
        type=float,
        default=0.0,
        metavar="MINUTES",
        help="Minimum interval between events (minutes).",
    )
    parser.add_argument(
        "--interval-max",
        type=float,
        default=30.0,
        metavar="MINUTES",
        help="Maximum interval between events (minutes).",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=5,
        metavar="N",
        help="Number of Kafka send retries per event.",
    )
    parser.add_argument(
        "--loglevel",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity.",
    )
    return parser.parse_args()


# ─────────────────────────────────────────────
# Kafka producer factory
# ─────────────────────────────────────────────
def make_producer(brokers: str, retries: int) -> KafkaProducer:
    """Create and return a KafkaProducer with JSON serialisation."""
    return KafkaProducer(
        bootstrap_servers=[b.strip() for b in brokers.split(",")],
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        retries=retries,
        acks="all",                     # wait for all in-sync replicas
        compression_type="gzip",
        linger_ms=0,                    # send immediately
        request_timeout_ms=30_000,
    )


# ─────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────
def main() -> None:
    args = parse_args()

    logging.getLogger().setLevel(args.loglevel)

    if args.interval_min > args.interval_max:
        log.error("--interval-min must be <= --interval-max.")
        sys.exit(1)

    log.info("Connecting to Kafka broker(s): %s", args.broker)
    try:
        producer = make_producer(args.broker, args.retries)
    except NoBrokersAvailable:
        log.error("Could not connect to any Kafka broker at: %s", args.broker)
        sys.exit(1)

    log.info("Publishing to topic: %s", args.topic)
    log.info("Interval: %.1f – %.1f minutes", args.interval_min, args.interval_max)
    log.info("Press Ctrl+C to stop.\n")

    counter = 0
    try:
        while True:
            counter += 1
            flight  = generate_flight()
            payload = build_payload(flight)

            # Use the flight id as the Kafka message key (ensures ordering per flight)
            message_key = flight["id"]

            log.info(
                "Event #%d  airport=%-3s  flight=%s%s%s  route=%s→%s  "
                "movement=%-11s  status=%s",
                counter,
                flight["airportIataCode"],
                flight["airlineIataCode"],
                flight["flightNumber"],
                flight["flightOperationalSuffix"],
                flight["departureAirportIataCode"],
                flight["arrivalAirportIataCode"],
                flight["movementType"],
                flight["operationalStatus"],
            )

            try:
                future = producer.send(
                    topic=args.topic,
                    key=message_key,
                    value=payload,
                )
                record_metadata = future.get(timeout=30)
                log.info(
                    "  ✓ published  key=%s  partition=%d  offset=%d",
                    message_key,
                    record_metadata.partition,
                    record_metadata.offset,
                )
            except KafkaError as exc:
                log.error("  ✗ Failed to publish event #%d: %s", counter, exc)

            interval_secs = random.uniform(
                args.interval_min,
                args.interval_max,
            )
            log.info(
                "Next event in %.1f seconds (%.1f min)\n",
                interval_secs,
                interval_secs / 60,
            )
            time.sleep(interval_secs)

    except KeyboardInterrupt:
        log.info("Interrupted — flushing pending messages…")
        producer.flush(timeout=15)
        producer.close()
        log.info("Generator stopped after %d event(s).", counter)


if __name__ == "__main__":
    main()

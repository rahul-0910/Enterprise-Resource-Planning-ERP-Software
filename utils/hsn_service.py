"""
HSN Code Service — HOE Billing Software
Priority: 1) Local DB  2) API  3) Manual entry
"""
import json, re
from difflib import SequenceMatcher

# ── Local HSN Database ───────────────────────────────────────────────────────
# Electrical, Hardware, Electronics — common Indian products
HSN_LOCAL_DB = [
    # ── Wires & Cables ────────────────────────────────────────────────────
    {"hsn": "8544", "gst": 18, "desc": "Insulated wire, cable, coaxial cable"},
    {"hsn": "8544.11", "gst": 18, "desc": "Winding wire of copper"},
    {"hsn": "8544.19", "gst": 18, "desc": "Winding wire — other"},
    {"hsn": "8544.20", "gst": 18, "desc": "Co-axial cable"},
    {"hsn": "8544.42", "gst": 18, "desc": "Electric conductors 1000V or less — with connectors"},
    {"hsn": "8544.49", "gst": 18, "desc": "Electric conductors 1000V or less — other"},
    {"hsn": "8544.60", "gst": 18, "desc": "Electric conductors exceeding 1000V"},

    # ── Switches & Sockets ────────────────────────────────────────────────
    {"hsn": "8536", "gst": 18, "desc": "Electrical switches, sockets, relays for voltage ≤1000V"},
    {"hsn": "8536.10", "gst": 18, "desc": "Fuses — electrical"},
    {"hsn": "8536.20", "gst": 18, "desc": "Automatic circuit breakers"},
    {"hsn": "8536.41", "gst": 18, "desc": "Relays for voltage ≤60V"},
    {"hsn": "8536.49", "gst": 18, "desc": "Relays — other"},
    {"hsn": "8536.50", "gst": 18, "desc": "Switches — electrical"},
    {"hsn": "8536.61", "gst": 18, "desc": "Lamp holders — electrical"},
    {"hsn": "8536.69", "gst": 18, "desc": "Plugs and sockets — electrical"},
    {"hsn": "8536.90", "gst": 18, "desc": "Other electrical apparatus for switching"},

    # ── MCB / RCCB / Distribution Boards ─────────────────────────────────
    {"hsn": "8535", "gst": 18, "desc": "Electrical apparatus for switching/protecting circuits >1000V"},
    {"hsn": "8535.10", "gst": 18, "desc": "Fuses for voltage >1000V"},
    {"hsn": "8535.21", "gst": 18, "desc": "Automatic circuit breakers — oil"},
    {"hsn": "8535.29", "gst": 18, "desc": "Automatic circuit breakers — other (MCB/MCCB)"},
    {"hsn": "8535.40", "gst": 18, "desc": "Lightning arrestors, voltage limiters"},
    {"hsn": "8537", "gst": 18, "desc": "Boards, panels for electrical control — switchboards"},
    {"hsn": "8537.10", "gst": 18, "desc": "Electrical control panels ≤1000V — distribution boards"},
    {"hsn": "8537.20", "gst": 18, "desc": "Electrical control panels >1000V"},

    # ── Motors & Generators ───────────────────────────────────────────────
    {"hsn": "8501", "gst": 18, "desc": "Electric motors and generators"},
    {"hsn": "8501.10", "gst": 18, "desc": "Motors of output ≤37.5W"},
    {"hsn": "8501.20", "gst": 18, "desc": "Universal AC/DC motors >37.5W"},
    {"hsn": "8501.31", "gst": 18, "desc": "DC motors/generators ≤750W"},
    {"hsn": "8501.32", "gst": 18, "desc": "DC motors/generators 750W–75kW"},
    {"hsn": "8501.40", "gst": 18, "desc": "AC motors single phase"},
    {"hsn": "8501.51", "gst": 18, "desc": "AC motors multi-phase ≤750W"},
    {"hsn": "8501.52", "gst": 18, "desc": "AC motors multi-phase 750W–75kW"},

    # ── Transformers & Chargers ───────────────────────────────────────────
    {"hsn": "8504", "gst": 18, "desc": "Electrical transformers, static converters, inductors, chargers"},
    {"hsn": "8504.10", "gst": 18, "desc": "Ballasts for discharge lamps"},
    {"hsn": "8504.21", "gst": 18, "desc": "Liquid dielectric transformers ≤650 kVA"},
    {"hsn": "8504.31", "gst": 18, "desc": "Transformers ≤1 kVA — other"},
    {"hsn": "8504.32", "gst": 18, "desc": "Transformers 1–16 kVA"},
    {"hsn": "8504.40", "gst": 18, "desc": "Static converters — UPS, inverters, chargers, adapters"},
    {"hsn": "8504.50", "gst": 18, "desc": "Inductors — electrical"},
    {"hsn": "8504.90", "gst": 18, "desc": "Parts of transformers and chargers"},

    # ── Lighting ──────────────────────────────────────────────────────────
    {"hsn": "9405", "gst": 12, "desc": "Lamps, light fittings, illuminated signs"},
    {"hsn": "9405.10", "gst": 12, "desc": "Chandeliers and electric ceiling/wall light fittings"},
    {"hsn": "9405.40", "gst": 12, "desc": "LED lamps, other electric lamps and light fittings"},
    {"hsn": "9405.50", "gst": 12, "desc": "Non-electrical lamps and lighting fittings"},
    {"hsn": "8539", "gst": 12, "desc": "Electric filament/discharge lamps — LED bulbs, tube lights"},
    {"hsn": "8539.10", "gst": 12, "desc": "Sealed beam lamp units"},
    {"hsn": "8539.21", "gst": 12, "desc": "Tungsten halogen lamps"},
    {"hsn": "8539.22", "gst": 12, "desc": "Filament lamps — other"},
    {"hsn": "8539.31", "gst": 12, "desc": "Fluorescent lamps — hot cathode"},
    {"hsn": "8539.39", "gst": 12, "desc": "Discharge lamps — other"},
    {"hsn": "8539.50", "gst": 12, "desc": "LED lamps"},

    # ── Fans ──────────────────────────────────────────────────────────────
    {"hsn": "8414", "gst": 18, "desc": "Air pumps, vacuum pumps, fans, air compressors"},
    {"hsn": "8414.51", "gst": 18, "desc": "Ceiling fans"},
    {"hsn": "8414.59", "gst": 18, "desc": "Table fans, wall fans, exhaust fans — other"},

    # ── Pumps ─────────────────────────────────────────────────────────────
    {"hsn": "8413", "gst": 18, "desc": "Pumps for liquids — water pumps, submersible pumps"},
    {"hsn": "8413.11", "gst": 18, "desc": "Pumps for dispensing fuel"},
    {"hsn": "8413.70", "gst": 18, "desc": "Centrifugal pumps — other (water pumps)"},
    {"hsn": "8413.81", "gst": 18, "desc": "Pumps — other"},

    # ── Batteries & Inverters ─────────────────────────────────────────────
    {"hsn": "8507", "gst": 18, "desc": "Electric accumulators — lead acid batteries, lithium batteries"},
    {"hsn": "8507.10", "gst": 18, "desc": "Lead acid batteries for starting piston engines"},
    {"hsn": "8507.20", "gst": 18, "desc": "Lead acid batteries — other (inverter batteries)"},
    {"hsn": "8507.60", "gst": 18, "desc": "Lithium-ion batteries"},
    {"hsn": "8507.80", "gst": 18, "desc": "Batteries — other"},

    # ── Mobile Phones & Accessories ───────────────────────────────────────
    {"hsn": "8517", "gst": 18, "desc": "Telephone sets, mobile phones, smartphones"},
    {"hsn": "8517.12", "gst": 18, "desc": "Mobile phones, smartphones"},
    {"hsn": "8517.70", "gst": 18, "desc": "Parts of mobile phones and telephones"},

    # ── USB Cables & Data Cables ──────────────────────────────────────────
    {"hsn": "8544.42", "gst": 18, "desc": "USB cable, data cable, charging cable — with connectors"},

    # ── Earphones / Headphones ────────────────────────────────────────────
    {"hsn": "8518", "gst": 18, "desc": "Microphones, headphones, earphones, speakers, amplifiers"},
    {"hsn": "8518.10", "gst": 18, "desc": "Microphones"},
    {"hsn": "8518.21", "gst": 18, "desc": "Loudspeakers — single"},
    {"hsn": "8518.30", "gst": 18, "desc": "Headphones and earphones"},
    {"hsn": "8518.40", "gst": 18, "desc": "Audio-frequency amplifiers"},

    # ── Power Banks ───────────────────────────────────────────────────────
    {"hsn": "8507.60", "gst": 18, "desc": "Power bank — lithium-ion battery"},

    # ── CCTV & Security ───────────────────────────────────────────────────
    {"hsn": "8525", "gst": 18, "desc": "CCTV cameras, transmission apparatus"},
    {"hsn": "8525.80", "gst": 18, "desc": "CCTV cameras, webcams, TV cameras"},

    # ── DVR / NVR ─────────────────────────────────────────────────────────
    {"hsn": "8521", "gst": 18, "desc": "Video recording apparatus — DVR, NVR"},

    # ── Computer & Peripherals ────────────────────────────────────────────
    {"hsn": "8471", "gst": 18, "desc": "Computers, laptops, printers, input/output units"},
    {"hsn": "8471.30", "gst": 18, "desc": "Laptops, portable computers"},
    {"hsn": "8471.41", "gst": 18, "desc": "Desktop computers"},
    {"hsn": "8473", "gst": 18, "desc": "Parts and accessories for computers"},
    {"hsn": "8443", "gst": 18, "desc": "Printers — laser, inkjet"},

    # ── TV & Display ──────────────────────────────────────────────────────
    {"hsn": "8528", "gst": 28, "desc": "LED TV, LCD TV, monitors, projectors"},
    {"hsn": "8528.72", "gst": 28, "desc": "LED/LCD television sets"},

    # ── AC / Refrigerator ─────────────────────────────────────────────────
    {"hsn": "8415", "gst": 28, "desc": "Air conditioners — window, split"},
    {"hsn": "8418", "gst": 12, "desc": "Refrigerators, freezers"},

    # ── Washing Machine ───────────────────────────────────────────────────
    {"hsn": "8450", "gst": 28, "desc": "Washing machines"},

    # ── Geysers / Water Heaters ───────────────────────────────────────────
    {"hsn": "8516", "gst": 18, "desc": "Electric water heaters, geysers, immersion heaters, irons"},
    {"hsn": "8516.10", "gst": 18, "desc": "Immersion heaters, instant geysers"},
    {"hsn": "8516.40", "gst": 18, "desc": "Electric irons"},
    {"hsn": "8516.50", "gst": 18, "desc": "Microwave ovens"},
    {"hsn": "8516.60", "gst": 18, "desc": "Cooking ovens — electric"},

    # ── Conduit & Pipes ───────────────────────────────────────────────────
    {"hsn": "3917", "gst": 18, "desc": "Plastic tubes, pipes, conduit pipes"},
    {"hsn": "7304", "gst": 18, "desc": "Seamless iron/steel tubes and pipes"},

    # ── Junction Boxes & Enclosures ───────────────────────────────────────
    {"hsn": "8538", "gst": 18, "desc": "Parts for switchboards, control panels, junction boxes"},

    # ── PVC Tape / Insulation ─────────────────────────────────────────────
    {"hsn": "3919", "gst": 18, "desc": "Self-adhesive plates, film, tape — PVC insulation tape"},

    # ── Tools ─────────────────────────────────────────────────────────────
    {"hsn": "8205", "gst": 18, "desc": "Hand tools — pliers, screwdrivers, hammers, spanners"},
    {"hsn": "8467", "gst": 18, "desc": "Power tools — drills, grinders"},

    # ── Soldering ─────────────────────────────────────────────────────────
    {"hsn": "8515", "gst": 18, "desc": "Soldering, brazing, welding equipment"},

    # ── Capacitors / Resistors ────────────────────────────────────────────
    {"hsn": "8532", "gst": 18, "desc": "Electrical capacitors — fixed, variable"},
    {"hsn": "8533", "gst": 18, "desc": "Electrical resistors"},

    # ── Meters ────────────────────────────────────────────────────────────
    {"hsn": "9030", "gst": 18, "desc": "Multimeters, oscilloscopes, measuring instruments"},
    {"hsn": "9028", "gst": 18, "desc": "Electricity meters, gas meters, water meters"},

    # ── Stabilizers / Voltage Regulators ─────────────────────────────────
    {"hsn": "8504.40", "gst": 18, "desc": "Voltage stabilizer, servo stabilizer, voltage regulator"},

    # ── Solar Panels ──────────────────────────────────────────────────────
    {"hsn": "8541", "gst": 5, "desc": "Solar cells, solar panels, photovoltaic cells"},
    {"hsn": "8541.40", "gst": 5, "desc": "Solar panels, photovoltaic modules"},

    # ── Extension Cords / Power Strip ─────────────────────────────────────
    {"hsn": "8544.42", "gst": 18, "desc": "Extension cord, power strip with connectors"},

    # ── Earthing Material ─────────────────────────────────────────────────
    {"hsn": "7408", "gst": 18, "desc": "Copper wire — earthing wire"},
    {"hsn": "7605", "gst": 18, "desc": "Aluminium wire — earthing"},

    # ── Connectors / Lugs ─────────────────────────────────────────────────
    {"hsn": "8536.90", "gst": 18, "desc": "Electrical connectors, lugs, terminal blocks"},

    # ── Condenser / Motor Capacitor ───────────────────────────────────────
    {"hsn": "8532.21", "gst": 18, "desc": "Motor running capacitor, AC capacitor"},

    # ── Inverter / UPS ────────────────────────────────────────────────────
    {"hsn": "8504.40", "gst": 18, "desc": "Inverter, UPS, online UPS, offline UPS"},

    # ── Cable Ties / Clips ────────────────────────────────────────────────
    {"hsn": "3926", "gst": 18, "desc": "Cable ties, plastic clips, cable clamps — plastic"},

    # ── Screws & Fasteners ────────────────────────────────────────────────
    {"hsn": "7318", "gst": 18, "desc": "Screws, bolts, nuts, washers — iron/steel"},

    # ── Pipes (GI/MS) ─────────────────────────────────────────────────────
    {"hsn": "7306", "gst": 18, "desc": "Tubes and pipes — GI pipe, MS pipe"},
]

# ── Keyword mapping for smart search ────────────────────────────────────────
KEYWORD_MAP = {
    # Wires & Cables
    "wire": "8544", "cable": "8544", "coaxial": "8544.20",
    "usb cable": "8544.42", "data cable": "8544.42", "charging cable": "8544.42",
    "extension": "8544.42", "power strip": "8544.42", "earthing wire": "7408",
    "copper wire": "7408", "aluminium wire": "7605",

    # Switches & Sockets
    "switch": "8536.50", "socket": "8536.69", "plug": "8536.69",
    "outlet": "8536.69", "relay": "8536.49", "fuse": "8536.10",
    "lamp holder": "8536.61", "bulb holder": "8536.61",

    # MCB / Boards
    "mcb": "8535.29", "mccb": "8535.29", "rccb": "8535.29",
    "circuit breaker": "8535.29", "distribution board": "8537.10",
    "db box": "8537.10", "main switch": "8537.10", "panel": "8537.10",
    "switchboard": "8537.10", "junction box": "8538",

    # Charger / Transformer
    "charger": "8504.40", "adapter": "8504.40", "transformer": "8504.31",
    "ups": "8504.40", "inverter": "8504.40", "stabilizer": "8504.40",
    "voltage stabilizer": "8504.40", "servo stabilizer": "8504.40",

    # Motors
    "motor": "8501.40", "pump": "8413.70", "water pump": "8413.70",
    "submersible": "8413.70", "submersible pump": "8413.70",
    "generator": "8501.31",

    # Fans
    "fan": "8414.51", "ceiling fan": "8414.51", "table fan": "8414.59",
    "wall fan": "8414.59", "exhaust fan": "8414.59", "pedestal fan": "8414.59",

    # Lights
    "led": "8539.50", "bulb": "8539.22", "tube light": "8539.31",
    "tubelight": "8539.31", "cfl": "8539.39", "lamp": "9405.40",
    "batten": "8539.31", "downlight": "9405.40", "spotlight": "9405.40",
    "street light": "9405.40", "panel light": "9405.40", "strip light": "9405.40",

    # Battery
    "battery": "8507.20", "inverter battery": "8507.20",
    "lithium battery": "8507.60", "power bank": "8507.60",

    # Mobile
    "mobile": "8517.12", "smartphone": "8517.12", "phone": "8517.12",
    "earphone": "8518.30", "headphone": "8518.30", "speaker": "8518.21",

    # CCTV
    "cctv": "8525.80", "camera": "8525.80", "dvr": "8521", "nvr": "8521",

    # Appliances
    "ac": "8415", "air conditioner": "8415", "refrigerator": "8418",
    "fridge": "8418", "washing machine": "8450", "geyser": "8516.10",
    "water heater": "8516.10", "iron": "8516.40", "microwave": "8516.50",

    # Solar
    "solar panel": "8541.40", "solar": "8541.40",

    # Tools
    "drill": "8467", "grinder": "8467", "screwdriver": "8205",
    "pliers": "8205", "hammer": "8205", "spanner": "8205",
    "multimeter": "9030", "meter": "9028",

    # Capacitor
    "capacitor": "8532.21", "condenser": "8532.21",

    # Tape
    "tape": "3919", "pvc tape": "3919", "insulation tape": "3919",

    # Pipes & Conduit
    "conduit": "3917", "pipe": "7306", "gi pipe": "7306",
    "cable tie": "3926",

    # Screws
    "screw": "7318", "bolt": "7318", "nut": "7318",
}


def _similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def search_hsn(product_name: str) -> list:
    """
    Product name se HSN suggestions return karo.
    Returns list of dicts: [{hsn, gst, desc, score}]
    """
    if not product_name or len(product_name.strip()) < 2:
        return []

    name_lower = product_name.strip().lower()
    results = []

    # Step 1: Exact keyword match
    for kw, hsn_code in KEYWORD_MAP.items():
        if kw in name_lower:
            # HSN DB se details lo
            for entry in HSN_LOCAL_DB:
                if entry["hsn"] == hsn_code:
                    score = 1.0 if kw == name_lower else (0.9 if name_lower.startswith(kw) else 0.8)
                    results.append({**entry, "score": score, "match_type": "keyword"})
                    break

    # Step 2: Description similarity search
    name_words = set(re.findall(r'\w+', name_lower))
    for entry in HSN_LOCAL_DB:
        desc_lower = entry["desc"].lower()
        desc_words = set(re.findall(r'\w+', desc_lower))
        common = name_words & desc_words
        if common:
            score = len(common) / max(len(name_words), 1) * 0.7
            # Already added via keyword? Skip
            if not any(r["hsn"] == entry["hsn"] for r in results):
                if score > 0.2:
                    results.append({**entry, "score": score, "match_type": "desc"})

    # Step 3: Sort by score, remove duplicates (keep highest score per HSN)
    seen = {}
    for r in results:
        h = r["hsn"]
        if h not in seen or r["score"] > seen[h]["score"]:
            seen[h] = r

    sorted_results = sorted(seen.values(), key=lambda x: -x["score"])
    return sorted_results[:6]   # Top 6 suggestions


def get_hsn_details(hsn_code: str) -> dict | None:
    """HSN code se details fetch karo"""
    for entry in HSN_LOCAL_DB:
        if entry["hsn"] == hsn_code:
            return entry
    return None


def get_gst_rate(hsn_code: str) -> float:
    """HSN code se GST rate lo"""
    entry = get_hsn_details(hsn_code)
    return entry["gst"] if entry else 18.0

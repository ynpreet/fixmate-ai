#!/usr/bin/env python3
"""
FixMate AI -- The Intelligent Equipment Maintenance Agent
Demo 6 of 6, Agentic AI Workshop.

"Diagnose faster. Fix smarter. Keep every store running."

Fictional company: BrewPoint Retail (a convenience-store chain).
Everything in this file is SYNTHETIC data. Fully offline, stdlib-only,
zero API keys. Output is byte-identical across runs (no timestamps,
no randomness, no network).

Honesty note (also in README.md): the orchestrator's "LLM" is a
deterministic policy engine, not a real language model. The agentic
loop -- plan -> tool call -> observe -> re-plan -- is real code, and
every plan step and tool call is printed so students can watch it work.
"""

import hashlib

DIV = "=" * 72
THIN = "-" * 72

# ---------------------------------------------------------------------------
# Print helpers -- the agentic loop is demo-visible through these.
# ---------------------------------------------------------------------------

def section(title):
    print("\n" + DIV)
    print(title)
    print(DIV)


def plan(n, text):
    print("[PLAN] %d. %s" % (n, text))


def think(text):
    print("[THINK] %s" % text)


def tool(name, params, result):
    print("[TOOL] %s(%s)" % (name, params))
    print("       -> %s" % result)


def obs(text):
    print("[OBS ] %s" % text)


def safety(text):
    print("[SAFETY] %s" % text)


def decide(text):
    print("[DECIDE] %s" % text)


def gapnote(text):
    print("[GAP ] %s" % text)


# ---------------------------------------------------------------------------
# SYNTHETIC KNOWLEDGE BASE -- BrewPoint Retail (fictional).
# 3 coffee-machine models, synthetic service manuals with versions,
# error codes, procedures, parts, safety classes.
# ---------------------------------------------------------------------------

def build_kb():
    """Return a fresh, pristine knowledge base. Scenario B mutates the live
    copy (expert manual update); the evaluation section rebuilds a pristine
    copy so the test set measures the documented behavior, not the demo's
    scripted update."""
    manuals = {
        "CP-100": {
            "model_name": "BrewPoint Classic CP-100",
            "manual_id": "MAN-CP100-2.1",
            "version": "2.1",
            "sections_indexed": ["1", "2", "3", "4", "5", "6"],
            "error_codes": {
                "E10": {
                    "title": "Water tank empty",
                    "section": "3.2", "page": 41,
                    "procedure_id": "P-CP100-10",
                },
                "E11": {
                    "title": "Brew temperature low",
                    "section": "3.4", "page": 44,
                    "procedure_id": "P-CP100-11",
                },
                "E50": {
                    "title": "Heating element resistance out of range",
                    "section": "5.1", "page": 102,
                    "procedure_id": "P-CP100-50",
                },
                "E14": {
                    "title": "Drip tray sensor fault",
                    "section": "3.6", "page": 47,
                    "procedure_id": "P-CP100-14",
                },
                "E20": {
                    "title": "Pump motor current out of range",
                    "section": "5.4", "page": 108,
                    "procedure_id": "P-CP100-20",
                },
            },
        },
        "CP-200": {
            "model_name": "BrewPoint Pro CP-200",
            "manual_id": "MAN-CP200-3.2",
            "version": "3.2",
            "sections_indexed": ["1", "2", "3", "4", "5", "6", "7"],
            "error_codes": {
                "E17": {
                    "title": "Brew group blockage -- descaling required",
                    "section": "4.7", "page": 88,
                    "procedure_id": "P-CP200-17",
                },
                "E23": {
                    "title": "Grinder jam",
                    "section": "4.3", "page": 79,
                    "procedure_id": "P-CP200-23",
                },
                "E31": {
                    "title": "Heating element resistance out of range",
                    "section": "5.2", "page": 111,
                    "procedure_id": "P-CP200-31",
                },
                "E28": {
                    "title": "Milk frother fault -- purge and clean",
                    "section": "4.9", "page": 93,
                    "procedure_id": "P-CP200-28",
                },
                "E35": {
                    "title": "Water filter expired",
                    "section": "6.2", "page": 124,
                    "procedure_id": "P-CP200-35",
                },
            },
        },
        "CP-300": {
            "model_name": "BrewPoint Xpress CP-300",
            "manual_id": "MAN-CP300-1.4",
            "version": "1.4",
            "sections_indexed": ["1", "2", "3", "4", "5", "6"],
            "error_codes": {
                "E05": {
                    "title": "Drip tray full",
                    "section": "2.1", "page": 22,
                    "procedure_id": "P-CP300-05",
                },
                "E12": {
                    "title": "Bean hopper empty",
                    "section": "2.4", "page": 26,
                    "procedure_id": "P-CP300-12",
                },
                "E18": {
                    "title": "Grinder calibration drift",
                    "section": "4.2", "page": 71,
                    "procedure_id": "P-CP300-18",
                },
                "E25": {
                    "title": "Steam wand blocked",
                    "section": "3.8", "page": 52,
                    "procedure_id": "P-CP300-25",
                },
                # E42 deliberately ABSENT -- this is the knowledge gap.
            },
        },
    }

    procedures = {
        "P-CP100-10": {
            "id": "P-CP100-10", "model": "CP-100", "error_code": "E10",
            "title": "Refill the water tank",
            "safety_class": "ROUTINE", "caution": None,
            "citation": "BrewPoint CP-100 Service Manual v2.1, §3.2 (p. 41)",
            "steps": [
                "Switch the machine OFF.",
                "Slide the water tank out from the rear of the machine.",
                "Rinse the tank; fill with fresh cold water up to the MAX line.",
                "Slide the tank back until it clicks into place.",
                "Switch the machine ON. E10 clears within 30 seconds.",
            ],
            "symptoms": ["display shows E10", "no water flow", "tank indicator lit"],
            "part": None,
        },
        "P-CP100-11": {
            "id": "P-CP100-11", "model": "CP-100", "error_code": "E11",
            "title": "Run the preheat cycle",
            "safety_class": "HOT_WATER_CAUTION",
            "caution": ("HOT WATER / STEAM: keep hands clear of the brew head and "
                        "hot-water spout during this procedure."),
            "citation": "BrewPoint CP-100 Service Manual v2.1, §3.4 (p. 44)",
            "steps": [
                "From the menu, select Maintenance > Preheat cycle.",
                "Place a large cup under the spout and dispense 8 oz of hot water.",
                "Wait 2 minutes, then brew a test shot.",
                "If E11 persists after two preheat cycles, escalate to a technician.",
            ],
            "symptoms": ["display shows E11", "lukewarm coffee", "slow heat-up"],
            "part": None,
        },
        "P-CP100-50": {
            "id": "P-CP100-50", "model": "CP-100", "error_code": "E50",
            "title": "Heating element failure -- qualified technician only",
            "safety_class": "ELECTRICAL",
            "caution": ("120V MAINS INSIDE THE CHASSIS. Do not open the machine. "
                        "Risk of electric shock."),
            "citation": "BrewPoint CP-100 Service Manual v2.1, §5.1 (p. 102)",
            "steps": [
                "STOP. Do not attempt self-service.",
                "Power the machine OFF and unplug it.",
                "A qualified technician must confirm the failure on-site, "
                "then replace the heating element.",
            ],
            "symptoms": ["display shows E50", "no heat", "breaker trips"],
            "part": "HE-2200",
        },
        "P-CP200-17": {
            "id": "P-CP200-17", "model": "CP-200", "error_code": "E17",
            "title": "Descale and clear the brew-group blockage",
            "safety_class": "ROUTINE",
            "caution": ("HOT WATER / STEAM during the descale cycle: keep hands "
                        "clear of the brew head."),
            "citation": "BrewPoint CP-200 Service Manual v3.2, §4.7 (p. 88)",
            "steps": [
                "Power OFF and let the machine cool for 10 minutes.",
                "Remove the drip tray. Unlatch the brew group (latch A) and slide it out.",
                "Rinse the brew group under warm water; check the seals for scale buildup.",
                "Empty and replace the drip tray.",
                "Add BrewPoint descaler DC-9000 per label (or 1:1 white vinegar and water) to the tank.",
                "Power ON; run Maintenance > Descale cycle.",
                "Rinse the tank and run 2 rinse cycles with fresh water.",
                "Verify E17 is cleared; brew a test shot.",
                "If E17 persists after two descale cycles, log a knowledge gap and escalate.",
            ],
            "symptoms": ["display shows E17",
                         "visible scale buildup on brew group seals",
                         "slow or no coffee flow", "grinding noise during brew"],
            "part": "DC-9000",
        },
        "P-CP200-23": {
            "id": "P-CP200-23", "model": "CP-200", "error_code": "E23",
            "title": "Clear the grinder jam",
            "safety_class": "ROUTINE",
            "caution": "Never put fingers near the burrs. Use the cleaning brush only.",
            "citation": "BrewPoint CP-200 Service Manual v3.2, §4.3 (p. 79)",
            "steps": [
                "Power OFF and unplug the machine.",
                "Remove the bean hopper.",
                "Clear jammed beans from the burr chamber with the cleaning brush.",
                "Replace the hopper, power ON, and grind a test dose.",
                "If E23 persists, escalate to a technician.",
            ],
            "symptoms": ["display shows E23", "grinder hums but no grounds",
                         "burnt smell from grinder"],
            "part": "BR-2210",
        },
        "P-CP100-14": {
            "id": "P-CP100-14", "model": "CP-100", "error_code": "E14",
            "title": "Drip tray sensor fault -- clean and reseat",
            "safety_class": "ROUTINE", "caution": None,
            "citation": "BrewPoint CP-100 Service Manual v2.1, §3.6 (p. 47)",
            "steps": [
                "Switch the machine OFF.",
                "Slide the drip tray out and empty it.",
                "Wipe the two metal sensor contacts under the tray bay with a dry cloth.",
                "Slide the tray back until it clicks into place.",
                "Switch the machine ON. E14 clears if the sensor reads the tray.",
                "If E14 persists with a clean, seated tray, escalate to a technician.",
            ],
            "symptoms": ["display shows E14", "tray-full indicator lit with empty tray"],
            "part": None,
        },
        "P-CP100-20": {
            "id": "P-CP100-20", "model": "CP-100", "error_code": "E20",
            "title": "Pump motor fault -- qualified technician only",
            "safety_class": "ELECTRICAL",
            "caution": ("120V MAINS INSIDE THE CHASSIS. The pump circuit carries "
                        "mains voltage. Risk of electric shock."),
            "citation": "BrewPoint CP-100 Service Manual v2.1, §5.4 (p. 108)",
            "steps": [
                "STOP. Do not attempt self-service.",
                "Switch the machine OFF and unplug it.",
                "A qualified technician must confirm the pump fault on-site, "
                "then repair or replace the pump motor.",
            ],
            "symptoms": ["display shows E20", "no water pressure", "pump hums then cuts out"],
            "part": "PM-1100",
        },
        "P-CP200-28": {
            "id": "P-CP200-28", "model": "CP-200", "error_code": "E28",
            "title": "Milk frother fault -- purge and clean",
            "safety_class": "ROUTINE", "caution": None,
            "citation": "BrewPoint CP-200 Service Manual v3.2, §4.9 (p. 93)",
            "steps": [
                "Run the frother purge cycle from Maintenance > Frother purge.",
                "Remove the frother wand tip and soak it in hot soapy water for 5 minutes.",
                "Clear the wand bore with the cleaning pin from the tool kit.",
                "Reattach the tip and run one more purge cycle.",
                "If E28 persists after two purge cycles, escalate to a technician.",
            ],
            "symptoms": ["display shows E28", "weak or no steam from frother", "milk not foaming"],
            "part": None,
        },
        "P-CP200-35": {
            "id": "P-CP200-35", "model": "CP-200", "error_code": "E35",
            "title": "Water filter expired -- replace cartridge",
            "safety_class": "ROUTINE", "caution": None,
            "citation": "BrewPoint CP-200 Service Manual v3.2, §6.2 (p. 124)",
            "steps": [
                "Open the filter door on the left side of the machine.",
                "Twist the old cartridge counter-clockwise and pull it out.",
                "Insert a new FL-2200 cartridge and twist clockwise until seated.",
                "From the menu, select Maintenance > Reset filter timer.",
                "Brew a test shot to confirm E35 clears.",
            ],
            "symptoms": ["display shows E35", "filter timer at 0 days"],
            "part": "FL-2200",
        },
        "P-CP300-18": {
            "id": "P-CP300-18", "model": "CP-300", "error_code": "E18",
            "title": "Grinder calibration drift -- recalibrate",
            "safety_class": "ROUTINE", "caution": None,
            "citation": "BrewPoint CP-300 Service Manual v1.4, §4.2 (p. 71)",
            "steps": [
                "From the menu, select Maintenance > Grinder calibration.",
                "Run the calibration cycle with an empty hopper (takes ~2 minutes).",
                "Grind a test dose and check the particle spread on the test card.",
                "If E18 persists after two calibration cycles, escalate to a technician.",
            ],
            "symptoms": ["display shows E18", "inconsistent grind", "shots pulling too fast or slow"],
            "part": None,
        },
        "P-CP300-25": {
            "id": "P-CP300-25", "model": "CP-300", "error_code": "E25",
            "title": "Steam wand blocked -- clear and purge",
            "safety_class": "HOT_WATER_CAUTION",
            "caution": ("HOT STEAM: the wand stays hot for several minutes after "
                        "use. Keep hands clear of the tip during purging."),
            "citation": "BrewPoint CP-300 Service Manual v1.4, §3.8 (p. 52)",
            "steps": [
                "Let the wand cool for 5 minutes, then wipe the exterior with a damp cloth.",
                "Remove the steam tip and soak it in hot soapy water for 5 minutes.",
                "Clear the tip holes with the cleaning pin.",
                "Reattach the tip, keeping hands clear, and purge steam for 10 seconds.",
                "If E25 persists, escalate to a technician.",
            ],
            "symptoms": ["display shows E25", "weak steam", "wand sputters"],
            "part": None,
        },
        "P-CP200-31": {
            "id": "P-CP200-31", "model": "CP-200", "error_code": "E31",
            "title": "Heating element failure -- qualified technician only",
            "safety_class": "ELECTRICAL",
            "caution": ("120V MAINS INSIDE THE CHASSIS. Do not open the machine. "
                        "Risk of electric shock."),
            "citation": "BrewPoint CP-200 Service Manual v3.2, §5.2 (p. 111)",
            "steps": [
                "STOP. Do not attempt self-service.",
                "Power the machine OFF and unplug it.",
                "A qualified technician must confirm the failure on-site, "
                "then replace the heating element.",
            ],
            "symptoms": ["display shows E31", "no heat", "resistance reading out of range"],
            "part": "HE-2200",
        },
        "P-CP300-05": {
            "id": "P-CP300-05", "model": "CP-300", "error_code": "E05",
            "title": "Empty the drip tray",
            "safety_class": "ROUTINE", "caution": None,
            "citation": "BrewPoint CP-300 Service Manual v1.4, §2.1 (p. 22)",
            "steps": [
                "Slide the drip tray out from the front.",
                "Empty and rinse it.",
                "Slide it back until it clicks. E05 clears immediately.",
            ],
            "symptoms": ["display shows E05", "tray-full indicator lit"],
            "part": None,
        },
        "P-CP300-12": {
            "id": "P-CP300-12", "model": "CP-300", "error_code": "E12",
            "title": "Refill the bean hopper",
            "safety_class": "ROUTINE", "caution": None,
            "citation": "BrewPoint CP-300 Service Manual v1.4, §2.4 (p. 26)",
            "steps": [
                "Open the bean hopper lid.",
                "Fill with whole beans up to the MAX line; close the lid.",
                "Grind a test dose. E12 clears automatically.",
            ],
            "symptoms": ["display shows E12", "grinder runs empty"],
            "part": None,
        },
    }

    parts = {
        "HE-2200": {
            "name": "Heating element, 120V / 1500W",
            "compatible_models": ["CP-100", "CP-200"],
            "safety_note": "ELECTRICAL part. Replacement by qualified technician only.",
        },
        "DC-9000": {
            "name": "BrewPoint descaler, 32 oz",
            "compatible_models": ["CP-100", "CP-200", "CP-300"],
            "safety_note": "Food-safe when label directions are followed.",
        },
        "BR-2210": {
            "name": "Grinder cleaning brush",
            "compatible_models": ["CP-200"],
            "safety_note": "No safety restriction.",
        },
        "BG-4400": {
            "name": "Brew group seal kit",
            "compatible_models": ["CP-200"],
            "safety_note": "Install per manual §4.7; machine must be cool.",
        },
        "PS-3300": {
            "name": "Pressure sensor, CP-300",
            "compatible_models": ["CP-300"],
            "safety_note": "PRESSURIZED circuit. Replacement by qualified technician only.",
        },
    }

    inventory = {"HE-2200": 14, "DC-9000": 220, "BR-2210": 61,
                 "BG-4400": 37, "PS-3300": 9}

    # Older / alternate documents kept ONLY to trap naive keyword search
    # (the baseline). FixMate never searches these: it resolves to the
    # current version via check_document_version.
    superseded_docs = [
        {"doc_id": "MAN-CP200-3.0 (SUPERSEDED)",
         "model": "CP-200", "version": "3.0",
         "text": ("CP-200 service manual v3.0 (superseded by v3.2). "
                   "E17 brew group blockage: power off, remove brew group, "
                   "soak in vinegar overnight, reassemble. "
                   "E23 grinder jam: unplug, clear burrs with brush.")},
        {"doc_id": "QSC-CP300-1.0 (quick-start card)",
         "model": "CP-300", "version": "1.0",
         "text": ("CP-300 quick-start card v1.0 (not the service manual). "
                   "E05 drip tray full: empty the tray. "
                   "E12 bean hopper empty: add beans. "
                   "Tip: if the machine leaks, wipe the counter.")},
    ]

    external_sources = [
        {"source": "BrewPoint manufacturer support library",
         "doc": "Service Bulletin SB-CP300-026",
         "published": "2026-08-15",
         "matches_query": "CP-300 E42",
         "summary": ("E42 on the CP-300 indicates pressure-sensor drift during "
                     "heat-up. Suggested: power-cycle the machine; if the code "
                     "returns, recalibrate the sensor via the service menu or "
                     "replace sensor PS-3300. Sensor replacement must be done "
                     "by a qualified technician.")},
    ]

    return {
        "manuals": manuals,
        "procedures": procedures,
        "parts": parts,
        "inventory": inventory,
        "superseded_docs": superseded_docs,
        "external_sources": external_sources,
    }


KB = build_kb()

# Deterministic ticket counter (no timestamps anywhere in this demo).
_TICKET_SEQ = [847]


def next_ticket_id():
    _TICKET_SEQ[0] += 1
    return "FM-2026-%04d" % _TICKET_SEQ[0]


# ---------------------------------------------------------------------------
# DETERMINISTIC SAFETY / AUTHORIZATION LAYER.
# The orchestrator's reasoning policy CANNOT bypass this layer: guided
# execution requires a token that only SafetyLayer.authorize() can mint,
# and the token is verified before any step runs.
# ---------------------------------------------------------------------------

SAFETY_POLICY = {
    "ROUTINE": {"store_employee", "shift_supervisor", "qualified_technician"},
    "HOT_WATER_CAUTION": {"store_employee", "shift_supervisor",
                          "qualified_technician"},
    "ELECTRICAL": {"qualified_technician"},
    "PRESSURIZED": {"qualified_technician"},
}

SAFETY_EXPLANATIONS = {
    "ROUTINE": "Routine frontline procedure. Any trained store role may perform it.",
    "HOT_WATER_CAUTION": ("Routine procedure with a hot-water/steam caution. "
                          "Any trained store role may perform it with care."),
    "ELECTRICAL": ("RESTRICTED: 120V mains inside the chassis. Risk of electric "
                   "shock. Qualified technician ONLY."),
    "PRESSURIZED": ("RESTRICTED: pressurized hot-water circuit. Risk of burns "
                    "and component rupture. Qualified technician ONLY."),
}


def safety_authorize(procedure_id, user_role, kb):
    """Mint an authorization token, or deny. Deterministic: same inputs
    always produce the same token."""
    proc = kb["procedures"][procedure_id]
    sclass = proc["safety_class"]
    allowed = user_role in SAFETY_POLICY[sclass]
    token = None
    if allowed:
        payload = "FIXMATE-SAFETY-V1|%s|%s" % (procedure_id, user_role)
        token = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return {"allowed": allowed, "token": token,
            "safety_class": sclass,
            "reason": SAFETY_EXPLANATIONS[sclass]}


def safety_execute(procedure_id, user_role, token, kb):
    """Execute a guided procedure ONLY with a valid token. No token (or a
    forged one) -> PermissionError. This is what makes the safety layer
    unbypassable: the tool itself enforces it, not the orchestrator."""
    expected = safety_authorize(procedure_id, user_role, kb)["token"]
    if token is None or token != expected:
        raise PermissionError(
            "SAFETY GATE: execution of %s denied -- no valid authorization "
            "token. The safety layer cannot be bypassed." % procedure_id)
    return kb["procedures"][procedure_id]["steps"]


# ---------------------------------------------------------------------------
# VISION -- pluggable interface. The bundled implementation is SIMULATED
# (structured image metadata stands in for a real multimodal model).
# ---------------------------------------------------------------------------

class VisionInterface:
    """Pluggable contract. To use a real multimodal model, implement
    describe() to return a list of detection dicts and swap it in below."""

    def describe(self, image_metadata):
        raise NotImplementedError


class SimulatedVisionModel(VisionInterface):
    """OFFLINE STAND-IN -- NOT a real vision model. Returns the detections
    embedded in the structured image-metadata input. In production this
    would call a real multimodal model; the policy below (never definitive
    without manual cross-check or human confirmation) stays the same."""

    def describe(self, image_metadata):
        return image_metadata["simulated_detections"]


VISION = SimulatedVisionModel()

# Policy constants: vision output is evidence, never proof.
VISION_CONFIRM_THRESHOLD = 0.90   # at/above: "strong" (still cross-checked)
VISION_SUPPORT_THRESHOLD = 0.50   # at/above: "supporting"; below: rejected


def assess_visual_evidence(detections):
    assessed = []
    for d in detections:
        c = d["confidence"]
        if c >= VISION_CONFIRM_THRESHOLD:
            verdict = "STRONG (still requires manual cross-check)"
        elif c >= VISION_SUPPORT_THRESHOLD:
            verdict = "SUPPORTING (not definitive on its own)"
        else:
            verdict = "REJECTED (below 0.50 -- request clearer photo or human confirmation)"
        assessed.append({"component": d["component"],
                         "observation": d["observation"],
                         "confidence": c, "verdict": verdict})
    return assessed

# ---------------------------------------------------------------------------
# TOOLS -- the orchestrator's only way to touch the world. Each prints its
# call so students see the agentic loop.
# ---------------------------------------------------------------------------

def identify_equipment(model_code, kb):
    m = kb["manuals"].get(model_code)
    if m is None:
        tool("identify_equipment", "model_code='%s'" % model_code,
             "UNKNOWN MODEL -- no manual indexed")
        return None
    tool("identify_equipment", "model_code='%s'" % model_code,
         "%s | manual %s (v%s) | %d error codes indexed"
         % (m["model_name"], m["manual_id"], m["version"],
            len(m["error_codes"])))
    return m


def search_internal_manual(model_code, query, kb):
    """Search the CURRENT indexed manual for this model only.
    Returns the matching procedure, or None (a real 'not found')."""
    m = kb["manuals"][model_code]
    q = query.strip().upper()
    hit = None
    if q in m["error_codes"]:
        hit = m["error_codes"][q]
    else:
        # symptom search across this model's procedures only
        ql = query.strip().lower()
        for code in sorted(m["error_codes"]):
            proc = kb["procedures"][m["error_codes"][code]["procedure_id"]]
            if any(ql in s for s in proc["symptoms"]) or ql in proc["title"].lower():
                hit = m["error_codes"][code]
                break
    if hit is None:
        tool("search_internal_manual",
             "model='%s', query='%s'" % (model_code, query),
             "NO MATCH in %s (v%s) -- sections searched: %s"
             % (m["manual_id"], m["version"], ",".join(m["sections_indexed"])))
        return None
    proc = kb["procedures"][hit["procedure_id"]]
    tool("search_internal_manual",
         "model='%s', query='%s'" % (model_code, query),
         "MATCH: %s -- %s | %s"
         % (hit["procedure_id"], proc["title"], proc["citation"]))
    return proc


def check_document_version(model_code, kb):
    m = kb["manuals"][model_code]
    tool("check_document_version", "model='%s'" % model_code,
         "indexed manual: %s | version %s | sections: %s | LATEST KNOWN: v%s -- %s"
         % (m["manual_id"], m["version"], ",".join(m["sections_indexed"]),
            m["version"],
            "CURRENT (no newer version published)" if not m.get("superseded_by")
            else "SUPERSEDED by v" + m["superseded_by"]))
    return m


def prove_search_conclusive(model_code, query, kb):
    """The agent must PROVE a 'not found' is a documentation gap, not a
    search miss: right model? right manual? right (current) version?
    correct manual fully indexed?"""
    m = kb["manuals"][model_code]
    checks = [
        ("model resolved to a known model", model_code in kb["manuals"]),
        ("searched the service manual (not a quick-start card)",
         m["manual_id"].startswith("MAN-")),
        ("manual version is the current published version",
         not m.get("superseded_by")),
        ("all manual sections indexed",
         len(m["sections_indexed"]) == int(m["sections_indexed"][-1])),
    ]
    for label, ok in checks:
        tool("prove_search_conclusive", "'%s'" % label,
             "PASS" if ok else "FAIL")
    conclusive = all(ok for _, ok in checks)
    obs("Search for '%s' on %s was %s: this is a DOCUMENTATION GAP, not a search miss."
        % (query, model_code, "CONCLUSIVE" if conclusive else "INCONCLUSIVE"))
    return conclusive


def retrieve_part_details(part_number, kb):
    p = kb["parts"].get(part_number)
    if p is None:
        tool("retrieve_part_details", "part_number='%s'" % part_number,
             "UNKNOWN PART NUMBER")
        return None
    tool("retrieve_part_details", "part_number='%s'" % part_number,
         "%s | fits: %s | %s"
         % (p["name"], ", ".join(p["compatible_models"]), p["safety_note"]))
    return p


def search_approved_external_sources(query, kb):
    """Only AFTER the internal search is proven conclusive. Results are
    ALWAYS labeled EXTERNAL -- never presented as approved procedure."""
    hits = [s for s in kb["external_sources"]
            if s["matches_query"].lower() == query.strip().lower()]
    if not hits:
        tool("search_approved_external_sources", "query='%s'" % query,
             "no approved external source covers this query")
        return []
    for h in hits:
        tool("search_approved_external_sources", "query='%s'" % query,
             "[EXTERNAL -- NOT an approved BrewPoint procedure] %s | %s | published %s"
             % (h["source"], h["doc"], h["published"]))
        print("       summary: %s" % h["summary"])
    return hits


def check_part_availability(part_number, kb):
    qty = kb["inventory"].get(part_number, 0)
    tool("check_part_availability", "part_number='%s'" % part_number,
         "%d unit(s) at regional depot" % qty if qty else "OUT OF STOCK")
    return qty


TICKET_FIELDS = ["ticket_id", "store_id", "model", "error_code", "diagnosis",
                 "diagnosis_status", "safety_class", "part_number",
                 "part_availability", "status", "created_by_role", "next_step"]


def create_maintenance_ticket(store_id, model, error_code, diagnosis,
                              diagnosis_status, safety_class, part_number,
                              part_availability, user_role):
    t = {
        "ticket_id": next_ticket_id(),
        "store_id": store_id,
        "model": model,
        "error_code": error_code,
        "diagnosis": diagnosis,
        "diagnosis_status": diagnosis_status,   # SUSPECTED vs CONFIRMED
        "safety_class": safety_class,
        "part_number": part_number,
        "part_availability": part_availability,
        "status": "OPEN",
        "created_by_role": user_role,
        "next_step": "Dispatch qualified technician for on-site confirmation",
    }
    tool("create_maintenance_ticket",
         "store='%s', model='%s', error='%s'" % (store_id, model, error_code),
         "ticket %s OPEN | diagnosis: %s (%s) | part %s (%s)"
         % (t["ticket_id"], diagnosis, diagnosis_status, part_number,
            part_availability))
    return t


def verify_resolution(ticket_id, evidence):
    tool("verify_resolution", "ticket_id='%s'" % ticket_id,
         "RESOLVED -- evidence: %s" % evidence)
    return {"ticket_id": ticket_id, "status": "RESOLVED", "evidence": evidence}


# ---------------------------------------------------------------------------
# KNOWLEDGE GAP AGENT -- the continuous-improvement loop.
# Every unanswered question is logged; recurring gaps are reported to the
# documentation team; expert manual updates are re-indexed.
# ---------------------------------------------------------------------------

# Pre-seeded synthetic history (prior logged gaps).
GAP_LOG = [
    {"model": "CP-300", "error_code": "E42", "store_id": "#2077",
     "docs_searched": ["MAN-CP300-1.4 (§1-§6)"],
     "why_insufficient": "Error code absent from manual; no approved procedure."},
    {"model": "CP-300", "error_code": "E42", "store_id": "#3310",
     "docs_searched": ["MAN-CP300-1.4 (§1-§6)"],
     "why_insufficient": "Error code absent from manual; no approved procedure."},
]

GAP_REPORT_THRESHOLD = 3


def log_knowledge_gap(model, error_code, docs_searched, why_insufficient,
                      store_id):
    GAP_LOG.append({"model": model, "error_code": error_code,
                    "store_id": store_id, "docs_searched": docs_searched,
                    "why_insufficient": why_insufficient})
    gapnote("logged gap #%d: %s %s (store %s) -- %s"
            % (len(GAP_LOG), model, error_code, store_id, why_insufficient))


def recurring_gap_report():
    counts = {}
    for g in GAP_LOG:
        key = (g["model"], g["error_code"])
        counts[key] = counts.get(key, 0) + 1
    print("\n[KNOWLEDGE-GAP REPORT -- for the Documentation Team]")
    print(THIN)
    flagged = 0
    for (model, code) in sorted(counts):
        n = counts[(model, code)]
        status = ("RECURRING -- FLAGGED for manual update"
                  if n >= GAP_REPORT_THRESHOLD else "watching")
        print("  %s %s: %d report(s) -> %s" % (model, code, n, status))
        if n >= GAP_REPORT_THRESHOLD:
            flagged += 1
    if flagged == 0:
        print("  No recurring gaps. Nothing flagged.")
    return flagged


def apply_expert_manual_update(model, new_version, new_error_codes, kb):
    """Simulate the documentation team publishing an expert update, then
    re-index it so the agent's next search finds the answer internally."""
    m = kb["manuals"][model]
    old_version = m["version"]
    for code, entry in new_error_codes.items():
        m["error_codes"][code] = entry
        kb["procedures"][entry["procedure_id"]] = entry["procedure"]
    m["version"] = new_version
    m["manual_id"] = "MAN-%s-%s" % (model, new_version)
    m["sections_indexed"] = sorted(
        set(m["sections_indexed"]) | {e["section"].split(".")[0]
                                       for e in new_error_codes.values()})
    print("\n[DOCUMENTATION UPDATE -- expert loop]")
    print("  Documentation team published %s v%s (was v%s): added %s."
          % (model, new_version, old_version,
             ", ".join(sorted(new_error_codes))))
    print("  New version indexed. Future '%s' searches now resolve INTERNALLY."
          % (", ".join(sorted(new_error_codes))))


# ---------------------------------------------------------------------------
# SCENARIO A -- CP-200 + E17. The answer IS in the manual.
# ---------------------------------------------------------------------------

def scenario_a(kb):
    section("SCENARIO A -- 7:00 AM, store #1042: CP-200 shows Error E17")
    print("User: \"Coffee machine is down, display says E17. Customers are")
    print("arriving. I don't know what E17 means, which part it needs, or")
    print("whether I need a technician.\" [photo attached]")
    print()
    think("Simulated-LLM deliberation: E17 is a machine error code -> identify "
          "the exact model first (procedures differ by model), then check the "
          "internal manual FIRST. Web is a last resort.")
    print()
    plan(1, "identify_equipment('CP-200') -- confirm model + manual version")
    plan(2, "vision_describe(photo) -- collect visual evidence (policy: never definitive)")
    plan(3, "search_internal_manual('CP-200','E17') -- is the answer documented?")
    plan(4, "check_document_version -- cite the CURRENT version")
    plan(5, "SafetyLayer.authorize -- mandatory gate before guiding anyone")
    plan(6, "Guide the user through the DOCUMENTED steps, with citation")
    plan(7, "verify_resolution -- record the resolution")
    print()

    identify_equipment("CP-200", kb)

    photo = {
        "photo_id": "PH-1042-E17-01",
        "captured_by": "store camera upload",
        "simulated_detections": [
            {"component": "brew group",
             "observation": "white scale buildup around seals",
             "confidence": 0.62},
            {"component": "heating element casing",
             "observation": "possible discoloration",
             "confidence": 0.41},
        ],
    }
    detections = VISION.describe(photo)
    tool("vision_describe", "photo_id='PH-1042-E17-01' (SIMULATED vision)",
         "%d detection(s) returned by the vision interface" % len(detections))
    obs("Vision policy: image output is NEVER treated as definitive proof of "
        "component failure. Cross-check against the manual; require the error "
        "code/manual match or human confirmation.")
    for a in assess_visual_evidence(detections):
        print("       - %s: '%s' (confidence %.2f) -> %s"
              % (a["component"], a["observation"], a["confidence"], a["verdict"]))
    obs("Detection 1 (0.62) is SUPPORTING evidence and matches a documented "
        "E17 symptom. Detection 2 (0.41) is REJECTED -- too weak to use; "
        "the agent will NOT claim heating-element damage from it.")
    print()

    proc = search_internal_manual("CP-200", "E17", kb)
    check_document_version("CP-200", kb)
    print()
    think("Internal answer found and version-current. Safety gate next: the "
          "procedure involves hot water, so I must check the authorization "
          "policy for a store_employee before guiding.")
    auth = safety_authorize(proc["id"], "store_employee", kb)
    safety("authorize('%s', role='store_employee') -> %s | class=%s | token=%s"
           % (proc["id"], "ALLOWED" if auth["allowed"] else "DENIED",
              auth["safety_class"], auth["token"]))
    safety("reason: %s" % auth["reason"])
    if proc["caution"]:
        safety("caution surfaced to user: %s" % proc["caution"])
    print()
    decide("Diagnosis: E17 CONFIRMED by error-code + manual match "
           "(BrewPoint CP-200 Service Manual v3.2, §4.7). Photo is SUPPORTING "
           "evidence only. No technician needed -- guiding self-service.")
    print()
    print("GUIDED FIX -- follow these steps (from the manual, not from me):")
    print("Citation: %s" % proc["citation"])
    steps = safety_execute(proc["id"], "store_employee", auth["token"], kb)
    for i, s in enumerate(steps, 1):
        print("  %d. %s" % (i, s))
    if proc["part"]:
        retrieve_part_details(proc["part"], kb)
    print()
    verify_resolution("N/A (self-service)", "E17 cleared after descale cycle; "
                                            "test shot brewed OK (store #1042)")
    decide("SCENARIO A complete: diagnosed in one contact, cited procedure, "
           "resolution recorded. Time-to-diagnosis: 7 orchestrator steps.")
    return 7

# ---------------------------------------------------------------------------
# SCENARIO B -- CP-300 + E42. The answer is NOT in the manual.
# Demonstrates: conclusive-search proof -> approved external sources ->
# EXTERNAL labeling -> escalation -> knowledge-gap logging -> the expert
# update loop (field problem -> AI investigation -> documentation update ->
# better troubleshooting).
# ---------------------------------------------------------------------------

def scenario_b(kb):
    section("SCENARIO B -- store #1042: CP-300 shows Error E42 (unknown code)")
    print("User: \"Different machine -- the new CP-300. Display says E42. "
          "The quick-start card doesn't list it.\"")
    print()
    think("Simulated-LLM deliberation: unknown code on the newest model. "
          "Internal documents FIRST. If the manual truly lacks it, I must "
          "prove the search was conclusive before touching the web -- and I "
          "must NEVER invent a procedure to fill the gap.")
    print()
    plan(1, "identify_equipment('CP-300') -- confirm model + manual version")
    plan(2, "search_internal_manual('CP-300','E42') -- internal first")
    plan(3, "prove_search_conclusive -- is this a gap or a search miss?")
    plan(4, "check_document_version -- rule out a stale manual")
    plan(5, "search_approved_external_sources -- manufacturer docs first, labeled EXTERNAL")
    plan(6, "escalate + create ticket -- external guidance is unverified")
    plan(7, "log_knowledge_gap -- feed the continuous-improvement loop")
    print()

    identify_equipment("CP-300", kb)
    proc = search_internal_manual("CP-300", "E42", kb)
    print()
    conclusive = prove_search_conclusive("CP-300", "E42", kb)
    check_document_version("CP-300", kb)
    print()
    if proc is None and conclusive:
        think("No internal procedure exists. Per policy: approved external "
              "sources next (manufacturer docs first). Whatever I find will be "
              "labeled EXTERNAL -- never presented as approved procedure.")
        external = search_approved_external_sources("CP-300 E42", kb)
        print()
        if external:
            h = external[0]
            decide("External bulletin SB-CP300-026 (published %s) suggests "
                   "pressure-sensor drift and mentions sensor replacement "
                   "PS-3300. This is EXTERNAL, UNVERIFIED guidance -- it is "
                   "NOT an approved BrewPoint internal procedure, so I will "
                   "not guide the user through it. Escalating to a qualified "
                   "technician instead." % h["published"])
            part = retrieve_part_details("PS-3300", kb)
            qty = check_part_availability("PS-3300", kb)
            create_maintenance_ticket(
                "#1042", "CP-300", "E42",
                "suspected pressure-sensor drift (per EXTERNAL bulletin "
                "SB-CP300-026, 2026-08-15 -- unverified internally)",
                "SUSPECTED", "PRESSURIZED", "PS-3300",
                "%d in stock" % qty, "store_employee")
        else:
            decide("No approved external source covers E42 either. "
                   "Escalating with no speculative guidance.")
    print()
    log_knowledge_gap("CP-300", "E42", ["MAN-CP300-1.4 (§1-§6)"],
                      "Error code absent from manual; external bulletin "
                      "SB-CP300-026 exists but is unverified as internal "
                      "procedure.", "#1042")
    print()
    print("--- The continuous-improvement loop (Knowledge Gap Agent) ---")
    flagged = recurring_gap_report()
    if flagged:
        print()
        print("Field problem -> AI investigation -> technician resolution -> "
              "documentation update -> better troubleshooting.")
        print("The documentation team investigates the flagged E42 gap with")
        print("engineering, approves a procedure, and publishes CP-300 manual v1.5.")
        apply_expert_manual_update("CP-300", "1.5", {
            "E42": {
                "title": "Pressure sensor drift",
                "section": "7.1", "page": 118,
                "procedure_id": "P-CP300-42",
                "procedure": {
                    "id": "P-CP300-42", "model": "CP-300", "error_code": "E42",
                    "title": "Pressure-sensor recalibration / replacement",
                    "safety_class": "PRESSURIZED",
                    "caution": ("Pressurized hot-water circuit. Recalibration "
                                "via the service menu is routine; any physical "
                                "sensor work is qualified-technician only."),
                    "citation": "BrewPoint CP-300 Service Manual v1.5, §7.1 (p. 118)",
                    "steps": [
                        "Power-cycle the machine. If E42 clears, monitor for 24h.",
                        "If E42 returns, a qualified technician recalibrates the "
                        "sensor via the service menu, or replaces sensor PS-3300.",
                    ],
                    "symptoms": ["display shows E42",
                                 "pressure reading drifts during heat-up"],
                    "part": "PS-3300",
                },
            },
        }, kb)
        print()
        print("Same question, asked again after the update:")
        proc2 = search_internal_manual("CP-300", "E42", kb)
        decide("E42 now resolves INTERNALLY with citation: %s. "
               "The loop is closed -- the next store with E42 gets an instant, "
               "cited answer." % proc2["citation"])
    return 8


# ---------------------------------------------------------------------------
# SCENARIO C -- CP-200 + E31. The repair requires a qualified technician.
# The agent STOPS self-service, explains why, retrieves part info, checks
# inventory, creates a structured ticket, and tracks it until resolved.
# The part is ordered ONLY after the failure is verified on-site.
# ---------------------------------------------------------------------------

def scenario_c(kb):
    section("SCENARIO C -- store #2077: CP-200 shows Error E31 (heating element)")
    print("User: \"Machine won't heat, display says E31. Can you walk me")
    print("through fixing it?\" [photo attached: inconclusive, confidence 0.41]")
    print()
    think("Simulated-LLM deliberation: heating-element codes can mean 120V "
          "mains work. Internal manual first; then the safety gate decides "
          "whether I may guide -- the gate is deterministic and I cannot "
          "bypass it.")
    print()
    plan(1, "identify_equipment('CP-200')")
    plan(2, "search_internal_manual('CP-200','E31')")
    plan(3, "SafetyLayer.authorize for role='store_employee' -- the gate decides")
    plan(4, "STOP self-service if denied; explain why in plain language")
    plan(5, "retrieve_part_details + check_part_availability (info only -- no order yet)")
    plan(6, "create_maintenance_ticket with SUSPECTED (not confirmed) diagnosis")
    plan(7, "Track ticket -> technician confirms -> order part -> resolve -> verify")
    print()

    identify_equipment("CP-200", kb)
    proc = search_internal_manual("CP-200", "E31", kb)
    print()
    think("The manual HAS a procedure for E31 -- but its safety class is "
          "ELECTRICAL. I must ask the safety layer, not decide myself.")
    auth = safety_authorize(proc["id"], "store_employee", kb)
    safety("authorize('%s', role='store_employee') -> %s | class=%s"
           % (proc["id"], "ALLOWED" if auth["allowed"] else "DENIED",
              auth["safety_class"]))
    safety("reason: %s" % auth["reason"])
    # Demonstrate that the gate cannot be bypassed: a direct call without a
    # token is refused by the tool itself, not by the orchestrator's goodwill.
    try:
        safety_execute(proc["id"], "store_employee", None, kb)
    except PermissionError as e:
        safety("bypass attempt (direct call, no token) -> PermissionError: gate holds.")
    print()
    decide("STOPPING self-service. Why, in plain language: E31 means the "
           "heating element's resistance is out of range, and reaching it "
           "means opening a chassis with 120V mains inside. That is a shock "
           "hazard and would void the warranty. This is a job for a qualified "
           "technician -- my job now is to get you one, fast.")
    obs("Diagnosis status: SUSPECTED heating-element failure (error code "
        "reports it; the attached photo at 0.41 confidence proves nothing). "
        "FixMate always distinguishes CONFIRMED vs SUSPECTED failures.")
    print()
    part = retrieve_part_details(proc["part"], kb)
    decide("Part info retrieved for the ticket -- but NOT ordered yet. Policy: "
           "the part is ordered only after the failure is sufficiently "
           "verified on-site.")
    ticket = create_maintenance_ticket(
        "#2077", "CP-200", "E31",
        "heating element resistance out of range (manual §5.2)",
        "SUSPECTED", "ELECTRICAL", proc["part"], "availability checked at order time",
        "store_employee")
    print()
    print("--- Ticket lifecycle (simulated dispatch board) ---")
    timeline = [
        ("OPEN", "ticket created by store_employee; diagnosis SUSPECTED"),
        ("TECHNICIAN_DISPATCHED", "qualified tech assigned, ETA 2h"),
        ("FAILURE_CONFIRMED",
         "technician on-site: heating element confirmed failed (was SUSPECTED, now CONFIRMED)"),
    ]
    for status, note in timeline:
        ticket["status"] = status
        print("  [%s] %s" % (status, note))
    qty = check_part_availability(proc["part"], kb)
    ticket["part_availability"] = ("%d in stock" % qty if qty
                                   else "OUT OF STOCK")
    if qty:
        print("  [PART_ORDERED] HE-2200 ordered from regional depot -- only now, "
              "after on-site verification.")
        ticket["status"] = "PART_ORDERED"
        print("  [INSTALLED] technician replaced the heating element; machine heats; E31 cleared.")
        ticket["status"] = "RESOLVED"
        verify_resolution(ticket["ticket_id"],
                          "E31 cleared; heat-up test passed (technician sign-off)")
        decide("SCENARIO C complete: unsafe self-service refused, structured "
               "ticket created with a SUSPECTED->CONFIRMED trail, part ordered "
               "only after verification, resolution verified.")
    else:
        # T5/safety: zero inventory -- the part dependency stays unresolved.
        # Never claim the part is ordered or the repair is complete.
        print("  [PART_UNAVAILABLE] part is OUT OF STOCK -- flagged on the ticket; "
              "manager notified to order it and reschedule the dispatch.")
        ticket["status"] = "AWAITING_PART"
        decide("SCENARIO C complete: unsafe self-service refused, structured "
               "ticket created with a SUSPECTED->CONFIRMED trail. Repair NOT "
               "complete -- unresolved dependency: part out of stock.")
    return 9

# ---------------------------------------------------------------------------
# EVALUATION -- FixMate vs naive manual document search, on a fixed test set.
# Both systems run as real code over the same synthetic manuals. Metrics:
# internal-doc accuracy, citation accuracy, correct escalation rate,
# first-contact resolution, time to diagnosis (orchestrator steps, a
# deterministic offline proxy), knowledge-gap detection, ticket completeness.
# ---------------------------------------------------------------------------

TEST_SET = [
    # id, model, query, role, ground-truth procedure, ground-truth outcome
    {"id": "T1", "model": "CP-200", "query": "E17", "role": "store_employee",
     "gt_proc": "P-CP200-17", "gt_outcome": "guided"},
    {"id": "T2", "model": "CP-100", "query": "E10", "role": "store_employee",
     "gt_proc": "P-CP100-10", "gt_outcome": "guided"},
    {"id": "T3", "model": "CP-300", "query": "E05", "role": "store_employee",
     "gt_proc": "P-CP300-05", "gt_outcome": "guided"},
    {"id": "T4", "model": "CP-200", "query": "E23", "role": "store_employee",
     "gt_proc": "P-CP200-23", "gt_outcome": "guided"},
    {"id": "T5", "model": "CP-100", "query": "E11", "role": "store_employee",
     "gt_proc": "P-CP100-11", "gt_outcome": "guided"},
    {"id": "T6", "model": "CP-300", "query": "E12", "role": "store_employee",
     "gt_proc": "P-CP300-12", "gt_outcome": "guided"},
    {"id": "T7", "model": "CP-200", "query": "E31", "role": "store_employee",
     "gt_proc": "P-CP200-31", "gt_outcome": "ticket"},
    {"id": "T8", "model": "CP-100", "query": "E50", "role": "store_employee",
     "gt_proc": "P-CP100-50", "gt_outcome": "ticket"},
    {"id": "T9", "model": "CP-300", "query": "E42", "role": "store_employee",
     "gt_proc": None, "gt_outcome": "escalate"},
    {"id": "T10", "model": "CP-300", "query": "E99", "role": "store_employee",
     "gt_proc": None, "gt_outcome": "escalate"},
    {"id": "T11", "model": "CP-100", "query": "loud grinding noise",
     "role": "store_employee", "gt_proc": None, "gt_outcome": "escalate"},
    {"id": "T12", "model": "CP-200", "query": "E17", "role": "qualified_technician",
     "gt_proc": "P-CP200-17", "gt_outcome": "guided"},
    {"id": "T13", "model": "CP-100", "query": "E14", "role": "store_employee",
     "gt_proc": "P-CP100-14", "gt_outcome": "guided"},
    {"id": "T14", "model": "CP-100", "query": "E20", "role": "store_employee",
     "gt_proc": "P-CP100-20", "gt_outcome": "ticket"},
    {"id": "T15", "model": "CP-200", "query": "E28", "role": "store_employee",
     "gt_proc": "P-CP200-28", "gt_outcome": "guided"},
    {"id": "T16", "model": "CP-200", "query": "E35", "role": "store_employee",
     "gt_proc": "P-CP200-35", "gt_outcome": "guided"},
    {"id": "T17", "model": "CP-300", "query": "E18", "role": "store_employee",
     "gt_proc": "P-CP300-18", "gt_outcome": "guided"},
    {"id": "T18", "model": "CP-300", "query": "E25", "role": "store_employee",
     "gt_proc": "P-CP300-25", "gt_outcome": "guided"},
    {"id": "T19", "model": "CP-200", "query": "e28", "role": "store_employee",
     "gt_proc": "P-CP200-28", "gt_outcome": "guided"},
    {"id": "T20", "model": "CP-999", "query": "E17", "role": "store_employee",
     "gt_proc": None, "gt_outcome": "escalate"},
]


def fixmate_policy(case, kb):
    """The FixMate agent policy, run quietly for evaluation. Returns a
    result dict plus the orchestrator step count."""
    steps = 0
    model, query, role = case["model"], case["query"], case["role"]
    steps += 1  # identify_equipment
    m = kb["manuals"].get(model)
    if m is None:
        return ({"outcome": "escalate", "proc": None, "citation": None,
                 "gap_logged": True, "ticket_fields_ok": None}, steps)
    steps += 1  # search_internal_manual
    q = query.strip().upper()
    proc = None
    if q in m["error_codes"]:
        proc = kb["procedures"][m["error_codes"][q]["procedure_id"]]
    else:
        ql = query.strip().lower()
        for code in sorted(m["error_codes"]):
            p = kb["procedures"][m["error_codes"][code]["procedure_id"]]
            if any(ql in s for s in p["symptoms"]) or ql in p["title"].lower():
                proc = p
                break
    if proc is not None:
        steps += 1  # check_document_version
        newer = kb["manuals"][model].get("superseded_by")
        if newer:
            # T4/safety: the indexed manual is SUPERSEDED -- never trust the
            # old procedure as current. Escalate and log a version gap
            # instead of guiding from the stale manual.
            steps += 1  # escalate (version gap)
            steps += 1  # log_knowledge_gap
            return ({"outcome": "escalate", "proc": None, "citation": None,
                     "gap_logged": True, "ticket_fields_ok": None,
                     "version_gap": newer}, steps)
        steps += 1  # safety_authorize
        auth = safety_authorize(proc["id"], role, kb)
        if auth["allowed"]:
            steps += 2  # guide + record resolution
            return ({"outcome": "guided", "proc": proc["id"],
                     "citation": proc["citation"], "gap_logged": False,
                     "ticket_fields_ok": None}, steps)
        steps += 1  # create_maintenance_ticket
        # T5/safety: record the OBSERVED part availability on the ticket --
        # never a placeholder. A zero-stock dependency stays unresolved on
        # the ticket and changes the next step; the repair is never marked
        # complete on a part that isn't there.
        qty = kb["inventory"].get(proc["part"], 0)
        availability = "%d in stock" % qty if qty else "OUT OF STOCK"
        next_step = ("Dispatch qualified technician for on-site confirmation"
                     if qty else
                     "Part OUT OF STOCK -- notify manager, order replacement "
                     "part, and reschedule dispatch")
        t = {"ticket_id": "FM-2026-0000", "store_id": "#0000",
             "model": model, "error_code": q, "diagnosis": proc["title"],
             "diagnosis_status": "SUSPECTED", "safety_class": proc["safety_class"],
             "part_number": proc["part"], "part_availability": availability,
             "status": "OPEN", "created_by_role": role,
             "next_step": next_step}
        fields_ok = all(f in t and t[f] for f in TICKET_FIELDS)
        steps += 1  # track to resolution
        return ({"outcome": "ticket", "proc": proc["id"],
                 "citation": proc["citation"], "gap_logged": False,
                 "ticket_fields_ok": fields_ok}, steps)
    # No internal hit: prove the search conclusive, then go external.
    steps += 1  # prove_search_conclusive
    steps += 1  # search_approved_external_sources
    external = [s for s in kb["external_sources"]
                if s["matches_query"].lower() == ("%s %s" % (model, query)).lower()]
    steps += 1  # escalate (external guidance is never auto-applied)
    steps += 1  # log_knowledge_gap
    return ({"outcome": "escalate", "proc": None, "citation": None,
             "gap_logged": True, "ticket_fields_ok": None,
             "external_hits": len(external)}, steps)


def baseline_search(case, kb):
    """NAIVE BASELINE: keyword search over ALL indexed text, including
    superseded manuals and quick-start cards (oldest first). Returns the
    first text match with NO citation, NO safety gate, NO escalation,
    NO gap logging, NO tickets. One step, always."""
    tokens = (case["query"].lower() + " " + case["model"].lower()).split()
    docs = []
    # Superseded/secondary docs are indexed FIRST -- the trap.
    for d in kb["superseded_docs"]:
        docs.append({"model": d["model"], "proc": None,
                     "text": d["text"], "citation": None})
    for model in sorted(kb["manuals"]):
        m = kb["manuals"][model]
        for code in sorted(m["error_codes"]):
            p = kb["procedures"][m["error_codes"][code]["procedure_id"]]
            docs.append({"model": model, "proc": p["id"],
                         "text": (code + " " + p["title"] + " "
                                  + " ".join(p["symptoms"]) + " "
                                  + " ".join(p["steps"])),
                         "citation": None})
    best, best_score = None, 0
    for d in docs:
        score = sum(1 for t in tokens if t in d["text"].lower())
        if score > best_score:
            best, best_score = d, score
    if best is None:
        return ({"outcome": "no_answer", "proc": None, "citation": None,
                 "gap_logged": False, "ticket_fields_ok": None,
                 "unsafe_guided": False}, 1)
    # The baseline "guides" whatever it found -- even ELECTRICAL procedures.
    unsafe = (best["proc"] is not None
              and kb["procedures"][best["proc"]]["safety_class"]
              in ("ELECTRICAL", "PRESSURIZED"))
    return ({"outcome": "guided", "proc": best["proc"], "citation": None,
             "gap_logged": False, "ticket_fields_ok": None,
             "unsafe_guided": unsafe}, 1)


def evaluate():
    section("EVALUATION -- FixMate vs naive manual document search (fixed test set)")
    print("%d fixed cases. Both systems run as real code over the same"
          % len(TEST_SET))
    print("synthetic manuals. Metrics computed by the harness, not hand-written.")
    print()
    kb = build_kb()  # pristine copy -- scenario B's scripted update is excluded
    fix, base = [], []
    for case in TEST_SET:
        r, s = fixmate_policy(case, kb)
        r["steps"] = s
        fix.append(r)
        r2, s2 = baseline_search(case, kb)
        r2["steps"] = s2
        base.append(r2)

    def pct(n, d):
        return 100.0 * n / d if d else 0.0

    rows = []
    # 1. internal-doc accuracy (cases with a ground-truth doc)
    doc_cases = [i for i, c in enumerate(TEST_SET) if c["gt_proc"]]
    f = sum(1 for i in doc_cases if fix[i]["proc"] == TEST_SET[i]["gt_proc"])
    b = sum(1 for i in doc_cases if base[i]["proc"] == TEST_SET[i]["gt_proc"])
    rows.append(("Internal-doc accuracy", pct(f, len(doc_cases)),
                 pct(b, len(doc_cases)),
                 "%d/%d vs %d/%d cases picked the right document"
                 % (f, len(doc_cases), b, len(doc_cases))))
    # 2. citation accuracy (exact versioned citation)
    f = sum(1 for i in doc_cases
            if fix[i]["citation"] == kb["procedures"][TEST_SET[i]["gt_proc"]]["citation"])
    b = sum(1 for i in doc_cases if base[i]["citation"] is not None)
    rows.append(("Citation accuracy", pct(f, len(doc_cases)),
                 pct(b, len(doc_cases)),
                 "FixMate cites §+version every time; baseline prints raw text"))
    # 3. correct escalation rate (ticket/escalate ground truth)
    esc_cases = [i for i, c in enumerate(TEST_SET)
                 if c["gt_outcome"] in ("ticket", "escalate")]
    f = sum(1 for i in esc_cases
            if fix[i]["outcome"] in ("ticket", "escalate"))
    b = sum(1 for i in esc_cases
            if base[i]["outcome"] in ("ticket", "escalate"))
    rows.append(("Correct escalation rate", pct(f, len(esc_cases)),
                 pct(b, len(esc_cases)),
                 "FixMate escalates unsafe/unknown cases; baseline never does"))
    # 4. first-contact resolution (guided ground truth, correct + safe)
    guided_cases = [i for i, c in enumerate(TEST_SET)
                    if c["gt_outcome"] == "guided"]
    f = sum(1 for i in guided_cases
            if fix[i]["outcome"] == "guided"
            and fix[i]["proc"] == TEST_SET[i]["gt_proc"])
    b = sum(1 for i in guided_cases
            if base[i]["outcome"] == "guided"
            and base[i]["proc"] == TEST_SET[i]["gt_proc"]
            and not base[i]["unsafe_guided"])
    rows.append(("First-contact resolution", pct(f, len(guided_cases)),
                 pct(b, len(guided_cases)),
                 "correct AND safe resolution without escalation"))
    # 5. time to diagnosis (avg orchestrator steps -- deterministic offline proxy)
    f_steps = sum(r["steps"] for r in fix) / len(fix)
    b_steps = sum(r["steps"] for r in base) / len(base)
    rows.append(("Time to diagnosis (avg steps)", f_steps, b_steps,
                 "offline proxy; FixMate spends steps on safety + verification"))
    # 6. knowledge-gap detection (no ground-truth doc)
    gap_cases = [i for i, c in enumerate(TEST_SET) if c["gt_proc"] is None]
    f = sum(1 for i in gap_cases if fix[i]["gap_logged"])
    b = sum(1 for i in gap_cases if base[i]["gap_logged"])
    rows.append(("Knowledge-gap detection", pct(f, len(gap_cases)),
                 pct(b, len(gap_cases)),
                 "FixMate logs every unanswered question for the docs team"))
    # 7. ticket completeness (required fields present)
    f_tix = [r for r in fix if r["ticket_fields_ok"] is not None]
    f = sum(1 for r in f_tix if r["ticket_fields_ok"])
    rows.append(("Ticket completeness", pct(f, len(f_tix)) if f_tix else 0.0,
                 0.0, "FixMate tickets carry all %d required fields; "
                 "baseline creates no tickets" % len(TICKET_FIELDS)))

    print("%-34s %12s %12s" % ("Metric", "FixMate", "Baseline"))
    print(THIN)
    for name, fv, bv, note in rows:
        if "steps" in name:
            print("%-34s %11.1f  %11.1f" % (name, fv, bv))
        else:
            print("%-34s %11.1f%% %11.1f%%" % (name, fv, bv))
        print("%-34s   %s" % ("", note))
    print()
    print("Reading the table honestly: the baseline is FASTER (1 step vs %.1f)"
          % f_steps)
    print("but its answers are less accurate, never cited, never safety-gated")
    print("(it would have walked a store employee through a 120V repair), and")
    print("it learns nothing from failure. FixMate trades steps for safety,")
    print("citations, escalation, and the knowledge-gap loop.")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print(DIV)
    print("FixMate AI -- The Intelligent Equipment Maintenance Agent")
    print("Diagnose faster. Fix smarter. Keep every store running.")
    print(DIV)
    print("Fictional demo for BrewPoint Retail (a fictional convenience-store")
    print("chain). All equipment, manuals, error codes, and people are synthetic.")
    print("One orchestrating agent + 8 tools + a deterministic safety layer")
    print("the reasoning policy cannot bypass.")
    print()
    print("CORE PRINCIPLE: internal documents FIRST, web SECOND.")
    print("  internal search -> answer supported? -> YES: validate + guide.")
    print("  NO -> prove the search was conclusive -> approved external sources")
    print("  -> label EXTERNAL, never as approved procedure -> escalate if unsure.")
    print("  NEVER invent a maintenance procedure to fill a documentation gap.")
    print()
    print("TOOLS: identify_equipment | search_internal_manual |")
    print("       check_document_version | retrieve_part_details |")
    print("       search_approved_external_sources | create_maintenance_ticket |")
    print("       check_part_availability | verify_resolution")
    print("       (+ vision_describe via a pluggable, SIMULATED vision interface)")

    scenario_a(KB)
    scenario_b(KB)
    scenario_c(KB)
    evaluate()

    section("DEMO COMPLETE")
    print("Three scenarios, one loop, one principle:")
    print("  A. CP-200/E17  -> answered from the manual, cited, resolved.")
    print("  B. CP-300/E42  -> proven gap -> external (labeled) -> escalated ->")
    print("                    logged -> expert update v1.5 -> answered internally.")
    print("  C. CP-200/E31  -> safety gate DENIED self-service -> ticket with a")
    print("                    SUSPECTED->CONFIRMED trail -> part ordered only")
    print("                    after verification -> resolution verified.")
    print()
    print("Run again any time:  python3 demo.py")
    print("(stdlib only, fully offline, byte-identical output every run)")


if __name__ == "__main__":
    main()

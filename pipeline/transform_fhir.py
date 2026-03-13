"""
ClinicalMind AI — FHIR R4 → Schema Transformer

Maps FHIR Bundle resources (from generate_fhir.py or real Synthea output)
to the canonical patient dicts expected by seed.py.

Two extraction strategies, tried in order:
  1. _meta shortcut  — populated by generate_fhir.py (fast path)
  2. FHIR resource parsing — works with real Synthea / any FHIR source

LOINC / coding systems used:
  PHQ-9 total:  44261-6    GAD-7 total: 70274-6
  WHODAS total: 81678-5    SSRS:        http://columbia-suicide-severity.org/fhir/CodeSystem
  KPI:          http://clinicalmind.ai/fhir/kpi
  Crisis:       http://clinicalmind.ai/fhir/crisis
"""
from __future__ import annotations



import json
from datetime import datetime

# ── LOINC & coding constants ──────────────────────────────────────────────────

PHQ9_TOTAL_LOINC  = "44261-6"
GAD7_TOTAL_LOINC  = "70274-6"
WHODAS_TOTAL_LOINC = "81678-5"

PHQ9_ITEM_LOINCS = {
    "44250-9", "44255-8", "44259-0", "44254-1",
    "44251-7", "44258-2", "44252-5", "44253-3", "44260-8",
}

GAD7_ITEM_LOINCS = {
    "69725-0", "68509-9", "69733-4", "69734-2",
    "69735-9", "69736-7", "69737-5",
}

SSRS_SYSTEM  = "http://columbia-suicide-severity.org/fhir/CodeSystem"
KPI_SYSTEM   = "http://clinicalmind.ai/fhir/kpi"
CRISIS_SYS   = "http://clinicalmind.ai/fhir/crisis"

KPI_NAMES    = ["bha", "sra", "aims", "whodas", "phq9", "beh_tp", "beh_csp"]
KPI_TARGET   = 75


# ── Helpers ───────────────────────────────────────────────────────────────────

def _coding_matches(resource: dict, system: str | None, code: str) -> bool:
    for c in resource.get("code", {}).get("coding", []):
        if (system is None or c.get("system") == system) and c.get("code") == code:
            return True
    return False


def _ext_value(extensions: list[dict], url_fragment: str):
    """Extract value from the first extension whose URL ends with url_fragment."""
    for ext in extensions:
        if ext.get("url", "").endswith(url_fragment):
            for vkey in ("valueBoolean", "valueInteger", "valueString",
                         "valueCode", "valueDate"):
                if vkey in ext:
                    return ext[vkey]
    return None


def _get_component_value(obs: dict, code: str):
    for comp in obs.get("component", []):
        if any(c.get("code") == code for c in comp.get("code", {}).get("coding", [])):
            for vkey in ("valueString", "valueBoolean", "valueInteger"):
                if vkey in comp:
                    return comp[vkey]
    return None


def _int_value(obs: dict) -> int:
    return int(obs.get("valueInteger") or obs.get("valueQuantity", {}).get("value") or 0)


def _phq9_severity(total: int, si: bool) -> str:
    if total >= 15 or si:
        return "High"
    if total >= 10:
        return "Moderately Severe"
    if total >= 5:
        return "Moderate"
    return "Minimal"


def _gad7_severity(total: int) -> str:
    if total >= 15:
        return "High"
    if total >= 10:
        return "Moderate"
    if total >= 5:
        return "Mild"
    return "Minimal"


def _kpi_compliance_pct(kpi: dict) -> int:
    completed = sum(1 for k in KPI_NAMES if not kpi.get(k, {}).get("overdue", True))
    return round(completed / len(KPI_NAMES) * 100)


# ── FHIR resource parser (used when _meta is absent) ─────────────────────────

def _parse_fhir(bundle: dict) -> dict:
    """
    Parse a real FHIR R4 Bundle into our canonical patient dict.
    This path is used when _meta is absent (e.g. actual Synthea output).
    """
    entries = [e["resource"] for e in bundle.get("entry", [])]

    by_type: dict[str, list] = {}
    for r in entries:
        rt = r.get("resourceType", "Unknown")
        by_type.setdefault(rt, []).append(r)

    # Patient ──────────────────────────────────────────────────────────────────
    pat = by_type.get("Patient", [{}])[0]
    pid = pat.get("id", bundle.get("id", "UNKNOWN"))

    name_obj = pat.get("name", [{}])[0]
    full_name = " ".join(name_obj.get("given", [])) + " " + name_obj.get("family", "")
    dob       = pat.get("birthDate", "")
    county    = pat.get("address", [{}])[0].get("district", "")

    exts      = pat.get("extension", [])
    svc       = _ext_value(exts, "serviceType")   or "ACT"
    prov_id   = _ext_value(exts, "providerId")    or ""
    risk      = _ext_value(exts, "riskLevel")     or "Low"
    engaged   = _ext_value(exts, "engagementFlag")
    kpi_pct   = _ext_value(exts, "kpiCompliance") or 0

    # Practitioner ─────────────────────────────────────────────────────────────
    prac = next(
        (p for p in by_type.get("Practitioner", []) if p.get("id") == prov_id),
        {},
    )
    prov_name = prac.get("name", [{}])[0].get("text", prov_id)
    prov_team = _ext_value(prac.get("extension", []), "team") or ""

    # Condition ────────────────────────────────────────────────────────────────
    cond   = by_type.get("Condition", [{}])[0]
    dx_txt = cond.get("code", {}).get("text", "Unknown")

    # Observations (keyed by LOINC / system code) ──────────────────────────────
    obs_all = by_type.get("Observation", [])

    def _find_obs(system: str | None, code: str) -> dict | None:
        return next((o for o in obs_all if _coding_matches(o, system, code)), None)

    def _find_obs_all(system: str | None, code: str) -> list[dict]:
        return [o for o in obs_all if _coding_matches(o, system, code)]

    # PHQ-9
    phq9_obs = _find_obs(None, PHQ9_TOTAL_LOINC)
    if phq9_obs:
        phq9_total    = _int_value(phq9_obs)
        phq9_si       = bool(_get_component_value(phq9_obs, "suicidal-ideation") or False)
        phq9_sev      = _get_component_value(phq9_obs, "severity") or _phq9_severity(phq9_total, phq9_si)
        phq9_date     = phq9_obs.get("effectiveDateTime", "")[:10]
        # Gather item scores in LOINC order
        phq9_item_obs = [_find_obs(None, lc) for lc, _ in [
            ("44250-9", ""), ("44255-8", ""), ("44259-0", ""), ("44254-1", ""),
            ("44251-7", ""), ("44258-2", ""), ("44252-5", ""), ("44253-3", ""), ("44260-8", ""),
        ]]
        phq9_items = [_int_value(o) if o else 0 for o in phq9_item_obs]
    else:
        phq9_total, phq9_items, phq9_si, phq9_sev, phq9_date = 0, [0]*9, False, "Minimal", ""

    # GAD-7
    gad7_obs = _find_obs(None, GAD7_TOTAL_LOINC)
    if gad7_obs:
        gad7_total = _int_value(gad7_obs)
        gad7_sev   = _get_component_value(gad7_obs, "severity") or _gad7_severity(gad7_total)
        gad7_date  = gad7_obs.get("effectiveDateTime", "")[:10]
        gad7_item_obs = [_find_obs(None, lc) for lc, _ in [
            ("69725-0", ""), ("68509-9", ""), ("69733-4", ""), ("69734-2", ""),
            ("69735-9", ""), ("69736-7", ""), ("69737-5", ""),
        ]]
        gad7_items = [_int_value(o) if o else 0 for o in gad7_item_obs]
    else:
        gad7_total, gad7_items, gad7_sev, gad7_date = 0, [0]*7, "Minimal", ""

    # WHODAS
    whodas_obs = _find_obs(None, WHODAS_TOTAL_LOINC)
    if whodas_obs:
        whodas_total = _int_value(whodas_obs)
        whodas_dl    = _get_component_value(whodas_obs, "disability-level") or "Mild"
        whodas_date  = whodas_obs.get("effectiveDateTime", "")[:10]
    else:
        whodas_total, whodas_dl, whodas_date = 0, "Mild", ""

    # SSRS
    def _ssrs_bool(code: str) -> bool:
        o = _find_obs(SSRS_SYSTEM, code)
        return bool(o.get("valueBoolean", False)) if o else False

    def _ssrs_val(code: str, default):
        o = _find_obs(SSRS_SYSTEM, code)
        if o is None:
            return default
        return o.get("valueString") or o.get("valueInteger") or o.get("valueBoolean") or default

    ssrs_ideation  = _ssrs_bool("C-SSRS-I")
    ssrs_intent    = _ssrs_bool("C-SSRS-IN")
    ssrs_plan      = _ssrs_bool("C-SSRS-P")
    ssrs_method    = _ssrs_bool("C-SSRS-M")
    ssrs_history   = _ssrs_bool("C-SSRS-H")
    ssrs_intensity = int(_ssrs_val("C-SSRS-II", 0))
    ssrs_risk      = str(_ssrs_val("C-SSRS-RL", "Low"))
    ssrs_date_obs  = _find_obs(SSRS_SYSTEM, "C-SSRS-RL")
    ssrs_date      = ssrs_date_obs.get("effectiveDateTime", "")[:10] if ssrs_date_obs else ""

    # KPI
    kpi: dict = {}
    for kname in KPI_NAMES:
        kpi_obs = _find_obs(KPI_SYSTEM, kname.upper())
        if kpi_obs:
            kpi_exts = kpi_obs.get("extension", [])
            kpi[kname] = {
                "last_completed": kpi_obs.get("effectiveDateTime", "")[:10],
                "due_date":       _ext_value(kpi_exts, "dueDate") or "",
                "overdue":        bool(_ext_value(kpi_exts, "overdue") or False),
            }
        else:
            kpi[kname] = {"last_completed": None, "due_date": None, "overdue": True}

    computed_kpi_pct = _kpi_compliance_pct(kpi)

    # Crisis events
    crisis_obs = _find_obs_all(CRISIS_SYS, "CRISIS-EVENT")
    crisis_events = []
    for co in crisis_obs:
        cexts = co.get("extension", [])
        crisis_events.append({
            "event_id":       _ext_value(cexts, "eventId") or co["id"],
            "crisis_date":    co.get("effectiveDateTime", "")[:10],
            "crisis_type":    co.get("valueString", "Unknown"),
            "within_7_days":  bool(_ext_value(cexts, "within7Days") or False),
            "within_28_days": bool(_ext_value(cexts, "within28Days") or False),
            "days_since":     int(_ext_value(cexts, "daysSince") or 0),
        })

    # Encounters & contacts
    enc_all = by_type.get("Encounter", [])
    treatment_enc = [e for e in enc_all if e["id"].startswith("ENC")]
    contact_enc   = [e for e in enc_all if e["id"].startswith("CON")]

    encounters = []
    for e in treatment_enc:
        enc_exts = e.get("extension", [])
        encounters.append({
            "encounter_id":   e["id"],
            "admit_date":     e.get("period", {}).get("start", ""),
            "discharge_date": e.get("period", {}).get("end"),
            "encounter_type": e.get("type", [{}])[0].get("text", "")
        })

    contacts = []
    for c in sorted(contact_enc, key=lambda x: x.get("period", {}).get("start", ""), reverse=True):
        cexts = c.get("extension", [])
        contacts.append({
            "contact_id":   c["id"],
            "contact_date": c.get("period", {}).get("start", ""),
            "contact_type": c.get("type", [{}])[0].get("text", "F2F"),
            "provider_id":  (c.get("participant", [{}])[0]
                              .get("individual", {})
                              .get("reference", "").replace("Practitioner/", "")),
            "days_since":   int(_ext_value(cexts, "daysSinceContact") or 0),
        })

    last_contact = contacts[0] if contacts else {}
    contact_ago  = int(last_contact.get("days_since", 0))
    contact_date = last_contact.get("contact_date", "")

    return {
        "patient_id":              pid,
        "name":                    full_name.strip(),
        "date_of_birth":           dob,
        "diagnosis":               dx_txt,
        "county":                  county,
        "service_type":            svc,
        "provider_id":             prov_id,
        "provider_name":           prov_name,
        "team":                    prov_team,
        "risk_level":              risk,
        "days_since_last_contact": contact_ago,
        "last_contact_date":       contact_date,
        "engagement_flag":         bool(engaged) if engaged is not None else contact_ago > 30,
        "kpi_compliance_pct":      int(kpi_pct or computed_kpi_pct),
        "has_crisis_7d":           any(c["within_7_days"] for c in crisis_events),
        "has_crisis_28d":          any(c["within_28_days"] for c in crisis_events),
        "phq9": {
            "assessment_date":   phq9_date,
            "total_score":       phq9_total,
            "item_scores":       phq9_items,
            "suicidal_ideation": phq9_si,
            "severity":          phq9_sev,
        },
        "gad7": {
            "assessment_date": gad7_date,
            "total_score":     gad7_total,
            "item_scores":     gad7_items,
            "severity":        gad7_sev,
        },
        "whodas": {
            "assessment_date": whodas_date,
            "total_score":     whodas_total,
            "disability_level": whodas_dl,
        },
        "ssrs": {
            "assessment_date":    ssrs_date,
            "suicidal_ideation":  ssrs_ideation,
            "ideation_intensity": ssrs_intensity,
            "intent":             ssrs_intent,
            "plan":               ssrs_plan,
            "method":             ssrs_method,
            "history_attempt":    ssrs_history,
            "risk_level":         ssrs_risk,
        },
        "kpi":           kpi,
        "crisis_events": crisis_events,
        "encounters":    encounters,
        "contacts":      contacts,
    }


# ── Public API ────────────────────────────────────────────────────────────────

def transform_bundles(bundles: list[dict]) -> list[dict]:
    """
    Transform a list of FHIR R4 Bundles into canonical patient dicts.

    Uses _meta fast-path when available (generated by generate_fhir.py).
    Falls back to full FHIR resource parsing for real Synthea / external data.

    Returns:
        List of patient dicts matching the mock_adapter / sql_adapter interface.
    """
    patients = []
    for bundle in bundles:
        meta = bundle.get("_meta")
        if meta:
            # Fast path: _meta already contains all extracted fields
            patients.append(meta)
        else:
            # Full FHIR parse (real Synthea output or external source)
            patients.append(_parse_fhir(bundle))
    return patients


def transform_from_file(path: str) -> list[dict]:
    """Load FHIR bundles from a JSON file and transform them."""
    with open(path) as f:
        bundles = json.load(f)
    if isinstance(bundles, dict):
        bundles = [bundles]
    return transform_bundles(bundles)

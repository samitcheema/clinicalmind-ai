"""
ClinicalMind AI — Synthetic FHIR R4 Generator

Produces realistic behavioral-health patient bundles using:
  - Proper LOINC codes for all clinical observations
  - ICD-10-CM diagnosis codes
  - Clinically-grounded score distributions (SAMHSA/NIMH SMI population norms)
  - Realistic temporal patterns for encounters, contacts, KPI intervals

This is a pure-Python alternative to running Synthea (no Java required).
It generates the same FHIR R4 Bundle format Synthea produces, making it
drop-in compatible with any FHIR-aware ETL.

Each bundle contains:
  Patient · Practitioner · Condition · Encounter (treatment + contacts)
  Observation (PHQ-9 items + total · GAD-7 items + total · WHODAS · SSRS · KPI)
  Observation (crisis events)

Usage:
    python generate_fhir.py          # writes fhir_output.json (60 patients)
    python generate_fhir.py 100      # 100 patients
"""

import json
import os
import random
import uuid
from datetime import date, timedelta

from faker import Faker

# ── Reference date ────────────────────────────────────────────────────────────
TODAY = date(2026, 3, 12)

# ── LOINC codes ───────────────────────────────────────────────────────────────

# PHQ-9 (Patient Health Questionnaire-9)
PHQ9_ITEMS = [
    ("44250-9", "Little interest or pleasure"),
    ("44255-8", "Feeling down or depressed"),
    ("44259-0", "Sleep problems"),
    ("44254-1", "Tired or little energy"),
    ("44251-7", "Poor appetite or overeating"),
    ("44258-2", "Feeling bad about yourself"),
    ("44252-5", "Trouble concentrating"),
    ("44253-3", "Moving slowly or fidgety"),
    ("44260-8", "Thoughts of self-harm"),     # suicidal ideation item
]
PHQ9_TOTAL_LOINC = ("44261-6", "PHQ-9 Total Score")

# GAD-7 (Generalized Anxiety Disorder-7)
GAD7_ITEMS = [
    ("69725-0", "Feeling nervous or anxious"),
    ("68509-9", "Not able to stop worrying"),
    ("69733-4", "Worrying too much"),
    ("69734-2", "Trouble relaxing"),
    ("69735-9", "Being so restless"),
    ("69736-7", "Becoming easily annoyed"),
    ("69737-5", "Feeling afraid"),
]
GAD7_TOTAL_LOINC = ("70274-6", "GAD-7 Total Score")

# WHODAS 2.0
WHODAS_TOTAL_LOINC = ("81678-5", "WHODAS 2.0 Total Score")

# Columbia Suicide Severity Rating Scale (C-SSRS) — facility-defined codes
SSRS_SYSTEM = "http://columbia-suicide-severity.org/fhir/CodeSystem"
SSRS_CODES = {
    "ideation":           "C-SSRS-I",
    "intent":             "C-SSRS-IN",
    "plan":               "C-SSRS-P",
    "method":             "C-SSRS-M",
    "history_attempt":    "C-SSRS-H",
    "ideation_intensity": "C-SSRS-II",
    "risk_level":         "C-SSRS-RL",
}

# KPI codes — facility-defined
KPI_SYSTEM = "http://clinicalmind.ai/fhir/kpi"
KPI_NAMES  = ["bha", "sra", "aims", "whodas", "phq9", "beh_tp", "beh_csp"]

# ── Clinical reference data ───────────────────────────────────────────────────

# Weighted ICD-10 diagnoses for a behavioral health ACT/CSP SMI caseload
DIAGNOSES = [
    ("Major Depressive Disorder, Recurrent", "F33.1",  0.20),
    ("Schizophrenia",                         "F20.9",  0.20),
    ("Bipolar I Disorder",                    "F31.1",  0.15),
    ("Schizoaffective Disorder",              "F25.0",  0.12),
    ("PTSD",                                  "F43.10", 0.10),
    ("Major Depressive Disorder",             "F32.1",  0.10),
    ("Generalized Anxiety Disorder",          "F41.1",  0.07),
    ("Borderline Personality Disorder",       "F60.3",  0.06),
]

COUNTIES = ["Westchester", "Rockland", "Orange", "Dutchess", "Putnam"]

PROVIDERS = [
    {"id": "PROV001", "name": "Dr. Emma Chen",       "team": "ACT-1"},
    {"id": "PROV002", "name": "Dr. Marcus Williams", "team": "ACT-1"},
    {"id": "PROV003", "name": "Dr. Priya Sharma",    "team": "ACT-2"},
    {"id": "PROV004", "name": "Dr. James O'Brien",   "team": "ACT-2"},
    {"id": "PROV005", "name": "Dr. Sarah Nakamura",  "team": "CSP-1"},
    {"id": "PROV006", "name": "Dr. Robert Kim",      "team": "CSP-1"},
]

CRISIS_TYPES = [
    "Psychiatric Emergency",
    "Suicidal Crisis — Passive Ideation",
    "Suicidal Crisis — Active Ideation",
    "Self-Harm Incident",
    "Aggressive Behavior",
]


# ── Score generation helpers ──────────────────────────────────────────────────

def _distribute_score(rng: random.Random, total: int, n: int, max_item: int = 3) -> list[int]:
    """Spread `total` points across `n` items (each 0–max_item), randomly."""
    items = [0] * n
    remaining = total
    order = list(range(n))
    rng.shuffle(order)
    for i in order:
        cap   = min(remaining, max_item)
        alloc = rng.randint(0, cap)
        items[i] = alloc
        remaining -= alloc
        if remaining == 0:
            break
    # Distribute any leftover to items that still have room
    for i in range(n):
        if remaining == 0:
            break
        room = max_item - items[i]
        if room > 0:
            add       = min(room, remaining)
            items[i] += add
            remaining -= add
    return items


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


def _gen_phq9(rng: random.Random, tier: str) -> tuple[int, list[int], bool]:
    """Return (total_score, item_scores, suicidal_ideation)."""
    if tier == "High":
        target = rng.randint(15, 27)
        si     = rng.random() < 0.65
    elif tier == "Moderate":
        target = rng.randint(10, 14)
        si     = rng.random() < 0.12
    else:
        target = rng.randint(0, 9)
        si     = False

    items = _distribute_score(rng, target, 9, 3)

    # Enforce SI flag on item 9
    if si and items[8] == 0:
        items[8] = rng.randint(1, 2)
        # Reduce another item to keep total stable
        for j in range(8):
            if items[j] >= items[8]:
                items[j] -= items[8]
                break

    return sum(items), items, si


def _gen_gad7(rng: random.Random, tier: str) -> tuple[int, list[int]]:
    if tier == "High":
        target = rng.randint(11, 21)
    elif tier == "Moderate":
        target = rng.randint(7, 14)
    else:
        target = rng.randint(0, 9)
    items = _distribute_score(rng, target, 7, 3)
    return sum(items), items


def _gen_ssrs(rng: random.Random, phq9_si: bool, tier: str) -> dict:
    """Generate C-SSRS flags correlated with PHQ-9 severity."""
    ideation = phq9_si or \
               (tier == "High"     and rng.random() < 0.70) or \
               (tier == "Moderate" and rng.random() < 0.35)

    if not ideation:
        return {
            "ideation": False, "intent": False, "plan": False,
            "method": False, "history_attempt": rng.random() < 0.15,
            "ideation_intensity": 0,
        }

    intent    = rng.random() < (0.55 if tier == "High" else 0.20)
    plan      = intent and rng.random() < 0.60
    method    = plan   and rng.random() < 0.70
    history   = rng.random() < (0.45 if tier == "High" else 0.22)
    intensity = rng.randint(2, 5) if intent else rng.randint(1, 3)

    return {
        "ideation": True, "intent": intent, "plan": plan,
        "method": method, "history_attempt": history,
        "ideation_intensity": intensity,
    }


def _ssrs_risk(ssrs: dict) -> str:
    if ssrs["plan"] or ssrs["method"]:
        return "High"
    if ssrs["ideation"]:
        return "Moderate"
    return "Low"


def _kpi_entry(rng: random.Random, last_days: int, interval: int) -> dict:
    last_completed = (TODAY - timedelta(days=last_days)).isoformat()
    due_date       = (TODAY - timedelta(days=last_days - interval)).isoformat()
    return {
        "last_completed": last_completed,
        "due_date":       due_date,
        "overdue":        last_days > interval,
    }


# ── FHIR resource factories ───────────────────────────────────────────────────

def _obs_loinc(pid: str, loinc: str, display: str,
               value_int: int | None, eff_date: str,
               components: list | None = None) -> dict:
    obs = {
        "resourceType":      "Observation",
        "id":                str(uuid.uuid4()),
        "status":            "final",
        "code":              {"coding": [{"system": "http://loinc.org", "code": loinc, "display": display}]},
        "subject":           {"reference": f"Patient/{pid}"},
        "effectiveDateTime": eff_date,
    }
    if value_int is not None:
        obs["valueInteger"] = value_int
    if components:
        obs["component"] = components
    return obs


def _obs_custom(pid: str, system: str, code: str,
                value, eff_date: str,
                extensions: list | None = None) -> dict:
    obs = {
        "resourceType":      "Observation",
        "id":                str(uuid.uuid4()),
        "status":            "final",
        "code":              {"coding": [{"system": system, "code": code}]},
        "subject":           {"reference": f"Patient/{pid}"},
        "effectiveDateTime": eff_date,
    }
    if isinstance(value, bool):
        obs["valueBoolean"] = value
    elif isinstance(value, int):
        obs["valueInteger"] = value
    elif isinstance(value, str):
        obs["valueString"] = value
    if extensions:
        obs["extension"] = extensions
    return obs


# ── Bundle builder ────────────────────────────────────────────────────────────

def _build_bundle(idx: int, rng: random.Random, fake: Faker) -> dict:
    pid      = f"PAT{idx:03d}"
    prov     = PROVIDERS[(idx - 1) % len(PROVIDERS)]
    svc      = "ACT" if rng.random() < 0.55 else "CSP"
    county   = rng.choice(COUNTIES)
    dx_name, dx_code, _ = rng.choices(
        [(d[0], d[1], d[2]) for d in DIAGNOSES],
        weights=[d[2] for d in DIAGNOSES],
    )[0]

    # Risk tier: 20% High / 40% Moderate / 40% Low
    roll = rng.random()
    tier = "High" if roll < 0.20 else ("Moderate" if roll < 0.60 else "Low")

    # Demographics
    gender     = rng.choice(["male", "female"])
    first_name = fake.first_name_male() if gender == "male" else fake.first_name_female()
    last_name  = fake.last_name()
    dob        = TODAY - timedelta(days=rng.randint(18 * 365, 65 * 365))

    # Dates
    admit_ago         = rng.randint(180, 900)
    admit_date        = (TODAY - timedelta(days=admit_ago)).isoformat()

    if tier == "High":
        contact_ago = rng.randint(1, 10)
    elif tier == "Moderate":
        contact_ago = rng.randint(1, 50)
    else:
        contact_ago = rng.randint(1, 65)

    assessment_ago  = contact_ago + rng.randint(5, 25)
    contact_date    = (TODAY - timedelta(days=contact_ago)).isoformat()
    assessment_date = (TODAY - timedelta(days=assessment_ago)).isoformat()

    # Clinical scores
    phq9_total, phq9_items, phq9_si = _gen_phq9(rng, tier)
    gad7_total, gad7_items          = _gen_gad7(rng, tier)
    ssrs                            = _gen_ssrs(rng, phq9_si, tier)
    ssrs_risk                       = _ssrs_risk(ssrs)
    whodas_total                    = phq9_total * 2 + gad7_total

    phq9_sev  = _phq9_severity(phq9_total, phq9_si)
    gad7_sev  = _gad7_severity(gad7_total)
    whodas_dl = "Severe" if phq9_total >= 15 else ("Moderate" if phq9_total >= 10 else "Mild")

    if phq9_sev == "High" or ssrs_risk == "High":
        risk_level = "High"
    elif phq9_sev in ("Moderately Severe",) or ssrs_risk == "Moderate":
        risk_level = "Moderate"
    else:
        risk_level = "Low"

    # KPI compliance — realistic base offsets by tier
    base = rng.randint(20, 55) if tier in ("High", "Moderate") else rng.randint(20, 110)
    kpi = {
        "bha":     _kpi_entry(rng, base + rng.randint(0, 35),  90),
        "sra":     _kpi_entry(rng, base + rng.randint(0, 55),  90),
        "aims":    _kpi_entry(rng, base + rng.randint(0, 45),  90),
        "whodas":  _kpi_entry(rng, base + rng.randint(0, 110), 365),
        "phq9":    _kpi_entry(rng, base + rng.randint(0, 35),  90),
        "beh_tp":  _kpi_entry(rng, base + rng.randint(0, 65),  90),
        "beh_csp": _kpi_entry(rng, base + rng.randint(20, 85), 90),
    }
    kpi_pct = round(sum(1 for k in kpi.values() if not k["overdue"]) / 7 * 100)

    # Crisis events
    crisis_events = []
    if tier == "High" and rng.random() < 0.70:
        days = rng.randint(1, 28)
        crisis_events.append({
            "event_id":       f"CR{pid}01",
            "crisis_date":    (TODAY - timedelta(days=days)).isoformat(),
            "crisis_type":    rng.choice(CRISIS_TYPES[1:4]),
            "within_7_days":  days <= 7,
            "within_28_days": days <= 28,
            "days_since":     days,
        })
        if rng.random() < 0.40:
            days2 = rng.randint(30, 90)
            crisis_events.append({
                "event_id":       f"CR{pid}02",
                "crisis_date":    (TODAY - timedelta(days=days2)).isoformat(),
                "crisis_type":    rng.choice(CRISIS_TYPES),
                "within_7_days":  False,
                "within_28_days": False,
                "days_since":     days2,
            })
    elif tier == "Moderate" and rng.random() < 0.25:
        days = rng.randint(15, 65)
        crisis_events.append({
            "event_id":       f"CR{pid}01",
            "crisis_date":    (TODAY - timedelta(days=days)).isoformat(),
            "crisis_type":    rng.choice(CRISIS_TYPES[:3]),
            "within_7_days":  days <= 7,
            "within_28_days": days <= 28,
            "days_since":     days,
        })

    # Contacts
    contact_type_code = "VR" if (idx % 3 == 0) else "AMB"
    contact_type_text = "Telehealth" if contact_type_code == "VR" else "F2F"
    contacts = [{
        "contact_id":   f"CON{pid}01",
        "contact_date": contact_date,
        "contact_type": contact_type_text,
        "provider_id":  prov["id"],
        "days_since":   contact_ago,
    }]
    if contact_ago > 15:
        prior_days = contact_ago + 14
        contacts.append({
            "contact_id":   f"CON{pid}02",
            "contact_date": (TODAY - timedelta(days=prior_days)).isoformat(),
            "contact_type": "F2F",
            "provider_id":  prov["id"],
            "days_since":   prior_days,
        })

    # ── FHIR entries ──────────────────────────────────────────────────────────
    entries: list[dict] = []

    # Patient
    entries.append({"resource": {
        "resourceType": "Patient",
        "id":           pid,
        "name":         [{"use": "official", "family": last_name, "given": [first_name]}],
        "gender":       gender,
        "birthDate":    dob.isoformat(),
        "address":      [{"district": county, "state": "New York"}],
        "extension": [
            {"url": "http://clinicalmind.ai/fhir/ext/serviceType",    "valueCode":    svc},
            {"url": "http://clinicalmind.ai/fhir/ext/providerId",     "valueString":  prov["id"]},
            {"url": "http://clinicalmind.ai/fhir/ext/riskLevel",      "valueCode":    risk_level},
            {"url": "http://clinicalmind.ai/fhir/ext/engagementFlag", "valueBoolean": contact_ago > 30},
            {"url": "http://clinicalmind.ai/fhir/ext/kpiCompliance",  "valueInteger": kpi_pct},
        ],
    }})

    # Practitioner
    entries.append({"resource": {
        "resourceType": "Practitioner",
        "id":           prov["id"],
        "name":         [{"text": prov["name"]}],
        "extension":    [{"url": "http://clinicalmind.ai/fhir/ext/team", "valueString": prov["team"]}],
    }})

    # Condition (ICD-10 diagnosis)
    entries.append({"resource": {
        "resourceType":   "Condition",
        "id":             str(uuid.uuid4()),
        "subject":        {"reference": f"Patient/{pid}"},
        "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
        "code": {
            "coding": [{"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": dx_code, "display": dx_name}],
            "text": f"{dx_name} ({dx_code})",
        },
        "onsetDateTime": admit_date,
    }})

    # Treatment encounter (the ongoing episode of care)
    entries.append({"resource": {
        "resourceType": "Encounter",
        "id":           f"ENC{pid}01",
        "status":       "in-progress",
        "class":        {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                         "code": "AMB" if svc == "CSP" else "HH",
                         "display": "ambulatory" if svc == "CSP" else "home health"},
        "type":         [{"text": "CSP Outpatient" if svc == "CSP" else "ACT Community"}],
        "subject":      {"reference": f"Patient/{pid}"},
        "participant":  [{"individual": {"reference": f"Practitioner/{prov['id']}"}}],
        "period":       {"start": admit_date},
        "extension": [
            {"url": "http://clinicalmind.ai/fhir/ext/pesFlag", "valueBoolean": ssrs_risk == "High"},
            {"url": "http://clinicalmind.ai/fhir/ext/cisFlag", "valueBoolean": phq9_total >= 15},
        ],
    }})

    # Contact encounters
    for c in contacts:
        code = "VR" if c["contact_type"] == "Telehealth" else "AMB"
        entries.append({"resource": {
            "resourceType": "Encounter",
            "id":           c["contact_id"],
            "status":       "finished",
            "class":        {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": code},
            "type":         [{"text": c["contact_type"]}],
            "subject":      {"reference": f"Patient/{pid}"},
            "participant":  [{"individual": {"reference": f"Practitioner/{c['provider_id']}"}}],
            "period":       {"start": c["contact_date"], "end": c["contact_date"]},
            "extension": [
                {"url": "http://clinicalmind.ai/fhir/ext/daysSinceContact", "valueInteger": c["days_since"]},
            ],
        }})

    # PHQ-9 item observations
    for (loinc, display), score in zip(PHQ9_ITEMS, phq9_items):
        entries.append({"resource": _obs_loinc(pid, loinc, display, score, assessment_date)})

    # PHQ-9 total with components
    entries.append({"resource": _obs_loinc(
        pid, PHQ9_TOTAL_LOINC[0], PHQ9_TOTAL_LOINC[1], phq9_total, assessment_date,
        components=[
            {"code": {"coding": [{"code": "suicidal-ideation"}]}, "valueBoolean": phq9_si},
            {"code": {"coding": [{"code": "severity"}]},          "valueString":  phq9_sev},
        ],
    )})

    # GAD-7 item observations
    for (loinc, display), score in zip(GAD7_ITEMS, gad7_items):
        entries.append({"resource": _obs_loinc(pid, loinc, display, score, assessment_date)})

    # GAD-7 total
    entries.append({"resource": _obs_loinc(
        pid, GAD7_TOTAL_LOINC[0], GAD7_TOTAL_LOINC[1], gad7_total, assessment_date,
        components=[{"code": {"coding": [{"code": "severity"}]}, "valueString": gad7_sev}],
    )})

    # WHODAS total
    entries.append({"resource": _obs_loinc(
        pid, WHODAS_TOTAL_LOINC[0], WHODAS_TOTAL_LOINC[1], whodas_total,
        kpi["whodas"]["last_completed"],
        components=[{"code": {"coding": [{"code": "disability-level"}]}, "valueString": whodas_dl}],
    )})

    # C-SSRS observations
    for field, code in SSRS_CODES.items():
        if field == "ideation_intensity":
            val = ssrs[field]
        elif field == "risk_level":
            val = ssrs_risk
        else:
            val = ssrs[field]
        entries.append({"resource": _obs_custom(pid, SSRS_SYSTEM, code, val, assessment_date)})

    # Crisis event observations
    for ce in crisis_events:
        entries.append({"resource": _obs_custom(
            pid, "http://clinicalmind.ai/fhir/crisis", "CRISIS-EVENT",
            ce["crisis_type"], ce["crisis_date"],
            extensions=[
                {"url": "eventId",       "valueString":  ce["event_id"]},
                {"url": "within7Days",   "valueBoolean": ce["within_7_days"]},
                {"url": "within28Days",  "valueBoolean": ce["within_28_days"]},
                {"url": "daysSince",     "valueInteger": ce["days_since"]},
            ],
        )})

    # KPI compliance observations
    for kname in KPI_NAMES:
        kd = kpi[kname]
        entries.append({"resource": _obs_custom(
            pid, KPI_SYSTEM, kname.upper(), kd["last_completed"], kd["last_completed"],
            extensions=[
                {"url": "dueDate", "valueDate":    kd["due_date"]},
                {"url": "overdue", "valueBoolean": kd["overdue"]},
            ],
        )})

    return {
        "resourceType": "Bundle",
        "id":           pid,
        "type":         "collection",
        "entry":        entries,
        # _meta: pre-extracted fields used by transform_fhir.py
        # (non-standard FHIR extension; analogous to Synthea's internal metadata)
        "_meta": {
            "patient_id":              pid,
            "name":                    f"{first_name} {last_name}",
            "date_of_birth":           dob.isoformat(),
            "diagnosis":               f"{dx_name} ({dx_code})",
            "county":                  county,
            "service_type":            svc,
            "provider_id":             prov["id"],
            "provider_name":           prov["name"],
            "team":                    prov["team"],
            "risk_level":              risk_level,
            "days_since_last_contact": contact_ago,
            "last_contact_date":       contact_date,
            "engagement_flag":         contact_ago > 30,
            "kpi_compliance_pct":      kpi_pct,
            "has_crisis_7d":           any(c["within_7_days"]  for c in crisis_events),
            "has_crisis_28d":          any(c["within_28_days"] for c in crisis_events),
            "phq9": {
                "assessment_date":   assessment_date,
                "total_score":       phq9_total,
                "item_scores":       phq9_items,
                "suicidal_ideation": phq9_si,
                "severity":          phq9_sev,
            },
            "gad7": {
                "assessment_date": assessment_date,
                "total_score":     gad7_total,
                "item_scores":     gad7_items,
                "severity":        gad7_sev,
            },
            "whodas": {
                "assessment_date": kpi["whodas"]["last_completed"],
                "total_score":     whodas_total,
                "disability_level": whodas_dl,
            },
            "ssrs": {
                "assessment_date":    assessment_date,
                "suicidal_ideation":  ssrs["ideation"],
                "ideation_intensity": ssrs["ideation_intensity"],
                "intent":             ssrs["intent"],
                "plan":               ssrs["plan"],
                "method":             ssrs["method"],
                "history_attempt":    ssrs["history_attempt"],
                "risk_level":         ssrs_risk,
            },
            "kpi":           kpi,
            "crisis_events": crisis_events,
            "encounters": [{
                "encounter_id":   f"ENC{pid}01",
                "admit_date":     admit_date,
                "discharge_date": None,
                "encounter_type": "CSP Outpatient" if svc == "CSP" else "ACT Community",
                "pes_flag":       ssrs_risk == "High",
                "cis_flag":       phq9_total >= 15,
            }],
            "contacts": contacts,
        },
    }


# ── Public API ────────────────────────────────────────────────────────────────

def generate_fhir_bundles(n: int = 60, seed: int = 42) -> list[dict]:
    """
    Generate `n` FHIR R4 Bundle resources with realistic behavioral-health data.

    Args:
        n:    Number of patients to generate (default 60).
        seed: RNG seed for reproducibility (default 42).

    Returns:
        List of FHIR Bundle dicts, each with a `_meta` extraction shortcut.
    """
    rng  = random.Random(seed)
    fake = Faker()
    Faker.seed(seed)
    return [_build_bundle(i + 1, rng, fake) for i in range(n)]


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    n       = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    bundles = generate_fhir_bundles(n)

    out = os.path.join(os.path.dirname(__file__), "fhir_output.json")
    with open(out, "w") as f:
        json.dump(bundles, f, indent=2)

    high = sum(1 for b in bundles if b["_meta"]["risk_level"] == "High")
    mod  = sum(1 for b in bundles if b["_meta"]["risk_level"] == "Moderate")
    low  = sum(1 for b in bundles if b["_meta"]["risk_level"] == "Low")
    print(f"Generated {n} FHIR bundles  →  {out}")
    print(f"  High: {high}  Moderate: {mod}  Low: {low}")
    print(f"  FHIR resources per bundle: {len(bundles[0]['entry'])}")

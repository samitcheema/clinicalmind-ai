"""
ClinicalMind AI — Mock Data Generator

Generates 45 mock patients faithfully representing the production SQL schema:
  mast_processing.encounter
  mast_processing.assessment_phq9 / assessment_gad7 / assessment_whodas / assessment_ssrs
  mast_processing.contact
  mast_processing.crisis_event
  output.su  (KPI compliance columns)
  output.su_staff  (provider-patient assignments)

Reference date: 2026-03-12  (today in the system)
Clinical scoring rules:
  PHQ-9  — score >= 15 OR item 9 (suicidal ideation) > 0  -> High severity
  GAD-7  — score >= 15 -> High severity
  SSRS   — method or plan present -> High; ideation only -> Moderate
  KPI    — 75% completion target; BHA/SRA/AIMS/PHQ-9 quarterly, WHODAS annual
  Engagement — no contact in > 30 days -> disengaged flag
  Crisis — 7-day and 28-day flags tracked
"""

from datetime import date, timedelta
from functools import lru_cache

TODAY = date(2026, 3, 12)

# ── Date helpers ──────────────────────────────────────────────────────────────

def days_ago(n: int) -> str:
    return (TODAY - timedelta(days=n)).isoformat()

def days_from_now(n: int) -> str:
    return (TODAY + timedelta(days=n)).isoformat()

def days_between(date_str: str) -> int:
    return (TODAY - date.fromisoformat(date_str)).days

# ── Providers (output.su_staff) ───────────────────────────────────────────────

PROVIDERS = [
    {"provider_id": "PROV001", "name": "Dr. Emma Chen",       "team": "ACT-1", "specialty": "BH"},
    {"provider_id": "PROV002", "name": "Dr. Marcus Williams", "team": "ACT-1", "specialty": "BH"},
    {"provider_id": "PROV003", "name": "Dr. Priya Sharma",    "team": "ACT-2", "specialty": "BH"},
    {"provider_id": "PROV004", "name": "Dr. James O'Brien",   "team": "ACT-2", "specialty": "BH"},
    {"provider_id": "PROV005", "name": "Dr. Sarah Nakamura",  "team": "CSP-1", "specialty": "BH"},
    {"provider_id": "PROV006", "name": "Dr. Robert Kim",      "team": "CSP-1", "specialty": "BH"},
]

DIAGNOSES = [
    "Major Depressive Disorder (F32.1)",
    "Bipolar I Disorder (F31.1)",
    "Schizophrenia (F20.9)",
    "PTSD (F43.10)",
    "Generalized Anxiety Disorder (F41.1)",
    "Schizoaffective Disorder (F25.0)",
    "Borderline Personality Disorder (F60.3)",
    "Major Depressive Disorder, Recurrent (F33.1)",
]

COUNTIES = ["Westchester", "Rockland", "Orange", "Dutchess", "Putnam"]

CRISIS_TYPES = [
    "Psychiatric Emergency",
    "Suicidal Crisis — Passive Ideation",
    "Suicidal Crisis — Active Ideation",
    "Self-Harm Incident",
    "Aggressive Behavior",
]

# ── Clinical scoring helpers ──────────────────────────────────────────────────

def phq9_severity(score: int, suicidal_ideation: bool) -> str:
    if score >= 15 or suicidal_ideation:
        return "High"
    if score >= 10:
        return "Moderately Severe"
    if score >= 5:
        return "Moderate"
    return "Minimal"

def gad7_severity(score: int) -> str:
    if score >= 15:
        return "High"
    if score >= 10:
        return "Moderate"
    if score >= 5:
        return "Mild"
    return "Minimal"

def kpi_entry(last_days_ago: int, interval_days: int) -> dict:
    last_completed = days_ago(last_days_ago)
    due_date       = days_ago(last_days_ago - interval_days)
    overdue        = days_between(due_date) > 0
    return {"last_completed": last_completed, "due_date": due_date, "overdue": overdue}

def kpi_compliance_rate(kpi: dict) -> int:
    keys = ["bha", "sra", "aims", "whodas", "phq9", "beh_tp", "beh_csp"]
    completed = sum(1 for k in keys if not kpi[k]["overdue"])
    return round((completed / len(keys)) * 100)

def overall_risk(phq9: dict, ssrs: dict) -> str:
    if phq9["severity"] == "High" or ssrs["risk_level"] == "High":
        return "High"
    if phq9["severity"] == "Moderately Severe" or ssrs["risk_level"] == "Moderate":
        return "Moderate"
    return "Low"

# ── Raw patient definitions ───────────────────────────────────────────────────

_RAW = [
    # ── HIGH RISK (9) ──────────────────────────────────────────────────────────
    {
        "name": "Sarah Mitchell",    "dob": "1978-05-14", "diag_idx": 0, "county_idx": 0, "prov_idx": 0, "svc": "ACT",
        "phq9_score": 22, "phq9_si": True,  "item_offset": 2, "gad7_score": 16,
        "ssrs_ideation": True,  "ssrs_intent": True,  "ssrs_plan": True,  "ssrs_method": True,  "ssrs_hx": True,
        "last_contact": 5,
        "crisis": [{"days_ago": 4, "type": 2}, {"days_ago": 45, "type": 0}],
        "kpi": {"bha": kpi_entry(30, 90), "sra": kpi_entry(95, 90), "aims": kpi_entry(120, 90),
                "whodas": kpi_entry(400, 365), "phq9": kpi_entry(30, 90),
                "beh_tp": kpi_entry(15, 90), "beh_csp": kpi_entry(200, 90)},
    },
    {
        "name": "Marcus Johnson",    "dob": "1985-11-22", "diag_idx": 1, "county_idx": 1, "prov_idx": 1, "svc": "ACT",
        "phq9_score": 19, "phq9_si": True,  "item_offset": 2, "gad7_score": 14,
        "ssrs_ideation": True,  "ssrs_intent": True,  "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": True,
        "last_contact": 3,
        "crisis": [{"days_ago": 6, "type": 2}, {"days_ago": 32, "type": 1}],
        "kpi": {"bha": kpi_entry(20, 90), "sra": kpi_entry(110, 90), "aims": kpi_entry(25, 90),
                "whodas": kpi_entry(380, 365), "phq9": kpi_entry(20, 90),
                "beh_tp": kpi_entry(35, 90), "beh_csp": kpi_entry(185, 90)},
    },
    {
        "name": "Diana Reyes",       "dob": "1993-03-08", "diag_idx": 2, "county_idx": 0, "prov_idx": 2, "svc": "ACT",
        "phq9_score": 17, "phq9_si": False, "item_offset": 2, "gad7_score": 15,
        "ssrs_ideation": True,  "ssrs_intent": False, "ssrs_plan": True,  "ssrs_method": True,  "ssrs_hx": False,
        "last_contact": 12,
        "crisis": [{"days_ago": 10, "type": 2}],
        "kpi": {"bha": kpi_entry(50, 90), "sra": kpi_entry(130, 90), "aims": kpi_entry(88, 90),
                "whodas": kpi_entry(410, 365), "phq9": kpi_entry(50, 90),
                "beh_tp": kpi_entry(70, 90), "beh_csp": kpi_entry(170, 90)},
    },
    {
        "name": "Thomas Hargrove",   "dob": "1966-08-30", "diag_idx": 5, "county_idx": 2, "prov_idx": 3, "svc": "ACT",
        "phq9_score": 21, "phq9_si": True,  "item_offset": 2, "gad7_score": 13,
        "ssrs_ideation": True,  "ssrs_intent": True,  "ssrs_plan": True,  "ssrs_method": False, "ssrs_hx": True,
        "last_contact": 7,
        "crisis": [{"days_ago": 20, "type": 2}, {"days_ago": 75, "type": 0}],
        "kpi": {"bha": kpi_entry(40, 90), "sra": kpi_entry(145, 90), "aims": kpi_entry(55, 90),
                "whodas": kpi_entry(430, 365), "phq9": kpi_entry(40, 90),
                "beh_tp": kpi_entry(60, 90), "beh_csp": kpi_entry(210, 90)},
    },
    {
        "name": "Angela Foster",     "dob": "1982-01-17", "diag_idx": 6, "county_idx": 3, "prov_idx": 0, "svc": "CSP",
        "phq9_score": 18, "phq9_si": True,  "item_offset": 2, "gad7_score": 17,
        "ssrs_ideation": True,  "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": True,
        "last_contact": 2,
        "crisis": [{"days_ago": 14, "type": 1}],
        "kpi": {"bha": kpi_entry(25, 90), "sra": kpi_entry(100, 90), "aims": kpi_entry(45, 90),
                "whodas": kpi_entry(395, 365), "phq9": kpi_entry(25, 90),
                "beh_tp": kpi_entry(55, 90), "beh_csp": kpi_entry(195, 90)},
    },
    {
        "name": "Kevin Osei",        "dob": "1975-09-04", "diag_idx": 0, "county_idx": 4, "prov_idx": 4, "svc": "CSP",
        "phq9_score": 16, "phq9_si": False, "item_offset": 2, "gad7_score": 9,
        "ssrs_ideation": True,  "ssrs_intent": True,  "ssrs_plan": True,  "ssrs_method": True,  "ssrs_hx": False,
        "last_contact": 45,
        "crisis": [{"days_ago": 25, "type": 2}],
        "kpi": {"bha": kpi_entry(105, 90), "sra": kpi_entry(120, 90), "aims": kpi_entry(140, 90),
                "whodas": kpi_entry(440, 365), "phq9": kpi_entry(105, 90),
                "beh_tp": kpi_entry(130, 90), "beh_csp": kpi_entry(220, 90)},
    },
    {
        "name": "Patricia Nguyen",   "dob": "1990-06-23", "diag_idx": 3, "county_idx": 1, "prov_idx": 5, "svc": "CSP",
        "phq9_score": 20, "phq9_si": True,  "item_offset": 2, "gad7_score": 18,
        "ssrs_ideation": True,  "ssrs_intent": True,  "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": True,
        "last_contact": 8,
        "crisis": [{"days_ago": 5, "type": 1}, {"days_ago": 60, "type": 0}],
        "kpi": {"bha": kpi_entry(35, 90), "sra": kpi_entry(92, 90), "aims": kpi_entry(75, 90),
                "whodas": kpi_entry(420, 365), "phq9": kpi_entry(35, 90),
                "beh_tp": kpi_entry(45, 90), "beh_csp": kpi_entry(180, 90)},
    },
    {
        "name": "Robert Castillo",   "dob": "1971-12-11", "diag_idx": 7, "county_idx": 2, "prov_idx": 1, "svc": "ACT",
        "phq9_score": 15, "phq9_si": False, "item_offset": 1, "gad7_score": 12,
        "ssrs_ideation": True,  "ssrs_intent": False, "ssrs_plan": True,  "ssrs_method": True,  "ssrs_hx": False,
        "last_contact": 6,
        "crisis": [{"days_ago": 18, "type": 3}],
        "kpi": {"bha": kpi_entry(60, 90), "sra": kpi_entry(155, 90), "aims": kpi_entry(80, 90),
                "whodas": kpi_entry(460, 365), "phq9": kpi_entry(60, 90),
                "beh_tp": kpi_entry(90, 90), "beh_csp": kpi_entry(240, 90)},
    },
    {
        "name": "Yolanda Marsh",     "dob": "1980-04-29", "diag_idx": 1, "county_idx": 0, "prov_idx": 2, "svc": "ACT",
        "phq9_score": 23, "phq9_si": True,  "item_offset": 2, "gad7_score": 19,
        "ssrs_ideation": True,  "ssrs_intent": True,  "ssrs_plan": True,  "ssrs_method": False, "ssrs_hx": True,
        "last_contact": 1,
        "crisis": [{"days_ago": 3, "type": 2}, {"days_ago": 22, "type": 1}],
        "kpi": {"bha": kpi_entry(15, 90), "sra": kpi_entry(88, 90), "aims": kpi_entry(30, 90),
                "whodas": kpi_entry(370, 365), "phq9": kpi_entry(15, 90),
                "beh_tp": kpi_entry(25, 90), "beh_csp": kpi_entry(160, 90)},
    },
    # ── MODERATE RISK (18) ────────────────────────────────────────────────────
    {
        "name": "James Whitfield",   "dob": "1988-07-15", "diag_idx": 4, "county_idx": 1, "prov_idx": 3, "svc": "CSP",
        "phq9_score": 13, "phq9_si": False, "item_offset": 1, "gad7_score": 11,
        "ssrs_ideation": True,  "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 18,
        "crisis": [],
        "kpi": {"bha": kpi_entry(80, 90), "sra": kpi_entry(70, 90), "aims": kpi_entry(65, 90),
                "whodas": kpi_entry(340, 365), "phq9": kpi_entry(80, 90),
                "beh_tp": kpi_entry(50, 90), "beh_csp": kpi_entry(100, 90)},
    },
    {
        "name": "Lucia Fernandez",   "dob": "1994-02-28", "diag_idx": 6, "county_idx": 0, "prov_idx": 4, "svc": "CSP",
        "phq9_score": 12, "phq9_si": False, "item_offset": 1, "gad7_score": 14,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": True,
        "last_contact": 22,
        "crisis": [{"days_ago": 50, "type": 1}],
        "kpi": {"bha": kpi_entry(85, 90), "sra": kpi_entry(75, 90), "aims": kpi_entry(60, 90),
                "whodas": kpi_entry(300, 365), "phq9": kpi_entry(85, 90),
                "beh_tp": kpi_entry(40, 90), "beh_csp": kpi_entry(115, 90)},
    },
    {
        "name": "Andre Thompson",    "dob": "1969-10-05", "diag_idx": 2, "county_idx": 3, "prov_idx": 5, "svc": "ACT",
        "phq9_score": 14, "phq9_si": False, "item_offset": 1, "gad7_score": 10,
        "ssrs_ideation": True,  "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 35,
        "crisis": [],
        "kpi": {"bha": kpi_entry(95, 90), "sra": kpi_entry(40, 90), "aims": kpi_entry(50, 90),
                "whodas": kpi_entry(280, 365), "phq9": kpi_entry(95, 90),
                "beh_tp": kpi_entry(30, 90), "beh_csp": kpi_entry(80, 90)},
    },
    {
        "name": "Cynthia Brooks",    "dob": "1987-05-19", "diag_idx": 0, "county_idx": 2, "prov_idx": 0, "svc": "ACT",
        "phq9_score": 11, "phq9_si": False, "item_offset": 1, "gad7_score": 8,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": True,
        "last_contact": 14,
        "crisis": [{"days_ago": 40, "type": 0}],
        "kpi": {"bha": kpi_entry(70, 90), "sra": kpi_entry(55, 90), "aims": kpi_entry(72, 90),
                "whodas": kpi_entry(310, 365), "phq9": kpi_entry(70, 90),
                "beh_tp": kpi_entry(80, 90), "beh_csp": kpi_entry(90, 90)},
    },
    {
        "name": "William Grant",     "dob": "1977-08-12", "diag_idx": 5, "county_idx": 4, "prov_idx": 1, "svc": "ACT",
        "phq9_score": 13, "phq9_si": False, "item_offset": 1, "gad7_score": 9,
        "ssrs_ideation": True,  "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 40,
        "crisis": [],
        "kpi": {"bha": kpi_entry(100, 90), "sra": kpi_entry(85, 90), "aims": kpi_entry(95, 90),
                "whodas": kpi_entry(320, 365), "phq9": kpi_entry(100, 90),
                "beh_tp": kpi_entry(110, 90), "beh_csp": kpi_entry(130, 90)},
    },
    {
        "name": "Denise Patel",      "dob": "1991-01-30", "diag_idx": 3, "county_idx": 1, "prov_idx": 2, "svc": "CSP",
        "phq9_score": 10, "phq9_si": False, "item_offset": 1, "gad7_score": 13,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 10,
        "crisis": [],
        "kpi": {"bha": kpi_entry(65, 90), "sra": kpi_entry(50, 90), "aims": kpi_entry(58, 90),
                "whodas": kpi_entry(260, 365), "phq9": kpi_entry(65, 90),
                "beh_tp": kpi_entry(75, 90), "beh_csp": kpi_entry(88, 90)},
    },
    {
        "name": "Samuel Okonkwo",    "dob": "1983-06-17", "diag_idx": 7, "county_idx": 0, "prov_idx": 3, "svc": "ACT",
        "phq9_score": 12, "phq9_si": False, "item_offset": 1, "gad7_score": 7,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": True,
        "last_contact": 28,
        "crisis": [{"days_ago": 55, "type": 0}],
        "kpi": {"bha": kpi_entry(78, 90), "sra": kpi_entry(62, 90), "aims": kpi_entry(68, 90),
                "whodas": kpi_entry(295, 365), "phq9": kpi_entry(78, 90),
                "beh_tp": kpi_entry(88, 90), "beh_csp": kpi_entry(105, 90)},
    },
    {
        "name": "Tanya Morrison",    "dob": "1972-11-08", "diag_idx": 1, "county_idx": 3, "prov_idx": 4, "svc": "CSP",
        "phq9_score": 14, "phq9_si": False, "item_offset": 1, "gad7_score": 11,
        "ssrs_ideation": True,  "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 16,
        "crisis": [],
        "kpi": {"bha": kpi_entry(90, 90), "sra": kpi_entry(78, 90), "aims": kpi_entry(82, 90),
                "whodas": kpi_entry(330, 365), "phq9": kpi_entry(90, 90),
                "beh_tp": kpi_entry(100, 90), "beh_csp": kpi_entry(125, 90)},
    },
    {
        "name": "Carlos Rivera",     "dob": "1986-03-22", "diag_idx": 4, "county_idx": 2, "prov_idx": 5, "svc": "CSP",
        "phq9_score": 11, "phq9_si": False, "item_offset": 1, "gad7_score": 10,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 50,
        "crisis": [],
        "kpi": {"bha": kpi_entry(115, 90), "sra": kpi_entry(95, 90), "aims": kpi_entry(105, 90),
                "whodas": kpi_entry(350, 365), "phq9": kpi_entry(115, 90),
                "beh_tp": kpi_entry(120, 90), "beh_csp": kpi_entry(145, 90)},
    },
    {
        "name": "Monique Stewart",   "dob": "1979-09-14", "diag_idx": 6, "county_idx": 4, "prov_idx": 0, "svc": "ACT",
        "phq9_score": 13, "phq9_si": False, "item_offset": 1, "gad7_score": 12,
        "ssrs_ideation": True,  "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 24,
        "crisis": [{"days_ago": 70, "type": 1}],
        "kpi": {"bha": kpi_entry(72, 90), "sra": kpi_entry(58, 90), "aims": kpi_entry(65, 90),
                "whodas": kpi_entry(285, 365), "phq9": kpi_entry(72, 90),
                "beh_tp": kpi_entry(82, 90), "beh_csp": kpi_entry(95, 90)},
    },
    {
        "name": "Derek Lawson",      "dob": "1968-04-03", "diag_idx": 5, "county_idx": 0, "prov_idx": 1, "svc": "ACT",
        "phq9_score": 14, "phq9_si": False, "item_offset": 1, "gad7_score": 8,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": True,
        "last_contact": 38,
        "crisis": [],
        "kpi": {"bha": kpi_entry(98, 90), "sra": kpi_entry(82, 90), "aims": kpi_entry(92, 90),
                "whodas": kpi_entry(315, 365), "phq9": kpi_entry(98, 90),
                "beh_tp": kpi_entry(108, 90), "beh_csp": kpi_entry(135, 90)},
    },
    {
        "name": "Felicia Barnes",    "dob": "1992-07-27", "diag_idx": 0, "county_idx": 1, "prov_idx": 2, "svc": "CSP",
        "phq9_score": 10, "phq9_si": False, "item_offset": 1, "gad7_score": 14,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 12,
        "crisis": [],
        "kpi": {"bha": kpi_entry(60, 90), "sra": kpi_entry(48, 90), "aims": kpi_entry(55, 90),
                "whodas": kpi_entry(270, 365), "phq9": kpi_entry(60, 90),
                "beh_tp": kpi_entry(70, 90), "beh_csp": kpi_entry(82, 90)},
    },
    {
        "name": "Howard Campbell",   "dob": "1974-02-16", "diag_idx": 2, "county_idx": 3, "prov_idx": 3, "svc": "ACT",
        "phq9_score": 12, "phq9_si": False, "item_offset": 1, "gad7_score": 7,
        "ssrs_ideation": True,  "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 20,
        "crisis": [],
        "kpi": {"bha": kpi_entry(85, 90), "sra": kpi_entry(68, 90), "aims": kpi_entry(75, 90),
                "whodas": kpi_entry(305, 365), "phq9": kpi_entry(85, 90),
                "beh_tp": kpi_entry(95, 90), "beh_csp": kpi_entry(112, 90)},
    },
    {
        "name": "Ingrid Sorensen",   "dob": "1989-12-05", "diag_idx": 3, "county_idx": 2, "prov_idx": 4, "svc": "CSP",
        "phq9_score": 11, "phq9_si": False, "item_offset": 1, "gad7_score": 13,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 55,
        "crisis": [],
        "kpi": {"bha": kpi_entry(120, 90), "sra": kpi_entry(102, 90), "aims": kpi_entry(110, 90),
                "whodas": kpi_entry(360, 365), "phq9": kpi_entry(120, 90),
                "beh_tp": kpi_entry(125, 90), "beh_csp": kpi_entry(150, 90)},
    },
    {
        "name": "Jerome Washington", "dob": "1981-08-20", "diag_idx": 7, "county_idx": 4, "prov_idx": 5, "svc": "ACT",
        "phq9_score": 13, "phq9_si": False, "item_offset": 1, "gad7_score": 9,
        "ssrs_ideation": True,  "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 30,
        "crisis": [{"days_ago": 45, "type": 4}],
        "kpi": {"bha": kpi_entry(93, 90), "sra": kpi_entry(76, 90), "aims": kpi_entry(83, 90),
                "whodas": kpi_entry(325, 365), "phq9": kpi_entry(93, 90),
                "beh_tp": kpi_entry(103, 90), "beh_csp": kpi_entry(128, 90)},
    },
    {
        "name": "Keisha Douglas",    "dob": "1996-03-11", "diag_idx": 4, "county_idx": 0, "prov_idx": 0, "svc": "CSP",
        "phq9_score": 10, "phq9_si": False, "item_offset": 1, "gad7_score": 11,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 9,
        "crisis": [],
        "kpi": {"bha": kpi_entry(68, 90), "sra": kpi_entry(52, 90), "aims": kpi_entry(60, 90),
                "whodas": kpi_entry(275, 365), "phq9": kpi_entry(68, 90),
                "beh_tp": kpi_entry(78, 90), "beh_csp": kpi_entry(90, 90)},
    },
    {
        "name": "Nathaniel Cruz",    "dob": "1970-06-28", "diag_idx": 1, "county_idx": 1, "prov_idx": 1, "svc": "ACT",
        "phq9_score": 14, "phq9_si": False, "item_offset": 1, "gad7_score": 10,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": True,
        "last_contact": 42,
        "crisis": [],
        "kpi": {"bha": kpi_entry(107, 90), "sra": kpi_entry(90, 90), "aims": kpi_entry(98, 90),
                "whodas": kpi_entry(345, 365), "phq9": kpi_entry(107, 90),
                "beh_tp": kpi_entry(115, 90), "beh_csp": kpi_entry(140, 90)},
    },
    {
        "name": "Olivia Hart",       "dob": "1984-10-17", "diag_idx": 6, "county_idx": 3, "prov_idx": 2, "svc": "CSP",
        "phq9_score": 11, "phq9_si": False, "item_offset": 1, "gad7_score": 12,
        "ssrs_ideation": True,  "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 17,
        "crisis": [],
        "kpi": {"bha": kpi_entry(75, 90), "sra": kpi_entry(60, 90), "aims": kpi_entry(68, 90),
                "whodas": kpi_entry(290, 365), "phq9": kpi_entry(75, 90),
                "beh_tp": kpi_entry(85, 90), "beh_csp": kpi_entry(98, 90)},
    },
    # ── LOW RISK (18) ─────────────────────────────────────────────────────────
    {
        "name": "Peter Huang",       "dob": "1995-01-09", "diag_idx": 0, "county_idx": 4, "prov_idx": 3, "svc": "CSP",
        "phq9_score": 4,  "phq9_si": False, "item_offset": 0, "gad7_score": 3,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 7,
        "crisis": [],
        "kpi": {"bha": kpi_entry(20, 90), "sra": kpi_entry(15, 90), "aims": kpi_entry(22, 90),
                "whodas": kpi_entry(180, 365), "phq9": kpi_entry(20, 90),
                "beh_tp": kpi_entry(25, 90), "beh_csp": kpi_entry(30, 90)},
    },
    {
        "name": "Quinn Abernathy",   "dob": "1973-09-26", "diag_idx": 4, "county_idx": 0, "prov_idx": 4, "svc": "CSP",
        "phq9_score": 6,  "phq9_si": False, "item_offset": 0, "gad7_score": 5,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 13,
        "crisis": [],
        "kpi": {"bha": kpi_entry(55, 90), "sra": kpi_entry(42, 90), "aims": kpi_entry(48, 90),
                "whodas": kpi_entry(210, 365), "phq9": kpi_entry(55, 90),
                "beh_tp": kpi_entry(65, 90), "beh_csp": kpi_entry(72, 90)},
    },
    {
        "name": "Rachel Simmons",    "dob": "1990-04-14", "diag_idx": 3, "county_idx": 1, "prov_idx": 5, "svc": "CSP",
        "phq9_score": 3,  "phq9_si": False, "item_offset": 0, "gad7_score": 2,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 4,
        "crisis": [],
        "kpi": {"bha": kpi_entry(10, 90), "sra": kpi_entry(8, 90), "aims": kpi_entry(12, 90),
                "whodas": kpi_entry(150, 365), "phq9": kpi_entry(10, 90),
                "beh_tp": kpi_entry(15, 90), "beh_csp": kpi_entry(18, 90)},
    },
    {
        "name": "Steven Yates",      "dob": "1967-07-31", "diag_idx": 5, "county_idx": 2, "prov_idx": 0, "svc": "ACT",
        "phq9_score": 7,  "phq9_si": False, "item_offset": 0, "gad7_score": 6,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 21,
        "crisis": [],
        "kpi": {"bha": kpi_entry(72, 90), "sra": kpi_entry(58, 90), "aims": kpi_entry(65, 90),
                "whodas": kpi_entry(240, 365), "phq9": kpi_entry(72, 90),
                "beh_tp": kpi_entry(82, 90), "beh_csp": kpi_entry(90, 90)},
    },
    {
        "name": "Tamara Ellis",      "dob": "1988-12-20", "diag_idx": 7, "county_idx": 3, "prov_idx": 1, "svc": "ACT",
        "phq9_score": 5,  "phq9_si": False, "item_offset": 0, "gad7_score": 4,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 6,
        "crisis": [],
        "kpi": {"bha": kpi_entry(35, 90), "sra": kpi_entry(28, 90), "aims": kpi_entry(32, 90),
                "whodas": kpi_entry(190, 365), "phq9": kpi_entry(35, 90),
                "beh_tp": kpi_entry(40, 90), "beh_csp": kpi_entry(46, 90)},
    },
    {
        "name": "Ulrich Brennan",    "dob": "1976-03-07", "diag_idx": 0, "county_idx": 4, "prov_idx": 2, "svc": "CSP",
        "phq9_score": 8,  "phq9_si": False, "item_offset": 0, "gad7_score": 7,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 19,
        "crisis": [],
        "kpi": {"bha": kpi_entry(82, 90), "sra": kpi_entry(68, 90), "aims": kpi_entry(75, 90),
                "whodas": kpi_entry(255, 365), "phq9": kpi_entry(82, 90),
                "beh_tp": kpi_entry(92, 90), "beh_csp": kpi_entry(100, 90)},
    },
    {
        "name": "Valeria Montes",    "dob": "1993-08-15", "diag_idx": 4, "county_idx": 0, "prov_idx": 3, "svc": "CSP",
        "phq9_score": 4,  "phq9_si": False, "item_offset": 0, "gad7_score": 3,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 11,
        "crisis": [],
        "kpi": {"bha": kpi_entry(28, 90), "sra": kpi_entry(22, 90), "aims": kpi_entry(26, 90),
                "whodas": kpi_entry(170, 365), "phq9": kpi_entry(28, 90),
                "beh_tp": kpi_entry(32, 90), "beh_csp": kpi_entry(38, 90)},
    },
    {
        "name": "Walter Jennings",   "dob": "1963-11-24", "diag_idx": 5, "county_idx": 1, "prov_idx": 4, "svc": "ACT",
        "phq9_score": 6,  "phq9_si": False, "item_offset": 0, "gad7_score": 5,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 25,
        "crisis": [],
        "kpi": {"bha": kpi_entry(62, 90), "sra": kpi_entry(50, 90), "aims": kpi_entry(56, 90),
                "whodas": kpi_entry(225, 365), "phq9": kpi_entry(62, 90),
                "beh_tp": kpi_entry(72, 90), "beh_csp": kpi_entry(80, 90)},
    },
    {
        "name": "Xena Kowalski",     "dob": "1991-05-18", "diag_idx": 6, "county_idx": 2, "prov_idx": 5, "svc": "CSP",
        "phq9_score": 3,  "phq9_si": False, "item_offset": 0, "gad7_score": 2,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 3,
        "crisis": [],
        "kpi": {"bha": kpi_entry(12, 90), "sra": kpi_entry(9, 90), "aims": kpi_entry(14, 90),
                "whodas": kpi_entry(155, 365), "phq9": kpi_entry(12, 90),
                "beh_tp": kpi_entry(18, 90), "beh_csp": kpi_entry(22, 90)},
    },
    {
        "name": "Yvette Chambers",   "dob": "1985-02-03", "diag_idx": 0, "county_idx": 3, "prov_idx": 0, "svc": "ACT",
        "phq9_score": 8,  "phq9_si": False, "item_offset": 0, "gad7_score": 6,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 29,
        "crisis": [],
        "kpi": {"bha": kpi_entry(88, 90), "sra": kpi_entry(74, 90), "aims": kpi_entry(80, 90),
                "whodas": kpi_entry(265, 365), "phq9": kpi_entry(88, 90),
                "beh_tp": kpi_entry(98, 90), "beh_csp": kpi_entry(108, 90)},
    },
    {
        "name": "Zachary Pope",      "dob": "1978-06-30", "diag_idx": 3, "county_idx": 4, "prov_idx": 1, "svc": "CSP",
        "phq9_score": 5,  "phq9_si": False, "item_offset": 0, "gad7_score": 4,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 8,
        "crisis": [],
        "kpi": {"bha": kpi_entry(40, 90), "sra": kpi_entry(32, 90), "aims": kpi_entry(36, 90),
                "whodas": kpi_entry(200, 365), "phq9": kpi_entry(40, 90),
                "beh_tp": kpi_entry(48, 90), "beh_csp": kpi_entry(54, 90)},
    },
    {
        "name": "Alice Mercer",      "dob": "1997-01-14", "diag_idx": 4, "county_idx": 0, "prov_idx": 2, "svc": "CSP",
        "phq9_score": 4,  "phq9_si": False, "item_offset": 0, "gad7_score": 3,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 5,
        "crisis": [],
        "kpi": {"bha": kpi_entry(18, 90), "sra": kpi_entry(14, 90), "aims": kpi_entry(16, 90),
                "whodas": kpi_entry(145, 365), "phq9": kpi_entry(18, 90),
                "beh_tp": kpi_entry(22, 90), "beh_csp": kpi_entry(28, 90)},
    },
    {
        "name": "Brian Adkins",      "dob": "1972-09-08", "diag_idx": 7, "county_idx": 1, "prov_idx": 3, "svc": "ACT",
        "phq9_score": 7,  "phq9_si": False, "item_offset": 0, "gad7_score": 5,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 15,
        "crisis": [],
        "kpi": {"bha": kpi_entry(75, 90), "sra": kpi_entry(62, 90), "aims": kpi_entry(68, 90),
                "whodas": kpi_entry(248, 365), "phq9": kpi_entry(75, 90),
                "beh_tp": kpi_entry(85, 90), "beh_csp": kpi_entry(93, 90)},
    },
    {
        "name": "Clara Nguyen",      "dob": "1986-04-25", "diag_idx": 0, "county_idx": 2, "prov_idx": 4, "svc": "CSP",
        "phq9_score": 6,  "phq9_si": False, "item_offset": 0, "gad7_score": 4,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 23,
        "crisis": [],
        "kpi": {"bha": kpi_entry(58, 90), "sra": kpi_entry(46, 90), "aims": kpi_entry(52, 90),
                "whodas": kpi_entry(218, 365), "phq9": kpi_entry(58, 90),
                "beh_tp": kpi_entry(68, 90), "beh_csp": kpi_entry(76, 90)},
    },
    {
        "name": "Damien Price",      "dob": "1965-12-16", "diag_idx": 2, "county_idx": 3, "prov_idx": 5, "svc": "ACT",
        "phq9_score": 9,  "phq9_si": False, "item_offset": 0, "gad7_score": 7,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 60,
        "crisis": [],
        "kpi": {"bha": kpi_entry(125, 90), "sra": kpi_entry(108, 90), "aims": kpi_entry(115, 90),
                "whodas": kpi_entry(375, 365), "phq9": kpi_entry(125, 90),
                "beh_tp": kpi_entry(132, 90), "beh_csp": kpi_entry(155, 90)},
    },
    {
        "name": "Elena Vásquez",     "dob": "1994-07-07", "diag_idx": 6, "county_idx": 4, "prov_idx": 0, "svc": "CSP",
        "phq9_score": 4,  "phq9_si": False, "item_offset": 0, "gad7_score": 3,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 4,
        "crisis": [],
        "kpi": {"bha": kpi_entry(22, 90), "sra": kpi_entry(17, 90), "aims": kpi_entry(20, 90),
                "whodas": kpi_entry(165, 365), "phq9": kpi_entry(22, 90),
                "beh_tp": kpi_entry(28, 90), "beh_csp": kpi_entry(34, 90)},
    },
    {
        "name": "Floyd McAllister",  "dob": "1980-03-19", "diag_idx": 5, "county_idx": 0, "prov_idx": 1, "svc": "ACT",
        "phq9_score": 7,  "phq9_si": False, "item_offset": 0, "gad7_score": 6,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 31,
        "crisis": [],
        "kpi": {"bha": kpi_entry(92, 90), "sra": kpi_entry(78, 90), "aims": kpi_entry(84, 90),
                "whodas": kpi_entry(258, 365), "phq9": kpi_entry(92, 90),
                "beh_tp": kpi_entry(102, 90), "beh_csp": kpi_entry(118, 90)},
    },
    {
        "name": "Grace Kim",         "dob": "1989-10-01", "diag_idx": 4, "county_idx": 1, "prov_idx": 2, "svc": "CSP",
        "phq9_score": 5,  "phq9_si": False, "item_offset": 0, "gad7_score": 4,
        "ssrs_ideation": False, "ssrs_intent": False, "ssrs_plan": False, "ssrs_method": False, "ssrs_hx": False,
        "last_contact": 10,
        "crisis": [],
        "kpi": {"bha": kpi_entry(45, 90), "sra": kpi_entry(36, 90), "aims": kpi_entry(40, 90),
                "whodas": kpi_entry(205, 365), "phq9": kpi_entry(45, 90),
                "beh_tp": kpi_entry(52, 90), "beh_csp": kpi_entry(58, 90)},
    },
]

# ── Patient builder ───────────────────────────────────────────────────────────

def _build_patient(raw: dict, idx: int) -> dict:
    pid      = f"PAT{idx + 1:03d}"
    provider = PROVIDERS[raw["prov_idx"]]
    county   = COUNTIES[raw["county_idx"]]
    diagnosis = DIAGNOSES[raw["diag_idx"]]

    # PHQ-9
    items = [raw["item_offset"]] * 9
    item_sum = sum(items)
    remainder = raw["phq9_score"] - item_sum
    items[0] += remainder
    if raw["phq9_si"]:
        items[8] = max(items[8], 1)
    phq9_total = sum(items)
    phq9 = {
        "assessment_date":    days_ago(raw["last_contact"] + 10),
        "total_score":        phq9_total,
        "item_scores":        items,
        "suicidal_ideation":  raw["phq9_si"],
        "severity":           phq9_severity(phq9_total, raw["phq9_si"]),
    }

    # GAD-7
    g = [raw["gad7_score"] // 7] * 7
    g[0] += raw["gad7_score"] - sum(g)
    gad7 = {
        "assessment_date": days_ago(raw["last_contact"] + 10),
        "total_score":     raw["gad7_score"],
        "item_scores":     g,
        "severity":        gad7_severity(raw["gad7_score"]),
    }

    # WHODAS
    whodas = {
        "assessment_date": raw["kpi"]["whodas"]["last_completed"],
        "total_score":     raw["phq9_score"] * 2 + raw["gad7_score"],
        "disability_level": (
            "Severe" if raw["phq9_score"] >= 15
            else "Moderate" if raw["phq9_score"] >= 10
            else "Mild"
        ),
    }

    # SSRS
    ssrs_risk = "Low"
    if raw["ssrs_plan"] or raw["ssrs_method"]:
        ssrs_risk = "High"
    elif raw["ssrs_ideation"]:
        ssrs_risk = "Moderate"
    ssrs = {
        "assessment_date":    days_ago(raw["last_contact"] + 10),
        "suicidal_ideation":  raw["ssrs_ideation"],
        "ideation_intensity": (3 if raw["ssrs_intent"] else 1) if raw["ssrs_ideation"] else 0,
        "intent":             raw["ssrs_intent"],
        "plan":               raw["ssrs_plan"],
        "method":             raw["ssrs_method"],
        "history_attempt":    raw["ssrs_hx"],
        "risk_level":         ssrs_risk,
    }

    # Encounters
    encounters = [{
        "encounter_id":    f"ENC{pid}01",
        "admit_date":      days_ago(365 + idx * 3),
        "discharge_date":  None,
        "encounter_type":  "ACT Community" if raw["svc"] == "ACT" else "CSP Outpatient"
    }]

    # Contacts
    last_contact_date = days_ago(raw["last_contact"])
    contacts = [{
        "contact_id":   f"CON{pid}01",
        "contact_date": last_contact_date,
        "contact_type": "Telehealth" if idx % 3 == 0 else "F2F",
        "provider_id":  provider["provider_id"],
        "days_since":   raw["last_contact"],
    }]
    if raw["last_contact"] > 15:
        contacts.append({
            "contact_id":   f"CON{pid}02",
            "contact_date": days_ago(raw["last_contact"] + 14),
            "contact_type": "F2F",
            "provider_id":  provider["provider_id"],
            "days_since":   raw["last_contact"] + 14,
        })

    # Crisis events
    crisis_events = [
        {
            "event_id":      f"CR{pid}{ci + 1:02d}",
            "crisis_date":   days_ago(c["days_ago"]),
            "crisis_type":   CRISIS_TYPES[c["type"]],
            "within_7_days": c["days_ago"] <= 7,
            "within_28_days": c["days_ago"] <= 28,
            "days_since":    c["days_ago"],
        }
        for ci, c in enumerate(raw.get("crisis", []))
    ]

    risk_level = overall_risk(phq9, ssrs)

    return {
        "patient_id":               pid,
        "name":                     raw["name"],
        "date_of_birth":            raw["dob"],
        "diagnosis":                diagnosis,
        "county":                   county,
        "service_type":             raw["svc"],
        "provider_id":              provider["provider_id"],
        "provider_name":            provider["name"],
        "team":                     provider["team"],
        "risk_level":               risk_level,
        "days_since_last_contact":  raw["last_contact"],
        "last_contact_date":        last_contact_date,
        "engagement_flag":          raw["last_contact"] > 30,
        "encounters":               encounters,
        "contacts":                 contacts,
        "phq9":                     phq9,
        "gad7":                     gad7,
        "whodas":                   whodas,
        "ssrs":                     ssrs,
        "kpi":                      raw["kpi"],
        "kpi_compliance_pct":       kpi_compliance_rate(raw["kpi"]),
        "crisis_events":            crisis_events,
        "has_crisis_7d":            any(e["within_7_days"] for e in crisis_events),
        "has_crisis_28d":           any(e["within_28_days"] for e in crisis_events),
    }

# ── Cached export ─────────────────────────────────────────────────────────────

_cache: list[dict] | None = None

def generate_patients() -> list[dict]:
    global _cache
    if _cache is None:
        _cache = [_build_patient(raw, idx) for idx, raw in enumerate(_RAW)]
    return _cache

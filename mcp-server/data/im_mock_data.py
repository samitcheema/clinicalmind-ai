"""
ClinicalMind AI — Internal Medicine Mock Data

Generates 12 IM patients covering diabetes, CKD, and hypertension.
Each patient has longitudinal lab/vitals history for trajectory analysis.

Risk classification:
  High     — latest A1c > 9.0 OR eGFR slope ≤ -5/yr OR latest systolic > 150
  Moderate — latest A1c 7.5-9.0 OR eGFR 30-45 stable OR systolic 140-150
  Low      — A1c < 7.5, eGFR > 45, BP controlled
"""

from datetime import date
from functools import lru_cache

TODAY = date(2026, 3, 21)

IM_PROVIDERS = [
    {"provider_id": "PROV007", "name": "Dr. Linda Park",    "team": "IM-1", "specialty": "IM"},
    {"provider_id": "PROV008", "name": "Dr. Ahmed Hassan",  "team": "IM-1", "specialty": "IM"},
]

def _days_since(iso: str) -> int:
    return (TODAY - date.fromisoformat(iso)).days


@lru_cache(maxsize=1)
def generate_im_patients() -> list[dict]:
    return [

        # ── IM001: Diabetic + Hypertensive, HIGH risk (A1c 9.4, worsening) ────
        {
            "patient_id":        "IM001",
            "name":              "Robert Fitzgerald",
            "date_of_birth":     "1958-04-12",
            "specialty":         "IM",
            "conditions":        ["Type 2 Diabetes (E11.9)", "Hypertension (I10)", "Dyslipidemia (E78.5)"],
            "county":            "Westchester",
            "provider_id":       "PROV007",
            "provider_name":     "Dr. Linda Park",
            "risk_level":        "High",
            "a1c_history": [
                {"date": "2025-03-01", "value": 7.8},
                {"date": "2025-06-01", "value": 8.3},
                {"date": "2025-09-01", "value": 8.9},
                {"date": "2025-12-01", "value": 9.4},
            ],
            "egfr_history": [
                {"date": "2025-01-01", "value": 58},
                {"date": "2025-07-01", "value": 54},
                {"date": "2026-01-01", "value": 51},
            ],
            "bp_history": [
                {"date": "2025-06-01", "systolic": 148, "diastolic": 88},
                {"date": "2025-09-01", "systolic": 152, "diastolic": 92},
                {"date": "2025-12-15", "systolic": 155, "diastolic": 94},
            ],
            "cholesterol_history": [
                {"date": "2025-06-01", "ldl": 148, "hdl": 36, "total": 218},
            ],
            "medications": [
                {"name": "Metformin",    "class": "biguanide",     "dose": "1000mg BID",   "start_date": "2020-01-15"},
                {"name": "Lisinopril",   "class": "ace_inhibitor", "dose": "10mg daily",   "start_date": "2021-03-10"},
                {"name": "Atorvastatin", "class": "statin",        "dose": "40mg daily",   "start_date": "2021-03-10"},
                {"name": "Amlodipine",   "class": "ccb",           "dose": "5mg daily",    "start_date": "2023-06-01"},
            ],
            "preventive_care": {
                "colonoscopy":         {"last_done": "2018-04-01", "due_date": "2028-04-01", "overdue": False},
                "flu_vaccine":         {"last_done": "2024-10-01", "due_date": "2025-10-01", "overdue": True},
                "eye_exam_diabetic":   {"last_done": "2024-01-15", "due_date": "2025-01-15", "overdue": True},
                "microalbumin":        {"last_done": "2024-06-01", "due_date": "2025-06-01", "overdue": True},
                "foot_exam_diabetic":  {"last_done": "2024-06-01", "due_date": "2025-06-01", "overdue": True},
            },
            "last_visit_date":       "2025-12-15",
            "days_since_last_visit": _days_since("2025-12-15"),
        },

        # ── IM002: CKD Stage 3, HIGH risk (eGFR declining fast) ──────────────
        {
            "patient_id":        "IM002",
            "name":              "Gloria Okafor",
            "date_of_birth":     "1962-09-25",
            "specialty":         "IM",
            "conditions":        ["CKD Stage 3 (N18.3)", "Hypertension (I10)", "Type 2 Diabetes (E11.9)"],
            "county":            "Rockland",
            "provider_id":       "PROV008",
            "provider_name":     "Dr. Ahmed Hassan",
            "risk_level":        "High",
            "a1c_history": [
                {"date": "2025-03-01", "value": 7.2},
                {"date": "2025-09-01", "value": 7.5},
                {"date": "2026-01-01", "value": 7.8},
            ],
            "egfr_history": [
                {"date": "2024-01-01", "value": 52},
                {"date": "2024-07-01", "value": 45},
                {"date": "2025-01-01", "value": 38},
                {"date": "2025-07-01", "value": 31},
                {"date": "2026-01-01", "value": 26},
            ],
            "bp_history": [
                {"date": "2025-06-01", "systolic": 142, "diastolic": 86},
                {"date": "2025-09-01", "systolic": 138, "diastolic": 84},
                {"date": "2026-01-15", "systolic": 136, "diastolic": 82},
            ],
            "cholesterol_history": [
                {"date": "2025-09-01", "ldl": 112, "hdl": 44, "total": 188},
            ],
            "medications": [
                {"name": "Lisinopril",   "class": "ace_inhibitor",  "dose": "20mg daily", "start_date": "2019-06-01"},
                {"name": "Furosemide",   "class": "loop_diuretic",  "dose": "40mg daily", "start_date": "2023-01-01"},
                {"name": "Metformin",    "class": "biguanide",      "dose": "500mg BID",  "start_date": "2018-03-01"},
                {"name": "Amlodipine",   "class": "ccb",            "dose": "10mg daily", "start_date": "2020-11-01"},
            ],
            "preventive_care": {
                "colonoscopy":         {"last_done": "2020-02-10", "due_date": "2030-02-10", "overdue": False},
                "flu_vaccine":         {"last_done": "2024-10-15", "due_date": "2025-10-15", "overdue": True},
                "eye_exam_diabetic":   {"last_done": "2025-01-20", "due_date": "2026-01-20", "overdue": True},
                "microalbumin":        {"last_done": "2024-03-01", "due_date": "2025-03-01", "overdue": True},
                "foot_exam_diabetic":  {"last_done": "2024-09-01", "due_date": "2025-09-01", "overdue": True},
            },
            "last_visit_date":       "2026-01-15",
            "days_since_last_visit": _days_since("2026-01-15"),
        },

        # ── IM003: Hypertension only, HIGH risk (BP > 150 consistently) ──────
        {
            "patient_id":        "IM003",
            "name":              "Thomas Byrne",
            "date_of_birth":     "1955-07-19",
            "specialty":         "IM",
            "conditions":        ["Hypertension (I10)", "Dyslipidemia (E78.5)"],
            "county":            "Orange",
            "provider_id":       "PROV007",
            "provider_name":     "Dr. Linda Park",
            "risk_level":        "High",
            "a1c_history":       [],
            "egfr_history": [
                {"date": "2025-01-01", "value": 68},
                {"date": "2025-07-01", "value": 65},
            ],
            "bp_history": [
                {"date": "2025-03-01", "systolic": 158, "diastolic": 96},
                {"date": "2025-06-01", "systolic": 162, "diastolic": 98},
                {"date": "2025-09-01", "systolic": 165, "diastolic": 100},
                {"date": "2025-12-01", "systolic": 160, "diastolic": 97},
            ],
            "cholesterol_history": [
                {"date": "2025-06-01", "ldl": 155, "hdl": 40, "total": 225},
            ],
            "medications": [
                {"name": "Amlodipine",    "class": "ccb",           "dose": "10mg daily",  "start_date": "2020-04-01"},
                {"name": "Lisinopril",    "class": "ace_inhibitor", "dose": "40mg daily",  "start_date": "2020-04-01"},
                {"name": "Hydrochlorothiazide", "class": "thiazide_diuretic", "dose": "25mg daily", "start_date": "2021-08-01"},
                {"name": "Rosuvastatin",  "class": "statin",        "dose": "20mg daily",  "start_date": "2022-01-01"},
            ],
            "preventive_care": {
                "colonoscopy":  {"last_done": "2016-05-01", "due_date": "2026-05-01", "overdue": False},
                "flu_vaccine":  {"last_done": "2023-10-01", "due_date": "2024-10-01", "overdue": True},
            },
            "last_visit_date":       "2025-12-01",
            "days_since_last_visit": _days_since("2025-12-01"),
        },

        # ── IM004: Diabetic, MODERATE risk (A1c 8.2, stable) ─────────────────
        {
            "patient_id":        "IM004",
            "name":              "Carmen Delgado",
            "date_of_birth":     "1969-02-03",
            "specialty":         "IM",
            "conditions":        ["Type 2 Diabetes (E11.9)", "Obesity (E66.9)"],
            "county":            "Dutchess",
            "provider_id":       "PROV007",
            "provider_name":     "Dr. Linda Park",
            "risk_level":        "Moderate",
            "a1c_history": [
                {"date": "2025-03-01", "value": 8.0},
                {"date": "2025-09-01", "value": 8.2},
                {"date": "2026-01-01", "value": 8.1},
            ],
            "egfr_history": [
                {"date": "2025-01-01", "value": 72},
                {"date": "2025-07-01", "value": 70},
            ],
            "bp_history": [
                {"date": "2025-06-01", "systolic": 132, "diastolic": 82},
                {"date": "2025-12-01", "systolic": 130, "diastolic": 80},
            ],
            "cholesterol_history": [
                {"date": "2025-09-01", "ldl": 98, "hdl": 52, "total": 178},
            ],
            "medications": [
                {"name": "Metformin",    "class": "biguanide",  "dose": "1000mg BID",   "start_date": "2017-06-01"},
                {"name": "Semaglutide",  "class": "glp1_ra",   "dose": "1mg weekly",   "start_date": "2023-09-01"},
            ],
            "preventive_care": {
                "colonoscopy":        {"last_done": "2021-03-01", "due_date": "2031-03-01", "overdue": False},
                "flu_vaccine":        {"last_done": "2025-10-01", "due_date": "2026-10-01", "overdue": False},
                "eye_exam_diabetic":  {"last_done": "2025-02-01", "due_date": "2026-02-01", "overdue": True},
                "microalbumin":       {"last_done": "2024-09-01", "due_date": "2025-09-01", "overdue": True},
                "foot_exam_diabetic": {"last_done": "2024-09-01", "due_date": "2025-09-01", "overdue": True},
            },
            "last_visit_date":       "2026-01-01",
            "days_since_last_visit": _days_since("2026-01-01"),
        },

        # ── IM005: CKD Stage 3, MODERATE risk (slow/stable decline, -2.5/yr — intentionally below outlier threshold of -3)
        {
            "patient_id":        "IM005",
            "name":              "Howard Steinberg",
            "date_of_birth":     "1950-11-30",
            "specialty":         "IM",
            "conditions":        ["CKD Stage 3 (N18.3)", "Hypertension (I10)"],
            "county":            "Westchester",
            "provider_id":       "PROV008",
            "provider_name":     "Dr. Ahmed Hassan",
            "risk_level":        "Moderate",
            "a1c_history":       [],
            "egfr_history": [
                {"date": "2024-01-01", "value": 44},
                {"date": "2024-07-01", "value": 42},
                {"date": "2025-01-01", "value": 41},
                {"date": "2025-07-01", "value": 40},
                {"date": "2026-01-01", "value": 39},
            ],
            "bp_history": [
                {"date": "2025-06-01", "systolic": 138, "diastolic": 84},
                {"date": "2025-12-01", "systolic": 136, "diastolic": 82},
            ],
            "cholesterol_history": [
                {"date": "2025-06-01", "ldl": 102, "hdl": 48, "total": 182},
            ],
            "medications": [
                {"name": "Lisinopril",    "class": "ace_inhibitor", "dose": "10mg daily", "start_date": "2018-01-01"},
                {"name": "Atorvastatin",  "class": "statin",        "dose": "20mg daily", "start_date": "2019-03-01"},
            ],
            "preventive_care": {
                "colonoscopy":  {"last_done": "2019-04-01", "due_date": "2029-04-01", "overdue": False},
                "flu_vaccine":  {"last_done": "2025-10-01", "due_date": "2026-10-01", "overdue": False},
            },
            "last_visit_date":       "2026-01-01",
            "days_since_last_visit": _days_since("2026-01-01"),
        },

        # ── IM006: Hypertension, MODERATE risk (BP 140-150) ──────────────────
        {
            "patient_id":        "IM006",
            "name":              "Yolanda Prescott",
            "date_of_birth":     "1972-06-14",
            "specialty":         "IM",
            "conditions":        ["Hypertension (I10)"],
            "county":            "Putnam",
            "provider_id":       "PROV007",
            "provider_name":     "Dr. Linda Park",
            "risk_level":        "Moderate",
            "a1c_history":       [],
            "egfr_history": [
                {"date": "2025-01-01", "value": 74},
                {"date": "2025-07-01", "value": 72},
            ],
            "bp_history": [
                {"date": "2025-03-01", "systolic": 144, "diastolic": 88},
                {"date": "2025-09-01", "systolic": 148, "diastolic": 90},
                {"date": "2026-01-01", "systolic": 146, "diastolic": 89},
            ],
            "cholesterol_history": [
                {"date": "2025-06-01", "ldl": 118, "hdl": 56, "total": 198},
            ],
            "medications": [
                {"name": "Losartan",     "class": "arb",   "dose": "50mg daily", "start_date": "2021-02-01"},
                {"name": "Amlodipine",   "class": "ccb",   "dose": "5mg daily",  "start_date": "2022-08-01"},
            ],
            "preventive_care": {
                "colonoscopy":  {"last_done": None,         "due_date": "2022-06-14", "overdue": True},
                "flu_vaccine":  {"last_done": "2025-10-01", "due_date": "2026-10-01", "overdue": False},
                "mammogram":    {"last_done": "2024-07-01", "due_date": "2025-07-01", "overdue": True},
            },
            "last_visit_date":       "2026-01-01",
            "days_since_last_visit": _days_since("2026-01-01"),
        },

        # ── IM007: Diabetic, MODERATE risk (A1c 7.6, trend flat) ─────────────
        {
            "patient_id":        "IM007",
            "name":              "Darren Osei",
            "date_of_birth":     "1975-08-22",
            "specialty":         "IM",
            "conditions":        ["Type 2 Diabetes (E11.9)", "Hypertension (I10)"],
            "county":            "Rockland",
            "provider_id":       "PROV008",
            "provider_name":     "Dr. Ahmed Hassan",
            "risk_level":        "Moderate",
            "a1c_history": [
                {"date": "2025-01-01", "value": 7.8},
                {"date": "2025-07-01", "value": 7.6},
                {"date": "2026-01-01", "value": 7.6},
            ],
            "egfr_history": [
                {"date": "2025-01-01", "value": 65},
                {"date": "2025-07-01", "value": 63},
            ],
            "bp_history": [
                {"date": "2025-06-01", "systolic": 136, "diastolic": 84},
                {"date": "2025-12-01", "systolic": 134, "diastolic": 82},
            ],
            "cholesterol_history": [
                {"date": "2025-09-01", "ldl": 88, "hdl": 50, "total": 168},
            ],
            "medications": [
                {"name": "Metformin",    "class": "biguanide",     "dose": "500mg BID",  "start_date": "2022-03-01"},
                {"name": "Lisinopril",   "class": "ace_inhibitor", "dose": "5mg daily",  "start_date": "2023-01-01"},
            ],
            "preventive_care": {
                "colonoscopy":        {"last_done": None,         "due_date": "2025-08-22", "overdue": True},
                "flu_vaccine":        {"last_done": "2025-10-01", "due_date": "2026-10-01", "overdue": False},
                "eye_exam_diabetic":  {"last_done": "2025-03-01", "due_date": "2026-03-01", "overdue": True},
                "microalbumin":       {"last_done": "2025-01-01", "due_date": "2026-01-01", "overdue": True},
                "foot_exam_diabetic": {"last_done": "2025-01-01", "due_date": "2026-01-01", "overdue": True},
            },
            "last_visit_date":       "2026-01-01",
            "days_since_last_visit": _days_since("2026-01-01"),
        },

        # ── IM008: CKD Stage 2, LOW risk (near-flat decline, will NOT appear in CKD outlier panel)
        {
            "patient_id":        "IM008",
            "name":              "Patricia Huang",
            "date_of_birth":     "1967-12-04",
            "specialty":         "IM",
            "conditions":        ["CKD Stage 2 (N18.2)", "Hypertension (I10)"],
            "county":            "Orange",
            "provider_id":       "PROV008",
            "provider_name":     "Dr. Ahmed Hassan",
            "risk_level":        "Low",
            "a1c_history":       [],
            "egfr_history": [
                {"date": "2024-01-01", "value": 68},
                {"date": "2024-07-01", "value": 67},
                {"date": "2025-01-01", "value": 67},
                {"date": "2025-07-01", "value": 66},
            ],
            "bp_history": [
                {"date": "2025-06-01", "systolic": 128, "diastolic": 78},
                {"date": "2025-12-01", "systolic": 126, "diastolic": 76},
            ],
            "cholesterol_history": [
                {"date": "2025-06-01", "ldl": 90, "hdl": 62, "total": 172},
            ],
            "medications": [
                {"name": "Lisinopril",  "class": "ace_inhibitor", "dose": "5mg daily",  "start_date": "2020-01-01"},
            ],
            "preventive_care": {
                "colonoscopy":  {"last_done": "2022-09-01", "due_date": "2032-09-01", "overdue": False},
                "flu_vaccine":  {"last_done": "2025-10-01", "due_date": "2026-10-01", "overdue": False},
                "mammogram":    {"last_done": "2025-01-01", "due_date": "2026-01-01", "overdue": True},
            },
            "last_visit_date":       "2025-12-01",
            "days_since_last_visit": _days_since("2025-12-01"),
        },

        # ── IM009: Diabetic, LOW risk (A1c 6.9, well-controlled — will NOT appear in diabetes outlier panel)
        {
            "patient_id":        "IM009",
            "name":              "Samuel Adeyemi",
            "date_of_birth":     "1980-05-17",
            "specialty":         "IM",
            "conditions":        ["Type 2 Diabetes (E11.9)"],
            "county":            "Dutchess",
            "provider_id":       "PROV007",
            "provider_name":     "Dr. Linda Park",
            "risk_level":        "Low",
            "a1c_history": [
                {"date": "2025-01-01", "value": 7.1},
                {"date": "2025-07-01", "value": 6.9},
                {"date": "2026-01-01", "value": 6.8},
            ],
            "egfr_history": [
                {"date": "2025-01-01", "value": 82},
            ],
            "bp_history": [
                {"date": "2025-06-01", "systolic": 122, "diastolic": 76},
                {"date": "2025-12-01", "systolic": 120, "diastolic": 74},
            ],
            "cholesterol_history": [
                {"date": "2025-06-01", "ldl": 78, "hdl": 65, "total": 158},
            ],
            "medications": [
                {"name": "Metformin",  "class": "biguanide", "dose": "500mg daily", "start_date": "2021-01-01"},
            ],
            "preventive_care": {
                "colonoscopy":        {"last_done": None,         "due_date": "2030-05-17", "overdue": False},
                "flu_vaccine":        {"last_done": "2025-10-01", "due_date": "2026-10-01", "overdue": False},
                "eye_exam_diabetic":  {"last_done": "2025-02-01", "due_date": "2026-02-01", "overdue": True},
                "microalbumin":       {"last_done": "2025-01-01", "due_date": "2026-01-01", "overdue": True},
                "foot_exam_diabetic": {"last_done": "2025-01-01", "due_date": "2026-01-01", "overdue": True},
            },
            "last_visit_date":       "2026-01-01",
            "days_since_last_visit": _days_since("2026-01-01"),
        },

        # ── IM010: Hypertension, LOW risk (BP well-controlled on meds — will NOT appear in HTN panel)
        {
            "patient_id":        "IM010",
            "name":              "Evelyn Kowalski",
            "date_of_birth":     "1963-03-28",
            "specialty":         "IM",
            "conditions":        ["Hypertension (I10)", "Dyslipidemia (E78.5)"],
            "county":            "Putnam",
            "provider_id":       "PROV008",
            "provider_name":     "Dr. Ahmed Hassan",
            "risk_level":        "Low",
            "a1c_history":       [],
            "egfr_history": [
                {"date": "2025-01-01", "value": 78},
            ],
            "bp_history": [
                {"date": "2025-03-01", "systolic": 128, "diastolic": 80},
                {"date": "2025-09-01", "systolic": 126, "diastolic": 78},
                {"date": "2026-01-01", "systolic": 124, "diastolic": 76},
            ],
            "cholesterol_history": [
                {"date": "2025-06-01", "ldl": 82, "hdl": 58, "total": 162},
            ],
            "medications": [
                {"name": "Amlodipine",   "class": "ccb",   "dose": "5mg daily",  "start_date": "2019-07-01"},
                {"name": "Rosuvastatin", "class": "statin", "dose": "10mg daily", "start_date": "2020-01-01"},
            ],
            "preventive_care": {
                "colonoscopy":  {"last_done": "2020-01-01", "due_date": "2030-01-01", "overdue": False},
                "flu_vaccine":  {"last_done": "2025-10-01", "due_date": "2026-10-01", "overdue": False},
                "mammogram":    {"last_done": "2025-06-01", "due_date": "2026-06-01", "overdue": False},
            },
            "last_visit_date":       "2026-01-01",
            "days_since_last_visit": _days_since("2026-01-01"),
        },

        # ── IM011: Diabetic + CKD Stage 4, HIGH risk (A1c 9.8, eGFR 24, rapid decline)
        {
            "patient_id":        "IM011",
            "name":              "Walter Ndiaye",
            "date_of_birth":     "1948-01-10",
            "specialty":         "IM",
            "conditions":        ["Type 2 Diabetes (E11.9)", "CKD Stage 4 (N18.4)", "Hypertension (I10)"],
            "county":            "Westchester",
            "provider_id":       "PROV008",
            "provider_name":     "Dr. Ahmed Hassan",
            "risk_level":        "High",
            "a1c_history": [
                {"date": "2025-01-01", "value": 8.8},
                {"date": "2025-07-01", "value": 9.4},
                {"date": "2026-01-01", "value": 9.8},
            ],
            "egfr_history": [
                {"date": "2023-01-01", "value": 38},
                {"date": "2024-01-01", "value": 32},
                {"date": "2025-01-01", "value": 28},
                {"date": "2026-01-01", "value": 24},
            ],
            "bp_history": [
                {"date": "2025-06-01", "systolic": 146, "diastolic": 90},
                {"date": "2025-09-01", "systolic": 150, "diastolic": 92},
                {"date": "2026-01-01", "systolic": 154, "diastolic": 94},
            ],
            "cholesterol_history": [
                {"date": "2025-09-01", "ldl": 128, "hdl": 34, "total": 202},
            ],
            "medications": [
                {"name": "Insulin Glargine",  "class": "insulin",       "dose": "20 units nightly", "start_date": "2022-01-01"},
                {"name": "Lisinopril",        "class": "ace_inhibitor", "dose": "40mg daily",       "start_date": "2018-01-01"},
                {"name": "Furosemide",        "class": "loop_diuretic", "dose": "80mg daily",       "start_date": "2023-06-01"},
                {"name": "Atorvastatin",      "class": "statin",        "dose": "80mg daily",       "start_date": "2020-01-01"},
            ],
            "preventive_care": {
                "colonoscopy":        {"last_done": "2018-01-01", "due_date": "2028-01-01", "overdue": False},
                "flu_vaccine":        {"last_done": "2023-10-01", "due_date": "2024-10-01", "overdue": True},
                "eye_exam_diabetic":  {"last_done": "2023-06-01", "due_date": "2024-06-01", "overdue": True},
                "microalbumin":       {"last_done": "2025-01-01", "due_date": "2026-01-01", "overdue": True},
                "foot_exam_diabetic": {"last_done": "2023-09-01", "due_date": "2024-09-01", "overdue": True},
            },
            "last_visit_date":       "2026-01-01",
            "days_since_last_visit": _days_since("2026-01-01"),
        },

        # ── IM012: Dyslipidemia only, LOW risk ────────────────────────────────
        {
            "patient_id":        "IM012",
            "name":              "Rachel Bloom",
            "date_of_birth":     "1984-10-05",
            "specialty":         "IM",
            "conditions":        ["Dyslipidemia (E78.5)"],
            "county":            "Orange",
            "provider_id":       "PROV007",
            "provider_name":     "Dr. Linda Park",
            "risk_level":        "Low",
            "a1c_history":       [],
            "egfr_history": [
                {"date": "2025-01-01", "value": 90},
            ],
            "bp_history": [
                {"date": "2025-06-01", "systolic": 118, "diastolic": 72},
                {"date": "2025-12-01", "systolic": 116, "diastolic": 70},
            ],
            "cholesterol_history": [
                {"date": "2025-01-01", "ldl": 168, "hdl": 44, "total": 238},
                {"date": "2025-09-01", "ldl": 105, "hdl": 48, "total": 185},
            ],
            "medications": [
                {"name": "Atorvastatin", "class": "statin", "dose": "40mg daily", "start_date": "2025-01-15"},
            ],
            "preventive_care": {
                "colonoscopy":  {"last_done": None,         "due_date": "2034-10-05", "overdue": False},
                "flu_vaccine":  {"last_done": "2025-10-01", "due_date": "2026-10-01", "overdue": False},
                "mammogram":    {"last_done": "2024-11-01", "due_date": "2025-11-01", "overdue": True},
            },
            "last_visit_date":       "2025-09-01",
            "days_since_last_visit": _days_since("2025-09-01"),
        },
    ]

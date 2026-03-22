# Internal Medicine Module — Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a parallel Internal Medicine data layer (mock data, adapter, MCP tools) alongside the existing BH module, gated by a `specialty` column on providers.

**Architecture:** The existing BH tools are unchanged. IM gets its own data module (`im_mock_data.py`), adapter (`im_mock_adapter.py`), and 4 MCP tools in `server.py`. A `specialty` column is added to the `providers` schema so downstream code can route by specialty. Frontend dashboard routing is a separate follow-on plan.

**Tech Stack:** Python 3.12, FastMCP, pytest 8, existing adapter pattern in `mcp-server/`

---

## Scope Note

This plan covers the **backend only**: schema, mock data, adapter, MCP tools, and tests. The React dashboard routing (showing different UIs per provider specialty) is a separate plan — `2026-03-21-im-dashboard-routing.md`.

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `pipeline/supabase_schema.sql` | Add `specialty TEXT DEFAULT 'BH'` to providers table |
| Modify | `mcp-server/data/mock_data.py` | Add `"specialty": "BH"` to all 6 BH providers in `PROVIDERS` |
| Create | `mcp-server/data/im_mock_data.py` | 12 IM patients, 2 IM providers, helper functions |
| Create | `mcp-server/requirements-dev.txt` | pytest dev dependency (separate from production deps) |
| Create | `mcp-server/pytest.ini` | testpaths + pythonpath config |
| Create | `mcp-server/tests/__init__.py` | empty, marks tests/ as package |
| Create | `mcp-server/tests/test_im_adapter.py` | 10 pytest tests for all 4 IM adapter functions |
| Create | `mcp-server/adapter/im_mock_adapter.py` | 4 adapter functions: get_im_patients, get_im_patient_detail, get_chronic_disease_panel, get_preventive_care_gaps |
| Modify | `mcp-server/server.py` | Add IM adapter imports, 4 MCP tools, 1 resource, 1 prompt |

---

## Task 1: Add specialty column to providers schema

**Files:**
- Modify: `pipeline/supabase_schema.sql`

- [ ] **Step 1: Edit the providers CREATE TABLE block**

Find the `providers` table definition and add the `specialty` column:

```sql
CREATE TABLE IF NOT EXISTS providers (
    provider_id  TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    team         TEXT NOT NULL,
    specialty    TEXT NOT NULL DEFAULT 'BH',   -- BH | IM
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
```

- [ ] **Step 2: Commit**

```bash
git add pipeline/supabase_schema.sql
git commit -m "feat: add specialty column to providers schema"
```

---

## Task 2: Tag existing BH providers with specialty

**Files:**
- Modify: `mcp-server/data/mock_data.py`

- [ ] **Step 1: Add `"specialty": "BH"` to all 6 provider dicts**

Find the `PROVIDERS` list (around line 40) and update each dict:

```python
PROVIDERS = [
    {"provider_id": "PROV001", "name": "Dr. Emma Chen",       "team": "ACT-1", "specialty": "BH"},
    {"provider_id": "PROV002", "name": "Dr. Marcus Williams", "team": "ACT-1", "specialty": "BH"},
    {"provider_id": "PROV003", "name": "Dr. Priya Sharma",    "team": "ACT-2", "specialty": "BH"},
    {"provider_id": "PROV004", "name": "Dr. James O'Brien",   "team": "ACT-2", "specialty": "BH"},
    {"provider_id": "PROV005", "name": "Dr. Sarah Nakamura",  "team": "CSP-1", "specialty": "BH"},
    {"provider_id": "PROV006", "name": "Dr. Robert Kim",      "team": "CSP-1", "specialty": "BH"},
]
```

- [ ] **Step 2: Commit**

```bash
git add mcp-server/data/mock_data.py
git commit -m "feat: tag BH mock providers with specialty field"
```

---

## Task 3: Create IM mock data module

**Files:**
- Create: `mcp-server/data/im_mock_data.py`

- [ ] **Step 1: Write `im_mock_data.py`**

```python
"""
ClinicalMind AI — Internal Medicine Mock Data

Generates 12 IM patients covering diabetes, CKD, and hypertension.
Each patient has longitudinal lab/vitals history for trajectory analysis.

Risk classification:
  High     — latest A1c > 9.0 OR eGFR slope ≤ -5/yr OR latest systolic > 150
  Moderate — latest A1c 7.5-9.0 OR eGFR 30-45 stable OR systolic 140-150
  Low      — A1c < 7.5, eGFR > 45, BP controlled
"""

from datetime import date, timedelta
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
                "flu_vaccine":         {"last_done": "2024-10-01", "due_date": "2025-10-01", "overdue": False},
                "eye_exam_diabetic":   {"last_done": "2024-01-15", "due_date": "2025-01-15", "overdue": True},
                "microalbumin":        {"last_done": "2024-06-01", "due_date": "2025-06-01", "overdue": False},
                "foot_exam_diabetic":  {"last_done": "2024-06-01", "due_date": "2025-06-01", "overdue": False},
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
                "flu_vaccine":         {"last_done": "2024-10-15", "due_date": "2025-10-15", "overdue": False},
                "eye_exam_diabetic":   {"last_done": "2025-01-20", "due_date": "2026-01-20", "overdue": False},
                "microalbumin":        {"last_done": "2024-03-01", "due_date": "2025-03-01", "overdue": True},
                "foot_exam_diabetic":  {"last_done": "2024-09-01", "due_date": "2025-09-01", "overdue": False},
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
                "eye_exam_diabetic":  {"last_done": "2025-02-01", "due_date": "2026-02-01", "overdue": False},
                "microalbumin":       {"last_done": "2024-09-01", "due_date": "2025-09-01", "overdue": False},
                "foot_exam_diabetic": {"last_done": "2024-09-01", "due_date": "2025-09-01", "overdue": False},
            },
            "last_visit_date":       "2026-01-01",
            "days_since_last_visit": _days_since("2026-01-01"),
        },

        # ── IM005: CKD Stage 3, MODERATE risk (stable decline) ───────────────
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
                "eye_exam_diabetic":  {"last_done": "2025-03-01", "due_date": "2026-03-01", "overdue": False},
                "microalbumin":       {"last_done": "2025-01-01", "due_date": "2026-01-01", "overdue": False},
                "foot_exam_diabetic": {"last_done": "2025-01-01", "due_date": "2026-01-01", "overdue": False},
            },
            "last_visit_date":       "2026-01-01",
            "days_since_last_visit": _days_since("2026-01-01"),
        },

        # ── IM008: CKD Stage 2, LOW risk ─────────────────────────────────────
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
                "mammogram":    {"last_done": "2025-01-01", "due_date": "2026-01-01", "overdue": False},
            },
            "last_visit_date":       "2025-12-01",
            "days_since_last_visit": _days_since("2025-12-01"),
        },

        # ── IM009: Diabetic, LOW risk (A1c 6.9, well-controlled) ─────────────
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
                "eye_exam_diabetic":  {"last_done": "2025-02-01", "due_date": "2026-02-01", "overdue": False},
                "microalbumin":       {"last_done": "2025-01-01", "due_date": "2026-01-01", "overdue": False},
                "foot_exam_diabetic": {"last_done": "2025-01-01", "due_date": "2026-01-01", "overdue": False},
            },
            "last_visit_date":       "2026-01-01",
            "days_since_last_visit": _days_since("2026-01-01"),
        },

        # ── IM010: Hypertension, LOW risk (BP well-controlled on meds) ────────
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

        # ── IM011: Diabetic + CKD, HIGH risk (A1c 9.8, eGFR 24, rapid decline)
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
                "microalbumin":       {"last_done": "2025-01-01", "due_date": "2026-01-01", "overdue": False},
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
                "mammogram":    {"last_done": "2024-11-01", "due_date": "2025-11-01", "overdue": False},
            },
            "last_visit_date":       "2025-09-01",
            "days_since_last_visit": _days_since("2025-09-01"),
        },
    ]
```

- [ ] **Step 2: Commit**

```bash
git add mcp-server/data/im_mock_data.py
git commit -m "feat: add IM mock data module with 12 patients"
```

---

## Task 4: Set up test infrastructure

**Files:**
- Modify: `mcp-server/requirements.txt`
- Create: `mcp-server/pytest.ini`
- Create: `mcp-server/tests/__init__.py`

- [ ] **Step 1: Create `requirements-dev.txt`**

Create `mcp-server/requirements-dev.txt`:

```
pytest>=8.0.0
```

pytest is a dev-only tool — it does not belong in `requirements.txt` alongside production deps.

- [ ] **Step 2: Create pytest.ini**

```ini
[pytest]
testpaths = tests
pythonpath = .
```

- [ ] **Step 3: Create empty `tests/__init__.py`**

```python
```

(empty file — marks directory as importable package)

- [ ] **Step 4: Commit**

```bash
git add mcp-server/requirements-dev.txt mcp-server/pytest.ini mcp-server/tests/__init__.py
git commit -m "chore: add pytest test infrastructure"
```

---

## Task 5: Write failing tests for IM adapter

**Files:**
- Create: `mcp-server/tests/test_im_adapter.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for the IM mock adapter — run from mcp-server/ directory."""

import pytest
from adapter.im_mock_adapter import (
    get_im_patients,
    get_im_patient_detail,
    get_chronic_disease_panel,
    get_preventive_care_gaps,
)


# ── get_im_patients ───────────────────────────────────────────────────────────

def test_get_im_patients_returns_all():
    result = get_im_patients()
    assert len(result) == 12
    for p in result:
        assert p["specialty"] == "IM"


def test_get_im_patients_has_expected_keys():
    result = get_im_patients()
    required = {"patient_id", "name", "specialty", "risk_level", "provider_name",
                "conditions", "county", "last_visit_date", "days_since_last_visit"}
    for p in result:
        assert required.issubset(p.keys()), f"Missing keys in {p['patient_id']}: {required - p.keys()}"


def test_get_im_patients_filter_by_risk():
    high = get_im_patients(risk_level="High")
    assert all(p["risk_level"] == "High" for p in high)
    assert len(high) == 4  # IM001, IM002, IM003, IM011


def test_get_im_patients_filter_by_condition():
    diabetics = get_im_patients(condition="diabetes")
    assert all(
        any("Diabetes" in c for c in p["conditions"])
        for p in diabetics
    )
    assert len(diabetics) == 6  # IM001, IM002, IM004, IM007, IM009, IM011


def test_get_im_patients_filter_by_provider():
    result = get_im_patients(provider="PROV007")
    assert all(p["provider_id"] == "PROV007" for p in result)
    assert len(result) > 0


# ── get_im_patient_detail ─────────────────────────────────────────────────────

def test_get_im_patient_detail_known_patient():
    p = get_im_patient_detail("IM001")
    assert p is not None
    assert p["patient_id"] == "IM001"
    assert len(p["a1c_history"]) == 4
    assert len(p["egfr_history"]) >= 1
    assert len(p["medications"]) >= 1
    assert "preventive_care" in p


def test_get_im_patient_detail_unknown_returns_none():
    assert get_im_patient_detail("DOESNOTEXIST") is None


# ── get_chronic_disease_panel ─────────────────────────────────────────────────

def test_get_chronic_disease_panel_diabetes():
    result = get_chronic_disease_panel("diabetes")
    # All returned patients should have latest A1c > 8.0
    for p in result:
        assert p["latest_a1c"] > 8.0, f"{p['patient_id']} has A1c {p['latest_a1c']}"
    # IM009 (A1c 6.8) should NOT appear
    ids = [p["patient_id"] for p in result]
    assert "IM009" not in ids


def test_get_chronic_disease_panel_ckd():
    result = get_chronic_disease_panel("ckd")
    # All should have a declining eGFR slope (≤ -3/yr)
    for p in result:
        assert p["egfr_slope"] <= -3, f"{p['patient_id']} slope {p['egfr_slope']}"
    # IM008 (near-flat eGFR decline) should NOT appear
    ids = [p["patient_id"] for p in result]
    assert "IM008" not in ids


def test_get_chronic_disease_panel_hypertension():
    result = get_chronic_disease_panel("hypertension")
    # All should have latest systolic > 140
    for p in result:
        assert p["latest_systolic"] > 140, f"{p['patient_id']} BP {p['latest_systolic']}"
    # IM010 (BP 124) should NOT appear
    ids = [p["patient_id"] for p in result]
    assert "IM010" not in ids


# ── get_preventive_care_gaps ──────────────────────────────────────────────────

def test_get_preventive_care_gaps_returns_only_overdue():
    result = get_preventive_care_gaps()
    for entry in result:
        assert len(entry["overdue_items"]) > 0, f"{entry['patient_id']} has no overdue items"


def test_get_preventive_care_gaps_filter_by_type():
    result = get_preventive_care_gaps(gap_type="flu_vaccine")
    for entry in result:
        assert any(item["type"] == "flu_vaccine" for item in entry["overdue_items"])
```

- [ ] **Step 2: Run tests and confirm they all fail (module doesn't exist yet)**

```bash
cd mcp-server && python -m pytest tests/test_im_adapter.py -v
```

Expected: `ModuleNotFoundError: No module named 'adapter.im_mock_adapter'`

- [ ] **Step 3: Commit the failing tests**

```bash
git add mcp-server/tests/test_im_adapter.py
git commit -m "test: add failing tests for IM adapter (TDD)"
```

---

## Task 6: Implement the IM mock adapter

**Files:**
- Create: `mcp-server/adapter/im_mock_adapter.py`

- [ ] **Step 1: Write the adapter**

```python
"""
ClinicalMind AI — Internal Medicine Mock Adapter

Implements the IM adapter interface over im_mock_data.

Interface:
  get_im_patients(risk_level, condition, provider)
  get_im_patient_detail(patient_id)
  get_chronic_disease_panel(condition)
  get_preventive_care_gaps(gap_type)
"""

from datetime import date
from data.im_mock_data import generate_im_patients


def _patients() -> list[dict]:
    return generate_im_patients()


def _latest(history: list[dict], key: str):
    """Return the value of `key` from the most recent history entry, or None."""
    if not history:
        return None
    return history[-1][key]


def _slope(history: list[dict], value_key: str) -> float | None:
    """Linear slope in units/year between first and last history entries."""
    if len(history) < 2:
        return None
    first, last = history[0], history[-1]
    days = (date.fromisoformat(last["date"]) - date.fromisoformat(first["date"])).days
    if days == 0:
        return None
    return round((last[value_key] - first[value_key]) / days * 365, 1)


# ── 1. get_im_patients ────────────────────────────────────────────────────────

def get_im_patients(
    risk_level: str | None = None,
    condition: str | None = None,
    provider: str | None = None,
) -> list[dict]:
    lst = _patients()

    if risk_level:
        rl = risk_level.lower()
        lst = [p for p in lst if p["risk_level"].lower() == rl]

    if condition:
        c = condition.lower()
        lst = [
            p for p in lst
            if any(c in cond.lower() for cond in p["conditions"])
        ]

    if provider:
        pv = provider.lower()
        lst = [
            p for p in lst
            if pv in p["provider_name"].lower() or p["provider_id"].lower() == pv
        ]

    return [
        {
            "patient_id":            p["patient_id"],
            "name":                  p["name"],
            "date_of_birth":         p["date_of_birth"],
            "specialty":             p["specialty"],
            "conditions":            p["conditions"],
            "county":                p["county"],
            "provider_id":           p["provider_id"],
            "provider_name":         p["provider_name"],
            "risk_level":            p["risk_level"],
            "latest_a1c":            _latest(p["a1c_history"], "value"),
            "latest_egfr":           _latest(p["egfr_history"], "value"),
            "latest_systolic":       _latest(p["bp_history"], "systolic"),
            "latest_diastolic":      _latest(p["bp_history"], "diastolic"),
            "last_visit_date":       p["last_visit_date"],
            "days_since_last_visit": p["days_since_last_visit"],
            "medication_count":      len(p["medications"]),
        }
        for p in lst
    ]


# ── 2. get_im_patient_detail ──────────────────────────────────────────────────

def get_im_patient_detail(patient_id: str) -> dict | None:
    return next(
        (p for p in _patients() if p["patient_id"].lower() == patient_id.lower()),
        None,
    )


# ── 3. get_chronic_disease_panel ──────────────────────────────────────────────

def get_chronic_disease_panel(
    condition: str,
) -> list[dict]:
    """
    Returns patients with poorly controlled chronic disease metrics.

    diabetes    — patients with latest A1c > 8.0
    ckd         — patients with eGFR slope ≤ -3 units/year
    hypertension — patients with latest systolic > 140
    """
    all_p = _patients()
    c = condition.lower()
    result = []

    for p in all_p:
        if c == "diabetes":
            if not any("Diabetes" in cond for cond in p["conditions"]):
                continue
            latest_a1c = _latest(p["a1c_history"], "value")
            if latest_a1c is None or latest_a1c <= 8.0:
                continue
            a1c_slope = _slope(p["a1c_history"], "value")
            result.append({
                "patient_id":    p["patient_id"],
                "name":          p["name"],
                "risk_level":    p["risk_level"],
                "provider_name": p["provider_name"],
                "conditions":    p["conditions"],
                "latest_a1c":    latest_a1c,
                "a1c_slope":     a1c_slope,
                "a1c_history":   p["a1c_history"],
                "medications":   p["medications"],
            })

        elif c == "ckd":
            if not any("CKD" in cond for cond in p["conditions"]):
                continue
            egfr_slope = _slope(p["egfr_history"], "value")
            latest_egfr = _latest(p["egfr_history"], "value")
            if egfr_slope is None or egfr_slope > -3:
                continue
            result.append({
                "patient_id":    p["patient_id"],
                "name":          p["name"],
                "risk_level":    p["risk_level"],
                "provider_name": p["provider_name"],
                "conditions":    p["conditions"],
                "latest_egfr":   latest_egfr,
                "egfr_slope":    egfr_slope,
                "egfr_history":  p["egfr_history"],
                "medications":   p["medications"],
            })

        elif c == "hypertension":
            if not any("Hypertension" in cond for cond in p["conditions"]):
                continue
            latest_systolic = _latest(p["bp_history"], "systolic")
            if latest_systolic is None or latest_systolic <= 140:
                continue
            bp_slope = _slope(p["bp_history"], "systolic")
            result.append({
                "patient_id":      p["patient_id"],
                "name":            p["name"],
                "risk_level":      p["risk_level"],
                "provider_name":   p["provider_name"],
                "conditions":      p["conditions"],
                "latest_systolic": latest_systolic,
                "latest_diastolic": _latest(p["bp_history"], "diastolic"),
                "bp_slope":        bp_slope,
                "bp_history":      p["bp_history"],
                "medications":     p["medications"],
            })

    return sorted(result, key=lambda x: x.get("risk_level") != "High")


# ── 4. get_preventive_care_gaps ───────────────────────────────────────────────

def get_preventive_care_gaps(gap_type: str | None = None) -> list[dict]:
    """
    Returns patients with overdue preventive care items.
    gap_type filters to a specific item (e.g. "flu_vaccine", "colonoscopy",
    "mammogram", "eye_exam_diabetic", "microalbumin", "foot_exam_diabetic").
    Omit for all overdue items.
    """
    all_p = _patients()
    result = []

    for p in all_p:
        overdue = [
            {
                "type":      item_name,
                "last_done": item["last_done"],
                "due_date":  item["due_date"],
            }
            for item_name, item in p["preventive_care"].items()
            if item["overdue"] and (gap_type is None or item_name == gap_type)
        ]
        if overdue:
            result.append({
                "patient_id":    p["patient_id"],
                "name":          p["name"],
                "risk_level":    p["risk_level"],
                "provider_name": p["provider_name"],
                "conditions":    p["conditions"],
                "overdue_items": overdue,
                "overdue_count": len(overdue),
            })

    return sorted(result, key=lambda x: -x["overdue_count"])
```

- [ ] **Step 2: Run tests — all should pass**

```bash
cd mcp-server && python -m pytest tests/test_im_adapter.py -v
```

Expected: `10 passed`

- [ ] **Step 3: Commit**

```bash
git add mcp-server/adapter/im_mock_adapter.py
git commit -m "feat: implement IM mock adapter with 4 query functions"
```

---

## Task 7: Add IM tools to the MCP server

**Files:**
- Modify: `mcp-server/server.py`

- [ ] **Step 1: Add IM adapter imports**

After the BH adapter import block (around line 63), add:

```python
from adapter.im_mock_adapter import (
    get_im_patients            as _get_im_patients,
    get_im_patient_detail      as _get_im_patient_detail,
    get_chronic_disease_panel  as _get_chronic_disease_panel,
    get_preventive_care_gaps   as _get_preventive_care_gaps,
)
```

- [ ] **Step 2: Add 4 IM tools**

Append to `server.py` before the `# ── Resource` block:

```python
# ── Tool 8: get_im_patients ───────────────────────────────────────────────────

@mcp.tool()
def get_im_patients(
    risk_level: Annotated[
        Literal["High", "Moderate", "Low"] | None,
        "Filter by risk level: High, Moderate, or Low",
    ] = None,
    condition: Annotated[
        Literal["diabetes", "ckd", "hypertension"] | None,
        "Filter by chronic condition. Options: diabetes, ckd, hypertension",
    ] = None,
    provider: Annotated[
        str | None,
        "Filter by provider name (partial match) or provider ID",
    ] = None,
) -> dict:
    """Returns Internal Medicine patient panel with summary chronic disease data.
    Optionally filter by risk level, condition, or provider."""
    result = _get_im_patients(risk_level=risk_level, condition=condition, provider=provider)
    return {
        "total":    len(result),
        "filters":  {"risk_level": risk_level, "condition": condition, "provider": provider},
        "patients": result,
    }


# ── Tool 9: get_im_patient_detail ─────────────────────────────────────────────

@mcp.tool()
def get_im_patient_detail(
    patient_id: Annotated[
        str,
        "The IM patient ID (e.g. IM001). Use get_im_patients to look up IDs.",
    ],
) -> dict:
    """Returns the complete IM record for one patient — all lab histories
    (A1c, eGFR, BP, cholesterol), medications, preventive care status,
    and longitudinal trends."""
    result = _get_im_patient_detail(patient_id)
    if result is None:
        return {"error": f"No IM patient found with ID: {patient_id}"}
    return result


# ── Tool 10: get_chronic_disease_panel ────────────────────────────────────────

@mcp.tool()
def get_chronic_disease_panel(
    condition: Annotated[
        Literal["diabetes", "ckd", "hypertension"],
        (
            'Chronic condition to surface outliers for. '
            '"diabetes" = latest A1c > 8.0; '
            '"ckd" = eGFR declining ≥ 3 units/year; '
            '"hypertension" = latest systolic BP > 140.'
        ),
    ],
) -> dict:
    """Returns IM patients with poorly controlled chronic disease metrics,
    ranked by risk level. Includes longitudinal history and computed trend slopes."""
    result = _get_chronic_disease_panel(condition=condition)
    return {
        "condition":     condition,
        "total_outliers": len(result),
        "patients":       result,
    }


# ── Tool 11: get_preventive_care_gaps ─────────────────────────────────────────

@mcp.tool()
def get_preventive_care_gaps(
    gap_type: Annotated[
        str | None,
        (
            "Specific preventive care item to filter by. "
            "Options: flu_vaccine, colonoscopy, mammogram, eye_exam_diabetic, "
            "microalbumin, foot_exam_diabetic. Omit for all gaps."
        ),
    ] = None,
) -> dict:
    """Returns IM patients who are overdue for preventive care items.
    Sorted by number of overdue items descending. Omit gap_type for all gaps."""
    result = _get_preventive_care_gaps(gap_type=gap_type)
    return {
        "gap_type_filter":             gap_type or "all",
        "total_patients_with_gaps":    len(result),
        "patients":                    result,
    }
```

- [ ] **Step 3: Add IM cohort resource**

After the existing `cohort_summary` resource, add:

```python
@mcp.resource("clinicalmind://im-cohort-summary")
def im_cohort_summary() -> str:
    """Live snapshot of the IM panel — risk breakdown, condition mix,
    and preventive care gap count."""
    patients = _get_im_patients()
    total = len(patients)

    risk_counts = {"High": 0, "Moderate": 0, "Low": 0}
    for p in patients:
        risk_counts[p["risk_level"]] = risk_counts.get(p["risk_level"], 0) + 1

    gaps = _get_preventive_care_gaps()

    return (
        f"IM panel snapshot — {total} patients total\n"
        f"Risk: {risk_counts['High']} High / {risk_counts['Moderate']} Moderate / {risk_counts['Low']} Low\n"
        f"Patients with preventive care gaps: {len(gaps)}"
    )
```

- [ ] **Step 4: Add IM panel review prompt**

After the existing prompts, add:

```python
@mcp.prompt()
def im_panel_review() -> str:
    """IM panel review prompt — surfaces high-risk chronic disease patients
    and patients with outstanding preventive care gaps."""
    return (
        "Run an IM panel review:\n"
        "1. Who are my high-risk IM patients? List each with their key out-of-control metric "
        "(A1c value, eGFR slope, or BP reading).\n"
        "2. Which patients have poorly controlled diabetes (A1c > 8)? Show their A1c trend direction.\n"
        "3. Which patients have declining kidney function? Show eGFR slope in units/year.\n"
        "4. Which patients are overdue for preventive care? Group by care type."
    )
```

- [ ] **Step 5: Run existing tests to confirm no regressions**

```bash
cd mcp-server && python -m pytest tests/ -v
```

Expected: `10 passed`

- [ ] **Step 6: Smoke-test the server starts**

```bash
cd mcp-server && python server.py --help 2>&1 | head -5
```

Expected: no import errors (FastMCP will print usage or start listening)

- [ ] **Step 7: Commit**

```bash
git add mcp-server/server.py
git commit -m "feat: add 4 IM MCP tools, IM cohort resource, and IM panel review prompt"
```

---

## What this plan does NOT cover

- **Frontend dashboard routing** — showing BH vs IM dashboards based on provider specialty. That is a separate plan (`2026-03-21-im-dashboard-routing.md`) to be written once this backend is merged.
- **SQL adapter for IM** — `adapter/sql_adapter.py` stub for IM functions. Follows the same swap pattern as BH when Phase 2 begins.
- **Provider identity / session context** — no auth or provider login yet. The frontend plan will address how the specialty is read at session start.

---

**Plan complete and saved to `docs/superpowers/plans/2026-03-21-im-module-backend.md`.**

Two execution options:

**1. Subagent-Driven (recommended)** — Fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?

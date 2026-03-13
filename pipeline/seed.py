#!/usr/bin/env python3
"""
ClinicalMind AI — Data Pipeline Seed Script

Pipeline stages:
  1. Generate   — synthetic FHIR R4 bundles via generate_fhir.py
                  (or load real Synthea output with --fhir-file path/to/bundles.json)
  2. Transform  — FHIR bundles → canonical patient dicts via transform_fhir.py
  3. Standardize — normalize dates, types, scoring fields
  4. De-identify — strip PII from the public clinic_stats row
  5. Insert      — upsert all tables into Supabase

Usage:
  cd pipeline
  pip install -r requirements.txt
  cp .env.example .env                   # fill in your Supabase URL + service key
  python seed.py                         # generate 60 synthetic patients
  python seed.py --count 100             # generate 100 patients
  python seed.py --fhir-file my.json     # load real Synthea FHIR output

Re-running is safe — all upserts use ON CONFLICT DO UPDATE (via Supabase upsert).
"""

import argparse
import os
import sys
import json
from datetime import date
from collections import Counter

from dotenv import load_dotenv
from supabase import create_client, Client

# ── Path setup — import FHIR pipeline from same directory ────────────────────
_HERE = os.path.dirname(__file__)
sys.path.insert(0, _HERE)
from generate_fhir import generate_fhir_bundles, PROVIDERS
from transform_fhir import transform_bundles, transform_from_file

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    sys.exit(
        "ERROR: Set SUPABASE_URL and SUPABASE_SERVICE_KEY in pipeline/.env\n"
        "       Copy pipeline/.env.example to pipeline/.env and fill in values."
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_str(d) -> str | None:
    """Ensure date-like values are ISO strings (or None)."""
    if d is None:
        return None
    if isinstance(d, date):
        return d.isoformat()
    return str(d)


def _standardize_patient(p: dict) -> dict:
    """Normalize a patient record coming out of mock_data into a clean shape."""
    return {
        "patient_id":               p["patient_id"],
        "name":                     p["name"],
        "date_of_birth":            _to_str(p.get("date_of_birth")),
        "diagnosis":                p.get("diagnosis"),
        "county":                   p.get("county"),
        "service_type":             p.get("service_type"),
        "provider_id":              p.get("provider_id"),
        "risk_level":               p.get("risk_level"),
        "engagement_flag":          bool(p.get("engagement_flag", False)),
        "days_since_last_contact":  int(p.get("days_since_last_contact", 0)),
        "last_contact_date":        _to_str(p.get("last_contact_date")),
        "kpi_compliance_pct":       int(p.get("kpi_compliance_pct", 0)),
        "has_crisis_7d":            bool(p.get("has_crisis_7d", False)),
        "has_crisis_28d":           bool(p.get("has_crisis_28d", False)),
    }


# ── Stage 1 + 2: Generate & Transform ────────────────────────────────────────

def load_data(fhir_file: str | None = None, count: int = 60) -> list[dict]:
    if fhir_file:
        print(f"Stage 1/5 — Loading FHIR bundles from {fhir_file}...")
        patients = transform_from_file(fhir_file)
    else:
        print(f"Stage 1/5 — Generating {count} synthetic FHIR R4 bundles...")
        bundles  = generate_fhir_bundles(n=count)
        print(f"Stage 2/5 — Transforming FHIR → schema...")
        patients = transform_bundles(bundles)
    print(f"           {len(patients)} patients loaded.")
    return patients


# ── Stage 3: De-identify (compute aggregate clinic_stats) ────────────────────

def build_clinic_stats(patients: list[dict]) -> dict:
    """Derive a fully de-identified summary row — zero PII, aggregate only."""
    total  = len(patients)
    high   = sum(1 for p in patients if p["risk_level"] == "High")
    mod    = sum(1 for p in patients if p["risk_level"] == "Moderate")
    low    = sum(1 for p in patients if p["risk_level"] == "Low")

    avg_kpi = round(sum(p["kpi_compliance_pct"] for p in patients) / total)
    below   = sum(1 for p in patients if p["kpi_compliance_pct"] < 75)

    crisis_7d  = sum(1 for p in patients if p["has_crisis_7d"])
    crisis_28d = sum(1 for p in patients if p["has_crisis_28d"])

    disengaged      = sum(1 for p in patients if p["days_since_last_contact"] > 30)
    hi_disengaged   = sum(1 for p in patients
                          if p["days_since_last_contact"] > 30 and p["risk_level"] == "High")

    dx_counter     = Counter(p["diagnosis"].split(" (")[0] for p in patients)
    county_counter = Counter(p["county"] for p in patients)
    svc_counter    = Counter(p["service_type"] for p in patients)

    return {
        "id":                         1,
        "total_patients":             total,
        "high_risk_count":            high,
        "moderate_risk_count":        mod,
        "low_risk_count":             low,
        "overall_kpi_compliance_pct": avg_kpi,
        "patients_below_kpi_target":  below,
        "crisis_events_7d":           crisis_7d,
        "crisis_events_28d":          crisis_28d,
        "disengaged_patients_count":  disengaged,
        "high_risk_disengaged_count": hi_disengaged,
        "diagnosis_breakdown":        json.dumps(dict(dx_counter.most_common())),
        "county_breakdown":           json.dumps(dict(county_counter.most_common())),
        "service_breakdown":          json.dumps(dict(svc_counter.most_common())),
        "updated_at":                 "now()",
    }


# ── Stage 4: Insert ───────────────────────────────────────────────────────────

def seed(client: Client, patients: list[dict]) -> None:
    print("Stage 3/5 — Standardizing records...")

    # ── providers ─────────────────────────────────────────────
    print("Stage 4/5 — Upserting to Supabase...")
    print("  → providers")
    prov_rows = [
        {"provider_id": p["provider_id"], "name": p["name"], "team": p["team"]}
        for p in PROVIDERS
    ]
    client.table("providers").upsert(prov_rows, on_conflict="provider_id").execute()

    # ── patients ──────────────────────────────────────────────
    print("  → patients")
    patient_rows = [_standardize_patient(p) for p in patients]
    client.table("patients").upsert(patient_rows, on_conflict="patient_id").execute()

    # ── assessments_phq9 ──────────────────────────────────────
    print("  → assessments_phq9")
    phq9_rows = [
        {
            "patient_id":        p["patient_id"],
            "assessment_date":   _to_str(p["phq9"]["assessment_date"]),
            "total_score":       int(p["phq9"]["total_score"]),
            "item_scores":       json.dumps(p["phq9"]["item_scores"]),
            "suicidal_ideation": bool(p["phq9"]["suicidal_ideation"]),
            "severity":          p["phq9"]["severity"],
        }
        for p in patients
    ]
    # Delete existing then insert (simpler than composite upsert for assessments)
    pids = [p["patient_id"] for p in patients]
    client.table("assessments_phq9").delete().in_("patient_id", pids).execute()
    client.table("assessments_phq9").insert(phq9_rows).execute()

    # ── assessments_gad7 ──────────────────────────────────────
    print("  → assessments_gad7")
    gad7_rows = [
        {
            "patient_id":      p["patient_id"],
            "assessment_date": _to_str(p["gad7"]["assessment_date"]),
            "total_score":     int(p["gad7"]["total_score"]),
            "item_scores":     json.dumps(p["gad7"]["item_scores"]),
            "severity":        p["gad7"]["severity"],
        }
        for p in patients
    ]
    client.table("assessments_gad7").delete().in_("patient_id", pids).execute()
    client.table("assessments_gad7").insert(gad7_rows).execute()

    # ── assessments_whodas ────────────────────────────────────
    print("  → assessments_whodas")
    whodas_rows = [
        {
            "patient_id":      p["patient_id"],
            "assessment_date": _to_str(p["whodas"]["assessment_date"]),
            "total_score":     int(p["whodas"]["total_score"]),
            "disability_level": p["whodas"]["disability_level"],
        }
        for p in patients
    ]
    client.table("assessments_whodas").delete().in_("patient_id", pids).execute()
    client.table("assessments_whodas").insert(whodas_rows).execute()

    # ── assessments_ssrs ──────────────────────────────────────
    print("  → assessments_ssrs")
    ssrs_rows = [
        {
            "patient_id":         p["patient_id"],
            "assessment_date":    _to_str(p["ssrs"]["assessment_date"]),
            "suicidal_ideation":  bool(p["ssrs"]["suicidal_ideation"]),
            "ideation_intensity": int(p["ssrs"]["ideation_intensity"]),
            "intent":             bool(p["ssrs"]["intent"]),
            "plan":               bool(p["ssrs"]["plan"]),
            "method":             bool(p["ssrs"]["method"]),
            "history_attempt":    bool(p["ssrs"]["history_attempt"]),
            "risk_level":         p["ssrs"]["risk_level"],
        }
        for p in patients
    ]
    client.table("assessments_ssrs").delete().in_("patient_id", pids).execute()
    client.table("assessments_ssrs").insert(ssrs_rows).execute()

    # ── encounters ────────────────────────────────────────────
    print("  → encounters")
    enc_rows = [
        {
            "encounter_id":   e["encounter_id"],
            "patient_id":     p["patient_id"],
            "admit_date":     _to_str(e["admit_date"]),
            "discharge_date": _to_str(e.get("discharge_date")),
            "encounter_type": e["encounter_type"]
        }
        for p in patients
        for e in p["encounters"]
    ]
    client.table("encounters").delete().in_("patient_id", pids).execute()
    client.table("encounters").insert(enc_rows).execute()

    # ── contacts ──────────────────────────────────────────────
    print("  → contacts")
    con_rows = [
        {
            "contact_id":   c["contact_id"],
            "patient_id":   p["patient_id"],
            "contact_date": _to_str(c["contact_date"]),
            "contact_type": c["contact_type"],
            "provider_id":  c["provider_id"],
            "days_since":   int(c["days_since"]),
        }
        for p in patients
        for c in p["contacts"]
    ]
    client.table("contacts").delete().in_("patient_id", pids).execute()
    client.table("contacts").insert(con_rows).execute()

    # ── crisis_events ─────────────────────────────────────────
    print("  → crisis_events")
    crisis_rows = [
        {
            "event_id":       e["event_id"],
            "patient_id":     p["patient_id"],
            "crisis_date":    _to_str(e["crisis_date"]),
            "crisis_type":    e["crisis_type"],
            "within_7_days":  bool(e["within_7_days"]),
            "within_28_days": bool(e["within_28_days"]),
            "days_since":     int(e["days_since"]),
        }
        for p in patients
        for e in p["crisis_events"]
    ]
    if crisis_rows:
        client.table("crisis_events").delete().in_("patient_id", pids).execute()
        client.table("crisis_events").insert(crisis_rows).execute()

    # ── kpi_compliance ────────────────────────────────────────
    print("  → kpi_compliance")
    kpi_keys = ["bha", "sra", "aims", "whodas", "phq9", "beh_tp", "beh_csp"]
    kpi_rows = [
        {
            "patient_id":     p["patient_id"],
            "kpi_name":       k,
            "last_completed": _to_str(p["kpi"][k]["last_completed"]),
            "due_date":       _to_str(p["kpi"][k]["due_date"]),
            "overdue":        bool(p["kpi"][k]["overdue"]),
        }
        for p in patients
        for k in kpi_keys
    ]
    client.table("kpi_compliance").delete().in_("patient_id", pids).execute()
    client.table("kpi_compliance").insert(kpi_rows).execute()

    # ── clinic_stats (de-identified public aggregate) ─────────
    print("  → clinic_stats (de-identified aggregate)")
    stats = build_clinic_stats(patients)
    stats.pop("updated_at", None)  # let Supabase handle the timestamp
    client.table("clinic_stats").upsert([stats], on_conflict="id").execute()

    print("Stage 5/5 — Done.\n")
    print(f"  Patients inserted:     {len(patients)}")
    print(f"  High risk:             {stats['high_risk_count']}")
    print(f"  KPI compliance:        {stats['overall_kpi_compliance_pct']}%")
    print(f"  Crisis events (28d):   {stats['crisis_events_28d']}")
    print(f"  Disengaged patients:   {stats['disengaged_patients_count']}")
    print("\nSupabase tables populated. clinic_stats is publicly readable via anon key.")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ClinicalMind AI data pipeline")
    parser.add_argument("--count",     type=int, default=60,  help="Number of patients to generate (default 60)")
    parser.add_argument("--fhir-file", type=str, default=None, help="Path to a real Synthea FHIR JSON file to load instead")
    args = parser.parse_args()

    print("ClinicalMind AI — Data Pipeline\n" + "=" * 40)
    client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    patients = load_data(fhir_file=args.fhir_file, count=args.count)
    seed(client, patients)

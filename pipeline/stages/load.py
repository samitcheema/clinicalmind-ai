"""
Stage 4 — Load

Upsert all canonical patient data into Supabase tables and refresh the
de-identified clinic_stats aggregate row.  All operations are idempotent:
  • patients / providers / clinic_stats  →  UPSERT on primary key
  • assessment / encounter / contact / crisis / kpi tables  →  DELETE + INSERT
    (simpler than composite-key upserts; safe because seed data is synthetic)

Supports --dry-run mode: all row-building logic runs but no network calls
are made, so the full pipeline can be tested without Supabase credentials.

Input:  Supabase client, validated patient dicts, run_id, dry_run flag
Output: clinic_stats dict, StageResult
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter
from datetime import date
from typing import Any

_PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PIPELINE_DIR not in sys.path:
    sys.path.insert(0, _PIPELINE_DIR)

from generate_fhir import PROVIDERS
from pipeline_run import StageResult


KPI_KEYS = ["bha", "sra", "aims", "whodas", "phq9", "beh_tp", "beh_csp"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_str(d: Any) -> str | None:
    if d is None:
        return None
    if isinstance(d, date):
        return d.isoformat()
    return str(d) if d else None


def _patient_row(p: dict) -> dict:
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


# ── clinic_stats builder (de-identified) ─────────────────────────────────────

def build_clinic_stats(patients: list[dict]) -> dict:
    """Derive a fully de-identified, aggregate-only stats row. Zero PII."""
    total = len(patients)
    if total == 0:
        return {"id": 1, "total_patients": 0}

    high  = sum(1 for p in patients if p["risk_level"] == "High")
    mod   = sum(1 for p in patients if p["risk_level"] == "Moderate")
    low   = sum(1 for p in patients if p["risk_level"] == "Low")

    avg_kpi    = round(sum(p["kpi_compliance_pct"] for p in patients) / total)
    below_kpi  = sum(1 for p in patients if p["kpi_compliance_pct"] < 75)

    crisis_7d  = sum(1 for p in patients if p["has_crisis_7d"])
    crisis_28d = sum(1 for p in patients if p["has_crisis_28d"])

    disengaged = sum(1 for p in patients if p["days_since_last_contact"] > 30)
    hi_dis     = sum(1 for p in patients
                     if p["days_since_last_contact"] > 30 and p["risk_level"] == "High")

    dx_ctr  = Counter(p["diagnosis"].split(" (")[0] for p in patients if p.get("diagnosis"))
    cty_ctr = Counter(p["county"] for p in patients if p.get("county"))
    svc_ctr = Counter(p["service_type"] for p in patients if p.get("service_type"))

    return {
        "id":                         1,
        "total_patients":             total,
        "high_risk_count":            high,
        "moderate_risk_count":        mod,
        "low_risk_count":             low,
        "overall_kpi_compliance_pct": avg_kpi,
        "patients_below_kpi_target":  below_kpi,
        "crisis_events_7d":           crisis_7d,
        "crisis_events_28d":          crisis_28d,
        "disengaged_patients_count":  disengaged,
        "high_risk_disengaged_count": hi_dis,
        "diagnosis_breakdown":        json.dumps(dict(dx_ctr.most_common())),
        "county_breakdown":           json.dumps(dict(cty_ctr.most_common())),
        "service_breakdown":          json.dumps(dict(svc_ctr.most_common())),
    }


# ── Public API ────────────────────────────────────────────────────────────────

def run(
    client,
    patients: list[dict],
    run_id: str,
    dry_run: bool = False,
) -> tuple[dict, StageResult]:
    """
    Load all tables into Supabase.

    Args:
        client:   Supabase client (ignored when dry_run=True)
        patients: validated + standardized patient dicts
        run_id:   current pipeline run ID (for logging)
        dry_run:  if True, build all rows but skip network calls

    Returns:
        stats:  clinic_stats dict (aggregate summary)
        result: StageResult with per-table row counts in metadata
    """
    t0    = time.perf_counter()
    pids  = [p["patient_id"] for p in patients]
    stats = build_clinic_stats(patients)
    table_counts: dict[str, int] = {}

    # ── Low-level helpers ─────────────────────────────────────────────────────

    def _upsert(table: str, rows: list[dict], on_conflict: str) -> None:
        table_counts[table] = len(rows)
        if dry_run or not rows:
            return
        client.table(table).upsert(rows, on_conflict=on_conflict).execute()

    def _delete_insert(table: str, rows: list[dict]) -> None:
        table_counts[table] = len(rows)
        if dry_run or not rows:
            return
        client.table(table).delete().in_("patient_id", pids).execute()
        client.table(table).insert(rows).execute()

    # ── Build all row lists ────────────────────────────────────────────────────

    try:
        # providers — seed hardcoded list, then add any patient-derived providers
        # (e.g. NPI-based IDs extracted from Synthea Encounter participants)
        prov_map = {
            p["id"]: {"provider_id": p["id"], "name": p["name"], "team": p["team"]}
            for p in PROVIDERS
        }
        for p in patients:
            pid = p.get("provider_id", "")
            if pid and pid not in prov_map:
                prov_map[pid] = {
                    "provider_id": pid,
                    "name":        p.get("provider_name", pid),
                    "team":        p.get("team", ""),
                }
        _upsert("providers", list(prov_map.values()), "provider_id")

        # patients
        _upsert("patients", [_patient_row(p) for p in patients], "patient_id")

        # assessments_phq9
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
        _delete_insert("assessments_phq9", phq9_rows)

        # assessments_gad7
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
        _delete_insert("assessments_gad7", gad7_rows)

        # assessments_whodas
        whodas_rows = [
            {
                "patient_id":       p["patient_id"],
                "assessment_date":  _to_str(p["whodas"]["assessment_date"]),
                "total_score":      int(p["whodas"]["total_score"]),
                "disability_level": p["whodas"]["disability_level"],
            }
            for p in patients
        ]
        _delete_insert("assessments_whodas", whodas_rows)

        # assessments_ssrs
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
        _delete_insert("assessments_ssrs", ssrs_rows)

        # encounters
        enc_rows = [
            {
                "encounter_id":   e["encounter_id"],
                "patient_id":     p["patient_id"],
                "admit_date":     _to_str(e["admit_date"]),
                "discharge_date": _to_str(e.get("discharge_date")),
                "encounter_type": e["encounter_type"],
                "pes_flag":       bool(e.get("pes_flag", False)),
                "cis_flag":       bool(e.get("cis_flag", False)),
            }
            for p in patients
            for e in p.get("encounters", [])
        ]
        _delete_insert("encounters", enc_rows)

        # contacts
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
            for c in p.get("contacts", [])
        ]
        _delete_insert("contacts", con_rows)

        # crisis_events
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
            for e in p.get("crisis_events", [])
        ]
        if crisis_rows:
            _delete_insert("crisis_events", crisis_rows)
        else:
            table_counts["crisis_events"] = 0

        # kpi_compliance
        kpi_rows = [
            {
                "patient_id":     p["patient_id"],
                "kpi_name":       k,
                "last_completed": _to_str(p["kpi"][k]["last_completed"]),
                "due_date":       _to_str(p["kpi"][k]["due_date"]),
                "overdue":        bool(p["kpi"][k]["overdue"]),
            }
            for p in patients
            for k in KPI_KEYS
        ]
        _delete_insert("kpi_compliance", kpi_rows)

        # clinic_stats (de-identified aggregate — public)
        _upsert("clinic_stats", [stats], "id")

        result = StageResult(
            name="load",
            status="ok",
            records_in=len(patients),
            records_out=len(patients),
            duration_secs=time.perf_counter() - t0,
            metadata={"dry_run": dry_run, "table_counts": table_counts},
        )

    except Exception as exc:
        result = StageResult(
            name="load",
            status="failed",
            records_in=len(patients),
            duration_secs=time.perf_counter() - t0,
            error=str(exc),
            metadata={"dry_run": dry_run, "table_counts": table_counts},
        )

    return stats, result

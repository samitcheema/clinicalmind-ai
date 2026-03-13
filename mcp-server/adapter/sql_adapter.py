"""
ClinicalMind AI — Supabase SQL Adapter (Phase 2)

Implements the same interface as mock_adapter.py using Supabase as the backend.
Return shapes are identical — server.py requires no changes.

Setup:
  1. Run pipeline/supabase_schema.sql in the Supabase SQL Editor
  2. Run pipeline/seed.py to populate the tables
  3. Set env vars: SUPABASE_URL, SUPABASE_SERVICE_KEY
  4. In server.py change the import from mock_adapter to sql_adapter
"""

import os
import json
from functools import lru_cache

import os as _os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".env"))

KPI_NAMES  = ["bha", "sra", "aims", "whodas", "phq9", "beh_tp", "beh_csp"]
KPI_TARGET = 75


# ── Supabase client (singleton) ───────────────────────────────────────────────

@lru_cache(maxsize=1)
def _client() -> Client:
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in the environment. "
            "Copy pipeline/.env.example to mcp-server/.env and fill in values."
        )
    return create_client(url, key)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _fetch_patients_with_assessments(
    risk_level: str | None = None,
    county: str | None = None,
    provider: str | None = None,
) -> list[dict]:
    """Pull patients joined with their latest assessments and KPI rows."""
    q = _client().table("patients").select(
        "*, providers(name, team), "
        "assessments_phq9(*), assessments_gad7(*), assessments_whodas(*), "
        "assessments_ssrs(*), kpi_compliance(*), crisis_events(*), contacts(*)"
    )

    if risk_level:
        q = q.eq("risk_level", risk_level)
    if county:
        q = q.ilike("county", f"%{county}%")
    if provider:
        q = q.or_(f"provider_id.ilike.%{provider}%,providers.name.ilike.%{provider}%")

    res = q.execute()
    return res.data or []


def _merge_patient(row: dict) -> dict:
    """Reshape a Supabase joined row into the canonical patient dict."""
    # Take the most recent assessment per type (last inserted = highest created_at)
    def _latest(lst: list[dict]) -> dict:
        if not lst:
            return {}
        return sorted(lst, key=lambda x: x.get("created_at", ""), reverse=True)[0]

    phq9_row   = _latest(row.get("assessments_phq9", []))
    gad7_row   = _latest(row.get("assessments_gad7", []))
    whodas_row = _latest(row.get("assessments_whodas", []))
    ssrs_row   = _latest(row.get("assessments_ssrs", []))

    phq9 = {
        "assessment_date":   phq9_row.get("assessment_date"),
        "total_score":       phq9_row.get("total_score", 0),
        "item_scores":       json.loads(phq9_row["item_scores"]) if isinstance(phq9_row.get("item_scores"), str) else (phq9_row.get("item_scores") or []),
        "suicidal_ideation": bool(phq9_row.get("suicidal_ideation", False)),
        "severity":          phq9_row.get("severity", "Minimal"),
    }

    gad7 = {
        "assessment_date": gad7_row.get("assessment_date"),
        "total_score":     gad7_row.get("total_score", 0),
        "item_scores":     json.loads(gad7_row["item_scores"]) if isinstance(gad7_row.get("item_scores"), str) else (gad7_row.get("item_scores") or []),
        "severity":        gad7_row.get("severity", "Minimal"),
    }

    whodas = {
        "assessment_date": whodas_row.get("assessment_date"),
        "total_score":     whodas_row.get("total_score", 0),
        "disability_level": whodas_row.get("disability_level", "Mild"),
    }

    ssrs = {
        "assessment_date":    ssrs_row.get("assessment_date"),
        "suicidal_ideation":  bool(ssrs_row.get("suicidal_ideation", False)),
        "ideation_intensity": int(ssrs_row.get("ideation_intensity", 0)),
        "intent":             bool(ssrs_row.get("intent", False)),
        "plan":               bool(ssrs_row.get("plan", False)),
        "method":             bool(ssrs_row.get("method", False)),
        "history_attempt":    bool(ssrs_row.get("history_attempt", False)),
        "risk_level":         ssrs_row.get("risk_level", "Low"),
    }

    # KPI — build dict keyed by kpi_name
    kpi_rows  = row.get("kpi_compliance", [])
    kpi: dict = {}
    for k in KPI_NAMES:
        match = next((r for r in kpi_rows if r["kpi_name"] == k), {})
        kpi[k] = {
            "last_completed": match.get("last_completed"),
            "due_date":       match.get("due_date"),
            "overdue":        bool(match.get("overdue", False)),
        }

    # Contacts — sort most-recent first
    contacts = sorted(
        row.get("contacts", []),
        key=lambda c: c.get("contact_date", ""),
        reverse=True,
    )

    # Crisis events
    crisis_events = [
        {
            "event_id":       e["event_id"],
            "crisis_date":    e["crisis_date"],
            "crisis_type":    e["crisis_type"],
            "within_7_days":  bool(e["within_7_days"]),
            "within_28_days": bool(e["within_28_days"]),
            "days_since":     int(e["days_since"]),
        }
        for e in row.get("crisis_events", [])
    ]

    provider_row = row.get("providers") or {}

    kpi_pct = round(
        sum(1 for k in KPI_NAMES if not kpi[k]["overdue"]) / len(KPI_NAMES) * 100
    ) if kpi else row.get("kpi_compliance_pct", 0)

    return {
        "patient_id":              row["patient_id"],
        "name":                    row["name"],
        "date_of_birth":           row["date_of_birth"],
        "diagnosis":               row.get("diagnosis"),
        "county":                  row.get("county"),
        "service_type":            row.get("service_type"),
        "provider_id":             row.get("provider_id"),
        "provider_name":           provider_row.get("name", row.get("provider_id", "")),
        "team":                    provider_row.get("team", ""),
        "risk_level":              row.get("risk_level", "Low"),
        "days_since_last_contact": row.get("days_since_last_contact", 0),
        "last_contact_date":       row.get("last_contact_date"),
        "engagement_flag":         bool(row.get("engagement_flag", False)),
        "encounters":              [],  # omitted from summary queries for performance
        "contacts":                contacts,
        "phq9":                    phq9,
        "gad7":                    gad7,
        "whodas":                  whodas,
        "ssrs":                    ssrs,
        "kpi":                     kpi,
        "kpi_compliance_pct":      kpi_pct,
        "crisis_events":           crisis_events,
        "has_crisis_7d":           bool(row.get("has_crisis_7d", False)),
        "has_crisis_28d":          bool(row.get("has_crisis_28d", False)),
    }


# ── 1. get_patients ───────────────────────────────────────────────────────────

def get_patients(
    risk_level: str | None = None,
    county: str | None = None,
    provider: str | None = None,
) -> list[dict]:
    rows = _fetch_patients_with_assessments(risk_level, county, provider)
    merged = [_merge_patient(r) for r in rows]
    return [
        {
            "patient_id":               p["patient_id"],
            "name":                     p["name"],
            "date_of_birth":            p["date_of_birth"],
            "diagnosis":                p["diagnosis"],
            "county":                   p["county"],
            "service_type":             p["service_type"],
            "provider_id":              p["provider_id"],
            "provider_name":            p["provider_name"],
            "team":                     p["team"],
            "risk_level":               p["risk_level"],
            "last_contact_date":        p["last_contact_date"],
            "days_since_last_contact":  p["days_since_last_contact"],
            "engagement_flag":          p["engagement_flag"],
            "kpi_compliance_pct":       p["kpi_compliance_pct"],
            "phq9_score":               p["phq9"]["total_score"],
            "phq9_severity":            p["phq9"]["severity"],
            "gad7_score":               p["gad7"]["total_score"],
            "ssrs_risk":                p["ssrs"]["risk_level"],
            "has_crisis_28d":           p["has_crisis_28d"],
            "has_crisis_7d":            p["has_crisis_7d"],
        }
        for p in merged
    ]


# ── 2. get_patient_detail ─────────────────────────────────────────────────────

def get_patient_detail(patient_id: str) -> dict | None:
    res = _client().table("patients").select(
        "*, providers(name, team), "
        "assessments_phq9(*), assessments_gad7(*), assessments_whodas(*), "
        "assessments_ssrs(*), kpi_compliance(*), crisis_events(*), "
        "contacts(*), encounters(*)"
    ).eq("patient_id", patient_id.upper()).execute()

    rows = res.data or []
    if not rows:
        return None

    p = _merge_patient(rows[0])

    # Add encounters for detail view
    enc_res = _client().table("encounters").select("*").eq("patient_id", patient_id.upper()).execute()
    p["encounters"] = enc_res.data or []
    return p


# ── 3. get_high_risk_patients ─────────────────────────────────────────────────

def get_high_risk_patients(risk_type: str | None = None) -> list[dict]:
    rt = (risk_type or "").lower()

    if not rt or rt == "all":
        rows = _fetch_patients_with_assessments(risk_level="High")
    elif rt in ("phq9", "depression"):
        all_rows = _fetch_patients_with_assessments()
        rows = [
            r for r in all_rows
            if _merge_patient(r)["phq9"]["severity"] == "High"
        ]
    elif rt in ("ssrs", "suicide"):
        all_rows = _fetch_patients_with_assessments()
        rows = [r for r in all_rows if _merge_patient(r)["ssrs"]["risk_level"] == "High"]
    elif rt == "crisis":
        all_rows = _fetch_patients_with_assessments()
        rows = [r for r in all_rows if r.get("has_crisis_28d")]
    else:
        rows = _fetch_patients_with_assessments(risk_level="High")

    patients = [_merge_patient(r) for r in rows]

    def _sort_key(p):
        ssrs_score = {"High": 2, "Moderate": 1}.get(p["ssrs"]["risk_level"], 0)
        return (-ssrs_score, -p["phq9"]["total_score"])

    return [
        {
            "patient_id":              p["patient_id"],
            "name":                    p["name"],
            "diagnosis":               p["diagnosis"],
            "risk_level":              p["risk_level"],
            "provider_name":           p["provider_name"],
            "phq9_score":              p["phq9"]["total_score"],
            "phq9_severity":           p["phq9"]["severity"],
            "phq9_suicidal_ideation":  p["phq9"]["suicidal_ideation"],
            "gad7_score":              p["gad7"]["total_score"],
            "ssrs_risk":               p["ssrs"]["risk_level"],
            "ssrs_plan":               p["ssrs"]["plan"],
            "ssrs_method":             p["ssrs"]["method"],
            "ssrs_intent":             p["ssrs"]["intent"],
            "has_crisis_7d":           p["has_crisis_7d"],
            "has_crisis_28d":          p["has_crisis_28d"],
            "days_since_last_contact": p["days_since_last_contact"],
            "last_contact_date":       p["last_contact_date"],
        }
        for p in sorted(patients, key=_sort_key)
    ]


# ── 4. get_kpi_compliance ─────────────────────────────────────────────────────

def get_kpi_compliance(kpi_name: str | None = None) -> dict:
    res = _client().table("kpi_compliance").select("*").execute()
    all_kpi = res.data or []

    pat_res = _client().table("patients").select("patient_id").execute()
    total   = len(pat_res.data or [])

    def _summary(name: str) -> dict:
        rows = [r for r in all_kpi if r["kpi_name"] == name]
        completed = sum(1 for r in rows if not r["overdue"])
        overdue   = len(rows) - completed
        pct       = round((completed / total) * 100) if total else 0
        meets     = pct >= KPI_TARGET
        return {
            "kpi_name":       name.upper().replace("_", "-"),
            "total_patients": total,
            "completed":      completed,
            "overdue":        overdue,
            "compliance_pct": pct,
            "target_pct":     KPI_TARGET,
            "meets_target":   meets,
            "gap_to_target":  0 if meets else KPI_TARGET - pct,
        }

    if kpi_name:
        k = kpi_name.lower().replace("-", "_")
        if k not in KPI_NAMES:
            return {"error": f"Unknown KPI: {kpi_name}. Valid: {', '.join(KPI_NAMES)}"}
        return _summary(k)

    by_kpi = [_summary(k) for k in KPI_NAMES]
    overall_completed = sum(s["completed"] for s in by_kpi)
    overall_total     = len(KPI_NAMES) * total
    overall_pct       = round((overall_completed / overall_total) * 100) if overall_total else 0

    # Count patients with all KPIs compliant
    pat_kpi_map: dict[str, int] = {}
    for r in all_kpi:
        pid = r["patient_id"]
        if pid not in pat_kpi_map:
            pat_kpi_map[pid] = 0
        if not r["overdue"]:
            pat_kpi_map[pid] += 1

    fully_compliant = sum(1 for v in pat_kpi_map.values() if v == len(KPI_NAMES))
    below_target_pids = set()
    for r in all_kpi:
        if r["overdue"]:
            below_target_pids.add(r["patient_id"])
    patients_below = len(below_target_pids)

    return {
        "overall_compliance_pct":   overall_pct,
        "target_pct":               KPI_TARGET,
        "meets_target":             overall_pct >= KPI_TARGET,
        "gap_to_target":            0 if overall_pct >= KPI_TARGET else KPI_TARGET - overall_pct,
        "by_kpi":                   by_kpi,
        "patients_fully_compliant": fully_compliant,
        "patients_below_target":    patients_below,
    }


# ── 5. get_overdue_assessments ────────────────────────────────────────────────

def get_overdue_assessments(assessment_type: str | None = None) -> list[dict]:
    at = (assessment_type or "").lower().replace("-", "_")
    if at and at not in KPI_NAMES:
        return [{"error": f"Unknown type: {assessment_type}. Valid: {', '.join(KPI_NAMES)}"}]

    types_to_check = [at] if at else KPI_NAMES

    kpi_res = _client().table("kpi_compliance").select("*").in_("kpi_name", types_to_check).eq("overdue", True).execute()
    overdue_kpi = kpi_res.data or []

    if not overdue_kpi:
        return []

    pids = list({r["patient_id"] for r in overdue_kpi})
    pat_res = _client().table("patients").select(
        "patient_id, name, diagnosis, provider_id, risk_level, providers(name)"
    ).in_("patient_id", pids).execute()

    pat_map = {p["patient_id"]: p for p in (pat_res.data or [])}

    # Group by patient
    by_patient: dict[str, list] = {}
    for r in overdue_kpi:
        pid = r["patient_id"]
        if pid not in by_patient:
            by_patient[pid] = []
        by_patient[pid].append({
            "assessment":     r["kpi_name"].upper().replace("_", "-"),
            "last_completed": r["last_completed"],
            "due_date":       r["due_date"],
        })

    result = []
    for pid, overdue_list in by_patient.items():
        p = pat_map.get(pid, {})
        prov = p.get("providers") or {}
        result.append({
            "patient_id":          pid,
            "name":                p.get("name", pid),
            "diagnosis":           p.get("diagnosis"),
            "provider_name":       prov.get("name", p.get("provider_id", "")),
            "risk_level":          p.get("risk_level", "Low"),
            "overdue_assessments": overdue_list,
            "overdue_count":       len(overdue_list),
        })

    return sorted(result, key=lambda x: -x["overdue_count"])


# ── 6. get_crisis_events ──────────────────────────────────────────────────────

def get_crisis_events(window_days: int = 28) -> dict:
    days = int(window_days)

    ev_res = _client().table("crisis_events").select("*").lte("days_since", days).execute()
    events_raw = ev_res.data or []

    if not events_raw:
        return {"window_days": days, "total_events": 0, "unique_patients": 0, "events": []}

    pids = list({e["patient_id"] for e in events_raw})
    pat_res = _client().table("patients").select(
        "patient_id, name, diagnosis, provider_id, risk_level, providers(name), "
        "assessments_phq9(total_score), assessments_ssrs(risk_level)"
    ).in_("patient_id", pids).execute()
    pat_map = {p["patient_id"]: p for p in (pat_res.data or [])}

    events = []
    for e in events_raw:
        p = pat_map.get(e["patient_id"], {})
        prov = p.get("providers") or {}
        phq9_rows = p.get("assessments_phq9") or [{}]
        ssrs_rows = p.get("assessments_ssrs") or [{}]
        events.append({
            "patient_id":    e["patient_id"],
            "name":          p.get("name", e["patient_id"]),
            "diagnosis":     p.get("diagnosis"),
            "provider_name": prov.get("name", p.get("provider_id", "")),
            "risk_level":    p.get("risk_level", "Low"),
            "event_id":      e["event_id"],
            "crisis_date":   e["crisis_date"],
            "crisis_type":   e["crisis_type"],
            "days_ago":      int(e["days_since"]),
            "within_7_days": bool(e["within_7_days"]),
            "ssrs_risk":     ssrs_rows[-1].get("risk_level", "Low") if ssrs_rows else "Low",
            "phq9_score":    phq9_rows[-1].get("total_score", 0) if phq9_rows else 0,
        })

    events.sort(key=lambda e: e["days_ago"])
    return {
        "window_days":     days,
        "total_events":    len(events),
        "unique_patients": len(pids),
        "events":          events,
    }


# ── 7. get_disengaged_patients ────────────────────────────────────────────────

def get_disengaged_patients(threshold_days: int = 30) -> dict:
    days = int(threshold_days)

    res = _client().table("patients").select(
        "*, providers(name), assessments_phq9(total_score), assessments_ssrs(risk_level), contacts(*)"
    ).gt("days_since_last_contact", days).order("days_since_last_contact", desc=True).execute()

    rows = res.data or []

    patients = []
    for r in rows:
        prov = r.get("providers") or {}
        phq9_rows = r.get("assessments_phq9") or [{}]
        ssrs_rows = r.get("assessments_ssrs") or [{}]
        contacts  = sorted(r.get("contacts", []), key=lambda c: c.get("contact_date", ""), reverse=True)
        patients.append({
            "patient_id":               r["patient_id"],
            "name":                     r["name"],
            "diagnosis":                r.get("diagnosis"),
            "provider_name":            prov.get("name", r.get("provider_id", "")),
            "risk_level":               r.get("risk_level", "Low"),
            "last_contact_date":        r.get("last_contact_date"),
            "days_since_last_contact":  int(r.get("days_since_last_contact", 0)),
            "last_contact_type":        contacts[0]["contact_type"] if contacts else "Unknown",
            "phq9_score":               phq9_rows[-1].get("total_score", 0) if phq9_rows else 0,
            "ssrs_risk":                ssrs_rows[-1].get("risk_level", "Low") if ssrs_rows else "Low",
            "has_crisis_28d":           bool(r.get("has_crisis_28d", False)),
        })

    return {
        "threshold_days":   days,
        "total_disengaged": len(patients),
        "patients":         patients,
    }

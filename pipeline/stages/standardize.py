"""
Stage 3 — Standardize

Three-pass processing applied to every canonical patient dict:
  1. Coerce   — normalise Python types (dates→ISO str, ints, bools, clamp ranges)
  2. Validate — enforce required fields, enum values, score ranges, business rules
  3. Dedupe   — drop duplicate patient_ids (keep last occurrence)

Records that fail validation are removed from the pipeline and returned
separately so the caller can log or inspect them without aborting the run.

Input:  list of canonical patient dicts (from stages/transform.py)
Output: (valid, rejected, StageResult)
"""
from __future__ import annotations



import os
import sys
import time
from datetime import date
from typing import Any

_PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PIPELINE_DIR not in sys.path:
    sys.path.insert(0, _PIPELINE_DIR)

from pipeline_run import StageResult


# ── Allowed enum values (aligned with generate_fhir.py) ──────────────────────

VALID_RISK_LEVELS   = {"High", "Moderate", "Low"}
VALID_SERVICE_TYPES = {"ACT", "CSP", "BHH", "Supported Housing", "Other"}
VALID_PHQ9_SEVERITY = {"Minimal", "Moderate", "Moderately Severe", "High"}
VALID_GAD7_SEVERITY = {"Minimal", "Mild", "Moderate", "High"}
VALID_SSRS_RISK     = {"Low", "Moderate", "High"}
VALID_WHODAS_DL     = {"None", "Mild", "Moderate", "Severe", "Extreme"}


# ── Pass 1: Coerce ────────────────────────────────────────────────────────────

def _to_str(d: Any) -> str | None:
    if d is None:
        return None
    if isinstance(d, date):
        return d.isoformat()
    return str(d) if d else None


def _coerce(p: dict) -> dict:
    """Return a new dict with all fields normalised to their expected Python types."""
    p = dict(p)

    # Top-level scalars
    p["days_since_last_contact"] = max(0, int(p.get("days_since_last_contact") or 0))
    p["kpi_compliance_pct"]      = max(0, min(100, int(p.get("kpi_compliance_pct") or 0)))
    p["engagement_flag"]         = bool(p.get("engagement_flag", False))
    p["has_crisis_7d"]           = bool(p.get("has_crisis_7d", False))
    p["has_crisis_28d"]          = bool(p.get("has_crisis_28d", False))
    p["last_contact_date"]       = _to_str(p.get("last_contact_date"))
    p["date_of_birth"]           = _to_str(p.get("date_of_birth"))

    # PHQ-9
    phq = dict(p.get("phq9") or {})
    phq["total_score"]       = max(0, min(27, int(phq.get("total_score") or 0)))
    phq["suicidal_ideation"] = bool(phq.get("suicidal_ideation", False))
    phq["assessment_date"]   = _to_str(phq.get("assessment_date"))
    raw_items = phq.get("item_scores") or []
    phq["item_scores"] = [max(0, min(3, int(x))) for x in raw_items] if raw_items else [0] * 9
    p["phq9"] = phq

    # GAD-7
    gad = dict(p.get("gad7") or {})
    gad["total_score"]     = max(0, min(21, int(gad.get("total_score") or 0)))
    gad["assessment_date"] = _to_str(gad.get("assessment_date"))
    raw_items = gad.get("item_scores") or []
    gad["item_scores"] = [max(0, min(3, int(x))) for x in raw_items] if raw_items else [0] * 7
    p["gad7"] = gad

    # WHODAS
    whodas = dict(p.get("whodas") or {})
    whodas["total_score"]      = max(0, min(48, int(whodas.get("total_score") or 0)))
    whodas["assessment_date"]  = _to_str(whodas.get("assessment_date"))
    p["whodas"] = whodas

    # SSRS
    ssrs = dict(p.get("ssrs") or {})
    ssrs["suicidal_ideation"]  = bool(ssrs.get("suicidal_ideation", False))
    ssrs["intent"]             = bool(ssrs.get("intent", False))
    ssrs["plan"]               = bool(ssrs.get("plan", False))
    ssrs["method"]             = bool(ssrs.get("method", False))
    ssrs["history_attempt"]    = bool(ssrs.get("history_attempt", False))
    ssrs["ideation_intensity"] = max(0, min(5, int(ssrs.get("ideation_intensity") or 0)))
    ssrs["assessment_date"]    = _to_str(ssrs.get("assessment_date"))
    p["ssrs"] = ssrs

    return p


# ── Pass 2: Validate ──────────────────────────────────────────────────────────

def _validate(p: dict) -> list[str]:
    """Return a list of validation error strings. Empty list means the record is valid."""
    errors: list[str] = []

    # Required fields
    for field_name in ("patient_id", "name", "date_of_birth", "risk_level",
                        "service_type", "provider_id"):
        if not p.get(field_name):
            errors.append(f"missing required field: {field_name}")

    # Enum constraints
    rl = p.get("risk_level")
    if rl and rl not in VALID_RISK_LEVELS:
        errors.append(f"invalid risk_level: {rl!r}")

    st = p.get("service_type")
    if st and st not in VALID_SERVICE_TYPES:
        errors.append(f"invalid service_type: {st!r}")

    # PHQ-9
    phq = p.get("phq9", {})
    score = phq.get("total_score", 0)
    if not (0 <= score <= 27):
        errors.append(f"phq9.total_score out of range: {score}")
    sev = phq.get("severity")
    if sev and sev not in VALID_PHQ9_SEVERITY:
        errors.append(f"invalid phq9.severity: {sev!r}")

    # GAD-7
    gad = p.get("gad7", {})
    score = gad.get("total_score", 0)
    if not (0 <= score <= 21):
        errors.append(f"gad7.total_score out of range: {score}")
    sev = gad.get("severity")
    if sev and sev not in VALID_GAD7_SEVERITY:
        errors.append(f"invalid gad7.severity: {sev!r}")

    # WHODAS
    whodas = p.get("whodas", {})
    score = whodas.get("total_score", 0)
    if not (0 <= score <= 48):
        errors.append(f"whodas.total_score out of range: {score}")

    # SSRS
    ssrs = p.get("ssrs", {})
    intensity = ssrs.get("ideation_intensity", 0)
    if not (0 <= intensity <= 5):
        errors.append(f"ssrs.ideation_intensity out of range: {intensity}")
    ssrs_rl = ssrs.get("risk_level")
    if ssrs_rl and ssrs_rl not in VALID_SSRS_RISK:
        errors.append(f"invalid ssrs.risk_level: {ssrs_rl!r}")

    # Business rules
    si_present = phq.get("suicidal_ideation") or ssrs.get("suicidal_ideation")
    if si_present and p.get("risk_level") == "Low":
        errors.append("business rule violation: suicidal ideation present but risk_level is Low")

    kpi_pct = p.get("kpi_compliance_pct", 0)
    if not (0 <= kpi_pct <= 100):
        errors.append(f"kpi_compliance_pct out of range: {kpi_pct}")

    dslc = p.get("days_since_last_contact", 0)
    if dslc < 0:
        errors.append(f"days_since_last_contact is negative: {dslc}")

    return errors


# ── Pass 3: Dedupe ────────────────────────────────────────────────────────────

def _dedupe(patients: list[dict]) -> tuple[list[dict], int]:
    """Keep the last record per patient_id. Returns (deduped_list, n_removed)."""
    seen: dict[str, dict] = {}
    for p in patients:
        seen[p["patient_id"]] = p
    deduped = list(seen.values())
    return deduped, len(patients) - len(deduped)


# ── Public API ────────────────────────────────────────────────────────────────

def run(patients: list[dict]) -> tuple[list[dict], list[dict], StageResult]:
    """
    Standardize and validate a list of canonical patient dicts.

    Returns:
        valid:    cleaned + validated patient dicts ready for loading
        rejected: list of {"patient_id": ..., "errors": [...]} dicts
        result:   StageResult
    """
    t0 = time.perf_counter()
    valid: list[dict] = []
    rejected: list[dict] = []

    for p in patients:
        coerced = _coerce(p)
        errors  = _validate(coerced)
        if errors:
            rejected.append({
                "patient_id": p.get("patient_id", "UNKNOWN"),
                "errors":     errors,
            })
        else:
            valid.append(coerced)

    valid, n_dupes = _dedupe(valid)

    result = StageResult(
        name="standardize",
        status="ok",
        records_in=len(patients),
        records_out=len(valid),
        duration_secs=time.perf_counter() - t0,
        metadata={
            "rejected":           len(rejected),
            "duplicates_removed": n_dupes,
            "rejection_detail":   rejected[:10],   # first 10 for log
        },
    )

    return valid, rejected, result

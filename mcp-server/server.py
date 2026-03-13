"""
ClinicalMind AI — FastMCP Server

Exposes behavioral health pipeline data as 7 discrete MCP tools.
Claude calls these tools on demand — fetching only the data needed to
answer each clinical question rather than injecting the entire cohort.

Transport: stdio  (compatible with Claude Desktop, Claude Code, and the
                   React chat UI via the MCP client library)

To switch to real SQL:
  Change the import below from 'adapter.mock_adapter'
                             to 'adapter.sql_adapter'
  No tool definitions need to change.

Tools:
  get_patients               — patient list with optional filters
  get_patient_detail         — full record for one patient
  get_high_risk_patients     — patients flagged by PHQ-9, SSRS, or crisis
  get_kpi_compliance         — cohort-wide KPI completion vs 75% target
  get_overdue_assessments    — patients past their assessment due dates
  get_crisis_events          — crisis episodes within a date window
  get_disengaged_patients    — no contact beyond a configurable threshold
"""

from typing import Annotated, Literal
from fastmcp import FastMCP

# ── Data adapter — auto-selects based on USE_SUPABASE env var ────────────────
# Set USE_SUPABASE=true in .env (with SUPABASE_URL + SUPABASE_SERVICE_KEY)
# to query live Supabase data. Falls back to mock data when not set.
import os
from dotenv import load_dotenv
load_dotenv()

if os.environ.get("USE_SUPABASE", "").lower() == "true":
    from adapter.sql_adapter import (
        get_patients            as _get_patients,
        get_patient_detail      as _get_patient_detail,
        get_high_risk_patients  as _get_high_risk_patients,
        get_kpi_compliance      as _get_kpi_compliance,
        get_overdue_assessments as _get_overdue_assessments,
        get_crisis_events       as _get_crisis_events,
        get_disengaged_patients as _get_disengaged_patients,
    )
else:
    from adapter.mock_adapter import (
        get_patients            as _get_patients,
        get_patient_detail      as _get_patient_detail,
        get_high_risk_patients  as _get_high_risk_patients,
        get_kpi_compliance      as _get_kpi_compliance,
        get_overdue_assessments as _get_overdue_assessments,
        get_crisis_events       as _get_crisis_events,
        get_disengaged_patients as _get_disengaged_patients,
    )

mcp = FastMCP("clinicalmind-mcp")


# ── Tool 1: get_patients ──────────────────────────────────────────────────────

@mcp.tool()
def get_patients(
    risk_level: Annotated[
        Literal["High", "Moderate", "Low"] | None,
        "Filter by overall risk level: High, Moderate, or Low",
    ] = None,
    county: Annotated[
        str | None,
        "Filter by county name (partial match)",
    ] = None,
    provider: Annotated[
        str | None,
        "Filter by provider name (partial match) or provider ID",
    ] = None,
) -> dict:
    """Returns the patient list for the caseload with summary clinical data.
    Optionally filter by risk level, county, or provider name/ID."""
    result = _get_patients(risk_level=risk_level, county=county, provider=provider)
    return {
        "total":    len(result),
        "filters":  {"risk_level": risk_level, "county": county, "provider": provider},
        "patients": result,
    }


# ── Tool 2: get_patient_detail ────────────────────────────────────────────────

@mcp.tool()
def get_patient_detail(
    patient_id: Annotated[
        str,
        "The patient ID (e.g. PAT001). Use get_patients to look up IDs.",
    ],
) -> dict:
    """Returns the complete clinical record for a single patient — all
    assessments (PHQ-9, GAD-7, WHODAS, SSRS), KPI compliance dates,
    contact history, encounters, and crisis events."""
    result = _get_patient_detail(patient_id)
    if result is None:
        return {"error": f"No patient found with ID: {patient_id}"}
    return result


# ── Tool 3: get_high_risk_patients ────────────────────────────────────────────

@mcp.tool()
def get_high_risk_patients(
    risk_type: Annotated[
        Literal["all", "phq9", "ssrs", "crisis", "depression", "suicide"] | None,
        (
            'Narrow results: "phq9" or "depression" = PHQ-9 >=15 or suicidal ideation; '
            '"ssrs" or "suicide" = SSRS High; "crisis" = crisis event in last 28 days. '
            'Omit or use "all" for all high-risk patients.'
        ),
    ] = None,
) -> dict:
    """Returns patients flagged as high risk, ranked by acuity.
    Covers PHQ-9 severity (score >= 15 or suicidal ideation), SSRS risk level
    (plan or method present = High), and recent crisis events."""
    result = _get_high_risk_patients(risk_type=risk_type)
    return {
        "total":             len(result),
        "risk_type_filter":  risk_type or "all",
        "patients":          result,
    }


# ── Tool 4: get_kpi_compliance ────────────────────────────────────────────────

@mcp.tool()
def get_kpi_compliance(
    kpi_name: Annotated[
        Literal["bha", "sra", "aims", "whodas", "phq9", "beh_tp", "beh_csp"] | None,
        "Specific KPI to report on. Omit for all KPIs. Options: bha, sra, aims, whodas, phq9, beh_tp, beh_csp",
    ] = None,
) -> dict:
    """Returns KPI completion rates for the cohort vs the 75% target.
    KPIs tracked: BHA, SRA, AIMS, WHODAS (annual), PHQ-9, BEH-TP, BEH-CSP.
    Omit kpi_name for a full cohort-wide summary; specify it for one KPI."""
    return _get_kpi_compliance(kpi_name=kpi_name)


# ── Tool 5: get_overdue_assessments ──────────────────────────────────────────

@mcp.tool()
def get_overdue_assessments(
    assessment_type: Annotated[
        Literal["bha", "sra", "aims", "whodas", "phq9", "beh_tp", "beh_csp"] | None,
        "Assessment to check. Omit to check all. Options: bha, sra, aims, whodas, phq9, beh_tp, beh_csp",
    ] = None,
) -> dict:
    """Returns patients whose next due date has already passed for a given
    assessment type. Sorted by number of overdue assessments descending.
    Omit assessment_type to see all overdue assessments across all KPIs."""
    result = _get_overdue_assessments(assessment_type=assessment_type)
    return {
        "assessment_type_filter":      assessment_type or "all",
        "total_patients_with_overdue": len(result),
        "patients":                    result,
    }


# ── Tool 6: get_crisis_events ─────────────────────────────────────────────────

@mcp.tool()
def get_crisis_events(
    window_days: Annotated[
        int | None,
        "Look-back window in days. Default: 28. Use 7 for the past week.",
    ] = 28,
) -> dict:
    """Returns crisis episodes within a recent date window, sorted by recency.
    Each event includes patient name, crisis type, date, and clinical context.
    Default window is 28 days; use 7 for the past week."""
    return _get_crisis_events(window_days=window_days or 28)


# ── Tool 7: get_disengaged_patients ──────────────────────────────────────────

@mcp.tool()
def get_disengaged_patients(
    threshold_days: Annotated[
        int | None,
        "Days since last contact to flag as disengaged. Default: 30.",
    ] = 30,
) -> dict:
    """Returns patients who have had no recorded contact beyond a configurable
    day threshold. Sorted by longest gap first. Default threshold is 30 days.
    Flags overlapping high-risk patients and recent crisis events."""
    return _get_disengaged_patients(threshold_days=threshold_days or 30)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()

"""
ClinicalMind AI — Mock Data Adapter (Phase 1)

Implements the canonical adapter interface over the in-memory mock dataset.
To swap in real SQL (Phase 2), replace this file with sql_adapter.py and
update the import in server.py — no tool definitions change.

Interface:
  get_patients(risk_level, county, provider)
  get_patient_detail(patient_id)
  get_high_risk_patients(risk_type)
  get_kpi_compliance(kpi_name)
  get_overdue_assessments(assessment_type)
  get_crisis_events(window_days)
  get_disengaged_patients(threshold_days)
"""

from data.mock_data import generate_patients

KPI_NAMES    = ["bha", "sra", "aims", "whodas", "phq9", "beh_tp", "beh_csp"]
KPI_TARGET   = 75


def _patients() -> list[dict]:
    return generate_patients()


# ── 1. get_patients ───────────────────────────────────────────────────────────

def get_patients(
    risk_level: str | None = None,
    county: str | None = None,
    provider: str | None = None,
) -> list[dict]:
    lst = _patients()

    if risk_level:
        rl = risk_level.lower()
        lst = [p for p in lst if p["risk_level"].lower() == rl]
    if county:
        c = county.lower()
        lst = [p for p in lst if c in p["county"].lower()]
    if provider:
        pv = provider.lower()
        lst = [
            p for p in lst
            if pv in p["provider_name"].lower() or p["provider_id"].lower() == pv
        ]

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
        for p in lst
    ]


# ── 2. get_patient_detail ─────────────────────────────────────────────────────

def get_patient_detail(patient_id: str) -> dict | None:
    return next(
        (p for p in _patients() if p["patient_id"].lower() == patient_id.lower()),
        None,
    )


# ── 3. get_high_risk_patients ─────────────────────────────────────────────────

def get_high_risk_patients(risk_type: str | None = None) -> list[dict]:
    all_p = _patients()
    rt = (risk_type or "").lower()

    if not rt or rt == "all":
        flagged = [p for p in all_p if p["risk_level"] == "High"]
    elif rt in ("phq9", "depression"):
        flagged = [p for p in all_p if p["phq9"]["severity"] == "High"]
    elif rt in ("ssrs", "suicide"):
        flagged = [p for p in all_p if p["ssrs"]["risk_level"] == "High"]
    elif rt == "crisis":
        flagged = [p for p in all_p if p["has_crisis_28d"]]
    else:
        flagged = [p for p in all_p if p["risk_level"] == "High"]

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
        for p in sorted(flagged, key=_sort_key)
    ]


# ── 4. get_kpi_compliance ─────────────────────────────────────────────────────

def get_kpi_compliance(kpi_name: str | None = None) -> dict:
    all_p = _patients()
    total = len(all_p)

    def _summary(name: str) -> dict:
        completed = sum(1 for p in all_p if not p["kpi"][name]["overdue"])
        overdue   = total - completed
        pct       = round((completed / total) * 100)
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
    overall_pct       = round((overall_completed / overall_total) * 100)

    return {
        "overall_compliance_pct":  overall_pct,
        "target_pct":              KPI_TARGET,
        "meets_target":            overall_pct >= KPI_TARGET,
        "gap_to_target":           0 if overall_pct >= KPI_TARGET else KPI_TARGET - overall_pct,
        "by_kpi":                  by_kpi,
        "patients_fully_compliant": sum(1 for p in all_p if p["kpi_compliance_pct"] == 100),
        "patients_below_target":    sum(1 for p in all_p if p["kpi_compliance_pct"] < KPI_TARGET),
    }


# ── 5. get_overdue_assessments ────────────────────────────────────────────────

def get_overdue_assessments(assessment_type: str | None = None) -> list[dict]:
    all_p = _patients()
    at = (assessment_type or "").lower().replace("-", "_")

    if at and at not in KPI_NAMES:
        return [{"error": f"Unknown type: {assessment_type}. Valid: {', '.join(KPI_NAMES)}"}]

    types_to_check = [at] if at else KPI_NAMES
    result = []

    for p in all_p:
        overdue_list = [
            {
                "assessment":    k.upper().replace("_", "-"),
                "last_completed": p["kpi"][k]["last_completed"],
                "due_date":       p["kpi"][k]["due_date"],
            }
            for k in types_to_check if p["kpi"][k]["overdue"]
        ]
        if overdue_list:
            result.append({
                "patient_id":          p["patient_id"],
                "name":                p["name"],
                "diagnosis":           p["diagnosis"],
                "provider_name":       p["provider_name"],
                "risk_level":          p["risk_level"],
                "overdue_assessments": overdue_list,
                "overdue_count":       len(overdue_list),
            })

    return sorted(result, key=lambda x: -x["overdue_count"])


# ── 6. get_crisis_events ──────────────────────────────────────────────────────

def get_crisis_events(window_days: int = 28) -> dict:
    all_p = _patients()
    days  = int(window_days)
    events = []

    for p in all_p:
        for e in p["crisis_events"]:
            if e["days_since"] <= days:
                events.append({
                    "patient_id":   p["patient_id"],
                    "name":         p["name"],
                    "diagnosis":    p["diagnosis"],
                    "provider_name": p["provider_name"],
                    "risk_level":   p["risk_level"],
                    "event_id":     e["event_id"],
                    "crisis_date":  e["crisis_date"],
                    "crisis_type":  e["crisis_type"],
                    "days_ago":     e["days_since"],
                    "within_7_days": e["within_7_days"],
                    "ssrs_risk":    p["ssrs"]["risk_level"],
                    "phq9_score":   p["phq9"]["total_score"],
                })

    events.sort(key=lambda e: e["days_ago"])

    return {
        "window_days":      window_days,
        "total_events":     len(events),
        "unique_patients":  len({e["patient_id"] for e in events}),
        "events":           events,
    }


# ── 7. get_disengaged_patients ────────────────────────────────────────────────

def get_disengaged_patients(threshold_days: int = 30) -> dict:
    all_p = _patients()
    days  = int(threshold_days)

    disengaged = sorted(
        [p for p in all_p if p["days_since_last_contact"] > days],
        key=lambda p: -p["days_since_last_contact"],
    )

    return {
        "threshold_days":   threshold_days,
        "total_disengaged": len(disengaged),
        "patients": [
            {
                "patient_id":               p["patient_id"],
                "name":                     p["name"],
                "diagnosis":                p["diagnosis"],
                "provider_name":            p["provider_name"],
                "risk_level":               p["risk_level"],
                "last_contact_date":        p["last_contact_date"],
                "days_since_last_contact":  p["days_since_last_contact"],
                "last_contact_type":        (p["contacts"][0]["contact_type"] if p["contacts"] else "Unknown"),
                "phq9_score":               p["phq9"]["total_score"],
                "ssrs_risk":                p["ssrs"]["risk_level"],
                "has_crisis_28d":           p["has_crisis_28d"],
            }
            for p in disengaged
        ],
    }

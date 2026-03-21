"""
ClinicalMind AI — Internal Medicine Mock Adapter

Implements the IM adapter interface over im_mock_data.

Interface:
  get_im_patients(risk_level, condition, provider)
  get_im_patient_detail(patient_id)
  get_chronic_disease_panel(condition)
  get_preventive_care_gaps(gap_type)
"""

from __future__ import annotations

from datetime import date
from typing import Optional
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

    diabetes     — patients with latest A1c > 8.0
    ckd          — patients with eGFR slope ≤ -3 units/year
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

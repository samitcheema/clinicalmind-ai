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

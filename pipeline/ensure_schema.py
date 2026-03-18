#!/usr/bin/env python3
"""
ClinicalMind AI — Schema Initialisation

Creates all required Supabase tables and RLS policies if they do not already
exist. Every statement is fully idempotent — safe to run on an empty database
or on one that already has all tables.

Standalone usage:
    cd pipeline
    python ensure_schema.py

Called automatically by orchestrator.py as Stage 1 of every live run.
Skipped in --dry-run mode (no database connection required).

Requires DATABASE_URL in pipeline/.env:
    Supabase Dashboard → Project Settings → Database → Connection string (URI)
    e.g. postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres
"""
from __future__ import annotations

import os
import sys
import time

import psycopg2

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from pipeline_run import StageResult


# ── Table DDL (CREATE IF NOT EXISTS — never destructive) ─────────────────────
# Ordered to satisfy FK dependencies.

_DDL: list[str] = [
    'CREATE EXTENSION IF NOT EXISTS "pgcrypto"',

    # ── providers ──────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS providers (
        provider_id  TEXT PRIMARY KEY,
        name         TEXT NOT NULL,
        team         TEXT NOT NULL,
        created_at   TIMESTAMPTZ DEFAULT NOW()
    )
    """,

    # ── patients (PHI — service_role only) ─────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS patients (
        patient_id                TEXT PRIMARY KEY,
        name                      TEXT NOT NULL,
        date_of_birth             DATE NOT NULL,
        diagnosis                 TEXT,
        county                    TEXT,
        service_type              TEXT,
        provider_id               TEXT REFERENCES providers(provider_id),
        risk_level                TEXT,
        engagement_flag           BOOLEAN DEFAULT FALSE,
        days_since_last_contact   INT,
        last_contact_date         DATE,
        kpi_compliance_pct        INT,
        has_crisis_7d             BOOLEAN DEFAULT FALSE,
        has_crisis_28d            BOOLEAN DEFAULT FALSE,
        created_at                TIMESTAMPTZ DEFAULT NOW(),
        updated_at                TIMESTAMPTZ DEFAULT NOW()
    )
    """,

    # ── assessments_phq9 ───────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS assessments_phq9 (
        id                UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        patient_id        TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
        assessment_date   DATE,
        total_score       INT,
        item_scores       JSONB,
        suicidal_ideation BOOLEAN DEFAULT FALSE,
        severity          TEXT,
        created_at        TIMESTAMPTZ DEFAULT NOW()
    )
    """,

    # ── assessments_gad7 ───────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS assessments_gad7 (
        id                UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        patient_id        TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
        assessment_date   DATE,
        total_score       INT,
        item_scores       JSONB,
        severity          TEXT,
        created_at        TIMESTAMPTZ DEFAULT NOW()
    )
    """,

    # ── assessments_whodas ─────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS assessments_whodas (
        id                UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        patient_id        TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
        assessment_date   DATE,
        total_score       INT,
        disability_level  TEXT,
        created_at        TIMESTAMPTZ DEFAULT NOW()
    )
    """,

    # ── assessments_ssrs ───────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS assessments_ssrs (
        id                  UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        patient_id          TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
        assessment_date     DATE,
        suicidal_ideation   BOOLEAN DEFAULT FALSE,
        ideation_intensity  INT DEFAULT 0,
        intent              BOOLEAN DEFAULT FALSE,
        plan                BOOLEAN DEFAULT FALSE,
        method              BOOLEAN DEFAULT FALSE,
        history_attempt     BOOLEAN DEFAULT FALSE,
        risk_level          TEXT,
        created_at          TIMESTAMPTZ DEFAULT NOW()
    )
    """,

    # ── encounters ─────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS encounters (
        encounter_id    TEXT PRIMARY KEY,
        patient_id      TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
        admit_date      DATE,
        discharge_date  DATE,
        encounter_type  TEXT,
        is_psychiatric_emergency BOOLEAN DEFAULT FALSE,
        is_crisis_intervention    BOOLEAN DEFAULT FALSE,
        created_at      TIMESTAMPTZ DEFAULT NOW()
    )
    """,

    # ── contacts ───────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS contacts (
        contact_id    TEXT PRIMARY KEY,
        patient_id    TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
        contact_date  DATE,
        contact_type  TEXT,
        provider_id   TEXT REFERENCES providers(provider_id),
        days_since    INT,
        created_at    TIMESTAMPTZ DEFAULT NOW()
    )
    """,

    # ── crisis_events ──────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS crisis_events (
        event_id         TEXT PRIMARY KEY,
        patient_id       TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
        crisis_date      DATE,
        crisis_type      TEXT,
        within_7_days    BOOLEAN DEFAULT FALSE,
        within_28_days   BOOLEAN DEFAULT FALSE,
        days_since       INT,
        created_at       TIMESTAMPTZ DEFAULT NOW()
    )
    """,

    # ── kpi_compliance ─────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS kpi_compliance (
        id             UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        patient_id     TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
        kpi_name       TEXT NOT NULL,
        last_completed DATE,
        due_date       DATE,
        overdue        BOOLEAN DEFAULT FALSE,
        created_at     TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE(patient_id, kpi_name)
    )
    """,

    # ── clinic_stats (public aggregate — anon-readable) ────────────────────
    """
    CREATE TABLE IF NOT EXISTS clinic_stats (
        id                          INT PRIMARY KEY DEFAULT 1,
        total_patients              INT,
        high_risk_count             INT,
        moderate_risk_count         INT,
        low_risk_count              INT,
        overall_kpi_compliance_pct  INT,
        patients_below_kpi_target   INT,
        crisis_events_7d            INT,
        crisis_events_28d           INT,
        disengaged_patients_count   INT,
        high_risk_disengaged_count  INT,
        diagnosis_breakdown         JSONB,
        county_breakdown            JSONB,
        service_breakdown           JSONB,
        updated_at                  TIMESTAMPTZ DEFAULT NOW()
    )
    """,

    # ── pipeline_runs (operational audit log) ──────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS pipeline_runs (
        run_id               TEXT PRIMARY KEY,
        started_at           TIMESTAMPTZ NOT NULL,
        completed_at         TIMESTAMPTZ,
        status               TEXT NOT NULL DEFAULT 'running',
        config               JSONB,
        records_extracted    INT DEFAULT 0,
        records_transformed  INT DEFAULT 0,
        records_loaded       INT DEFAULT 0,
        records_rejected     INT DEFAULT 0,
        stages               JSONB,
        error_message        TEXT
    )
    """,

    # ── assessments_dla20 (Daily Living Activities — 20 domains, 1–4 scale) ──
    """
    CREATE TABLE IF NOT EXISTS assessments_dla20 (
        id                   UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        patient_id           TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
        assessment_date      DATE NOT NULL,
        assessment_version   TEXT DEFAULT 'clinician_rated',
        assessor_id          TEXT REFERENCES providers(provider_id),
        family_relationships NUMERIC(3,1),
        problem_solving      NUMERIC(3,1),
        nutrition            NUMERIC(3,1),
        managing_money       NUMERIC(3,1),
        managing_time        NUMERIC(3,1),
        safety               NUMERIC(3,1),
        communication        NUMERIC(3,1),
        dress                NUMERIC(3,1),
        housing_stability    NUMERIC(3,1),
        grooming             NUMERIC(3,1),
        personal_hygiene     NUMERIC(3,1),
        behavior_norms       NUMERIC(3,1),
        coping_skills        NUMERIC(3,1),
        productivity         NUMERIC(3,1),
        sexuality            NUMERIC(3,1),
        social_network       NUMERIC(3,1),
        community_resources  NUMERIC(3,1),
        leisure              NUMERIC(3,1),
        alcohol_drug_use     NUMERIC(3,1),
        health_practices     NUMERIC(3,1),
        total_score          NUMERIC(5,2),
        composite_score      NUMERIC(4,2),
        difference_from_last NUMERIC(5,2),
        items_rated          INT DEFAULT 20,
        interpretation_level TEXT,
        created_at           TIMESTAMPTZ DEFAULT NOW()
    )
    """,

    # ── assessments_pain (enhanced pain assessment — NRS + interference) ───
    """
    CREATE TABLE IF NOT EXISTS assessments_pain (
        id                  UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        patient_id          TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
        assessment_date     DATE NOT NULL,
        scale_type          TEXT DEFAULT 'NRS',
        pain_score          NUMERIC(4,1),
        pain_locations      JSONB,
        pain_quality        TEXT[],
        onset_date          DATE,
        duration_type       TEXT,
        frequency_pattern   TEXT,
        interference_score  NUMERIC(3,1),
        affected_activities TEXT[],
        alleviating_factors TEXT[],
        aggravating_factors TEXT[],
        associated_symptoms TEXT[],
        pain_source_value   TEXT,
        created_at          TIMESTAMPTZ DEFAULT NOW()
    )
    """,

    # ── prescriptions (FHIR MedicationRequest — behavioral health enhanced) ─
    """
    CREATE TABLE IF NOT EXISTS prescriptions (
        id                        UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        patient_id                TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
        medication_name           TEXT NOT NULL,
        drug_class                TEXT,
        psychotropic_class        TEXT,
        status                    TEXT DEFAULT 'active',
        dosage                    TEXT,
        dose_value                NUMERIC(8,2),
        dose_unit                 TEXT,
        frequency                 TEXT,
        route                     TEXT DEFAULT 'PO',
        as_needed                 BOOLEAN DEFAULT FALSE,
        days_supply               INT,
        refills_authorized        INT,
        refills_remaining         INT,
        ordered_date              DATE,
        start_date                DATE,
        end_date                  DATE,
        is_lai                    BOOLEAN DEFAULT FALSE,
        lai_interval_days         INT,
        last_injection_date       DATE,
        next_injection_date       DATE,
        adherence_concern         TEXT DEFAULT 'none',
        refill_pattern            TEXT,
        prescribing_provider_id   TEXT REFERENCES providers(provider_id),
        prescribing_provider_name TEXT,
        created_at                TIMESTAMPTZ DEFAULT NOW()
    )
    """,

    # ── inpatient_admissions (FHIR Encounter — inpatient BH specific) ───────
    """
    CREATE TABLE IF NOT EXISTS inpatient_admissions (
        id                     UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        patient_id             TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
        encounter_id           TEXT,
        admission_date         DATE NOT NULL,
        discharge_date         DATE,
        length_of_stay_days    INT,
        ward                   TEXT,
        ward_specialty         TEXT,
        service_type           TEXT DEFAULT 'psychiatric',
        admission_type         TEXT DEFAULT 'voluntary',
        legal_hold_type        TEXT,
        admit_source           TEXT,
        discharge_disposition  TEXT,
        restraint_used         BOOLEAN DEFAULT FALSE,
        seclusion_used         BOOLEAN DEFAULT FALSE,
        out_of_area            BOOLEAN DEFAULT FALSE,
        readmitted_within_30d  BOOLEAN DEFAULT FALSE,
        primary_diagnosis_code TEXT,
        primary_diagnosis_desc TEXT,
        created_at             TIMESTAMPTZ DEFAULT NOW()
    )
    """,

    # ── crisis_safety_plans (Stanley-Brown Safety Planning Intervention) ────
    """
    CREATE TABLE IF NOT EXISTS crisis_safety_plans (
        id                      UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        patient_id              TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
        plan_status             TEXT DEFAULT 'active',
        crisis_risk_level       TEXT,
        created_date            DATE NOT NULL,
        last_reviewed_date      DATE,
        next_review_date        DATE,
        created_by_provider_id  TEXT REFERENCES providers(provider_id),
        warning_signs           JSONB,
        internal_coping         JSONB,
        social_distractions     JSONB,
        social_support_contacts JSONB,
        professional_contacts   JSONB,
        means_restriction       JSONB,
        risk_factors            TEXT[],
        protective_factors      TEXT[],
        patient_acknowledged    BOOLEAN DEFAULT FALSE,
        acknowledgment_date     DATE,
        created_at              TIMESTAMPTZ DEFAULT NOW()
    )
    """,

    # ── ai_risk_scores (Claude-computed risk assessments) ────────────────────
    """
    CREATE TABLE IF NOT EXISTS ai_risk_scores (
        id                 UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        patient_id         TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
        scored_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        risk_level         TEXT NOT NULL,
        propensity_score   FLOAT NOT NULL,
        early_warning      BOOLEAN DEFAULT FALSE,
        velocity_concern   BOOLEAN DEFAULT FALSE,
        top_factors        JSONB,
        reasoning          TEXT,
        recommended_action TEXT,
        model_used         TEXT,
        created_at         TIMESTAMPTZ DEFAULT NOW()
    )
    """,
]

# ── ALTER TABLE: add columns to existing tables (idempotent) ─────────────────
_ALTER: list[str] = [
    "ALTER TABLE encounters ADD COLUMN IF NOT EXISTS appt_missed BOOLEAN DEFAULT FALSE",
    "ALTER TABLE encounters ADD COLUMN IF NOT EXISTS appt_status TEXT",
]

# ── RLS enablement + policies ─────────────────────────────────────────────────
# ALTER TABLE ... ENABLE ROW LEVEL SECURITY is idempotent.
# CREATE POLICY IF NOT EXISTS requires PostgreSQL 15+ (Supabase runs PG 15+).

_PRIVATE_TABLES = [
    "providers", "patients",
    "assessments_phq9", "assessments_gad7", "assessments_whodas", "assessments_ssrs",
    "assessments_dla20", "assessments_pain",
    "prescriptions", "inpatient_admissions", "crisis_safety_plans", "ai_risk_scores",
    "encounters", "contacts", "crisis_events", "kpi_compliance", "pipeline_runs",
]

_ALL_TABLES = _PRIVATE_TABLES + ["clinic_stats"]


def _rls_statements() -> list[str]:
    stmts: list[str] = []

    # Enable RLS on every table (idempotent)
    for t in _ALL_TABLES:
        stmts.append(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")

    # Private tables: service_role gets full access, anon gets nothing
    # Uses DO block to skip gracefully if policy already exists (works on PG < 15)
    for t in _PRIVATE_TABLES:
        stmts.append(
            "DO $$ BEGIN "
            f'CREATE POLICY "service_role_all" ON {t} '
            f"FOR ALL TO service_role USING (true) WITH CHECK (true); "
            "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
        )

    # clinic_stats: anon can SELECT (for website dashboard), service_role full access
    stmts.append(
        "DO $$ BEGIN "
        'CREATE POLICY "anon_select" ON clinic_stats '
        "FOR SELECT TO anon USING (true); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    )
    stmts.append(
        "DO $$ BEGIN "
        'CREATE POLICY "service_role_all" ON clinic_stats '
        "FOR ALL TO service_role USING (true) WITH CHECK (true); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    )

    return stmts


# ── Public API ────────────────────────────────────────────────────────────────

def run(database_url: str) -> StageResult:
    """
    Connect to Postgres and ensure all tables + RLS policies exist.

    Args:
        database_url: PostgreSQL connection URI (from DATABASE_URL env var)

    Returns:
        StageResult with records_out = total DDL statements executed
    """
    t0 = time.perf_counter()
    all_stmts = _DDL + _rls_statements()
    executed = 0

    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cur = conn.cursor()

        for stmt in all_stmts + _ALTER:
            cur.execute(stmt)
            executed += 1

        cur.close()
        conn.close()

        result = StageResult(
            name="schema",
            status="ok",
            records_out=executed,
            duration_secs=time.perf_counter() - t0,
            metadata={
                "tables":     len(_ALL_TABLES),
                "statements": executed,
            },
        )

    except Exception as exc:
        result = StageResult(
            name="schema",
            status="failed",
            duration_secs=time.perf_counter() - t0,
            error=str(exc),
        )

    return result


# ── Standalone entry point ────────────────────────────────────────────────────

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_HERE, ".env"))

    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        sys.exit(
            "ERROR: DATABASE_URL not set.\n"
            "       Add it to pipeline/.env  (Supabase Dashboard → Settings →\n"
            "       Database → Connection string → URI format)"
        )

    print("ClinicalMind AI — Schema Initialisation")
    print("=" * 44)
    result = run(db_url)

    if result.status == "ok":
        n  = result.metadata.get("tables", 0)
        st = result.metadata.get("statements", 0)
        print(f"✓  {n} tables verified  ·  {st} statements executed  ({result.duration_secs:.2f}s)")
        print("All tables ready.")
    else:
        print(f"✗  FAILED: {result.error}")
        sys.exit(1)

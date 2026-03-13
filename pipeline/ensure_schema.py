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
        pes_flag        BOOLEAN DEFAULT FALSE,
        cis_flag        BOOLEAN DEFAULT FALSE,
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
]

# ── RLS enablement + policies ─────────────────────────────────────────────────
# ALTER TABLE ... ENABLE ROW LEVEL SECURITY is idempotent.
# CREATE POLICY IF NOT EXISTS requires PostgreSQL 15+ (Supabase runs PG 15+).

_PRIVATE_TABLES = [
    "providers", "patients",
    "assessments_phq9", "assessments_gad7", "assessments_whodas", "assessments_ssrs",
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

        for stmt in all_stmts:
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

-- ============================================================
-- ClinicalMind AI — Supabase Schema
-- Run this in the Supabase SQL Editor before running seed.py
--
-- Architecture:
--   Private tables  (service_role key only — MCP server):
--     providers, patients, assessments_*, encounters,
--     contacts, crisis_events, kpi_compliance
--   Public table  (anon key — website dashboard):
--     clinic_stats  (aggregate only, zero PII)
-- ============================================================

-- ── Extensions ───────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Drop existing tables (safe re-run) ───────────────────────
DROP TABLE IF EXISTS kpi_compliance   CASCADE;
DROP TABLE IF EXISTS crisis_events    CASCADE;
DROP TABLE IF EXISTS contacts         CASCADE;
DROP TABLE IF EXISTS encounters       CASCADE;
DROP TABLE IF EXISTS assessments_ssrs   CASCADE;
DROP TABLE IF EXISTS assessments_whodas CASCADE;
DROP TABLE IF EXISTS assessments_gad7   CASCADE;
DROP TABLE IF EXISTS assessments_phq9   CASCADE;
DROP TABLE IF EXISTS patients         CASCADE;
DROP TABLE IF EXISTS providers        CASCADE;
DROP TABLE IF EXISTS clinic_stats     CASCADE;


-- ── providers ─────────────────────────────────────────────────
CREATE TABLE providers (
    provider_id  TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    team         TEXT NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ── patients (PHI — service_role only) ────────────────────────
CREATE TABLE patients (
    patient_id                TEXT PRIMARY KEY,
    name                      TEXT NOT NULL,        -- synthetic only; strip in public views
    date_of_birth             DATE NOT NULL,        -- synthetic only
    diagnosis                 TEXT,
    county                    TEXT,
    service_type              TEXT,                 -- ACT | CSP
    provider_id               TEXT REFERENCES providers(provider_id),
    risk_level                TEXT,                 -- High | Moderate | Low
    engagement_flag           BOOLEAN DEFAULT FALSE,
    days_since_last_contact   INT,
    last_contact_date         DATE,
    kpi_compliance_pct        INT,
    has_crisis_7d             BOOLEAN DEFAULT FALSE,
    has_crisis_28d            BOOLEAN DEFAULT FALSE,
    created_at                TIMESTAMPTZ DEFAULT NOW(),
    updated_at                TIMESTAMPTZ DEFAULT NOW()
);

-- ── assessments_phq9 ──────────────────────────────────────────
CREATE TABLE assessments_phq9 (
    id                UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    patient_id        TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
    assessment_date   DATE,
    total_score       INT,
    item_scores       JSONB,
    suicidal_ideation BOOLEAN DEFAULT FALSE,
    severity          TEXT,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- ── assessments_gad7 ──────────────────────────────────────────
CREATE TABLE assessments_gad7 (
    id                UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    patient_id        TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
    assessment_date   DATE,
    total_score       INT,
    item_scores       JSONB,
    severity          TEXT,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- ── assessments_whodas ────────────────────────────────────────
CREATE TABLE assessments_whodas (
    id                UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    patient_id        TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
    assessment_date   DATE,
    total_score       INT,
    disability_level  TEXT,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- ── assessments_ssrs ──────────────────────────────────────────
CREATE TABLE assessments_ssrs (
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
);

-- ── encounters ────────────────────────────────────────────────
CREATE TABLE encounters (
    encounter_id    TEXT PRIMARY KEY,
    patient_id      TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
    admit_date      DATE,
    discharge_date  DATE,
    encounter_type  TEXT,
    pes_flag        BOOLEAN DEFAULT FALSE,
    cis_flag        BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── contacts ──────────────────────────────────────────────────
CREATE TABLE contacts (
    contact_id    TEXT PRIMARY KEY,
    patient_id    TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
    contact_date  DATE,
    contact_type  TEXT,
    provider_id   TEXT REFERENCES providers(provider_id),
    days_since    INT,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ── crisis_events ─────────────────────────────────────────────
CREATE TABLE crisis_events (
    event_id         TEXT PRIMARY KEY,
    patient_id       TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
    crisis_date      DATE,
    crisis_type      TEXT,
    within_7_days    BOOLEAN DEFAULT FALSE,
    within_28_days   BOOLEAN DEFAULT FALSE,
    days_since       INT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ── kpi_compliance ────────────────────────────────────────────
CREATE TABLE kpi_compliance (
    id             UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    patient_id     TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
    kpi_name       TEXT NOT NULL,
    last_completed DATE,
    due_date       DATE,
    overdue        BOOLEAN DEFAULT FALSE,
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(patient_id, kpi_name)
);

-- ── clinic_stats  (PUBLIC — anon can read, no PII) ────────────
-- Single-row summary refreshed by seed.py after every pipeline run.
-- The website reads this table with the anon key.
CREATE TABLE clinic_stats (
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
    diagnosis_breakdown         JSONB,   -- {"Major Depressive Disorder": 12, ...}
    county_breakdown            JSONB,   -- {"Westchester": 10, ...}
    service_breakdown           JSONB,   -- {"ACT": 24, "CSP": 21}
    updated_at                  TIMESTAMPTZ DEFAULT NOW()
);

-- ── Row Level Security ────────────────────────────────────────
ALTER TABLE providers          ENABLE ROW LEVEL SECURITY;
ALTER TABLE patients           ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessments_phq9   ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessments_gad7   ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessments_whodas ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessments_ssrs   ENABLE ROW LEVEL SECURITY;
ALTER TABLE encounters         ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts           ENABLE ROW LEVEL SECURITY;
ALTER TABLE crisis_events      ENABLE ROW LEVEL SECURITY;
ALTER TABLE kpi_compliance     ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinic_stats       ENABLE ROW LEVEL SECURITY;

-- Private tables: service_role full access, anon no access
DO $$
DECLARE
    t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'providers','patients','assessments_phq9','assessments_gad7',
        'assessments_whodas','assessments_ssrs','encounters','contacts',
        'crisis_events','kpi_compliance'
    ] LOOP
        EXECUTE format(
            'CREATE POLICY "service_role_all" ON %I FOR ALL TO service_role USING (true) WITH CHECK (true)',
            t
        );
    END LOOP;
END $$;

-- Public table: anon can SELECT, service_role has full access
CREATE POLICY "anon_select"        ON clinic_stats FOR SELECT TO anon         USING (true);
CREATE POLICY "service_role_all"   ON clinic_stats FOR ALL    TO service_role USING (true) WITH CHECK (true);

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

# ── src schema: staging / source tables ──────────────────────────────────────

_SRC_DDL: list[str] = [
    "CREATE SCHEMA IF NOT EXISTS src",

    # ── departments_of_interest ─────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS src.departments_of_interest (
        department_name      VARCHAR(255) NOT NULL PRIMARY KEY,
        is_inpatient         BOOLEAN NOT NULL,
        is_outpatient        BOOLEAN NOT NULL,
        is_crisis_department BOOLEAN NOT NULL
    )
    """,

    # ── departments ─────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS src.departments (
        department_key       BIGINT,
        department_name      VARCHAR(255),
        location_name        VARCHAR(255),
        county               VARCHAR(255),
        city                 VARCHAR(255),
        type                 VARCHAR(255),
        is_inpatient         BOOLEAN,
        is_outpatient        BOOLEAN,
        is_crisis_department BOOLEAN
    )
    """,

    # ── encounter ───────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS src.encounter (
        person_id                BIGINT,
        provider_id              BIGINT,
        encounter_id             BIGINT,
        note_id                  BIGINT,
        encounter_status         VARCHAR(100),
        encounter_type           VARCHAR(100),
        note_status              VARCHAR(100),
        encounter_date           DATE,
        appointment_date_time    TIMESTAMPTZ,
        service_instant          TIMESTAMPTZ,
        admit_date               DATE,
        admit_date_time          TIMESTAMPTZ,
        discharge_date           DATE,
        discharge_instant        TIMESTAMPTZ,
        encounter_visit_desc     VARCHAR(255),
        visit_desc               VARCHAR(255),
        visit_epic_id            VARCHAR(100),
        admission_source         VARCHAR(255),
        discharge_disposition    VARCHAR(255),
        department_key           BIGINT,
        department_name          VARCHAR(255),
        department_type          VARCHAR(100),
        pos_key                  BIGINT,
        pos_name                 VARCHAR(255),
        county                   VARCHAR(100),
        location_name            VARCHAR(255),
        provider_npi             VARCHAR(50),
        provider_type            VARCHAR(100),
        clinician_title          VARCHAR(100),
        last_name                VARCHAR(255),
        first_name               VARCHAR(255),
        role                     VARCHAR(100),
        role_category            VARCHAR(255),
        email                    VARCHAR(255),
        can_authorize_medication  BOOLEAN,
        doc_note_type            VARCHAR(100),
        appt_status              VARCHAR(50),
        pes_reason               VARCHAR(255),
        is_psychiatric_emergency  BOOLEAN,
        is_crisis_intervention    BOOLEAN
    )
    """,
    "CREATE INDEX IF NOT EXISTS IX_encounter_person    ON src.encounter (person_id)",
    "CREATE INDEX IF NOT EXISTS IX_encounter_encounter ON src.encounter (encounter_id)",

    # ── person ──────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS src.person (
        person_id                  BIGINT,
        start_date                 DATE,
        death_date                 DATE,
        gender_identity            VARCHAR(156),
        sex                        VARCHAR(156),
        sex_assigned_at_birth      VARCHAR(156),
        ethnicity                  VARCHAR(300),
        primary_care_provider_id   BIGINT,
        first_name                 VARCHAR(200),
        last_name                  VARCHAR(300),
        birth_date                 DATE,
        primary_mrn                VARCHAR(150),
        postal_code                VARCHAR(100),
        first_race                 VARCHAR(255),
        marital_status             VARCHAR(300)
    )
    """,
    "CREATE INDEX IF NOT EXISTS IX_person_person_id ON src.person (person_id)",

    # ── dla20 ───────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS src.dla20 (
        person_id            BIGINT,
        encounter_id         BIGINT,
        employee_id          BIGINT,
        assessment_date      TIMESTAMPTZ,
        accepted_flg         SMALLINT,
        total_score          NUMERIC(5,2),
        difference_from_last NUMERIC(5,2),
        family_relationships NUMERIC(3,2),
        problem_solving      NUMERIC(3,2),
        nutrition            NUMERIC(3,2),
        managing_money       NUMERIC(3,2),
        managing_time        NUMERIC(3,2),
        safety               NUMERIC(3,2),
        communication        NUMERIC(3,2),
        dress                NUMERIC(3,2),
        housing_stability    NUMERIC(3,2),
        grooming             NUMERIC(3,2),
        personal_hygiene     NUMERIC(3,2),
        behavior_norms       NUMERIC(3,2),
        coping_skills        NUMERIC(3,2),
        productivity         NUMERIC(3,2),
        sexuality            NUMERIC(3,2),
        social_network       NUMERIC(3,2),
        community_resources  NUMERIC(3,2),
        leisure              NUMERIC(3,2),
        alcohol_drug_use     NUMERIC(3,2),
        health_practices     NUMERIC(3,2)
    )
    """,

    # ── cssrs ────────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS src.cssrs (
        person_id               BIGINT,
        encounter_id            BIGINT,
        employee_id             BIGINT,
        assessment_date         TIMESTAMPTZ,
        accepted_flg            SMALLINT,
        passive_ideation        VARCHAR(4),
        active_ideation         VARCHAR(4),
        ideation_with_intent    VARCHAR(4),
        ideation_with_plan      VARCHAR(4),
        ideation_with_method    VARCHAR(4),
        prior_suicidal_behavior VARCHAR(4)
    )
    """,

    # ── gad7 ─────────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS src.gad7 (
        person_id                    BIGINT,
        encounter_id                 BIGINT,
        employee_id                  BIGINT,
        assessment_date              TIMESTAMPTZ,
        accepted_flg                 SMALLINT,
        feeling_nervous              NUMERIC(3,2),
        restless                     NUMERIC(3,2),
        worry_about_different_things NUMERIC(3,2),
        trouble_relaxing             NUMERIC(3,2),
        easily_annoyed               NUMERIC(3,2),
        feeling_afraid               NUMERIC(3,2),
        constant_worry               NUMERIC(3,2),
        total_score                  NUMERIC(4,2)
    )
    """,

    # ── phq9 ─────────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS src.phq9 (
        person_id             BIGINT,
        encounter_id          BIGINT,
        employee_id           BIGINT,
        assessment_date       TIMESTAMPTZ,
        accepted_flg          SMALLINT,
        interest              NUMERIC(3,2),
        feeling_hopeless      NUMERIC(3,2),
        trouble_sleeping      NUMERIC(3,2),
        feeling_tired         NUMERIC(3,2),
        poor_appetite         NUMERIC(3,2),
        feeling_bad           NUMERIC(3,2),
        trouble_concentrating NUMERIC(3,2),
        moving_slowly         NUMERIC(3,2),
        better_off_dead       NUMERIC(3,2),
        how_difficult         NUMERIC(3,2),
        total_score           NUMERIC(4,2)
    )
    """,

    # ── safety_plan_mapping ──────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS src.safety_plan_mapping (
        field_id      VARCHAR(50)  NOT NULL PRIMARY KEY,
        plan_name     VARCHAR(300) NOT NULL,
        step_number   SMALLINT     NOT NULL,
        step_label    VARCHAR(100) NOT NULL,
        field_label   VARCHAR(255) NOT NULL,
        data_type     VARCHAR(50)  NOT NULL,
        is_repeatable BOOLEAN      NOT NULL DEFAULT FALSE,
        display_order SMALLINT     NOT NULL
    )
    """,

    # ── crisis_safety_plan ───────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS src.crisis_safety_plan (
        person_id                  BIGINT,
        attribute_id               BIGINT,
        smart_data_element_epic_id VARCHAR(50),
        plan_name                  VARCHAR(300),
        input_name                 VARCHAR(300),
        input_abbreviation         VARCHAR(300),
        data_type                  VARCHAR(300),
        completion_date            DATE,
        input_value                VARCHAR(300),
        input_numeric_value        NUMERIC(18,2),
        input_date_value           DATE
    )
    """,

    # ── diagnosis ────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS src.diagnosis (
        person_id           BIGINT,
        diagnosis_key       BIGINT,
        encounter_id        BIGINT,
        diag_start_date     DATE,
        diag_end_date       DATE,
        diagnosis_code_type VARCHAR(300),
        diagnosis_code      VARCHAR(300),
        diagnosis_desc      VARCHAR(850),
        diagnosis_type      VARCHAR(350),
        category            VARCHAR(150)
    )
    """,

    # ── drug ─────────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS src.drug (
        person_id  BIGINT,
        drug_id    BIGINT,
        drug_name  VARCHAR(255),
        start_date DATE,
        end_date   DATE
    )
    """,

    # ── inpatient ───────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS src.inpatient (
        encounter_id   BIGINT,
        person_id      BIGINT,
        ward           VARCHAR(300),
        ward_specialty VARCHAR(300),
        out_of_area    BOOLEAN,
        start_date     DATE,
        end_date       DATE
    )
    """,

    # ── prescriptions ───────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS src.prescriptions (
        person_id                 BIGINT,
        drug_id                   BIGINT,
        drug_name                 VARCHAR(255),
        days_supply               NUMERIC(18,2),
        refills_remaining         SMALLINT,
        dosage                    TEXT,
        drug_route                VARCHAR(255),
        drug_class                VARCHAR(255),
        start_date                DATE,
        end_date                  DATE,
        ordered_date              DATE,
        prescribing_provider_name VARCHAR(255)
    )
    """,

    # ── procedures ──────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS src.procedures (
        person_id                  BIGINT,
        encounter_id               BIGINT,
        procedure_durable_key      BIGINT,
        order_provider_durable_key BIGINT,
        procedure_code             VARCHAR(50),
        template_description       VARCHAR(500),
        procedure_status           VARCHAR(10),
        ordered_date               DATE,
        event_start_date           DATE,
        event_end_date             DATE
    )
    """,
    "CREATE INDEX IF NOT EXISTS IX_procedures ON src.procedures (procedure_durable_key)",

    # ── providers ────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS src.providers (
        provider_id              BIGINT,
        provider_npi             VARCHAR(50),
        provider_type            VARCHAR(100),
        clinician_title          VARCHAR(100),
        provider_name            VARCHAR(255),
        role_category            VARCHAR(255),
        email                    TEXT,
        can_authorize_medication BOOLEAN
    )
    """,

    # ── substance_use ────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS src.substance_use (
        icd_concept_name VARCHAR(255),
        icd_code         VARCHAR(20)
    )
    """,

    # ── treatment_plan ───────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS src.treatment_plan (
        bh_treatment_plan_id     BIGINT,
        plan_of_care_id          BIGINT,
        encounter_id             BIGINT,
        person_id                BIGINT,
        provider_id              BIGINT,
        plan_of_care_name        VARCHAR(255),
        treatment_plan_date      DATE,
        next_treatment_plan_date DATE,
        plan_of_care_status      VARCHAR(255)
    )
    """,
]

# Reference data — idempotent inserts for seeded lookup tables
_SRC_REFERENCE_DATA: list[str] = [

    # departments_of_interest (PK on department_name → ON CONFLICT DO NOTHING)
    """
    INSERT INTO src.departments_of_interest (department_name, is_inpatient, is_outpatient, is_crisis_department) VALUES
    ('Behavioral Health Inpatient Unit A',      true,  false, true),
    ('Behavioral Health Inpatient Unit B',      true,  false, true),
    ('Behavioral Health Inpatient Unit C',      true,  false, true),
    ('Psychiatric Emergency Unit',              false, false, true),
    ('Midtown Behavioral Health',               false, true,  false),
    ('Outpatient Psychiatry - North Campus',    false, true,  false),
    ('Outpatient Psychiatry - South Campus',    false, true,  false),
    ('Outpatient Psychiatry - East Campus',     false, true,  false),
    ('Outpatient Psychiatry - West Campus',     false, true,  false),
    ('Westside Recovery Clinic',                false, true,  false),
    ('Eastside Behavioral Health Clinic',       false, true,  false),
    ('Northside Behavioral Health Clinic',      false, true,  false),
    ('Adult Outpatient Psychiatry',             false, true,  false),
    ('Assertive Community Treatment (ACT)',     false, true,  false),
    ('Behavioral Health Case Management',       false, true,  false),
    ('Community Support Team (CST)',            false, true,  false),
    ('CORE Services',                           false, true,  false),
    ('Integrated Care Team',                    false, true,  false),
    ('Community Care Management',               false, true,  false),
    ('Mobile Crisis Response',                  false, true,  false),
    ('Behavioral Health Primary Care Integration', false, true, false)
    ON CONFLICT DO NOTHING
    """,

    # safety_plan_mapping (PK on field_id → ON CONFLICT DO NOTHING)
    """
    INSERT INTO src.safety_plan_mapping
        (field_id, plan_name, step_number, step_label, field_label, data_type, is_repeatable, display_order)
    VALUES
    ('SPI-WS-01','Stanley-Brown Safety Planning Intervention',1,'Warning Signs','Warning sign 1 (thoughts/feelings)','text',true,1),
    ('SPI-WS-02','Stanley-Brown Safety Planning Intervention',1,'Warning Signs','Warning sign 2 (behaviors)','text',true,2),
    ('SPI-WS-03','Stanley-Brown Safety Planning Intervention',1,'Warning Signs','Warning sign 3 (situations/triggers)','text',true,3),
    ('SPI-IC-01','Stanley-Brown Safety Planning Intervention',2,'Internal Coping Strategies','Internal coping strategy 1','text',true,1),
    ('SPI-IC-02','Stanley-Brown Safety Planning Intervention',2,'Internal Coping Strategies','Internal coping strategy 2','text',true,2),
    ('SPI-IC-03','Stanley-Brown Safety Planning Intervention',2,'Internal Coping Strategies','Internal coping strategy 3','text',true,3),
    ('SPI-SD-01','Stanley-Brown Safety Planning Intervention',3,'Social Distractions','Social distraction contact/place 1','text',true,1),
    ('SPI-SD-02','Stanley-Brown Safety Planning Intervention',3,'Social Distractions','Social distraction contact/place 2','text',true,2),
    ('SPI-SD-03','Stanley-Brown Safety Planning Intervention',3,'Social Distractions','Social distraction contact/place 3','text',true,3),
    ('SPI-SH-01','Stanley-Brown Safety Planning Intervention',4,'Social Support Contacts','Support contact 1 – name','text',true,1),
    ('SPI-SH-02','Stanley-Brown Safety Planning Intervention',4,'Social Support Contacts','Support contact 1 – phone','phone',true,2),
    ('SPI-SH-03','Stanley-Brown Safety Planning Intervention',4,'Social Support Contacts','Support contact 2 – name','text',true,3),
    ('SPI-SH-04','Stanley-Brown Safety Planning Intervention',4,'Social Support Contacts','Support contact 2 – phone','phone',true,4),
    ('SPI-SH-05','Stanley-Brown Safety Planning Intervention',4,'Social Support Contacts','Support contact 3 – name','text',true,5),
    ('SPI-SH-06','Stanley-Brown Safety Planning Intervention',4,'Social Support Contacts','Support contact 3 – phone','phone',true,6),
    ('SPI-PR-01','Stanley-Brown Safety Planning Intervention',5,'Professional Contacts','Treating clinician – name','text',false,1),
    ('SPI-PR-02','Stanley-Brown Safety Planning Intervention',5,'Professional Contacts','Treating clinician – phone','phone',false,2),
    ('SPI-PR-03','Stanley-Brown Safety Planning Intervention',5,'Professional Contacts','Crisis line – name','text',false,3),
    ('SPI-PR-04','Stanley-Brown Safety Planning Intervention',5,'Professional Contacts','Crisis line – phone','phone',false,4),
    ('SPI-PR-05','Stanley-Brown Safety Planning Intervention',5,'Professional Contacts','Additional professional – name','text',true,5),
    ('SPI-PR-06','Stanley-Brown Safety Planning Intervention',5,'Professional Contacts','Additional professional – phone','phone',true,6),
    ('SPI-PR-07','Stanley-Brown Safety Planning Intervention',5,'Professional Contacts','Nearest emergency department – name','text',false,7),
    ('SPI-PR-08','Stanley-Brown Safety Planning Intervention',5,'Professional Contacts','Nearest emergency department – address','text',false,8),
    ('SPI-MR-01','Stanley-Brown Safety Planning Intervention',6,'Means Restriction','Lethal means identified','text',true,1),
    ('SPI-MR-02','Stanley-Brown Safety Planning Intervention',6,'Means Restriction','Means restriction plan','text',true,2),
    ('SPI-MR-03','Stanley-Brown Safety Planning Intervention',6,'Means Restriction','Responsible party for safekeeping','text',true,3),
    ('SPI-MR-04','Stanley-Brown Safety Planning Intervention',6,'Means Restriction','Firearms removed or secured','boolean',false,4),
    ('SPI-MR-05','Stanley-Brown Safety Planning Intervention',6,'Means Restriction','Medications secured or limited supply','boolean',false,5),
    ('SPI-AC-01','Stanley-Brown Safety Planning Intervention',0,'Acknowledgment','Patient acknowledged plan','boolean',false,1),
    ('SPI-AC-02','Stanley-Brown Safety Planning Intervention',0,'Acknowledgment','Clinician signature','text',false,2),
    ('SPI-AC-03','Stanley-Brown Safety Planning Intervention',0,'Acknowledgment','Plan completion date','date',false,3),
    ('SPI-AC-04','Stanley-Brown Safety Planning Intervention',0,'Acknowledgment','Next review date','date',false,4)
    ON CONFLICT DO NOTHING
    """,

    # substance_use — no PK so use insert-if-empty guard
    """
    DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM src.substance_use LIMIT 1) THEN
        INSERT INTO src.substance_use (icd_concept_name, icd_code) VALUES
        ('Cannabis dependence with psychotic disorder with delusions','F12.250'),
        ('Cannabis dependence with psychotic disorder with hallucinations','F12.251'),
        ('Cannabis dependence with psychotic disorder, unspecified','F12.259'),
        ('Cannabis dependence with other cannabis-induced disorder','F12.28'),
        ('Cannabis dependence with cannabis-induced anxiety disorder','F12.280'),
        ('Cannabis dependence with other cannabis-induced disorder','F12.288'),
        ('Cannabis dependence with unspecified cannabis-induced disorder','F12.29'),
        ('Cannabis use, unspecified','F12.9'),
        ('Cannabis use, unspecified with intoxication','F12.92'),
        ('Cannabis use, unspecified with intoxication, uncomplicated','F12.920'),
        ('Cannabis use, unspecified with intoxication delirium','F12.921'),
        ('Cannabis use, unspecified with intoxication with perceptual disturbance','F12.922'),
        ('Cannabis use, unspecified with intoxication, unspecified','F12.929'),
        ('Cannabis use, unspecified with withdrawal','F12.93'),
        ('Cannabis use, unspecified with psychotic disorder','F12.95'),
        ('Cannabis use, unspecified with psychotic disorder with delusions','F12.950'),
        ('Cannabis use, unspecified with psychotic disorder with hallucinations','F12.951'),
        ('Cannabis use, unspecified with psychotic disorder, unspecified','F12.959'),
        ('Cannabis use, unspecified with other cannabis-induced disorder','F12.98'),
        ('Cannabis use, unspecified with anxiety disorder','F12.980'),
        ('Cannabis use, unspecified with other cannabis-induced disorder','F12.988'),
        ('Cannabis use, unspecified with unspecified cannabis-induced disorder','F12.99'),
        ('Sedative, hypnotic, or anxiolytic related disorders','F13'),
        ('Sedative, hypnotic or anxiolytic-related abuse','F13.1'),
        ('Sedative, hypnotic or anxiolytic abuse, uncomplicated','F13.10'),
        ('Sedative, hypnotic or anxiolytic abuse with intoxication','F13.12'),
        ('Sedative, hypnotic or anxiolytic abuse with intoxication, uncomplicated','F13.120'),
        ('Sedative, hypnotic or anxiolytic abuse with intoxication delirium','F13.121'),
        ('Sedative, hypnotic or anxiolytic abuse with intoxication, unspecified','F13.129'),
        ('Sedative, hypnotic or anxiolytic abuse with withdrawal','F13.13'),
        ('Sedative, hypnotic or anxiolytic abuse with withdrawal, uncomplicated','F13.130'),
        ('Sedative, hypnotic or anxiolytic abuse with withdrawal delirium','F13.131'),
        ('Sedative, hypnotic or anxiolytic abuse with withdrawal with perceptual disturbance','F13.132'),
        ('Sedative, hypnotic or anxiolytic abuse with withdrawal, unspecified','F13.139'),
        ('Sedative, hypnotic or anxiolytic abuse with sedative, hypnotic or anxiolytic-induced mood disorder','F13.14'),
        ('Sedative, hypnotic or anxiolytic abuse with sedative, hypnotic or anxiolytic-induced psychotic disorder','F13.15'),
        ('Sedative, hypnotic or anxiolytic abuse with sedative, hypnotic or anxiolytic-induced psychotic disorder with delusions','F13.150'),
        ('Sedative, hypnotic or anxiolytic abuse with sedative, hypnotic or anxiolytic-induced psychotic disorder with hallucinations','F13.151'),
        ('Sedative, hypnotic or anxiolytic abuse with sedative, hypnotic or anxiolytic-induced psychotic disorder, unspecified','F13.159'),
        ('Sedative, hypnotic or anxiolytic abuse with other sedative, hypnotic or anxiolytic-induced disorders','F13.18'),
        ('Sedative, hypnotic or anxiolytic abuse with sedative, hypnotic or anxiolytic-induced anxiety disorder','F13.180'),
        ('Sedative, hypnotic or anxiolytic abuse with sedative, hypnotic or anxiolytic-induced sexual dysfunction','F13.181'),
        ('Sedative, hypnotic or anxiolytic abuse with sedative, hypnotic or anxiolytic-induced sleep disorder','F13.182'),
        ('Sedative, hypnotic or anxiolytic abuse with other sedative, hypnotic or anxiolytic-induced disorder','F13.188'),
        ('Sedative, hypnotic or anxiolytic abuse with unspecified sedative, hypnotic or anxiolytic-induced disorder','F13.19'),
        ('Sedative, hypnotic or anxiolytic-related dependence','F13.2'),
        ('Sedative, hypnotic or anxiolytic dependence, uncomplicated','F13.20'),
        ('Sedative, hypnotic or anxiolytic dependence with intoxication','F13.22'),
        ('Sedative, hypnotic or anxiolytic dependence with intoxication, uncomplicated','F13.220'),
        ('Sedative, hypnotic or anxiolytic dependence with intoxication delirium','F13.221'),
        ('Sedative, hypnotic or anxiolytic dependence with intoxication, unspecified','F13.229'),
        ('Sedative, hypnotic or anxiolytic dependence with withdrawal','F13.23'),
        ('Sedative, hypnotic or anxiolytic dependence with withdrawal, uncomplicated','F13.230'),
        ('Sedative, hypnotic or anxiolytic dependence with withdrawal delirium','F13.231'),
        ('Sedative, hypnotic or anxiolytic dependence with withdrawal with perceptual disturbance','F13.232'),
        ('Sedative, hypnotic or anxiolytic dependence with withdrawal, unspecified','F13.239'),
        ('Sedative, hypnotic or anxiolytic dependence with sedative, hypnotic or anxiolytic-induced mood disorder','F13.24'),
        ('Sedative, hypnotic or anxiolytic dependence with sedative, hypnotic or anxiolytic-induced psychotic disorder','F13.25'),
        ('Sedative, hypnotic or anxiolytic dependence with sedative, hypnotic or anxiolytic-induced psychotic disorder with delusions','F13.250'),
        ('Sedative, hypnotic or anxiolytic dependence with sedative, hypnotic or anxiolytic-induced psychotic disorder with hallucinations','F13.251'),
        ('Sedative, hypnotic or anxiolytic dependence with sedative, hypnotic or anxiolytic-induced psychotic disorder, unspecified','F13.259'),
        ('Sedative, hypnotic or anxiolytic dependence with sedative, hypnotic or anxiolytic-induced persisting amnestic disorder','F13.26'),
        ('Sedative, hypnotic or anxiolytic dependence with sedative, hypnotic or anxiolytic-induced persisting dementia','F13.27'),
        ('Sedative, hypnotic or anxiolytic dependence with other sedative, hypnotic or anxiolytic-induced disorders','F13.28'),
        ('Sedative, hypnotic or anxiolytic dependence with sedative, hypnotic or anxiolytic-induced anxiety disorder','F13.280'),
        ('Sedative, hypnotic or anxiolytic dependence with sedative, hypnotic or anxiolytic-induced sexual dysfunction','F13.281'),
        ('Sedative, hypnotic or anxiolytic dependence with sedative, hypnotic or anxiolytic-induced sleep disorder','F13.282'),
        ('Sedative, hypnotic or anxiolytic dependence with other sedative, hypnotic or anxiolytic-induced disorder','F13.288'),
        ('Sedative, hypnotic or anxiolytic dependence with unspecified sedative, hypnotic or anxiolytic-induced disorder','F13.29'),
        ('Sedative, hypnotic or anxiolytic-related use, unspecified','F13.9'),
        ('Sedative, hypnotic or anxiolytic use, unspecified with intoxication','F13.92'),
        ('Sedative, hypnotic or anxiolytic use, unspecified with intoxication, uncomplicated','F13.920'),
        ('Sedative, hypnotic or anxiolytic use, unspecified with intoxication delirium','F13.921'),
        ('Sedative, hypnotic or anxiolytic use, unspecified with intoxication, unspecified','F13.929'),
        ('Sedative, hypnotic or anxiolytic use, unspecified with withdrawal','F13.93'),
        ('Sedative, hypnotic or anxiolytic use, unspecified with withdrawal, uncomplicated','F13.930'),
        ('Sedative, hypnotic or anxiolytic use, unspecified with withdrawal delirium','F13.931'),
        ('Sedative, hypnotic or anxiolytic use, unspecified with withdrawal with perceptual disturbances','F13.932'),
        ('Sedative, hypnotic or anxiolytic use, unspecified with withdrawal, unspecified','F13.939'),
        ('Sedative, hypnotic or anxiolytic use, unspecified with sedative, hypnotic or anxiolytic-induced mood disorder','F13.94'),
        ('Sedative, hypnotic or anxiolytic use, unspecified with sedative, hypnotic or anxiolytic-induced psychotic disorder','F13.95'),
        ('Sedative, hypnotic or anxiolytic use, unspecified with sedative, hypnotic or anxiolytic-induced psychotic disorder with delusions','F13.950'),
        ('Sedative, hypnotic or anxiolytic use, unspecified with sedative, hypnotic or anxiolytic-induced psychotic disorder with hallucinations','F13.951'),
        ('Sedative, hypnotic or anxiolytic use, unspecified with sedative, hypnotic or anxiolytic-induced psychotic disorder, unspecified','F13.959'),
        ('Sedative, hypnotic or anxiolytic use, unspecified with sedative, hypnotic or anxiolytic-induced persisting amnestic disorder','F13.96'),
        ('Sedative, hypnotic or anxiolytic use, unspecified with sedative, hypnotic or anxiolytic-induced persisting dementia','F13.97'),
        ('Sedative, hypnotic or anxiolytic use, unspecified with other sedative, hypnotic or anxiolytic-induced disorders','F13.98'),
        ('Sedative, hypnotic or anxiolytic use, unspecified with sedative, hypnotic or anxiolytic-induced anxiety disorder','F13.980'),
        ('Sedative, hypnotic or anxiolytic use, unspecified with sedative, hypnotic or anxiolytic-induced sexual dysfunction','F13.981'),
        ('Sedative, hypnotic or anxiolytic use, unspecified with sedative, hypnotic or anxiolytic-induced sleep disorder','F13.982'),
        ('Sedative, hypnotic or anxiolytic use, unspecified with other sedative, hypnotic or anxiolytic-induced disorder','F13.988'),
        ('Sedative, hypnotic or anxiolytic use, unspecified with unspecified sedative, hypnotic or anxiolytic-induced disorder','F13.99'),
        ('Cocaine related disorders','F14'),('Cocaine abuse','F14.1'),('Cocaine abuse, uncomplicated','F14.10'),
        ('Cocaine abuse with intoxication','F14.12'),('Cocaine abuse with intoxication, uncomplicated','F14.120'),
        ('Cocaine abuse with intoxication with delirium','F14.121'),('Cocaine abuse with intoxication with perceptual disturbance','F14.122'),
        ('Cocaine abuse with intoxication, unspecified','F14.129'),('Cocaine abuse, unspecified with withdrawal','F14.13'),
        ('Cocaine abuse with cocaine-induced mood disorder','F14.14'),('Cocaine abuse with cocaine-induced psychotic disorder','F14.15'),
        ('Cocaine abuse with cocaine-induced psychotic disorder with delusions','F14.150'),('Cocaine abuse with cocaine-induced psychotic disorder with hallucinations','F14.151'),
        ('Cocaine abuse with cocaine-induced psychotic disorder, unspecified','F14.159'),('Cocaine abuse with other cocaine-induced disorder','F14.18'),
        ('Cocaine abuse with cocaine-induced anxiety disorder','F14.180'),('Cocaine abuse with cocaine-induced sexual dysfunction','F14.181'),
        ('Cocaine abuse with cocaine-induced sleep disorder','F14.182'),('Cocaine abuse with other cocaine-induced disorder','F14.188'),
        ('Cocaine abuse with unspecified cocaine-induced disorder','F14.19'),('Cocaine dependence','F14.2'),
        ('Cocaine dependence, uncomplicated','F14.20'),('Cocaine dependence with intoxication','F14.22'),
        ('Cocaine dependence with intoxication, uncomplicated','F14.220'),('Cocaine dependence with intoxication delirium','F14.221'),
        ('Cocaine dependence with intoxication with perceptual disturbance','F14.222'),('Cocaine dependence with intoxication, unspecified','F14.229'),
        ('Cocaine dependence with withdrawal','F14.23'),('Cocaine dependence with cocaine-induced mood disorder','F14.24'),
        ('Cocaine dependence with cocaine-induced psychotic disorder','F14.25'),('Cocaine dependence with cocaine-induced psychotic disorder with delusions','F14.250'),
        ('Cocaine dependence with cocaine-induced psychotic disorder with hallucinations','F14.251'),('Cocaine dependence with cocaine-induced psychotic disorder, unspecified','F14.259'),
        ('Cocaine dependence with other cocaine-induced disorder','F14.28'),('Cocaine dependence with cocaine-induced anxiety disorder','F14.280'),
        ('Cocaine dependence with cocaine-induced sexual dysfunction','F14.281'),('Cocaine dependence with cocaine-induced sleep disorder','F14.282'),
        ('Cocaine dependence with other cocaine-induced disorder','F14.288'),('Cocaine dependence with unspecified cocaine-induced disorder','F14.29'),
        ('Cocaine use, unspecified','F14.9'),('Cocaine use, unspecified, uncomplicated','F14.90'),
        ('Cocaine use, unspecified with intoxication','F14.92'),('Cocaine use, unspecified with intoxication, uncomplicated','F14.920'),
        ('Cocaine use, unspecified with intoxication delirium','F14.921'),('Cocaine use, unspecified with intoxication with perceptual disturbance','F14.922'),
        ('Cocaine use, unspecified with intoxication, unspecified','F14.929'),('Cocaine use, unspecified with withdrawal','F14.93'),
        ('Cocaine use, unspecified with cocaine-induced mood disorder','F14.94'),('Cocaine use, unspecified with cocaine-induced psychotic disorder','F14.95'),
        ('Cocaine use, unspecified with cocaine-induced psychotic disorder with delusions','F14.950'),('Cocaine use, unspecified with cocaine-induced psychotic disorder with hallucinations','F14.951'),
        ('Cocaine use, unspecified with cocaine-induced psychotic disorder, unspecified','F14.959'),('Cocaine use, unspecified with other specified cocaine-induced disorder','F14.98'),
        ('Cocaine use, unspecified with cocaine-induced anxiety disorder','F14.980'),('Cocaine use, unspecified with cocaine-induced sexual dysfunction','F14.981'),
        ('Cocaine use, unspecified with cocaine-induced sleep disorder','F14.982'),('Cocaine use, unspecified with other cocaine-induced disorder','F14.988'),
        ('Cocaine use, unspecified with unspecified cocaine-induced disorder','F14.99'),
        ('Other stimulant related disorders','F15'),('Other stimulant abuse','F15.1'),('Other stimulant abuse, uncomplicated','F15.10'),
        ('Other stimulant abuse with intoxication','F15.12'),('Other stimulant abuse with intoxication, uncomplicated','F15.120'),
        ('Other stimulant abuse with intoxication delirium','F15.121'),('Other stimulant abuse with intoxication with perceptual disturbance','F15.122'),
        ('Other stimulant abuse with intoxication, unspecified','F15.129'),('Other stimulant abuse with withdrawal','F15.13'),
        ('Other stimulant abuse with stimulant-induced mood disorder','F15.14'),('Other stimulant abuse with stimulant-induced psychotic disorder','F15.15'),
        ('Other stimulant abuse with stimulant-induced psychotic disorder with delusions','F15.150'),('Other stimulant abuse with stimulant-induced psychotic disorder with hallucinations','F15.151'),
        ('Other stimulant abuse with stimulant-induced psychotic disorder, unspecified','F15.159'),('Other stimulant abuse with other stimulant-induced disorder','F15.18'),
        ('Other stimulant abuse with stimulant-induced anxiety disorder','F15.180'),('Other stimulant abuse with stimulant-induced sexual dysfunction','F15.181'),
        ('Other stimulant abuse with stimulant-induced sleep disorder','F15.182'),('Other stimulant abuse with other stimulant-induced disorder','F15.188'),
        ('Other stimulant abuse with unspecified stimulant-induced disorder','F15.19'),('Other stimulant dependence','F15.2'),
        ('Other stimulant dependence, uncomplicated','F15.20'),('Other stimulant dependence with intoxication','F15.22'),
        ('Other stimulant dependence with intoxication, uncomplicated','F15.220'),('Other stimulant dependence with intoxication delirium','F15.221'),
        ('Other stimulant dependence with intoxication with perceptual disturbance','F15.222'),('Other stimulant dependence with intoxication, unspecified','F15.229'),
        ('Other stimulant dependence with withdrawal','F15.23'),('Other stimulant dependence with stimulant-induced mood disorder','F15.24'),
        ('Other stimulant dependence with stimulant-induced psychotic disorder','F15.25'),('Other stimulant dependence with stimulant-induced psychotic disorder with delusions','F15.250'),
        ('Other stimulant dependence with stimulant-induced psychotic disorder with hallucinations','F15.251'),('Other stimulant dependence with stimulant-induced psychotic disorder, unspecified','F15.259'),
        ('Other stimulant dependence with other stimulant-induced disorder','F15.28'),('Other stimulant dependence with stimulant-induced anxiety disorder','F15.280'),
        ('Other stimulant dependence with stimulant-induced sexual dysfunction','F15.281'),('Other stimulant dependence with stimulant-induced sleep disorder','F15.282'),
        ('Other stimulant dependence with other stimulant-induced disorder','F15.288'),('Other stimulant dependence with unspecified stimulant-induced disorder','F15.29'),
        ('Other stimulant use, unspecified','F15.9'),('Other stimulant use, unspecified, uncomplicated','F15.90'),
        ('Other stimulant use, unspecified with intoxication','F15.92'),('Other stimulant use, unspecified with intoxication, uncomplicated','F15.920'),
        ('Other stimulant use, unspecified with intoxication delirium','F15.921'),('Other stimulant use, unspecified with intoxication with perceptual disturbance','F15.922'),
        ('Other stimulant use, unspecified with intoxication, unspecified','F15.929'),('Other stimulant use, unspecified with withdrawal','F15.93'),
        ('Other stimulant use, unspecified with stimulant-induced mood disorder','F15.94'),('Other stimulant use, unspecified with stimulant-induced psychotic disorder','F15.95'),
        ('Other stimulant use, unspecified with stimulant-induced psychotic disorder with delusions','F15.950'),('Other stimulant use, unspecified with stimulant-induced psychotic disorder with hallucinations','F15.951'),
        ('Other stimulant use, unspecified with stimulant-induced psychotic disorder, unspecified','F15.959'),('Other stimulant use, unspecified with other stimulant-induced disorder','F15.98'),
        ('Other stimulant use, unspecified with stimulant-induced anxiety disorder','F15.980'),('Other stimulant use, unspecified with stimulant-induced sexual dysfunction','F15.981'),
        ('Other stimulant use, unspecified with stimulant-induced sleep disorder','F15.982'),('Other stimulant use, unspecified with other stimulant-induced disorder','F15.988'),
        ('Other stimulant use, unspecified with unspecified stimulant-induced disorder','F15.99'),
        ('Hallucinogen related disorders','F16'),('Hallucinogen abuse','F16.1'),('Hallucinogen abuse, uncomplicated','F16.10'),
        ('Hallucinogen abuse with intoxication','F16.12'),('Hallucinogen abuse with intoxication, uncomplicated','F16.120'),
        ('Hallucinogen abuse with intoxication with delirium','F16.121'),('Hallucinogen abuse with intoxication with perceptual disturbance','F16.122'),
        ('Hallucinogen abuse with intoxication, unspecified','F16.129'),('Hallucinogen abuse with hallucinogen-induced mood disorder','F16.14'),
        ('Hallucinogen abuse with hallucinogen-induced psychotic disorder','F16.15'),('Hallucinogen abuse with hallucinogen-induced psychotic disorder with delusions','F16.150'),
        ('Hallucinogen abuse with hallucinogen-induced psychotic disorder with hallucinations','F16.151'),('Hallucinogen abuse with hallucinogen-induced psychotic disorder, unspecified','F16.159'),
        ('Hallucinogen abuse with other hallucinogen-induced disorder','F16.18'),('Hallucinogen abuse with hallucinogen-induced anxiety disorder','F16.180'),
        ('Hallucinogen abuse with hallucinogen persisting perception disorder (flashbacks)','F16.183'),('Hallucinogen abuse with other hallucinogen-induced disorder','F16.188'),
        ('Hallucinogen abuse with unspecified hallucinogen-induced disorder','F16.19'),('Hallucinogen dependence','F16.2'),
        ('Hallucinogen dependence, uncomplicated','F16.20'),('Hallucinogen dependence with intoxication','F16.22'),
        ('Hallucinogen dependence with intoxication, uncomplicated','F16.220'),('Hallucinogen dependence with intoxication with delirium','F16.221'),
        ('Hallucinogen dependence with intoxication, unspecified','F16.229'),('Hallucinogen dependence with hallucinogen-induced mood disorder','F16.24'),
        ('Hallucinogen dependence with hallucinogen-induced psychotic disorder','F16.25'),('Hallucinogen dependence with hallucinogen-induced psychotic disorder with delusions','F16.250'),
        ('Hallucinogen dependence with hallucinogen-induced psychotic disorder with hallucinations','F16.251'),('Hallucinogen dependence with hallucinogen-induced psychotic disorder, unspecified','F16.259'),
        ('Hallucinogen dependence with other hallucinogen-induced disorder','F16.28'),('Hallucinogen dependence with hallucinogen-induced anxiety disorder','F16.280'),
        ('Hallucinogen dependence with hallucinogen persisting perception disorder (flashbacks)','F16.283'),('Hallucinogen dependence with other hallucinogen-induced disorder','F16.288'),
        ('Hallucinogen dependence with unspecified hallucinogen-induced disorder','F16.29'),('Hallucinogen use, unspecified','F16.9'),
        ('Hallucinogen use, unspecified, uncomplicated','F16.90'),('Hallucinogen use, unspecified with intoxication','F16.92'),
        ('Hallucinogen use, unspecified with intoxication, uncomplicated','F16.920'),('Hallucinogen use, unspecified with intoxication with delirium','F16.921'),
        ('Hallucinogen use, unspecified with intoxication, unspecified','F16.929'),('Hallucinogen use, unspecified with hallucinogen-induced mood disorder','F16.94'),
        ('Hallucinogen use, unspecified with hallucinogen-induced psychotic disorder','F16.95'),('Hallucinogen use, unspecified with hallucinogen-induced psychotic disorder with delusions','F16.950'),
        ('Hallucinogen use, unspecified with hallucinogen-induced psychotic disorder with hallucinations','F16.951'),('Hallucinogen use, unspecified with hallucinogen-induced psychotic disorder, unspecified','F16.959'),
        ('Hallucinogen use, unspecified with other specified hallucinogen-induced disorder','F16.98'),('Hallucinogen use, unspecified with hallucinogen-induced anxiety disorder','F16.980'),
        ('Hallucinogen use, unspecified with hallucinogen persisting perception disorder (flashbacks)','F16.983'),('Hallucinogen use, unspecified with other hallucinogen-induced disorder','F16.988'),
        ('Hallucinogen use, unspecified with unspecified hallucinogen-induced disorder','F16.99'),
        ('Inhalant related disorders','F18'),('Inhalant abuse','F18.1'),('Inhalant abuse, uncomplicated','F18.10'),
        ('Inhalant abuse with intoxication','F18.12'),('Inhalant abuse with intoxication, uncomplicated','F18.120'),
        ('Inhalant abuse with intoxication delirium','F18.121'),('Inhalant abuse with intoxication, unspecified','F18.129'),
        ('Inhalant abuse with inhalant-induced mood disorder','F18.14'),('Inhalant abuse with inhalant-induced psychotic disorder','F18.15'),
        ('Inhalant abuse with inhalant-induced psychotic disorder with delusions','F18.150'),('Inhalant abuse with inhalant-induced psychotic disorder with hallucinations','F18.151'),
        ('Inhalant abuse with inhalant-induced psychotic disorder, unspecified','F18.159'),('Inhalant abuse with inhalant-induced dementia','F18.17'),
        ('Inhalant abuse with other inhalant-induced disorders','F18.18'),('Inhalant abuse with inhalant-induced anxiety disorder','F18.180'),
        ('Inhalant abuse with other inhalant-induced disorder','F18.188'),('Inhalant abuse with unspecified inhalant-induced disorder','F18.19'),
        ('Inhalant dependence','F18.2'),('Inhalant dependence, uncomplicated','F18.20'),('Inhalant dependence with intoxication','F18.22'),
        ('Inhalant dependence with intoxication, uncomplicated','F18.220'),('Inhalant dependence with intoxication delirium','F18.221'),
        ('Inhalant dependence with intoxication, unspecified','F18.229'),('Inhalant dependence with inhalant-induced mood disorder','F18.24'),
        ('Inhalant dependence with inhalant-induced psychotic disorder','F18.25'),('Inhalant dependence with inhalant-induced psychotic disorder with delusions','F18.250'),
        ('Inhalant dependence with inhalant-induced psychotic disorder with hallucinations','F18.251'),('Inhalant dependence with inhalant-induced psychotic disorder, unspecified','F18.259'),
        ('Inhalant dependence with inhalant-induced dementia','F18.27'),('Inhalant dependence with other inhalant-induced disorders','F18.28'),
        ('Inhalant dependence with inhalant-induced anxiety disorder','F18.280'),('Inhalant dependence with other inhalant-induced disorder','F18.288'),
        ('Inhalant dependence with unspecified inhalant-induced disorder','F18.29'),('Inhalant use, unspecified','F18.9'),
        ('Inhalant use, unspecified, uncomplicated','F18.90'),('Inhalant use, unspecified, in remission','F18.91'),
        ('Inhalant use, unspecified with intoxication','F18.92'),('Inhalant use, unspecified with intoxication, uncomplicated','F18.920'),
        ('Inhalant use, unspecified with intoxication with delirium','F18.921'),('Inhalant use, unspecified with intoxication, unspecified','F18.929'),
        ('Inhalant use, unspecified with inhalant-induced mood disorder','F18.94'),('Inhalant use, unspecified with inhalant-induced psychotic disorder','F18.95'),
        ('Inhalant use, unspecified with inhalant-induced psychotic disorder with delusions','F18.950'),('Inhalant use, unspecified with inhalant-induced psychotic disorder with hallucinations','F18.951'),
        ('Inhalant use, unspecified with inhalant-induced psychotic disorder, unspecified','F18.959'),('Inhalant use, unspecified with inhalant-induced persisting dementia','F18.97'),
        ('Inhalant use, unspecified with other inhalant-induced disorders','F18.98'),('Inhalant use, unspecified with inhalant-induced anxiety disorder','F18.980'),
        ('Inhalant use, unspecified with other inhalant-induced disorder','F18.988'),('Inhalant use, unspecified with unspecified inhalant-induced disorder','F18.99'),
        ('Other psychoactive substance related disorders','F19'),('Other psychoactive substance abuse','F19.1'),('Other psychoactive substance abuse, uncomplicated','F19.10'),
        ('Other psychoactive substance abuse with intoxication','F19.12'),('Other psychoactive substance abuse with intoxication, uncomplicated','F19.120'),
        ('Other psychoactive substance abuse with intoxication delirium','F19.121'),('Other psychoactive substance abuse with intoxication with perceptual disturbances','F19.122'),
        ('Other psychoactive substance abuse with intoxication, unspecified','F19.129'),('Other psychoactive substance abuse with withdrawal','F19.13'),
        ('Other psychoactive substance abuse with withdrawal, uncomplicated','F19.130'),('Other psychoactive substance abuse with withdrawal delirium','F19.131'),
        ('Other psychoactive substance abuse with withdrawal with perceptual disturbance','F19.132'),('Other psychoactive substance abuse with withdrawal, unspecified','F19.139'),
        ('Other psychoactive substance abuse with psychoactive substance-induced mood disorder','F19.14'),('Other psychoactive substance abuse with psychoactive substance-induced psychotic disorder','F19.15'),
        ('Other psychoactive substance abuse with psychoactive substance-induced psychotic disorder with delusions','F19.150'),('Other psychoactive substance abuse with psychoactive substance-induced psychotic disorder with hallucinations','F19.151'),
        ('Other psychoactive substance abuse with psychoactive substance-induced psychotic disorder, unspecified','F19.159'),('Other psychoactive substance abuse with psychoactive substance-induced persisting amnestic disorder','F19.16'),
        ('Other psychoactive substance abuse with psychoactive substance-induced persisting dementia','F19.17'),('Other psychoactive substance abuse with other psychoactive substance-induced disorders','F19.18'),
        ('Other psychoactive substance abuse with psychoactive substance-induced anxiety disorder','F19.180'),('Other psychoactive substance abuse with psychoactive substance-induced sexual dysfunction','F19.181'),
        ('Other psychoactive substance abuse with psychoactive substance-induced sleep disorder','F19.182'),('Other psychoactive substance abuse with other psychoactive substance-induced disorder','F19.188'),
        ('Other psychoactive substance abuse with unspecified psychoactive substance-induced disorder','F19.19'),('Other psychoactive substance dependence','F19.2'),
        ('Other psychoactive substance dependence, uncomplicated','F19.20'),('Other psychoactive substance dependence with intoxication','F19.22'),
        ('Other psychoactive substance dependence with intoxication, uncomplicated','F19.220'),('Other psychoactive substance dependence with intoxication delirium','F19.221'),
        ('Other psychoactive substance dependence with intoxication with perceptual disturbance','F19.222'),('Other psychoactive substance dependence with intoxication, unspecified','F19.229'),
        ('Other psychoactive substance dependence with withdrawal','F19.23'),('Other psychoactive substance dependence with withdrawal, uncomplicated','F19.230'),
        ('Other psychoactive substance dependence with withdrawal delirium','F19.231'),('Other psychoactive substance dependence with withdrawal with perceptual disturbance','F19.232'),
        ('Other psychoactive substance dependence with withdrawal, unspecified','F19.239'),('Other psychoactive substance dependence with psychoactive substance-induced mood disorder','F19.24'),
        ('Other psychoactive substance dependence with psychoactive substance-induced psychotic disorder','F19.25'),('Other psychoactive substance dependence with psychoactive substance-induced psychotic disorder with delusions','F19.250'),
        ('Other psychoactive substance dependence with psychoactive substance-induced psychotic disorder with hallucinations','F19.251'),('Other psychoactive substance dependence with psychoactive substance-induced psychotic disorder, unspecified','F19.259'),
        ('Other psychoactive substance dependence with psychoactive substance-induced persisting amnestic disorder','F19.26'),('Other psychoactive substance dependence with psychoactive substance-induced persisting dementia','F19.27'),
        ('Other psychoactive substance dependence with other psychoactive substance-induced disorders','F19.28'),('Other psychoactive substance dependence with psychoactive substance-induced anxiety disorder','F19.280'),
        ('Other psychoactive substance dependence with psychoactive substance-induced sexual dysfunction','F19.281'),('Other psychoactive substance dependence with psychoactive substance-induced sleep disorder','F19.282'),
        ('Other psychoactive substance dependence with other psychoactive substance-induced disorder','F19.288'),('Other psychoactive substance dependence with unspecified psychoactive substance-induced disorder','F19.29'),
        ('Other psychoactive substance use, unspecified','F19.9'),('Other psychoactive substance use, unspecified, uncomplicated','F19.90'),
        ('Other psychoactive substance use, unspecified with intoxication','F19.92'),('Other psychoactive substance use, unspecified with intoxication, uncomplicated','F19.920'),
        ('Other psychoactive substance use, unspecified with intoxication with delirium','F19.921'),('Other psychoactive substance use, unspecified with intoxication with perceptual disturbance','F19.922'),
        ('Other psychoactive substance use, unspecified with intoxication, unspecified','F19.929'),('Other psychoactive substance use, unspecified with withdrawal','F19.93'),
        ('Other psychoactive substance use, unspecified with withdrawal, uncomplicated','F19.930'),('Other psychoactive substance use, unspecified with withdrawal delirium','F19.931'),
        ('Other psychoactive substance use, unspecified with withdrawal with perceptual disturbance','F19.932'),('Other psychoactive substance use, unspecified with withdrawal, unspecified','F19.939'),
        ('Other psychoactive substance use, unspecified with psychoactive substance-induced mood disorder','F19.94'),('Other psychoactive substance use, unspecified with psychoactive substance-induced psychotic disorder','F19.95'),
        ('Other psychoactive substance use, unspecified with psychoactive substance-induced psychotic disorder with delusions','F19.950'),('Other psychoactive substance use, unspecified with psychoactive substance-induced psychotic disorder with hallucinations','F19.951'),
        ('Other psychoactive substance use, unspecified with psychoactive substance-induced psychotic disorder, unspecified','F19.959'),('Other psychoactive substance use, unspecified with psychoactive substance-induced persisting amnestic disorder','F19.96'),
        ('Other psychoactive substance use, unspecified with psychoactive substance-induced persisting dementia','F19.97'),('Other psychoactive substance use, unspecified with other psychoactive substance-induced disorders','F19.98'),
        ('Other psychoactive substance use, unspecified with psychoactive substance-induced anxiety disorder','F19.980'),('Other psychoactive substance use, unspecified with psychoactive substance-induced sexual dysfunction','F19.981'),
        ('Other psychoactive substance use, unspecified with psychoactive substance-induced sleep disorder','F19.982'),('Other psychoactive substance use, unspecified with other psychoactive substance-induced disorder','F19.988'),
        ('Other psychoactive substance use, unspecified with unspecified psychoactive substance-induced disorder','F19.99'),
        ('Abuse of non-psychoactive substances','F55'),('Abuse of herbal or folk remedies','F55.1'),('Abuse of laxatives','F55.2'),
        ('Alcohol related disorders','F10'),('Alcohol abuse','F10.1'),('Alcohol abuse, uncomplicated','F10.10'),
        ('Alcohol abuse with intoxication','F10.12'),('Alcohol abuse with intoxication, uncomplicated','F10.120'),
        ('Alcohol abuse with intoxication delirium','F10.121'),('Alcohol abuse with intoxication, unspecified','F10.129'),
        ('Alcohol abuse, with withdrawal','F10.13'),('Alcohol abuse with withdrawal, uncomplicated','F10.130'),
        ('Alcohol abuse with withdrawal delirium','F10.131'),('Alcohol abuse with withdrawal with perceptual disturbance','F10.132'),
        ('Alcohol abuse with withdrawal, unspecified','F10.139'),('Alcohol abuse with alcohol-induced mood disorder','F10.14'),
        ('Alcohol abuse with alcohol-induced psychotic disorder','F10.15'),('Alcohol abuse with alcohol-induced psychotic disorder with delusions','F10.150'),
        ('Alcohol abuse with alcohol-induced psychotic disorder with hallucinations','F10.151'),('Alcohol abuse with alcohol-induced psychotic disorder, unspecified','F10.159'),
        ('Alcohol abuse with other alcohol-induced disorders','F10.18'),('Alcohol abuse with alcohol-induced anxiety disorder','F10.180'),
        ('Alcohol abuse with alcohol-induced sexual dysfunction','F10.181'),('Alcohol abuse with alcohol-induced sleep disorder','F10.182'),
        ('Alcohol abuse with other alcohol-induced disorder','F10.188'),('Alcohol abuse with unspecified alcohol-induced disorder','F10.19'),
        ('Alcohol dependence','F10.2'),('Alcohol dependence, uncomplicated','F10.20'),('Alcohol dependence with intoxication','F10.22'),
        ('Alcohol dependence with intoxication, uncomplicated','F10.220'),('Alcohol dependence with intoxication delirium','F10.221'),
        ('Alcohol dependence with intoxication, unspecified','F10.229'),('Alcohol dependence with withdrawal','F10.23'),
        ('Alcohol dependence with withdrawal, uncomplicated','F10.230'),('Alcohol dependence with withdrawal delirium','F10.231'),
        ('Alcohol dependence with withdrawal with perceptual disturbance','F10.232'),('Alcohol dependence with withdrawal, unspecified','F10.239'),
        ('Alcohol dependence with alcohol-induced mood disorder','F10.24'),('Alcohol dependence with alcohol-induced psychotic disorder','F10.25'),
        ('Alcohol dependence with alcohol-induced psychotic disorder with delusions','F10.250'),('Alcohol dependence with alcohol-induced psychotic disorder with hallucinations','F10.251'),
        ('Alcohol dependence with alcohol-induced psychotic disorder, unspecified','F10.259'),('Alcohol dependence with alcohol-induced persisting amnestic disorder','F10.26'),
        ('Alcohol dependence with alcohol-induced persisting dementia','F10.27'),('Alcohol dependence with other alcohol-induced disorders','F10.28'),
        ('Alcohol dependence with alcohol-induced anxiety disorder','F10.280'),('Alcohol dependence with alcohol-induced sexual dysfunction','F10.281'),
        ('Alcohol dependence with alcohol-induced sleep disorder','F10.282'),('Alcohol dependence with other alcohol-induced disorder','F10.288'),
        ('Alcohol dependence with unspecified alcohol-induced disorder','F10.29'),('Alcohol use, unspecified','F10.9'),
        ('Alcohol use, unspecified, uncomplicated','F10.90'),('Alcohol use, unspecified with intoxication','F10.92'),
        ('Alcohol use, unspecified with intoxication, uncomplicated','F10.920'),('Alcohol use, unspecified with intoxication delirium','F10.921'),
        ('Alcohol use, unspecified with intoxication, unspecified','F10.929'),('Alcohol use, unspecified with withdrawal','F10.93'),
        ('Alcohol use, unspecified with withdrawal, uncomplicated','F10.930'),('Alcohol use, unspecified with withdrawal delirium','F10.931'),
        ('Alcohol use, unspecified with withdrawal with perceptual disturbance','F10.932'),('Alcohol use, unspecified with withdrawal, unspecified','F10.939'),
        ('Alcohol use, unspecified with alcohol-induced mood disorder','F10.94'),('Alcohol use, unspecified with alcohol-induced psychotic disorder','F10.95'),
        ('Alcohol use, unspecified with alcohol-induced psychotic disorder with delusions','F10.950'),('Alcohol use, unspecified with alcohol-induced psychotic disorder with hallucinations','F10.951'),
        ('Alcohol use, unspecified with alcohol-induced psychotic disorder, unspecified','F10.959'),('Alcohol use, unspecified with alcohol-induced persisting amnestic disorder','F10.96'),
        ('Alcohol use, unspecified with alcohol-induced persisting dementia','F10.97'),('Alcohol use, unspecified with other alcohol-induced disorders','F10.98'),
        ('Alcohol use, unspecified with alcohol-induced anxiety disorder','F10.980'),('Alcohol use, unspecified with alcohol-induced sexual dysfunction','F10.981'),
        ('Alcohol use, unspecified with alcohol-induced sleep disorder','F10.982'),('Alcohol use, unspecified with other alcohol-induced disorder','F10.988'),
        ('Alcohol use, unspecified with unspecified alcohol-induced disorder','F10.99'),
        ('Opioid related disorders','F11'),('Opioid abuse','F11.1'),('Opioid abuse, uncomplicated','F11.10'),
        ('Opioid abuse with intoxication','F11.12'),('Opioid abuse with intoxication, uncomplicated','F11.120'),
        ('Opioid abuse with intoxication delirium','F11.121'),('Opioid abuse with intoxication with perceptual disturbance','F11.122'),
        ('Opioid abuse with intoxication, unspecified','F11.129'),('Opioid abuse with withdrawal','F11.13'),
        ('Opioid abuse with opioid-induced mood disorder','F11.14'),('Opioid abuse with opioid-induced psychotic disorder','F11.15'),
        ('Opioid abuse with opioid-induced psychotic disorder with delusions','F11.150'),('Opioid abuse with opioid-induced psychotic disorder with hallucinations','F11.151'),
        ('Opioid abuse with opioid-induced psychotic disorder, unspecified','F11.159'),('Opioid abuse with other opioid-induced disorder','F11.18'),
        ('Opioid abuse with opioid-induced sexual dysfunction','F11.181'),('Opioid abuse with opioid-induced sleep disorder','F11.182'),
        ('Opioid abuse with other opioid-induced disorder','F11.188'),('Opioid abuse with unspecified opioid-induced disorder','F11.19'),
        ('Opioid dependence','F11.2'),('Opioid dependence, uncomplicated','F11.20'),('Opioid dependence with intoxication','F11.22'),
        ('Opioid dependence with intoxication, uncomplicated','F11.220'),('Opioid dependence with intoxication delirium','F11.221'),
        ('Opioid dependence with intoxication with perceptual disturbance','F11.222'),('Opioid dependence with intoxication, unspecified','F11.229'),
        ('Opioid dependence with withdrawal','F11.23'),('Opioid dependence with opioid-induced mood disorder','F11.24'),
        ('Opioid dependence with opioid-induced psychotic disorder','F11.25'),('Opioid dependence with opioid-induced psychotic disorder with delusions','F11.250'),
        ('Opioid dependence with opioid-induced psychotic disorder with hallucinations','F11.251'),('Opioid dependence with opioid-induced psychotic disorder, unspecified','F11.259'),
        ('Opioid dependence with other opioid-induced disorder','F11.28'),('Opioid dependence with opioid-induced sexual dysfunction','F11.281'),
        ('Opioid dependence with opioid-induced sleep disorder','F11.282'),('Opioid dependence with other opioid-induced disorder','F11.288'),
        ('Opioid dependence with unspecified opioid-induced disorder','F11.29'),('Opioid use, unspecified','F11.9'),
        ('Opioid use, unspecified, uncomplicated','F11.90'),('Opioid use, unspecified with intoxication','F11.92'),
        ('Opioid use, unspecified with intoxication, uncomplicated','F11.920'),('Opioid use, unspecified with intoxication delirium','F11.921'),
        ('Opioid use, unspecified with intoxication with perceptual disturbance','F11.922'),('Opioid use, unspecified with intoxication, unspecified','F11.929'),
        ('Opioid use, unspecified with withdrawal','F11.93'),('Opioid use, unspecified with opioid-induced mood disorder','F11.94'),
        ('Opioid use, unspecified with opioid-induced psychotic disorder','F11.95'),('Opioid use, unspecified with opioid-induced psychotic disorder with delusions','F11.950'),
        ('Opioid use, unspecified with opioid-induced psychotic disorder with hallucinations','F11.951'),('Opioid use, unspecified with opioid-induced psychotic disorder, unspecified','F11.959'),
        ('Opioid use, unspecified with other specified opioid-induced disorder','F11.98'),('Opioid use, unspecified with opioid-induced sexual dysfunction','F11.981'),
        ('Opioid use, unspecified with other opioid-induced disorder','F11.988'),('Opioid use, unspecified with unspecified opioid-induced disorder','F11.99'),
        ('Cannabis related disorders','F12'),('Cannabis abuse','F12.1'),('Cannabis abuse, uncomplicated','F12.10'),
        ('Cannabis abuse with intoxication','F12.12'),('Cannabis abuse with intoxication, uncomplicated','F12.120'),
        ('Cannabis abuse with intoxication delirium','F12.121'),('Cannabis abuse with intoxication with perceptual disturbance','F12.122'),
        ('Cannabis abuse with intoxication, unspecified','F12.129'),('Cannabis abuse with withdrawal','F12.13'),
        ('Cannabis abuse with psychotic disorder','F12.15'),('Cannabis abuse with psychotic disorder with delusions','F12.150'),
        ('Cannabis abuse with psychotic disorder with hallucinations','F12.151'),('Cannabis abuse with psychotic disorder, unspecified','F12.159'),
        ('Cannabis abuse with other cannabis-induced disorder','F12.18'),('Cannabis abuse with cannabis-induced anxiety disorder','F12.180'),
        ('Cannabis abuse with other cannabis-induced disorder','F12.188'),('Cannabis abuse with unspecified cannabis-induced disorder','F12.19'),
        ('Cannabis dependence','F12.2'),('Cannabis dependence, uncomplicated','F12.20'),('Cannabis dependence with intoxication','F12.22'),
        ('Cannabis dependence with intoxication, uncomplicated','F12.220'),('Cannabis dependence with intoxication delirium','F12.221'),
        ('Cannabis dependence with intoxication with perceptual disturbance','F12.222'),('Cannabis dependence with intoxication, unspecified','F12.229'),
        ('Cannabis dependence with withdrawal','F12.23'),('Cannabis dependence with psychotic disorder','F12.25');
    END IF;
    END $$
    """,

]

# RLS for src schema tables (service_role only — pipeline-internal data)
_SRC_TABLES = [
    "src.departments_of_interest", "src.departments", "src.encounter",
    "src.person", "src.dla20", "src.cssrs", "src.gad7", "src.phq9",
    "src.safety_plan_mapping", "src.crisis_safety_plan", "src.diagnosis",
    "src.drug", "src.inpatient", "src.prescriptions",
    "src.procedures", "src.providers", "src.substance_use", "src.treatment_plan",
]


def _src_rls_statements() -> list[str]:
    stmts: list[str] = []
    for t in _SRC_TABLES:
        stmts.append(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        stmts.append(
            "DO $$ BEGIN "
            f'CREATE POLICY "service_role_all" ON {t} '
            "FOR ALL TO service_role USING (true) WITH CHECK (true); "
            "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
        )
    return stmts

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

        for stmt in all_stmts + _ALTER + _SRC_DDL + _SRC_REFERENCE_DATA + _src_rls_statements():
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
                "tables":     len(_ALL_TABLES) + len(_SRC_TABLES),
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

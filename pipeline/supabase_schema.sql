-- ============================================================
-- ClinicalMind AI — Supabase Schema  (reference copy)
--
-- NOTE: orchestrator.py runs ensure_schema.py automatically before
--       each pipeline run.  You only need this file if you want to
--       apply the schema manually in the Supabase SQL Editor.
--
-- All statements use CREATE TABLE IF NOT EXISTS — safe to re-run.
--
-- Architecture:
--   Private tables  (service_role key only — MCP server):
--     providers, patients, assessments_*, encounters,
--     contacts, crisis_events, kpi_compliance, pipeline_runs
--   Public table  (anon key — website dashboard):
--     clinic_stats  (aggregate only, zero PII)
-- ============================================================

-- ── Extensions ───────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- ── providers ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS providers (
    provider_id  TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    team         TEXT NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ── patients (PHI — service_role only) ────────────────────────
CREATE TABLE IF NOT EXISTS patients (
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
CREATE TABLE IF NOT EXISTS assessments_phq9 (
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
CREATE TABLE IF NOT EXISTS assessments_gad7 (
    id                UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    patient_id        TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
    assessment_date   DATE,
    total_score       INT,
    item_scores       JSONB,
    severity          TEXT,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- ── assessments_whodas ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS assessments_whodas (
    id                UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    patient_id        TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
    assessment_date   DATE,
    total_score       INT,
    disability_level  TEXT,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- ── assessments_ssrs ──────────────────────────────────────────
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
);

-- ── encounters ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS encounters (
    encounter_id    TEXT PRIMARY KEY,
    patient_id      TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
    admit_date      DATE,
    discharge_date  DATE,
    encounter_type  TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── contacts ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contacts (
    contact_id    TEXT PRIMARY KEY,
    patient_id    TEXT REFERENCES patients(patient_id) ON DELETE CASCADE,
    contact_date  DATE,
    contact_type  TEXT,
    provider_id   TEXT REFERENCES providers(provider_id),
    days_since    INT,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ── crisis_events ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS crisis_events (
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
CREATE TABLE IF NOT EXISTS kpi_compliance (
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
CREATE POLICY IF NOT EXISTS "anon_select"        ON clinic_stats FOR SELECT TO anon         USING (true);
CREATE POLICY IF NOT EXISTS "service_role_all"   ON clinic_stats FOR ALL    TO service_role USING (true) WITH CHECK (true);


-- ── pipeline_runs  (operational audit log — service_role only) ─────────────
-- One row per orchestrator.py execution. Persisted in Stage 5 of each run.
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id               TEXT PRIMARY KEY,           -- cm-YYYYMMDD-HHMMSS-xxxxxx
    started_at           TIMESTAMPTZ NOT NULL,
    completed_at         TIMESTAMPTZ,
    status               TEXT NOT NULL DEFAULT 'running', -- running | success | failed
    config               JSONB,                      -- CLI flags used for this run
    records_extracted    INT DEFAULT 0,
    records_transformed  INT DEFAULT 0,
    records_loaded       INT DEFAULT 0,
    records_rejected     INT DEFAULT 0,
    stages               JSONB,                      -- array of StageResult dicts
    error_message        TEXT
);

ALTER TABLE pipeline_runs ENABLE ROW LEVEL SECURITY;
CREATE POLICY IF NOT EXISTS "service_role_all" ON pipeline_runs
    FOR ALL TO service_role USING (true) WITH CHECK (true);


-- ============================================================
-- src schema — staging / source tables
-- All tables: service_role only (pipeline-internal, no PII
-- exposed to anon key).
-- ============================================================

CREATE SCHEMA IF NOT EXISTS src;


-- ── src.departments_of_interest ──────────────────────────────
CREATE TABLE IF NOT EXISTS src.departments_of_interest (
    department_name      VARCHAR(255) NOT NULL PRIMARY KEY,
    is_inpatient         BOOLEAN NOT NULL,
    is_outpatient        BOOLEAN NOT NULL,
    is_crisis_department BOOLEAN NOT NULL
);

INSERT INTO src.departments_of_interest (department_name, is_inpatient, is_outpatient, is_crisis_department) VALUES
('Behavioral Health Inpatient Unit A',         true,  false, true),
('Behavioral Health Inpatient Unit B',         true,  false, true),
('Behavioral Health Inpatient Unit C',         true,  false, true),
('Psychiatric Emergency Unit',                 false, false, true),
('Midtown Behavioral Health',                  false, true,  false),
('Outpatient Psychiatry - North Campus',       false, true,  false),
('Outpatient Psychiatry - South Campus',       false, true,  false),
('Outpatient Psychiatry - East Campus',        false, true,  false),
('Outpatient Psychiatry - West Campus',        false, true,  false),
('Westside Recovery Clinic',                   false, true,  false),
('Eastside Behavioral Health Clinic',          false, true,  false),
('Northside Behavioral Health Clinic',         false, true,  false),
('Adult Outpatient Psychiatry',                false, true,  false),
('Assertive Community Treatment (ACT)',        false, true,  false),
('Behavioral Health Case Management',          false, true,  false),
('Community Support Team (CST)',               false, true,  false),
('CORE Services',                              false, true,  false),
('Integrated Care Team',                       false, true,  false),
('Community Care Management',                  false, true,  false),
('Mobile Crisis Response',                     false, true,  false),
('Behavioral Health Primary Care Integration', false, true,  false)
ON CONFLICT DO NOTHING;


-- ── src.grady_departments ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS src.grady_departments (
    department_key       BIGINT,
    department_name      VARCHAR(255),
    location_name        VARCHAR(255),
    county               VARCHAR(255),
    city                 VARCHAR(255),
    type                 VARCHAR(255),
    is_inpatient         BOOLEAN,
    is_outpatient        BOOLEAN,
    is_crisis_department BOOLEAN
);


-- ── src.grady_encounter ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS src.grady_encounter (
    person_id                 BIGINT,
    provider_id               BIGINT,
    encounter_id              BIGINT,
    note_id                   BIGINT,
    encounter_status          VARCHAR(100),
    encounter_type            VARCHAR(100),
    note_status               VARCHAR(100),
    encounter_date            DATE,
    appointment_date_time     TIMESTAMPTZ,
    service_instant           TIMESTAMPTZ,
    admit_date                DATE,
    admit_date_time           TIMESTAMPTZ,
    discharge_date            DATE,
    discharge_instant         TIMESTAMPTZ,
    encounter_visit_desc      VARCHAR(255),
    visit_desc                VARCHAR(255),
    visit_epic_id             VARCHAR(100),
    admission_source          VARCHAR(255),
    discharge_disposition     VARCHAR(255),
    department_key            BIGINT,
    department_name           VARCHAR(255),
    department_type           VARCHAR(100),
    pos_key                   BIGINT,
    pos_name                  VARCHAR(255),
    county                    VARCHAR(100),
    location_name             VARCHAR(255),
    provider_npi              VARCHAR(50),
    provider_type             VARCHAR(100),
    clinician_title           VARCHAR(100),
    last_name                 VARCHAR(255),
    first_name                VARCHAR(255),
    role                      VARCHAR(100),
    role_category             VARCHAR(255),
    email                     VARCHAR(255),
    can_authorize_medication  BOOLEAN,
    doc_note_type             VARCHAR(100),
    appt_status               VARCHAR(50),
    pes_reason                VARCHAR(255),
    is_psychiatric_emergency  BOOLEAN,
    is_crisis_intervention    BOOLEAN
);
CREATE INDEX IF NOT EXISTS IX_grady_encounter_person    ON src.grady_encounter (person_id);
CREATE INDEX IF NOT EXISTS IX_grady_encounter_encounter ON src.grady_encounter (encounter_id);


-- ── src.grady_person ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS src.grady_person (
    DurableKey                    BIGINT,
    StartDate                     DATE,
    DeathDate                     DATE,
    GenderIdentity                VARCHAR(156),
    Sex                           VARCHAR(156),
    SexAssignedAtBirth            VARCHAR(156),
    Ethnicity                     VARCHAR(300),
    PrimaryCareProviderDurableKey BIGINT,
    FirstName                     VARCHAR(200),
    LastName                      VARCHAR(300),
    BirthDate                     DATE,
    PrimaryMRN                    VARCHAR(150),
    PostalCode                    VARCHAR(100),
    FirstRace                     VARCHAR(255),
    MaritalStatus                 VARCHAR(300)
);
CREATE INDEX IF NOT EXISTS IX_grady_person_durablekey ON src.grady_person ("DurableKey");


-- ── src.allergies ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS src.allergies (
    su_id             BIGINT NOT NULL,
    allergy_id        BIGINT NOT NULL,
    allergy_name      VARCHAR(255),
    "StartDateKey"    BIGINT,
    "StartDate"       DATE,
    "EndDateKey"      BIGINT,
    "EndDate"         DATE,
    "Severity"        VARCHAR(50),
    "Status"          VARCHAR(50),
    allergy_type      VARCHAR(100),
    unknown_allergies BOOLEAN
);
CREATE INDEX IF NOT EXISTS IX_allergies_su_id_allergy_id ON src.allergies (su_id, allergy_id);


-- ── src.grady_assessment ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS src.grady_assessment (
    "EncounterKey"      BIGINT,
    "PatientDurableKey" BIGINT,
    "DurableKey"        BIGINT,
    "FTDName"           VARCHAR(200),
    "DateValue"         DATE,
    "FRDName"           VARCHAR(300),
    "Value"             VARCHAR(2500)
);


-- ── src.grady_dla20 ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS src.grady_dla20 (
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
);


-- ── src.grady_cssrs ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS src.grady_cssrs (
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
);


-- ── src.grady_gad7 ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS src.grady_gad7 (
    person_id                    BIGINT,
    encounter_id                 BIGINT,
    employee_id                  BIGINT,
    assessment_date              TIMESTAMPTZ,
    feeling_nervous              NUMERIC(3,2),
    restless                     NUMERIC(3,2),
    worry_about_different_things NUMERIC(3,2),
    trouble_relaxing             NUMERIC(3,2),
    easily_annoyed               NUMERIC(3,2),
    feeling_afraid               NUMERIC(3,2),
    constant_worry               NUMERIC(3,2),
    total_score                  NUMERIC(4,2)
);


-- ── src.grady_pain_assessment ─────────────────────────────────
CREATE TABLE IF NOT EXISTS src.grady_pain_assessment (
    su_id             BIGINT,
    encounter_id      BIGINT,
    staff_id          BIGINT,
    assessment_date   TIMESTAMPTZ,
    accepted_flg      SMALLINT,
    pain_score        NUMERIC(4,2),
    pain_source_value VARCHAR(255)
);


-- ── src.grady_phq9 ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS src.grady_phq9 (
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
);


-- ── src.grady_safety_plan_mapping ────────────────────────────
CREATE TABLE IF NOT EXISTS src.grady_safety_plan_mapping (
    field_id      VARCHAR(50)  NOT NULL PRIMARY KEY,
    plan_name     VARCHAR(300) NOT NULL,
    step_number   SMALLINT     NOT NULL,
    step_label    VARCHAR(100) NOT NULL,
    field_label   VARCHAR(255) NOT NULL,
    data_type     VARCHAR(50)  NOT NULL,
    is_repeatable BOOLEAN      NOT NULL DEFAULT FALSE,
    display_order SMALLINT     NOT NULL
);

INSERT INTO src.grady_safety_plan_mapping
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
ON CONFLICT DO NOTHING;


-- ── src.grady_crisis_safety_plan ─────────────────────────────
CREATE TABLE IF NOT EXISTS src.grady_crisis_safety_plan (
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
);


-- ── src.grady_diagnosis ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS src.grady_diagnosis (
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
);


-- ── src.grady_drug ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS src.grady_drug (
    su_id      BIGINT,
    drug_id    BIGINT,
    name       VARCHAR(255),
    start_date DATE,
    end_date   DATE
);


-- ── src.drug_procedure_mapping ────────────────────────────────
CREATE TABLE IF NOT EXISTS src.drug_procedure_mapping (
    drug_id               BIGINT,
    procedure_code        VARCHAR(255),
    procedure_description VARCHAR(500)
);


-- ── src.inpatient ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS src.inpatient (
    encounter_id   BIGINT,
    patient_id     BIGINT,
    ward           VARCHAR(300),
    ward_specialty VARCHAR(300),
    out_of_area    BOOLEAN,
    start_date     DATE,
    end_date       DATE
);


-- ── src.prescriptions ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS src.prescriptions (
    su_id                     BIGINT,
    drug_id                   BIGINT,
    name                      VARCHAR(255),
    days_supply               NUMERIC(18,2),
    refills_remaining         SMALLINT,
    dosage                    TEXT,
    drug_route                VARCHAR(255),
    drug_class                VARCHAR(255),
    start_date                DATE,
    end_date                  DATE,
    ordered_date              DATE,
    prescribing_provider_name VARCHAR(255)
);


-- ── src.grady_procedures ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS src.grady_procedures (
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
);
CREATE INDEX IF NOT EXISTS IX_grady_procedures ON src.grady_procedures (procedure_durable_key);


-- ── src.grady_providers ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS src.grady_providers (
    provider_id              BIGINT,
    provider_npi             VARCHAR(50),
    provider_type            VARCHAR(100),
    clinician_title          VARCHAR(100),
    provider_name            VARCHAR(255),
    role_category            VARCHAR(255),
    email                    TEXT,
    can_authorize_medication BOOLEAN
);


-- ── src.grady_substanceuse ────────────────────────────────────
-- ICD-10 substance use disorder codes (reference data, no PK — dupes in source)
CREATE TABLE IF NOT EXISTS src.grady_substanceuse (
    icd_concept_name VARCHAR(255),
    icd_code         VARCHAR(20)
);
-- (Populated via ensure_schema.py insert-if-empty guard)


-- ── src.ZipCodeList ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS src."ZipCodeList" (
    "ZipCode" VARCHAR(5)   NOT NULL,
    "City"    VARCHAR(100) NOT NULL,
    "County"  VARCHAR(100) NOT NULL,
    "State"   CHAR(2)      NOT NULL
);
-- (Populated via ensure_schema.py insert-if-empty guard)


-- ── src.grady_treatment_plan ──────────────────────────────────
CREATE TABLE IF NOT EXISTS src.grady_treatment_plan (
    bh_treatment_plan_id     BIGINT,
    plan_of_care_id          BIGINT,
    encounter_id             BIGINT,
    person_id                BIGINT,
    provider_id              BIGINT,
    plan_of_care_name        VARCHAR(255),
    treatment_plan_date      DATE,
    next_treatment_plan_date DATE,
    plan_of_care_status      VARCHAR(255)
);


-- ── RLS: all src tables (service_role only) ───────────────────
DO $$
DECLARE t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'src.departments_of_interest','src.grady_departments','src.grady_encounter',
        'src.grady_person','src.allergies','src.grady_assessment','src.grady_dla20',
        'src.grady_cssrs','src.grady_gad7','src.grady_pain_assessment','src.grady_phq9',
        'src.grady_safety_plan_mapping','src.grady_crisis_safety_plan','src.grady_diagnosis',
        'src.grady_drug','src.drug_procedure_mapping','src.inpatient','src.prescriptions',
        'src.grady_procedures','src.grady_providers','src.grady_substanceuse',
        'src.grady_treatment_plan'
    ] LOOP
        EXECUTE format('ALTER TABLE %s ENABLE ROW LEVEL SECURITY', t);
        BEGIN
            EXECUTE format(
                'CREATE POLICY "service_role_all" ON %s FOR ALL TO service_role USING (true) WITH CHECK (true)',
                t
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END;
    END LOOP;
    -- ZipCodeList separately (quoted identifier)
    EXECUTE 'ALTER TABLE src."ZipCodeList" ENABLE ROW LEVEL SECURITY';
    BEGIN
        EXECUTE 'CREATE POLICY "service_role_all" ON src."ZipCodeList" FOR ALL TO service_role USING (true) WITH CHECK (true)';
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;
END $$;

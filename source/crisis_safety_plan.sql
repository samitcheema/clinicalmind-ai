/*
Maps each form field to its section in the Stanley-Brown Safety Planning Intervention (SPI).
The SPI has 6 standardized steps:
  Step 1 — Warning signs (WS): personal indicators that a crisis may be developing
  Step 2 — Internal coping strategies (IC): things the patient can do alone to distract
  Step 3 — Social distractions (SD): people/places that provide distraction without disclosure
  Step 4 — Social support contacts (SH): people the patient can ask for help
  Step 5 — Professional/agency contacts (PR): clinicians, crisis lines, emergency services
  Step 6 — Means restriction (MR): identifying and restricting access to lethal means
  Acknowledgment (AC): patient and clinician signatures confirming the plan
*/
IF OBJECT_ID('src.safety_plan_mapping') IS NOT NULL
    DROP TABLE src.safety_plan_mapping;
GO

CREATE TABLE src.safety_plan_mapping (
    field_id   NVARCHAR(50)  NOT NULL PRIMARY KEY   -- stable identifier for this form field
    , plan_name VARCHAR(300) NOT NULL                -- name of the safety plan this field belongs to
    , step_number TINYINT    NOT NULL                -- SPI step (1–6) or 0 for acknowledgment
    , step_label  NVARCHAR(100) NOT NULL             -- human-readable step name
    , field_label NVARCHAR(255) NOT NULL             -- label shown on the form
    , data_type   NVARCHAR(50)  NOT NULL             -- 'text', 'phone', 'date', 'boolean'
    , is_repeatable BIT NOT NULL DEFAULT 0           -- 1 if multiple values are collected per step
    , display_order TINYINT NOT NULL                 -- order within the step
);
PRINT 'Table src.safety_plan_mapping created.'
GO

INSERT INTO src.safety_plan_mapping
    (field_id, plan_name, step_number, step_label, field_label, data_type, is_repeatable, display_order)
VALUES
-- Step 1: Warning Signs
('SPI-WS-01', 'Stanley-Brown Safety Planning Intervention', 1, 'Warning Signs', 'Warning sign 1 (thoughts/feelings)',    'text', 1, 1)
, ('SPI-WS-02', 'Stanley-Brown Safety Planning Intervention', 1, 'Warning Signs', 'Warning sign 2 (behaviors)',             'text', 1, 2)
, ('SPI-WS-03', 'Stanley-Brown Safety Planning Intervention', 1, 'Warning Signs', 'Warning sign 3 (situations/triggers)',   'text', 1, 3)

-- Step 2: Internal Coping Strategies
, ('SPI-IC-01', 'Stanley-Brown Safety Planning Intervention', 2, 'Internal Coping Strategies', 'Internal coping strategy 1', 'text', 1, 1)
, ('SPI-IC-02', 'Stanley-Brown Safety Planning Intervention', 2, 'Internal Coping Strategies', 'Internal coping strategy 2', 'text', 1, 2)
, ('SPI-IC-03', 'Stanley-Brown Safety Planning Intervention', 2, 'Internal Coping Strategies', 'Internal coping strategy 3', 'text', 1, 3)

-- Step 3: Social Distractions (people/settings that provide distraction without disclosing suicidal ideation)
, ('SPI-SD-01', 'Stanley-Brown Safety Planning Intervention', 3, 'Social Distractions', 'Social distraction contact/place 1', 'text', 1, 1)
, ('SPI-SD-02', 'Stanley-Brown Safety Planning Intervention', 3, 'Social Distractions', 'Social distraction contact/place 2', 'text', 1, 2)
, ('SPI-SD-03', 'Stanley-Brown Safety Planning Intervention', 3, 'Social Distractions', 'Social distraction contact/place 3', 'text', 1, 3)

-- Step 4: Social Support Contacts (people to ask for help)
, ('SPI-SH-01', 'Stanley-Brown Safety Planning Intervention', 4, 'Social Support Contacts', 'Support contact 1 – name',  'text',  1, 1)
, ('SPI-SH-02', 'Stanley-Brown Safety Planning Intervention', 4, 'Social Support Contacts', 'Support contact 1 – phone', 'phone', 1, 2)
, ('SPI-SH-03', 'Stanley-Brown Safety Planning Intervention', 4, 'Social Support Contacts', 'Support contact 2 – name',  'text',  1, 3)
, ('SPI-SH-04', 'Stanley-Brown Safety Planning Intervention', 4, 'Social Support Contacts', 'Support contact 2 – phone', 'phone', 1, 4)
, ('SPI-SH-05', 'Stanley-Brown Safety Planning Intervention', 4, 'Social Support Contacts', 'Support contact 3 – name',  'text',  1, 5)
, ('SPI-SH-06', 'Stanley-Brown Safety Planning Intervention', 4, 'Social Support Contacts', 'Support contact 3 – phone', 'phone', 1, 6)

-- Step 5: Professional and Agency Contacts
, ('SPI-PR-01', 'Stanley-Brown Safety Planning Intervention', 5, 'Professional Contacts', 'Treating clinician – name',           'text',  0, 1)
, ('SPI-PR-02', 'Stanley-Brown Safety Planning Intervention', 5, 'Professional Contacts', 'Treating clinician – phone',          'phone', 0, 2)
, ('SPI-PR-03', 'Stanley-Brown Safety Planning Intervention', 5, 'Professional Contacts', 'Crisis line – name',                  'text',  0, 3)
, ('SPI-PR-04', 'Stanley-Brown Safety Planning Intervention', 5, 'Professional Contacts', 'Crisis line – phone',                 'phone', 0, 4)
, ('SPI-PR-05', 'Stanley-Brown Safety Planning Intervention', 5, 'Professional Contacts', 'Additional professional – name',      'text',  1, 5)
, ('SPI-PR-06', 'Stanley-Brown Safety Planning Intervention', 5, 'Professional Contacts', 'Additional professional – phone',     'phone', 1, 6)
, ('SPI-PR-07', 'Stanley-Brown Safety Planning Intervention', 5, 'Professional Contacts', 'Nearest emergency department – name', 'text',  0, 7)
, ('SPI-PR-08', 'Stanley-Brown Safety Planning Intervention', 5, 'Professional Contacts', 'Nearest emergency department – address', 'text', 0, 8)

-- Step 6: Means Restriction
, ('SPI-MR-01', 'Stanley-Brown Safety Planning Intervention', 6, 'Means Restriction', 'Lethal means identified',              'text',    1, 1)
, ('SPI-MR-02', 'Stanley-Brown Safety Planning Intervention', 6, 'Means Restriction', 'Means restriction plan',               'text',    1, 2)
, ('SPI-MR-03', 'Stanley-Brown Safety Planning Intervention', 6, 'Means Restriction', 'Responsible party for safekeeping',    'text',    1, 3)
, ('SPI-MR-04', 'Stanley-Brown Safety Planning Intervention', 6, 'Means Restriction', 'Firearms removed or secured',          'boolean', 0, 4)
, ('SPI-MR-05', 'Stanley-Brown Safety Planning Intervention', 6, 'Means Restriction', 'Medications secured or limited supply', 'boolean', 0, 5)

-- Acknowledgment
, ('SPI-AC-01', 'Stanley-Brown Safety Planning Intervention', 0, 'Acknowledgment', 'Patient acknowledged plan',     'boolean', 0, 1)
, ('SPI-AC-02', 'Stanley-Brown Safety Planning Intervention', 0, 'Acknowledgment', 'Clinician signature',          'text',    0, 2)
, ('SPI-AC-03', 'Stanley-Brown Safety Planning Intervention', 0, 'Acknowledgment', 'Plan completion date',         'date',    0, 3)
, ('SPI-AC-04', 'Stanley-Brown Safety Planning Intervention', 0, 'Acknowledgment', 'Next review date',             'date',    0, 4)
GO

/*
Table contains Crisis Safety Plan data for NBH patients

This table captures crisis safety plan information by linking patient attribute values to their corresponding safety plan.
It tracks details about the input fields (name, abbreviation, data type), the plan name, and when the plan was completed.
There is no attribution to encounters, so it does not require a join to the encounters table
*/
IF OBJECT_ID('src.crisis_safety_plan') IS NOT NULL
    DROP TABLE src.crisis_safety_plan;
GO

CREATE TABLE src.crisis_safety_plan (
    person_id BIGINT  -- Patient for whom the crisis safety plan record was created
    , attribute_id BIGINT -- Identifier for the attribute associated with the crisis safety plan
    , smart_data_element_epic_id NVARCHAR(50) -- EPIC identifier linking the attribute to the safety plan mapping
    , plan_name NVARCHAR(300) -- Name of the crisis safety plan as defined in the mapping table
    , input_name NVARCHAR(300) -- Name of the input field from the attribute data
    , input_abbreviation NVARCHAR(300) -- Abbreviation of the input field
    , data_type NVARCHAR(300) -- Data type of the input field (e.g., string, numeric, date)
    , completion_date DATE -- Date when the crisis safety plan element was completed
    , input_value NVARCHAR(300) -- Textual input value captured for the attribute
    , input_numeric_value NUMERIC(18, 2) -- Numeric input value captured for the attribute
    , input_date_value DATE -- Date input value captured for the attribute
);
PRINT 'Table src.crisis_safety_plan created.';
GO

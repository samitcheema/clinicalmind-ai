IF Object_Id('src.grady_encounter') IS NOT NULL
    DROP TABLE src.grady_encounter
GO

CREATE TABLE src.grady_encounter (
    person_id BIGINT
    , provider_id BIGINT
    , encounter_id BIGINT
    , note_id BIGINT
    , encounter_status NVARCHAR(100)    -- 'Completed', 'In Progress', 'Entered in Error', 'Possible'
    , encounter_type NVARCHAR(100)
    , note_status NVARCHAR(100)
    , encounter_date DATE               -- last contact date with staff. FIXME: Misleading column name should be fixed.
    , appointment_date_time DATETIME    -- appointment date and time
    , service_instant DATETIME          -- last contact date and time with staff
    , admit_date DATE                   -- admission date at facility
    , admit_date_time DATETIME          -- Admission date and time NOTE: This does not always map to the initial encounter date.
    , discharge_date DATE               -- discharge date at facility
    , discharge_instant DATETIME        -- discharge date and time from facility
    , encounter_visit_desc NVARCHAR(255)
    , visit_desc NVARCHAR(255)
    , visit_epic_id NVARCHAR(100)
    , admission_source NVARCHAR(255)
    , discharge_disposition NVARCHAR(255)
    , department_key BIGINT
    , department_name NVARCHAR(255)
    , department_type NVARCHAR(100)
    , pos_key BIGINT                    -- internal Place of Service Key NOTE: This does not correspond to actual CMS Place of Service Code
    , pos_name NVARCHAR(255)            -- Place of Service Name
    , county NVARCHAR(100)
    , location_name NVARCHAR(255)
    , provider_npi NVARCHAR(50)         -- National Provider ID number, Clinicians, Technicians, Social Workers, Counselors will have this field as blank
    , provider_type NVARCHAR(100)
    , clinician_title NVARCHAR(100)
    , last_name NVARCHAR(255)
    , first_name NVARCHAR(255)
    , role NVARCHAR(100)
    , role_category NVARCHAR(255)
    , email NVARCHAR(255)
    , can_authorize_medication BIT
    , doc_note_type NVARCHAR(100)
    , appt_status NVARCHAR(50)          -- 'Completed', 'Cancelled', 'Scheduled', 'Rescheduled', 'No Show', 'Confirmed', 'Arrived', 'Pending', 'Left Without Being Seen', 'Triaged, Not Seen', 'NULL', '*Unspecified'
    , pes_reason NVARCHAR(255)
    , is_psychiatric_emergency BIT      -- Psychiatric Emergency Services visit (suicidal chief complaint or diagnosis in ED)
    , is_crisis_intervention BIT        -- Crisis Intervention Services visit
);
GO

PRINT 'Table src.grady_encounter created.'
GO

CREATE NONCLUSTERED INDEX IX_grady_encounter_person
    ON src.grady_encounter (person_id)
    INCLUDE (
        encounter_id
        , encounter_date
        , encounter_status
        , department_key
    )
GO

CREATE NONCLUSTERED INDEX IX_grady_encounter_encounter
    ON src.grady_encounter (encounter_id)
    INCLUDE (
        person_id
        , encounter_date
        , encounter_status
        , department_key
    )
GO

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

-- Accumulate encounters from two sources:
--  1. PES encounters derived via chief complaints/suicide diagnoses (from 'GHS EMERGENCY'(6758))
--  2. Regular encounters defined via src.grady_departments (excluding department 6758)

-- Patients with relevant chief complaints
WITH patients_with_relevant_chief_complaints AS (
    SELECT DISTINCT
        CCEF.PatientDurableKey
        , CCEF.EncounterKey
        , CCD.Name AS ChiefComplaint
    FROM [CDW].[dbo].ChiefComplaintEventFact CCEF
    INNER JOIN [CDW].[dbo].ChiefComplaintDim CCD ON CCEF.ChiefComplaintKey = CCD.ChiefComplaintKey
    WHERE
        CCD.Name = 'PSYCHIATRIC EVALUATION'
        OR CCD.Name LIKE '%SUICI%'
        OR CCD.Name LIKE '%DEPRESSION%'
        OR CCD.Name LIKE '%ANXIETY%'
        OR CCD.Name LIKE '%HALLUC%'
        OR CCD.Name LIKE '%HOMIC%'
        OR CCD.Name LIKE '%PARANOID%'
        OR CCD.Name LIKE '%SUICIDE ATTEMPT%'
        OR CCD.Name LIKE '%MENTAL HEA%'
        OR CCD.Name LIKE '%PANIC ATTACK%'
        OR CCD.Name LIKE '%DELUSIONAL%'
        OR CCD.Name LIKE '%SCHIZOPHRENIA%'
        OR CCD.Name LIKE '%MANIC%'
        OR CCD.Name LIKE '%ADD%'
        OR CCD.Name LIKE '%OVERDOSE%'
        OR CCD.Name LIKE '%PSYCHO%'
)

-- Patients with suicide-related diagnosis
, patients_with_suicide_diagnosis AS (
    SELECT
        DEF.PatientDurableKey
        , DEF.EncounterKey
        , DTD.NameAndCode AS diagnosis_desc
    FROM [CDW].[dbo].DiagnosisEventFact DEF
    INNER JOIN [CDW].[dbo].DiagnosisTerminologyDim DTD ON DEF.DiagnosisKey = DTD.DiagnosisKey
    WHERE
        DTD.NameAndCode LIKE '%suici%'
        AND DEF.EncounterKey != -1
)

, pes_patients AS (
    SELECT DISTINCT
        SD.PatientDurableKey AS su_id
        , SD.EncounterKey
        , SD.diagnosis_desc AS reason
    FROM patients_with_suicide_diagnosis SD
    UNION
    SELECT DISTINCT
        RC.PatientDurableKey AS su_id
        , RC.EncounterKey
        , RC.ChiefComplaint AS reason
    FROM patients_with_relevant_chief_complaints RC
)

, pes_encounters AS (
    SELECT DISTINCT
        C.ClinicalNoteKey
        , C.PatientDurableKey
        , C.ServiceDateKey
        , C.AuthoringProviderDurableKey AS provider_id
        , C.EncounterKey
        , C.AuthorType
        , C.Status
        , C.Type AS doc_note_type
        , C.ServiceInstant
        , D.DepartmentName
        , D.Type
        , D.County
        , D.LocationName
        , E.DerivedEncounterStatus
        , E.Type AS encounter_type
        , E.AdmissionDateKey
        , E.DischargeDateKey
        , E.AdmissionInstant
        , E.DischargeInstant
        , E.VisitType
        , E.AdmissionSource
        , E.DischargeDisposition
        , E.DepartmentKey
        , E.PlaceOfServiceKey
        , 1
            AS is_psychiatric_emergency  -- Flag to identify PES patients
        , 0
            AS is_crisis_intervention
        , PES.reason AS pes_reason
    FROM [CDW].[dbo].[ClinicalNoteFact] C
    INNER JOIN [CDW].[dbo].[EncounterFact] E ON C.EncounterKey = E.EncounterKey
    INNER JOIN [CDW].[dbo].[DepartmentDim] D ON E.DepartmentKey = D.DepartmentKey
    INNER JOIN pes_patients PES
        ON
            C.PatientDurableKey = PES.su_id
            AND C.EncounterKey = PES.EncounterKey
    WHERE D.DepartmentName LIKE '%GHS EMERGENCY%'
)

-- Encounters derived from departments defined in src.grady_departments table
, department_encounters AS (
    SELECT DISTINCT
        C.ClinicalNoteKey
        , E.PatientDurableKey
        , C.ServiceDateKey
        , COALESCE(C.AuthoringProviderDurableKey, E.ProviderDurableKey) AS provider_id
        , E.EncounterKey
        , C.AuthorType
        , C.Status
        , C.Type AS doc_note_type
        , C.ServiceInstant
        , MGD.department_name
        , MGD.type
        , MGD.county
        , MGD.location_name
        , E.DerivedEncounterStatus
        , E.Type AS encounter_type
        , E.AdmissionDateKey
        , E.DischargeDateKey
        , E.AdmissionInstant
        , E.DischargeInstant
        , E.VisitType
        , E.AdmissionSource
        , E.DischargeDisposition
        , E.DepartmentKey
        , E.PlaceOfServiceKey
        , 0
            AS is_psychiatric_emergency
        -- Crisis Intervention Unit(6955) and GHS CRISIS INTERV SVCS(7276)
        , CASE WHEN E.DepartmentKey IN (6955, 7276) THEN 1 ELSE 0 END
            AS is_crisis_intervention
        , NULL AS pes_reason
    FROM [CDW].[dbo].[EncounterFact] E
    INNER JOIN [src].grady_departments MGD ON E.DepartmentKey = MGD.department_key
    LEFT JOIN [CDW].[dbo].[ClinicalNoteFact] C ON E.EncounterKey = C.EncounterKey
    -- Note: Our current `grady_departments` table returns a single department by key,
    -- so this filter works for now. However, if in the future multiple departments are linked to GHS Emergency,
    -- we may need to adjust this condition accordingly.
    WHERE MGD.department_key != 6758   -- Exclude records from department 'GHS EMERGENCY' (PES Patients).
)

, relevant_encounters AS (
    SELECT * FROM pes_encounters
    UNION
    SELECT * FROM department_encounters
)

INSERT INTO src.grady_encounter (
    person_id
    , provider_id
    , encounter_id
    , note_id
    , encounter_status
    , encounter_type
    , note_status
    , encounter_date
    , appointment_date_time
    , service_instant
    , admit_date
    , admit_date_time
    , discharge_date
    , discharge_instant
    , encounter_visit_desc
    , visit_desc
    , visit_epic_id
    , admission_source
    , discharge_disposition
    , department_key
    , department_name
    , department_type
    , pos_key
    , pos_name
    , county
    , location_name
    , provider_npi
    , provider_type
    , clinician_title
    , last_name
    , first_name
    , role
    , role_category
    , email
    , can_authorize_medication
    , doc_note_type
    , appt_status
    , pes_reason
    , is_psychiatric_emergency
    , is_crisis_intervention
)
SELECT DISTINCT
    RE.PatientDurableKey AS person_id
    , RE.provider_id
    , RE.EncounterKey AS encounter_id
    , RE.ClinicalNoteKey AS note_id
    , RE.DerivedEncounterStatus AS encounter_status
    , RE.encounter_type
    , RE.Status AS note_status
    , SRVC.DateValue AS encounter_date
    , V.AppointmentInstant AS appointment_date_time
    , RE.ServiceInstant AS service_instant
    /*
    NOTE: the minimum last contact date with staff per encounter_id does not always map to the initial encounter date.
    i.e. Patients comes to ED and is admitted around 23:00 but is seen the next day.
    NOTE: Any rules assuming this is strictly the initial encounter date should be resolved.
    */
    , ADMIT.DateValue AS admit_date
    , RE.AdmissionInstant AS admit_date_time
    , DISCH.DateValue AS discharge_date
    , RE.DischargeInstant AS discharge_instant
    , RE.VisitType AS encounter_visit_desc
    , V.VisitType AS visit_desc
    , V.visittypeepicid AS visit_epic_id
    , RE.AdmissionSource AS admission_source
    , RE.DischargeDisposition AS discharge_disposition
    , RE.DepartmentKey AS department_key
    , RE.DepartmentName AS department_name
    , RE.Type AS department_type
    , RE.PlaceOfServiceKey AS pos_key
    , POS.Name AS pos_name
    , RE.County
    , RE.LocationName AS location_name
    , CASE WHEN P.npi IN ('*Unspecified', '*Unknown') THEN '' ELSE P.npi END AS provider_npi
    , P.Type AS provider_type
    , P.ClinicianTitle AS clinician_title
    , CASE
        WHEN CHARINDEX(',', P.Name) > 0 THEN LEFT(P.Name, CHARINDEX(',', P.Name) - 1)
        ELSE P.Name
    END AS last_name
    , CASE
        WHEN CHARINDEX(',', P.Name) > 0 THEN LTRIM(RIGHT(P.Name, LEN(P.Name) - CHARINDEX(',', P.Name)))
        ELSE P.Name
    END AS first_name
    , RE.AuthorType AS role
    , P.PrimarySpecialty AS role_category
    , P.Email
    , P.ismedicationauthorizingprovider AS can_authorize_medication
    , RE.doc_note_type
    , V.appointmentstatus AS appt_status
    , RE.pes_reason
    , RE.is_psychiatric_emergency
    , RE.is_crisis_intervention
FROM relevant_encounters RE
LEFT JOIN [CDW].[dbo].[PlaceOfServiceDim] POS ON RE.PlaceOfServiceKey = POS.PlaceOfServiceKey
LEFT JOIN [CDW].[dbo].[ProviderDim] P ON RE.provider_id = P.DurableKey
LEFT JOIN [CDW].[dbo].[VisitFact] V ON RE.EncounterKey = V.EncounterKey
LEFT JOIN [CDW].[dbo].[DateDim] ADMIT ON RE.AdmissionDateKey = ADMIT.DateKey
LEFT JOIN [CDW].[dbo].[DateDim] DISCH ON RE.DischargeDateKey = DISCH.DateKey
LEFT JOIN [CDW].[dbo].[DateDim] SRVC ON RE.ServiceDateKey = SRVC.DateKey
WHERE
    CAST(COALESCE(RE.ServiceInstant, V.AppointmentInstant) AS DATE) BETWEEN DATEADD(MONTH, -24, GETDATE()) AND DATEADD(MONTH, 3, GETDATE())
    -- Exclude invalid providers, keep nulls for unassigned providers related to future encounters
    AND (P.IsCurrent = 1 OR P.IsCurrent IS NULL)
    AND (P.DurableKey NOT IN (-3, -2, -1) OR P.DurableKey IS NULL)
    AND (
        (V.CheckInTimeOfDayKey IS NOT NULL AND V.CheckOutTimeOfDayKey IS NOT NULL)
        OR RE.AdmissionDateKey IS NOT NULL
    )
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

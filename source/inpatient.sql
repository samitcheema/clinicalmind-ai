IF OBJECT_ID('src.inpatient') IS NOT NULL
    DROP TABLE src.inpatient
GO

CREATE TABLE src.inpatient (
    encounter_id BIGINT
    , patient_id BIGINT
    , ward NVARCHAR(300)
    , ward_specialty NVARCHAR(300)
    , out_of_area BIT
    , start_date DATE
    , end_date DATE
);
PRINT 'Table src.inpatient created.'
GO

INSERT INTO src.inpatient (
    encounter_id
    , patient_id
    , ward
    , ward_specialty
    , out_of_area
    , start_date
    , end_date
)
SELECT
    encounter_id
    , person_id AS patient_id
    , LocationName AS ward
    , role_category AS ward_specialty
    , CAST(0 AS BIT) AS out_of_area
    , admit_date AS start_date
    , discharge_date AS end_date
FROM src.grady_encounter
WHERE encounter_id IN (SELECT EncounterKey FROM [CDW].[dbo].[HospitalAdmissionFact])
GO

IF OBJECT_ID('src.grady_drug') IS NOT NULL
    DROP TABLE src.grady_drug;
GO

CREATE TABLE src.grady_drug (
    su_id BIGINT             -- patient id; will be NULL for drugs that don't appear in patient records
    , drug_id BIGINT         -- drug id
    , name NVARCHAR(255)     -- drug name
    , start_date DATE        -- aggregated start date (NULL for master rows)
    , end_date DATE          -- aggregated end date (NULL for master rows)
);
PRINT 'Table src.grady_drug created.';
GO

-- 1. Insert patient event data (all patient medication events)
INSERT INTO src.grady_drug (su_id, drug_id, name, start_date, end_date)
SELECT DISTINCT
    MEF.PatientDurableKey AS su_id
    , MCD.MedicationKey AS drug_id
    , MD.Name
    , STARTDT.DateValue AS start_date
    , ISNULL(ENDDT.DateValue, STARTDT.DateValue) AS end_date
FROM src.grady_person P
INNER JOIN [CDW].[dbo].[MedicationEventFact] MEF ON P.DurableKey = MEF.PatientDurableKey
INNER JOIN [CDW].[dbo].[MedicationCodeDim] MCD ON MEF.MedicationKey = MCD.MedicationKey
INNER JOIN [CDW].[dbo].MedicationDIM MD ON MCD.MedicationKey = MD.MedicationKey
LEFT JOIN [CDW].[dbo].[DateDim] STARTDT ON MEF.StartDateKey = STARTDT.DateKey
LEFT JOIN [CDW].[dbo].[DateDim] ENDDT ON MEF.EndDateKey = ENDDT.DateKey
GO

-- 2. Insert drug_ids that don't appear in patient records
INSERT INTO src.grady_drug (su_id, drug_id, name, start_date, end_date)
SELECT
    NULL AS su_id
    , MD.MedicationKey AS drug_id
    , MD.Name
    , NULL AS start_date
    , NULL AS end_date
FROM [CDW].[dbo].[MedicationDim] MD
WHERE
    MD.MedicationKey NOT IN (-3, -2, -1)  -- Remove unknown, unspecified, and deleted MedicationKeys.
    -- Exclude drugs that already appear in the patient event data
    AND NOT EXISTS (
        SELECT 1
        FROM src.grady_drug D
        WHERE D.drug_id = MD.MedicationKey
    )
GO

IF OBJECT_ID('src.allergies') IS NOT NULL
    DROP TABLE src.allergies;
GO

CREATE TABLE src.allergies (
    su_id BIGINT NOT NULL
    , allergy_id BIGINT NOT NULL
    , allergy_name NVARCHAR(255)
    , StartDateKey BIGINT
    , StartDate DATE
    , EndDateKey BIGINT
    , EndDate DATE
    , Severity NVARCHAR(50)
    , Status NVARCHAR(50)
    , allergy_type NVARCHAR(100)
    , unknown_allergies BIT
);
PRINT 'Table src.allergies created.'
GO
/*
Some patients are logged for the same allergy on different dates,
we are only retrieving the most recent date per patient allergy to
remove duplication
*/
WITH RemoveDuplicateAllergies AS (
    SELECT
        AF.PatientDurableKey AS su_id
        , AD.AllergenKey AS allergy_id
        , AF.StartDateKey
        , STARTDT.DateValue AS StartDate
        , AF.EndDateKey
        , ENDDT.DateValue AS EndDate
        , AF.Severity
        , AF.Status
        , AD.type AS allergy_type
        , AD.name AS allergy_name
        , 0 AS unknown_allergies
        , ROW_NUMBER() OVER (
            PARTITION BY AF.PatientDurableKey, AD.AllergenKey
            ORDER BY STARTDT.DateValue DESC
        ) AS rn
    FROM src.grady_person P
    INNER JOIN [CDW].[dbo].[AllergyFact] AF ON P.DurableKey = AF.PatientDurableKey
    INNER JOIN [CDW].[dbo].[AllergenDim] AD ON AF.AllergenKey = AD.allergenkey
    INNER JOIN [CDW].[dbo].[DateDim] STARTDT ON AF.StartDateKey = STARTDT.DateKey
    INNER JOIN [CDW].[dbo].[DateDim] ENDDT ON AF.EndDateKey = ENDDT.DateKey
    WHERE
        AF.Status = 'Active'
        AND AD.AllergenKey != 22998 -- Removing any rows where allergy_name = 'UNABLE TO ASSESS', we only want to idenitfy valid allergies at this moment.
        AND AD.type != 'Environmental'  -- We only want to classify drug related allergies or allergies that might affect prescription use.
)

INSERT INTO src.allergies (
    su_id
    , allergy_id
    , allergy_name
    , StartDateKey
    , StartDate
    , EndDateKey
    , EndDate
    , Severity
    , Status
    , allergy_type
    , unknown_allergies
)
SELECT
    su_id
    , allergy_id
    , allergy_name
    , StartDateKey
    , StartDate
    , EndDateKey
    , EndDate
    , Severity
    , Status
    , allergy_type
    , unknown_allergies
FROM RemoveDuplicateAllergies
WHERE rn = 1;
GO

CREATE INDEX IX_allergies_su_id_allergy_id ON src.allergies (su_id, allergy_id);

IF OBJECT_ID('src.grady_phq9') IS NOT NULL
    DROP TABLE src.grady_phq9;
GO

-- factors scored between 1.00 and 3.00
CREATE TABLE src.grady_phq9 (
    person_id BIGINT
    , encounter_id BIGINT
    , employee_id BIGINT
    , assessment_date DATETIME
    , accepted_flg TINYINT
    , interest NUMERIC(3, 2)
    , feeling_hopeless NUMERIC(3, 2)
    , trouble_sleeping NUMERIC(3, 2)
    , feeling_tired NUMERIC(3, 2)
    , poor_appetite NUMERIC(3, 2)
    , feeling_bad NUMERIC(3, 2)
    , trouble_concentrating NUMERIC(3, 2)
    , moving_slowly NUMERIC(3, 2)
    , better_off_dead NUMERIC(3, 2)
    , how_difficult NUMERIC(3, 2) -- NOTE: We are not utilizing this question in our assessment. Once we assess numeric mapping, it will be implemented.
    , total_score NUMERIC(4, 2)
)
PRINT 'Table src.grady_phq9 created.'
GO

INSERT INTO src.grady_phq9
SELECT
    person_id
    , encounter_id
    , employee_id
    , assessment_date
    , accepted_flg
    , interest
    , feeling_hopeless
    , trouble_sleeping
    , feeling_tired
    , poor_appetite
    , feeling_bad
    , trouble_concentrating
    , moving_slowly
    , better_off_dead
    , NULL AS how_difficult
    , total_score
FROM (
    SELECT
        FVF.PatientDurableKey AS person_id
        , FVF.EncounterKey AS encounter_id
        , FVF.TakenByEmployeeDurableKey AS employee_id
        , FVF.TakenInstant AS assessment_date
        , FVF.Accepted AS accepted_flg
        , FVF.NumericValue AS numeric_value
        , CASE
            WHEN FRD.Name = N'R PHQ-9 INTEREST OR PLEASURE' THEN N'interest'
            WHEN FRD.Name = N'R PHQ-9 FEELING HOPELESS' THEN N'feeling_hopeless'
            WHEN FRD.Name = N'R PHQ-9 TROUBLE SLEEPING' THEN N'trouble_sleeping'
            WHEN FRD.Name = N'R PHQ-9 FEELING TIRED' THEN N'feeling_tired'
            WHEN FRD.Name = N'R PHQ-9 POOR APPETITE' THEN N'poor_appetite'
            WHEN FRD.Name = N'R PHQ-9 FEELING BAD' THEN N'feeling_bad'
            WHEN FRD.Name = N'R PHQ-9 TROUBLE CONCENTRATING' THEN N'trouble_concentrating'
            WHEN FRD.Name = N'R PHQ-9 MOVING SLOWLY' THEN N'moving_slowly'
            WHEN FRD.Name = N'R PHQ-9 BETTER OFF DEAD' THEN N'better_off_dead'
            WHEN FRD.Name = N'R PHQ-9 DEPRESSION SCALE - TOTAL SCORE' THEN N'total_score'
        END AS question_orig
    FROM src.grady_person P
    INNER JOIN [CDW].[dbo].[FlowsheetValueFact] FVF ON P.DurableKey = FVF.PatientDurableKey
    INNER JOIN [CDW].[dbo].[FlowsheetTemplateDim] FTD ON FVF.FlowsheetTemplateKey = FTD.FlowsheetTemplateKey
    INNER JOIN [CDW].[dbo].[FlowsheetRowDim] FRD ON FVF.FlowsheetRowKey = FRD.FlowsheetRowKey
    WHERE
        FTD.Name = N'GHS PHQ9'
) T
PIVOT (
    MAX(numeric_value)
    FOR question_orig IN (
        [interest]
        , [feeling_hopeless]
        , [trouble_sleeping]
        , [feeling_tired]
        , [poor_appetite]
        , [feeling_bad]
        , [trouble_concentrating]
        , [moving_slowly]
        , [better_off_dead]
        , [total_score]
    )
) AS pivoted_results
ORDER BY person_id, assessment_date
GO

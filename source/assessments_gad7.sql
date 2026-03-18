IF OBJECT_ID('src.grady_gad7') IS NOT NULL
    DROP TABLE src.grady_gad7;
GO


-- factors scored between 1.00 and 3.00
CREATE TABLE src.grady_gad7 (
    person_id BIGINT
    , encounter_id BIGINT
    , employee_id BIGINT
    , assessment_date DATETIME
    , feeling_nervous NUMERIC(3, 2)
    , restless NUMERIC(3, 2)
    , worry_about_different_things NUMERIC(3, 2)
    , trouble_relaxing NUMERIC(3, 2)
    , easily_annoyed NUMERIC(3, 2)
    , feeling_afraid NUMERIC(3, 2)
    , constant_worry NUMERIC(3, 2)
    , total_score NUMERIC(4, 2)
)
PRINT 'Table src.grady_gad7 created.'
GO


INSERT INTO src.grady_gad7
SELECT *
FROM (
    SELECT
        FVF.PatientDurableKey AS person_id
        , FVF.EncounterKey AS encounter_id
        , FVF.TakenByEmployeeDurableKey AS employee_id
        , FVF.TakenInstant AS assessment_date
        , FVF.NumericValue AS numeric_value
        , CASE
            WHEN FRD.Name = N'R PSYCH GAD7 FEELING' THEN 'feeling_nervous'
            WHEN FRD.Name = N'R PSYCH GAD7 RESTLESS' THEN 'restless'
            WHEN FRD.Name = N'R PSYCH GAD7 WORRY' THEN 'worry_about_different_things'
            WHEN FRD.Name = N'R PSYCH GAD7 TROUBLE RELAXING' THEN 'trouble_relaxing'
            WHEN FRD.Name = N'R PSYCH GAD7 ANNOYED' THEN 'easily_annoyed'
            WHEN FRD.Name = N'R PSYCH GAD7 AFRAID' THEN 'feeling_afraid'
            WHEN FRD.Name = N'R PSYCH GAD7 SCORE' THEN 'total_score'
            WHEN FRD.Name = N'R PSYCH GAD7 NOT STOP' THEN 'constant_worry'
        END AS question_orig
    FROM src.grady_person P
    INNER JOIN [CDW].[dbo].[FlowsheetValueFact] FVF ON P.DurableKey = FVF.PatientDurableKey
    INNER JOIN [CDW].[dbo].[FlowsheetTemplateDim] FTD ON FVF.FlowsheetTemplateKey = FTD.FlowsheetTemplateKey
    INNER JOIN [CDW].[dbo].[FlowsheetRowDim] FRD ON FVF.FlowsheetRowKey = FRD.FlowsheetRowKey
    WHERE
        FTD.Name = N'T PSYCH GAD7'
        AND FRD.Name != N'R PSYCH GAD7 DIFFICULT'
) T
PIVOT (
    MAX(numeric_value)
    FOR question_orig IN (
        [feeling_nervous]
        , [restless]
        , [worry_about_different_things]
        , [trouble_relaxing]
        , [easily_annoyed]
        , [feeling_afraid]
        , [constant_worry]
        , [total_score]
    )
) AS pivoted_results
ORDER BY person_id, assessment_date
GO

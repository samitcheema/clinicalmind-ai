IF OBJECT_ID('src.grady_pain_assessment') IS NOT NULL
    DROP TABLE src.grady_pain_assessment;
GO

CREATE TABLE src.grady_pain_assessment (
    su_id BIGINT
    , encounter_id BIGINT
    , staff_id BIGINT
    , assessment_date DATETIME
    , accepted_flg TINYINT
    , pain_score NUMERIC(4, 2)
    , pain_source_value NVARCHAR(255)
)
PRINT 'Table src.grady_pain_assessment created.'
GO

INSERT INTO src.grady_pain_assessment
SELECT
    -- FTD.Name AS template_name,
    -- FTD.DisplayName AS template_display,
    -- FRD.Name AS question_orig,
    -- FRD.DisplayName as question_display,
    -- FVF.FlowsheetValueKey AS id,
    FVF.PatientDurableKey AS su_id
    , FVF.EncounterKey AS encounter_id
    , FVF.TakenByEmployeeDurableKey AS staff_id
    , FVF.TakenInstant AS assessment_date
    , FVF.Accepted AS accepted_flg
    , CASE
        WHEN FVF.Value = N'  0 - No pain' THEN 0.0
        WHEN FVF.Value = N' 10 - Worst pain ever' THEN 10.0
        ELSE FVF.NumericValue
    END AS pain_score
    , FVF.Value AS pain_source_value
FROM src.grady_person P
INNER JOIN [CDW].[dbo].[FlowsheetValueFact] FVF ON P.DurableKey = FVF.PatientDurableKey
INNER JOIN [CDW].[dbo].[FlowsheetTemplateDim] FTD ON FVF.FlowsheetTemplateKey = FTD.FlowsheetTemplateKey
INNER JOIN [CDW].[dbo].[FlowsheetRowDim] FRD ON FVF.FlowsheetRowKey = FRD.FlowsheetRowKey
WHERE
    FTD.Name = N'AMBULATORY VITALS FLOWSHEET'
    AND FRD.Name = N'PAIN SCORE (CATEGORY LIST)'
ORDER BY su_id, assessment_date
GO

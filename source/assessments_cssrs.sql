IF OBJECT_ID('src.grady_cssrs') IS NOT NULL
    DROP TABLE src.grady_cssrs;
GO

CREATE TABLE src.grady_cssrs (
    person_id BIGINT
    , encounter_id BIGINT
    , employee_id BIGINT
    , assessment_date DATETIME
    , accepted_flg TINYINT
    , passive_ideation NVARCHAR(4)
    , active_ideation NVARCHAR(4)
    , ideation_with_intent NVARCHAR(4)
    , ideation_with_plan NVARCHAR(4)
    , ideation_with_method NVARCHAR(4)
    , prior_suicidal_behavior NVARCHAR(4)
)
PRINT 'Table src.grady_cssrs created.'
GO

INSERT INTO src.grady_cssrs
SELECT
    person_id
    , encounter_id
    , employee_id
    , assessment_date
    , accepted_flg
    , passive_ideation
    , active_ideation
    , ideation_with_intent
    , ideation_with_plan
    , ideation_with_method
    , prior_suicidal_behavior
FROM (
    SELECT
        FVF.PatientDurableKey AS person_id
        , FVF.EncounterKey AS encounter_id
        , FVF.TakenByEmployeeDurableKey AS employee_id
        , FVF.TakenInstant AS assessment_date
        , FVF.Accepted AS accepted_flg
        , FVF.Value AS yes_no
        , CASE
            WHEN FRD.Name = N'R WISH TO BE DEAD' THEN 'passive_ideation'
            WHEN FRD.Name = N'R SUICIDAL THOUGHTS' THEN 'active_ideation'
            WHEN FRD.Name = N'R SUICIDAL INTENT (WITHOUT SPECIFIC PLAN)' THEN 'ideation_with_intent'
            WHEN FRD.Name = N'R SUICIDE INTENT WITH SPECIFIC PLAN' THEN 'ideation_with_plan'
            WHEN FRD.Name = N'R SUICIDAL THOUGHTS WITH METHOD (WITHOUT SPECIFIC PLAN OR INTENT TO ACT)' THEN 'ideation_with_method'
            WHEN FRD.Name = N'R SUICIDE BEHAVIOR QUESTION' THEN 'prior_suicidal_behavior'
        END AS question_orig
    FROM src.grady_person P
    INNER JOIN [CDW].[dbo].[FlowsheetValueFact] FVF ON P.DurableKey = FVF.PatientDurableKey
    INNER JOIN [CDW].[dbo].[FlowsheetTemplateDim] FTD ON FVF.FlowsheetTemplateKey = FTD.FlowsheetTemplateKey
    INNER JOIN [CDW].[dbo].[FlowsheetRowDim] FRD ON FVF.FlowsheetRowKey = FRD.FlowsheetRowKey
    WHERE FTD.Name = N'SUICIDE RISK SCREEN'
) source_table
PIVOT (
    MAX(yes_no)
    FOR question_orig IN (
        passive_ideation
        , active_ideation
        , ideation_with_intent
        , ideation_with_plan
        , ideation_with_method
        , prior_suicidal_behavior
    )
) AS pivoted_results
ORDER BY person_id, assessment_date
GO

/*
* Each row = One complete DLA-20 assessment for a patient
* 22 assessment columns (total_score, difference_from_last, + 20 domain scores)
* Scoring: 1-7 scale for individual domains, composite score for total
*/
IF OBJECT_ID('src.grady_dla20') IS NOT NULL
    DROP TABLE src.grady_dla20;
GO

CREATE TABLE src.grady_dla20 (
    person_id BIGINT
    , encounter_id BIGINT
    , employee_id BIGINT
    , assessment_date DATETIME
    , accepted_flg TINYINT
    , total_score NUMERIC(5, 2) -- total score per 'R DLA-20 TOTAL SCORE' field
    , difference_from_last NUMERIC(5, 2)
    -- 20 domain scores, each on a 1-7 scale
    , family_relationships NUMERIC(3, 2)
    , problem_solving NUMERIC(3, 2)
    , nutrition NUMERIC(3, 2)
    , managing_money NUMERIC(3, 2)
    , managing_time NUMERIC(3, 2)
    , safety NUMERIC(3, 2)
    , communication NUMERIC(3, 2)
    , dress NUMERIC(3, 2)
    , housing_stability NUMERIC(3, 2)
    , grooming NUMERIC(3, 2)
    , personal_hygiene NUMERIC(3, 2)
    , behavior_norms NUMERIC(3, 2)
    , coping_skills NUMERIC(3, 2)
    , productivity NUMERIC(3, 2)
    , sexuality NUMERIC(3, 2)
    , social_network NUMERIC(3, 2)
    , community_resources NUMERIC(3, 2)
    , leisure NUMERIC(3, 2)
    , alcohol_drug_use NUMERIC(3, 2)
    , health_practices NUMERIC(3, 2)
)
PRINT 'Table src.grady_dla20 created.'
GO

INSERT INTO src.grady_dla20
SELECT
    person_id
    , encounter_id
    , employee_id
    , assessment_date
    , accepted_flg
    , total_score
    , difference_from_last
    , family_relationships
    , problem_solving
    , nutrition
    , managing_money
    , managing_time
    , safety
    , communication
    , dress
    , housing_stability
    , grooming
    , personal_hygiene
    , behavior_norms
    , coping_skills
    , productivity
    , sexuality
    , social_network
    , community_resources
    , leisure
    , alcohol_drug_use
    , health_practices
FROM (
    SELECT
        FVF.PatientDurableKey AS person_id
        , FVF.EncounterKey AS encounter_id
        , FVF.TakenByEmployeeDurableKey AS employee_id
        , FVF.TakenInstant AS assessment_date
        , FVF.Accepted AS accepted_flg
        , TRY_CAST(FVF.Value AS NUMERIC(5, 2)) AS score_value
        , CASE
            WHEN FRD.Name = N'R DLA-20 TOTAL SCORE' THEN 'total_score'
            WHEN FRD.Name = N'R DLA-20 DIFFERENCE FROM LAST VALUE' THEN 'difference_from_last'
            WHEN FRD.Name = N'R DLA-20 FAMILY RELATIONSHIPS' THEN 'family_relationships'
            WHEN FRD.Name = N'R DLA-20 PROBLEM SOLVING' THEN 'problem_solving'
            WHEN FRD.Name = N'R DLA-20 NUTRITION' THEN 'nutrition'
            WHEN FRD.Name = N'R DLA-20 MANAGING MONEY' THEN 'managing_money'
            WHEN FRD.Name = N'R DLA-20 MANAGING TIME' THEN 'managing_time'
            WHEN FRD.Name = N'R DLA-20 SAFETY' THEN 'safety'
            WHEN FRD.Name = N'R DLA-20 COMMUNICATION' THEN 'communication'
            WHEN FRD.Name = N'R DLA-20 DRESS' THEN 'dress'
            WHEN FRD.Name = N'R DLA-20 HOUSING STABILITY MAINTENANCE' THEN 'housing_stability'
            WHEN FRD.Name = N'R DLA-20 GROOMING' THEN 'grooming'
            WHEN FRD.Name = N'R DLA-20 PERSONAL HYGIENE' THEN 'personal_hygiene'
            WHEN FRD.Name = N'R DLA-20 BEHAVIOR NORMS' THEN 'behavior_norms'
            WHEN FRD.Name = N'R DLA-20 COPING SKILLS' THEN 'coping_skills'
            WHEN FRD.Name = N'R DLA-20 PRODUCTIVITY' THEN 'productivity'
            WHEN FRD.Name = N'R DLA-20 SEXUALITY' THEN 'sexuality'
            WHEN FRD.Name = N'R DLA-20 SOCIAL NETWORK' THEN 'social_network'
            WHEN FRD.Name = N'R DLA-20 COMMUNITY RESOURCES' THEN 'community_resources'
            WHEN FRD.Name = N'R DLA-20 LEISURE' THEN 'leisure'
            WHEN FRD.Name = N'R DLA-20  ALCOHOL/ DRUG USE' THEN 'alcohol_drug_use'
            WHEN FRD.Name = N'R DLA-20 HEALTH PRACTICES' THEN 'health_practices'
        END AS question_orig
    FROM src.grady_person P
    INNER JOIN [CDW].[dbo].[FlowsheetValueFact] FVF ON P.DurableKey = FVF.PatientDurableKey
    INNER JOIN [CDW].[dbo].[FlowsheetTemplateDim] FTD ON FVF.FlowsheetTemplateKey = FTD.FlowsheetTemplateKey
    INNER JOIN [CDW].[dbo].[FlowsheetRowDim] FRD ON FVF.FlowsheetRowKey = FRD.FlowsheetRowKey
    WHERE FTD.Name = N'T DAILY LIVING ASSESSMENT (DLA-20)'
) source_table
PIVOT (
    MAX(score_value)
    FOR question_orig IN (
        total_score
        , difference_from_last
        , family_relationships
        , problem_solving
        , nutrition
        , managing_money
        , managing_time
        , safety
        , communication
        , dress
        , housing_stability
        , grooming
        , personal_hygiene
        , behavior_norms
        , coping_skills
        , productivity
        , sexuality
        , social_network
        , community_resources
        , leisure
        , alcohol_drug_use
        , health_practices
    )
) AS pivoted_results
GO

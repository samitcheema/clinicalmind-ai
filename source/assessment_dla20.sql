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

IF OBJECT_ID('src.cssrs') IS NOT NULL
    DROP TABLE src.cssrs;
GO

CREATE TABLE src.cssrs (
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
PRINT 'Table src.cssrs created.'
GO

IF OBJECT_ID('src.pain_assessment') IS NOT NULL
    DROP TABLE src.pain_assessment;
GO

CREATE TABLE src.pain_assessment (
    su_id BIGINT
    , encounter_id BIGINT
    , staff_id BIGINT
    , assessment_date DATETIME
    , accepted_flg TINYINT
    , pain_score NUMERIC(4, 2)
    , pain_source_value NVARCHAR(255)
)
PRINT 'Table src.pain_assessment created.'
GO

IF OBJECT_ID('src.gad7') IS NOT NULL
    DROP TABLE src.gad7;
GO

-- factors scored between 1.00 and 3.00
CREATE TABLE src.gad7 (
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
PRINT 'Table src.gad7 created.'
GO

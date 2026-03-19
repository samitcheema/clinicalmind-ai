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

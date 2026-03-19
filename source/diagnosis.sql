IF OBJECT_ID('src.grady_diagnosis') IS NOT NULL
    DROP TABLE src.grady_diagnosis;
GO

CREATE TABLE src.grady_diagnosis (
    person_id BIGINT
    , diagnosis_key BIGINT
    , encounter_id BIGINT
    , diag_start_date DATE
    , diag_end_date DATE
    , diagnosis_code_type NVARCHAR(300)
    , diagnosis_code NVARCHAR(300)
    , diagnosis_desc NVARCHAR(850)
    , diagnosis_type NVARCHAR(350)
)
PRINT 'Table src.grady_diagnosis created.'
GO

ALTER TABLE src.grady_diagnosis
ADD Category VARCHAR(150)
GO

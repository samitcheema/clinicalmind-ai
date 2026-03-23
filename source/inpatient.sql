IF OBJECT_ID('src.inpatient') IS NOT NULL
    DROP TABLE src.inpatient
GO

CREATE TABLE src.inpatient (
    encounter_id    BIGINT
    , person_id     BIGINT
    , ward          NVARCHAR(300)
    , ward_specialty NVARCHAR(300)
    , out_of_area   BIT
    , start_date    DATE
    , end_date      DATE
);
PRINT 'Table src.inpatient created.'
GO

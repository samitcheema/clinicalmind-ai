IF OBJECT_ID('src.allergies') IS NOT NULL
    DROP TABLE src.allergies;
GO

CREATE TABLE src.allergies (
    su_id BIGINT NOT NULL
    , allergy_id BIGINT NOT NULL
    , allergy_name NVARCHAR(255)
    , StartDateKey BIGINT
    , StartDate DATE
    , EndDateKey BIGINT
    , EndDate DATE
    , Severity NVARCHAR(50)
    , Status NVARCHAR(50)
    , allergy_type NVARCHAR(100)
    , unknown_allergies BIT
);
PRINT 'Table src.allergies created.'
GO

CREATE INDEX IX_allergies_su_id_allergy_id ON src.allergies (su_id, allergy_id);

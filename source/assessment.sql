IF OBJECT_ID('src.assessment') IS NOT NULL
    DROP TABLE src.assessment;
GO

CREATE TABLE src.assessment (
    EncounterKey BIGINT
    , PatientDurableKey BIGINT
    , DurableKey BIGINT
    , FTDName NVARCHAR(200)
    , DateValue DATE
    , FRDName NVARCHAR(300)
    , Value NVARCHAR(2500)
)
PRINT 'Table src.assessment created.'
GO

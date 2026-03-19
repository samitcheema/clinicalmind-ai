IF OBJECT_ID('src.grady_assessment') IS NOT NULL
    DROP TABLE src.grady_assessment;
GO

CREATE TABLE src.grady_assessment (
    EncounterKey BIGINT
    , PatientDurableKey BIGINT
    , DurableKey BIGINT
    , FTDName NVARCHAR(200)
    , DateValue DATE
    , FRDName NVARCHAR(300)
    , Value NVARCHAR(2500)
)
PRINT 'Table src.grady_assessment created.'
GO

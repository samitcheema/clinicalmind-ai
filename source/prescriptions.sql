IF OBJECT_ID('src.prescriptions') IS NOT NULL
    DROP TABLE src.prescriptions;
GO

CREATE TABLE src.prescriptions (
    su_id BIGINT
    , drug_id BIGINT
    , name NVARCHAR(255)
    , days_supply NUMERIC(18, 2)
    , refills_remaining SMALLINT
    , dosage NVARCHAR(4000)
    , drug_route NVARCHAR(255)
    , drug_class NVARCHAR(255)
    , start_date DATE
    , end_date DATE
    , ordered_date DATE
    , prescribing_provider_name NVARCHAR(255)
);
PRINT 'Table src.prescriptions created.'
GO

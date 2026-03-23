IF OBJECT_ID('src.drug') IS NOT NULL
    DROP TABLE src.drug;
GO

CREATE TABLE src.drug (
    person_id   BIGINT           -- patient id; will be NULL for drugs that don't appear in patient records
    , drug_id   BIGINT           -- drug id
    , drug_name NVARCHAR(255)    -- drug name
    , start_date DATE            -- aggregated start date (NULL for master rows)
    , end_date   DATE            -- aggregated end date (NULL for master rows)
);
PRINT 'Table src.drug created.';
GO

/*
This table maps drugs/medications to their associated HCPCS billing procedure codes and descriptions.
*/
IF OBJECT_ID('src.drug_procedure_mapping') IS NOT NULL
    DROP TABLE src.drug_procedure_mapping;
GO

CREATE TABLE src.drug_procedure_mapping (
    drug_id BIGINT
    , procedure_code NVARCHAR(255)
    , procedure_description NVARCHAR(500)
);
PRINT 'Table src.drug_procedure_mapping created.'
GO

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

INSERT INTO src.drug_procedure_mapping (
    drug_id
    , procedure_code
    , procedure_description
)
SELECT DISTINCT
    MCD.MedicationKey AS drug_id
    , BTP.BillingProcedureCode AS procedure_code
    , BTP.BillingProcedureDescription AS procedure_description
FROM [CDW].[dbo].[BillingTransactionFact] BTP
INNER JOIN [CDW].[dbo].[BillingTransactionMedicationMappingFact] BMMF ON BTP.BillingTransactionKey = BMMF.BillingTransactionKey
INNER JOIN [CDW].[dbo].[MedicationCodeDim] MCD ON BMMF.MedicationCodeKey = MCD.MedicationCodeKey
WHERE BTP.BillingProcedureCode LIKE 'J%'    -- HCPCS codes used to identify non-oral medications and services, particularly those administered by injection or infusion
GO

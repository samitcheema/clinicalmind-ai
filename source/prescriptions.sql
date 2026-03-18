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


INSERT INTO src.prescriptions (
    su_id						-- patient id
    , drug_id					-- drug id
    , name						-- order name (usually corresponds to drug name but not always)
    , days_supply				-- days supply provided to medication order
    , refills_remaining			-- refills prescribed to order
    , dosage					-- medication dosage
    , drug_route				-- The method by which drug was administered i.e. Inhalation, Injection etc.
    , drug_class                -- Class of drug, i.e. Antipsychotic, Calcium blocker etc.
    , start_date				-- drug start date
    , end_date					-- drug end date
    , ordered_date				-- drug order date
    , prescribing_provider_name -- prescribing provider name
)

SELECT DISTINCT
    P.DurableKey AS su_id
    , MOF.MedicationKey AS drug_id
    , MOF.OrderName AS name
    , MOF.DaysSupply AS days_supply
    , MOF.RefillsRemaining AS refills_remaining
    , MOF.SIG AS dosage
    , MEF.Route AS drug_route
    , MD.PharmaceuticalClass AS drug_class
    , CAST(STARTDT.DateValue AS DATE) AS start_date
    , CAST(ENDDT.DateValue AS DATE) AS end_date
    , CAST(ORDERDT.DateValue AS DATE) AS ordered_date
    , PD.Name AS prescribing_provider_name
FROM src.grady_person P
INNER JOIN [CDW].[dbo].[MedicationOrderFact] MOF ON P.DurableKey = MOF.PatientDurableKey
INNER JOIN [CDW].[dbo].[MedicationEventFact] MEF ON MOF.MedicationOrderKey = MEF.MedicationOrderKey
INNER JOIN [CDW].[dbo].[MedicationDim] MD ON MEF.MedicationKey = MD.MedicationKey
INNER JOIN [CDW].[dbo].[ProviderDim] PD ON MEF.PrescribingProviderKey = PD.ProviderKey
INNER JOIN [CDW].[dbo].[DateDim] ORDERDT ON MOF.OrderedDateKey = ORDERDT.DateKey
INNER JOIN [CDW].[dbo].[DateDim] STARTDT ON MOF.StartDateKey = STARTDT.DateKey
INNER JOIN [CDW].[dbo].[DateDim] ENDDT ON MOF.EndDateKey = ENDDT.DateKey
WHERE
    STARTDT.DateValue IS NOT NULL
    AND (STARTDT.DateValue <= ENDDT.DateValue OR ENDDT.DateValue IS NULL)
GO

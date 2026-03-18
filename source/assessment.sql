-- Create temp table of template names to avoid repeated LIKE pattern matching operations
-- This improves performance by storing filtered results in temp table instead of scanning full FlowsheetTemplateDim multiple times
SELECT DISTINCT
    FlowsheetTemplateKey
    , Name
INTO #template_names
FROM [CDW].[dbo].[FlowsheetTemplateDim]
WHERE
    Name LIKE N'%BH ADMISSION ASSESSMENT%'
    OR Name LIKE N'%IP BEHAVIORAL HEALTH ASSESSMENT%'
    ----- PHQ-9
    OR Name LIKE N'%AMB PHQ 2 DEPRESSION SCALE%'
    OR Name LIKE N'%AMB PHQ 9 DEPRESSION SCALE%'
    OR Name LIKE N'%GHS PHQ9%'
    OR Name LIKE N'%GHS PHQ-9%'
    ----- Suicide Risk Assessment  
    OR Name LIKE N'%BH SUICIDE RISK SCREEN%'
    OR Name LIKE N'%GHS ED SUICIDE NAV%'
    OR Name LIKE N'%SUICIDE RISK NAV%'
    OR Name LIKE N'%SUICIDE RISK SCREEN%'
    OR Name LIKE N'%T BH COLUMBIA-SUICIDE SEVERITY RATING SCALE (CSSRS) SINCE LAST VISIT%'
    OR Name LIKE N'%SUICIDE RISK ASSESSMENT%'
    ----- AIMS
    OR Name LIKE N'BH ABNORMAL INVOLUNTARY MOVEMENTS SCALE (AIMS)'
    OR Name LIKE N'T AMB PSYCH AIMS'
    ----- WHODAS
    OR Name LIKE N'%T BEH AMB WHODAS ASSESSMENT%'
    ----- DLA-20
    OR Name LIKE N'%T DAILY LIVING ASSESSMENT (DLA-20)%'
GO

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

INSERT INTO src.grady_assessment
SELECT DISTINCT
    FVF.EncounterKey
    , FVF.PatientDurableKey
    , P.DurableKey
    , TN.Name AS FTDName
    , D.DateValue
    , FRD.Name AS FRDName
    , FVF.Value
FROM [CDW].[dbo].[FlowsheetValueFact] FVF
INNER JOIN #template_names TN ON FVF.FlowsheetTemplateKey = TN.FlowsheetTemplateKey
INNER JOIN [CDW].[dbo].[FlowsheetRowDim] FRD ON FVF.FlowsheetRowKey = FRD.FlowsheetRowKey
INNER JOIN [CDW].[dbo].[DateDim] D ON FVF.DateKey = D.DateKey
INNER JOIN [CDW].[dbo].[EmployeeDim] E ON FVF.TakenByEmployeeDurableKey = E.DurableKey
INNER JOIN [CDW].[dbo].[ProviderDim] P ON E.EmployeeEpicId = P.EmployeeEpicId
WHERE
    FVF.EncounterKey IN (SELECT encounter_id FROM src.grady_encounter)
GO

DROP TABLE #template_names
GO

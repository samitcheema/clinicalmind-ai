IF OBJECT_ID('src.grady_providers') IS NOT NULL
    DROP TABLE src.grady_providers;
GO

CREATE TABLE src.grady_providers (
    provider_id BIGINT
    , provider_npi NVARCHAR(50)
    , provider_type NVARCHAR(100)
    , clinician_title NVARCHAR(100)
    , provider_name NVARCHAR(255)
    , role_category NVARCHAR(255)
    , email NVARCHAR(2550)
    , can_authorize_medication BIT
);
PRINT 'Table src.providers created.';
GO

INSERT INTO src.grady_providers (
    provider_id
    , provider_npi
    , provider_type
    , clinician_title
    , provider_name
    , role_category
    , email
    , can_authorize_medication
)
SELECT DISTINCT
    PD.DurableKey AS provider_id
    , PD.npi AS provider_npi
    , PD.Type AS provider_type
    , PD.ClinicianTitle AS clinician_title
    , PD.Name AS provider_name
    , PD.PrimarySpecialty AS role_category
    , PD.email
    , PD.ismedicationauthorizingprovider AS can_authorize_medication
FROM [CDW].[dbo].[ProviderDim] PD
INNER JOIN src.grady_encounter E ON PD.DurableKey = E.provider_id
WHERE
    PD.IsCurrent = 1
    AND PD.DurableKey NOT IN (-1, -2, -3)   -- Remove Unspecified, Not Applicable and Deleted keys
GO

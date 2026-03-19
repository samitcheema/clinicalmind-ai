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

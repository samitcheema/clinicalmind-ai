IF Object_Id('src.person') IS NOT NULL
    DROP TABLE src.person
GO

CREATE TABLE src.person (
    person_id                    BIGINT
    , start_date                 DATE
    , death_date                 DATE
    , gender_identity            NVARCHAR(156)
    , sex                        NVARCHAR(156)
    , sex_assigned_at_birth      NVARCHAR(156)
    , ethnicity                  NVARCHAR(300)
    , primary_care_provider_id   BIGINT
    , first_name                 NVARCHAR(200)
    , last_name                  NVARCHAR(300)
    , birth_date                 DATE
    , primary_mrn                NVARCHAR(150)
    , postal_code                NVARCHAR(100)
    , first_race                 NVARCHAR(255)
    , marital_status             NVARCHAR(300)
);
PRINT 'Table src.person created.'
GO

CREATE INDEX IX_person_person_id
    ON src.person (person_id);
GO

IF Object_Id('src.person') IS NOT NULL
    DROP TABLE src.person
GO

CREATE TABLE src.person (
    DurableKey BIGINT
    , StartDate DATE
    , DeathDate DATE
    , GenderIdentity NVARCHAR(156)
    , Sex NVARCHAR(156)
    , SexAssignedAtBirth NVARCHAR(156)
    , Ethnicity NVARCHAR(300)
    , PrimaryCareProviderDurableKey BIGINT
    , FirstName NVARCHAR(200)
    , LastName NVARCHAR(300)
    , BirthDate DATE
    , PrimaryMRN NVARCHAR(150)
    , PostalCode NVARCHAR(100)
    , FirstRace NVARCHAR(255)
    , MaritalStatus NVARCHAR(300)
);
PRINT 'Table src.person created.'
GO

CREATE INDEX IX_person_durablekey
    ON src.person (DurableKey);
GO

IF Object_Id('src.grady_person') IS NOT NULL
    DROP TABLE src.grady_person
GO

CREATE TABLE src.grady_person (
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
PRINT 'Table src.grady_person created.'
GO

CREATE INDEX IX_grady_person_durablekey
    ON src.grady_person (DurableKey);
GO

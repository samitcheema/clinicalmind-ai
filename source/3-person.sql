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

INSERT INTO [src].grady_person (
    DurableKey
    , StartDate
    , DeathDate
    , GenderIdentity
    , Sex
    , SexAssignedAtBirth
    , Ethnicity
    , PrimaryCareProviderDurableKey
    , FirstName
    , LastName
    , BirthDate
    , PrimaryMRN
    , PostalCode
    , FirstRace
    , MaritalStatus
)
SELECT
    Person.DurableKey
    , Person.StartDate
    , Person.DeathDate
    , Person.GenderIdentity
    , Person.Sex
    , Person.SexAssignedAtBirth
    , Person.Ethnicity
    , Person.PrimaryCareProviderDurableKey
    , Person.FirstName
    , Person.LastName
    , Person.BirthDate
    , Person.PrimaryMRN
    , Person.PostalCode
    , Person.FirstRace
    , Person.MaritalStatus
FROM [CDW].[dbo].[PatientDim] Person
WHERE
    LEN(Person.PrimaryMrn) <= 10
    AND Person.[IsValid] = 1 AND Person.IsCurrent = 1
    AND EXISTS (    -- This makes sure patient has had an encounter within our departments of interest
        SELECT 1
        FROM src.grady_encounter E
        WHERE E.person_id = Person.DurableKey
    )
GO

CREATE INDEX IX_grady_person_durablekey
    ON src.grady_person (DurableKey);
GO

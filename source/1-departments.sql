IF OBJECT_ID('src.departments_of_interest') IS NOT NULL
    DROP TABLE src.departments_of_interest;
GO

CREATE TABLE src.departments_of_interest (
    department_name NVARCHAR(255) NOT NULL PRIMARY KEY
    , is_inpatient BIT NOT NULL
    , is_outpatient BIT NOT NULL
    , is_crisis_department BIT NOT NULL
);
GO

INSERT INTO src.departments_of_interest (department_name, is_inpatient, is_outpatient, is_crisis_department)
VALUES
-- inpatient / crisis
(N'GHS 13A', 1, 0, 1)
, (N'GHS 13B', 1, 0, 1)
, (N'GHS 13CD', 1, 0, 1)
, (N'GHS EMERGENCY', 0, 0, 1)   -- Psychiatric Emergency Services (PES) patients only.

-- outpatient
, (N'ASA YANCEY PSYCH', 0, 1, 0)
, (N'GHS BH NORTH', 0, 1, 0)
, (N'GHS BH SOUTH', 0, 1, 0)
, (N'BROOKHAVEN PSYCH', 0, 1, 0)
, (N'CAMP CREEK PSYCH', 0, 1, 0)
, (N'EAST POINT PSYCH', 0, 1, 0)
, (N'KIRKWOOD PSYCH', 0, 1, 0)
, (N'NORTH FULTON PSYCH', 0, 1, 0)
, (N'GHS PSYCH ADULT OP', 0, 1, 0)
, (N'GHS ACT', 0, 1, 0)
, (N'GHS BH CASE MGMT', 0, 1, 0)
, (N'PONCE DE LEON CWB', 0, 1, 0)
, (N'PCC 1J PSYCH', 0, 1, 0)
, (N'PCC 1K PSYCH', 0, 1, 0)
, (N'PCC 1L PSYCH', 0, 1, 0)
, (N'PCC LK PSYCH', 0, 1, 0)
, (N'ZZ PSYCHIATRY', 0, 1, 0)
, (N'GHS BH PRIMARY CARE CL', 0, 1, 0)
GO

IF OBJECT_ID('src.grady_departments') IS NOT NULL
    DROP TABLE src.grady_departments;
GO

CREATE TABLE src.grady_departments (
    department_key BIGINT
    , department_name NVARCHAR(255)
    , location_name NVARCHAR(255)
    , county NVARCHAR(255)
    , city NVARCHAR(255)
    , type NVARCHAR(255)
    , is_inpatient BIT
    , is_outpatient BIT
    , is_crisis_department BIT
);
GO

INSERT INTO src.grady_departments (
    department_key
    , department_name
    , location_name
    , county
    , city
    , type
    , is_inpatient
    , is_outpatient
    , is_crisis_department
)
SELECT DISTINCT
    D.DepartmentKey
    , LTRIM(RTRIM(D.DepartmentName)) AS department_name
    , D.LocationName
    , D.County
    , D.City
    , D.Type
    , DOI.is_inpatient
    , DOI.is_outpatient
    , DOI.is_crisis_department
FROM [CDW].[dbo].[DepartmentDim] D
INNER JOIN src.departments_of_interest DOI ON LTRIM(RTRIM(D.DepartmentName)) = DOI.department_name
WHERE
    EXISTS (
        SELECT 1
        FROM [CDW].[dbo].[EncounterFact] E
        WHERE E.DepartmentKey = D.DepartmentKey
    )
    AND (
    -- retrieve only Park Place location for GHS PSYCH ADULT OP
        (DOI.department_name = N'GHS PSYCH ADULT OP' AND D.Address LIKE N'%Park Place%')
        OR DOI.department_name != N'GHS PSYCH ADULT OP'
    )
GO

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
(N'Behavioral Health Inpatient Unit A', 1, 0, 1)
, (N'Behavioral Health Inpatient Unit B', 1, 0, 1)
, (N'Behavioral Health Inpatient Unit C', 1, 0, 1)
, (N'Psychiatric Emergency Unit', 0, 0, 1)          -- PES patients only (suicidal chief complaint or BH diagnosis in ED)

-- outpatient
, (N'Midtown Behavioral Health', 0, 1, 0)
, (N'Outpatient Psychiatry - North Campus', 0, 1, 0)
, (N'Outpatient Psychiatry - South Campus', 0, 1, 0)
, (N'Outpatient Psychiatry - East Campus', 0, 1, 0)
, (N'Outpatient Psychiatry - West Campus', 0, 1, 0)
, (N'Westside Recovery Clinic', 0, 1, 0)
, (N'Eastside Behavioral Health Clinic', 0, 1, 0)
, (N'Northside Behavioral Health Clinic', 0, 1, 0)
, (N'Adult Outpatient Psychiatry', 0, 1, 0)
, (N'Assertive Community Treatment (ACT)', 0, 1, 0)
, (N'Behavioral Health Case Management', 0, 1, 0)
, (N'Community Support Team (CST)', 0, 1, 0)
, (N'CORE Services', 0, 1, 0)
, (N'Integrated Care Team', 0, 1, 0)
, (N'Community Care Management', 0, 1, 0)
, (N'Mobile Crisis Response', 0, 1, 0)
, (N'Behavioral Health Primary Care Integration', 0, 1, 0)
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

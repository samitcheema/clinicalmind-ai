-- This table contains a mapping for form elements and to the safety plan they link to
-- Each element is linked to a field on the specified safety plan form
IF OBJECT_ID('src.grady_safety_plan_mapping') IS NOT NULL
    DROP TABLE src.grady_safety_plan_mapping;
GO

CREATE TABLE src.grady_safety_plan_mapping (
    smart_data_element_epic_id NVARCHAR(50) NOT NULL PRIMARY KEY
    , plan_name VARCHAR(300) NOT NULL
);
PRINT 'Table src.grady_safety_plan_mapping created.'
GO

INSERT INTO src.grady_safety_plan_mapping (smart_data_element_epic_id, plan_name)
VALUES
('GHS#4874', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('GHS#4875', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('GHS#4763', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('GHS#4764', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('EPIC#31000169338', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('EPIC#31000169339', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('EPIC#31000169363', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('EPIC#31000169364', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('EPIC#31000169343', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('EPIC#31000169344', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('EPIC#31000204859', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('EPIC#31000188307', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('EPIC#31000188308', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('EPIC#31000188309', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('EPIC#31000204860', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('EPIC#31000188310', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('GHS#4684', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('GHS#4685', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('GHS#4686', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('GHS#4682', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('GHS#4687', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('GHS#4688', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('GHS#4689', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('EPIC#31000204861', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('EPIC#31000188315', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('EPIC#31000237024', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('EPIC#31000237021', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('EPIC#31000237022', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('EPIC#31000237023', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('GHS#4690', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('GHS#4691', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('GHS#4692', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('GHS#4693', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('EPIC#31000211455', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('EPIC#31000169361', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('EPIC#31000169362', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('GHS#4683', 'BH AMB STANELY BROWN SAFETY PLAN')
, ('GHS#4694', 'BH AMB STANELY BROWN SAFETY PLAN')
GO

/*
Table contains Crisis Safety Plan data for NBH patients

This table captures crisis safety plan information by linking patient attribute values to their corresponding safety plan.
It tracks details about the input fields (name, abbreviation, data type), the plan name, and when the plan was completed.
There is no attribution to encounters, so it does not require a join to the encounters table
*/
IF OBJECT_ID('src.grady_crisis_safety_plan') IS NOT NULL
    DROP TABLE src.grady_crisis_safety_plan;
GO

CREATE TABLE src.grady_crisis_safety_plan (
    person_id BIGINT  -- Patient for whom the crisis safety plan record was created
    , attribute_id BIGINT -- Identifier for the attribute associated with the crisis safety plan
    , smart_data_element_epic_id NVARCHAR(50) -- EPIC identifier linking the attribute to the safety plan mapping
    , plan_name NVARCHAR(300) -- Name of the crisis safety plan as defined in the mapping table
    , input_name NVARCHAR(300) -- Name of the input field from the attribute data
    , input_abbreviation NVARCHAR(300) -- Abbreviation of the input field
    , data_type NVARCHAR(300) -- Data type of the input field (e.g., string, numeric, date)
    , completion_date DATE -- Date when the crisis safety plan element was completed
    , input_value NVARCHAR(300) -- Textual input value captured for the attribute
    , input_numeric_value NUMERIC(18, 2) -- Numeric input value captured for the attribute
    , input_date_value DATE -- Date input value captured for the attribute
);
PRINT 'Table src.grady_crisis_safety_plan created.';
GO

INSERT INTO src.grady_crisis_safety_plan (
    person_id
    , attribute_id
    , smart_data_element_epic_id
    , plan_name
    , input_name
    , input_abbreviation
    , data_type
    , completion_date
    , input_value
    , input_numeric_value
    , input_date_value
)
SELECT
    PPAV.PatientDurableKey AS person_id
    , PPAV.AttributeKey AS attribute_id
    , AD.SmartDataElementEpicId AS smart_data_element_epic_id
    , SPM.plan_name
    , AD.Name AS input_name
    , AD.Abbreviation AS input_abbreviation
    , AD.DataType AS data_type
    , COMPLETIONDT.DateValue AS completion_date
    , PPAV.Value AS input_value
    , PPAV.NumericValue AS input_numeric_value
    , PPAV.DateValue AS input_date_value
FROM src.grady_person P
INNER JOIN [CDW].[dbo].PatientAttributeValueDim PPAV ON P.DurableKey = PPAV.PatientDurableKey
INNER JOIN [CDW].[dbo].AttributeDim AD ON PPAV.AttributeKey = AD.AttributeKey
INNER JOIN [CDW].[dbo].DateDim COMPLETIONDT ON PPAV.DateKey = COMPLETIONDT.DateKey
INNER JOIN src.grady_safety_plan_mapping SPM ON AD.SmartDataElementEpicId = SPM.smart_data_element_epic_id;
GO

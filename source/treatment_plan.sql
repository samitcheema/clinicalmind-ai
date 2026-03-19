/*
Table contains Treatment Plan data for NBH patients

Difference between Plan of Care and Treatment Plan(Will update once verifying actual meaning):
- Plan of Care is the whole plan which includes treatments
- Treatment Plan refers to a specific treatment within a Plan of Care
*/
IF Object_Id('src.grady_treatment_plan') IS NOT NULL
    DROP TABLE src.grady_treatment_plan
GO

CREATE TABLE src.grady_treatment_plan (
    bh_treatment_plan_id BIGINT -- Uniquely identify treatment plan record
    , plan_of_care_id BIGINT -- Plan of Care record ID
    , encounter_id BIGINT   -- Encounter in which treatment plan was completed
    , person_id BIGINT  -- Patient for whom treatment plan was created
    , provider_id BIGINT    -- Provider who completed treatment plan
    , plan_of_care_name NVARCHAR(255) -- Name associated with treatment plan
    , treatment_plan_date DATE  -- Date when plan of care was completed
    , next_treatment_plan_date DATE -- Date of the next treatment plan visit
    , plan_of_care_status NVARCHAR(255) -- Plan of Care status
);
PRINT 'Table src.grady_treatment_plan created.'
GO

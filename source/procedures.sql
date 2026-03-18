-- NOTE: There can be orders that are not in the events table and events that are not in the orders table.
-- This captures procedures that were ordered but may not have been performed yet
WITH procedure_orders AS (
    SELECT DISTINCT
        E.encounter_id
        , E.person_id
        , POF.ProcedureDurableKey AS procedure_durable_key
        , POF.originalOrderProviderDurableKey AS order_provider_durable_key
        , POF.OrderedDateKey AS date_key
        , NULL AS end_date_key  -- Orders don't have end dates
        , PD.Code AS procedure_code
        , 'Order' AS procedure_status
    FROM src.grady_encounter E
    INNER JOIN CDW.dbo.ProcedureOrderFact POF ON E.encounter_id = POF.EncounterKey
    INNER JOIN CDW.dbo.ProcedureDim PD ON POF.ProcedureKey = PD.ProcedureKey
)

-- This captures procedures that were actually performed
, procedure_events AS (
    SELECT DISTINCT
        E.encounter_id
        , E.person_id
        , PEF.ProcedureDurableKey AS procedure_durable_key
        , NULL AS order_provider_durable_key  -- Events don't track the ordering provider
        , PEF.ProcedureStartDateKey AS date_key
        , PEF.ProcedureEndDateKey AS end_date_key
        , PEF.ProcedureCode AS procedure_code
        , 'Event' AS procedure_status
    FROM src.grady_encounter E
    INNER JOIN CDW.dbo.ProcedureEventFact PEF ON E.encounter_id = PEF.EncounterKey
)

-- Combine order and event data into a single dataset
, combined_procedures AS (
    SELECT *
    FROM procedure_orders
    UNION ALL
    SELECT *
    FROM procedure_events
)

-- Create temp table to store encounter-procedure relation and index to optimize final query
SELECT *
INTO #encounter_procedures
FROM combined_procedures

CREATE CLUSTERED INDEX IX_encounter_procedures
    ON #encounter_procedures (procedure_durable_key, date_key)
GO

IF OBJECT_ID('src.grady_procedures') IS NOT NULL
    DROP TABLE src.grady_procedures
GO

CREATE TABLE src.grady_procedures (
    person_id BIGINT                        -- Person identifier
    , encounter_id BIGINT                   -- Encounter identifier associated with procedure
    , procedure_durable_key BIGINT          -- Procedure key identifier
    , order_provider_durable_key BIGINT     -- Provider key who ordered the procedure (NULL for events)
    , procedure_code NVARCHAR(50)           -- Standard procedure code (CPT, HCPCS etc.)
    , template_description NVARCHAR(500)    -- procedure description
    , procedure_status NVARCHAR(10)         -- Either 'Order' or 'Event'
    , ordered_date DATE                     -- Date when procedure was ordered (NULL for events)
    , event_start_date DATE                 -- Date when procedure was started (NULL for orders)
    , event_end_date DATE                   -- Date when procedure was completed (NULL for orders)
)
GO

INSERT INTO src.grady_procedures (
    person_id
    , encounter_id
    , procedure_durable_key
    , order_provider_durable_key
    , procedure_code
    , template_description
    , procedure_status
    , ordered_date
    , event_start_date
    , event_end_date
)
SELECT DISTINCT
    ep.person_id
    , ep.encounter_id
    , ep.procedure_durable_key
    , ep.order_provider_durable_key
    , PD.Code AS procedure_code
    , PD.Name AS template_description
    , ep.procedure_status
    -- Date handling:
    -- For orders, set ordered_date and leave event dates NULL
    -- For events, set event dates and leave ordered_date NULL
    , CASE WHEN ep.procedure_status = 'Order' THEN DD.DateValue ELSE NULL END AS ordered_date
    , CASE WHEN ep.procedure_status = 'Event' THEN DD.DateValue ELSE NULL END AS event_start_date
    , CASE WHEN ep.procedure_status = 'Event' THEN ENDDT.DateValue ELSE NULL END AS event_end_date
FROM #encounter_procedures ep
INNER JOIN CDW.dbo.ProcedureDim PD ON ep.procedure_durable_key = PD.ProcedureKey
INNER JOIN CDW.dbo.DateDim DD ON ep.date_key = DD.DateKey
LEFT JOIN CDW.dbo.DateDim ENDDT ON ep.end_date_key = ENDDT.DateKey

CREATE NONCLUSTERED INDEX IX_grady_procedures
    ON src.grady_procedures (procedure_durable_key)
    INCLUDE (ordered_date, event_start_date, event_end_date, procedure_code, procedure_status)
GO

DROP TABLE #encounter_procedures
GO

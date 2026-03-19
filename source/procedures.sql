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

CREATE NONCLUSTERED INDEX IX_grady_procedures
    ON src.grady_procedures (procedure_durable_key)
    INCLUDE (ordered_date, event_start_date, event_end_date, procedure_code, procedure_status)
GO

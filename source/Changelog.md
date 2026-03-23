# Source Schema Changelog

## 2026-03-23

### Unused table removal

Removed 5 tables with no BH clinical use case or KPI association from `source/`, `supabase_schema.sql`, and `ensure_schema.py`:

- **`src.zip_codes`** — county lookup table; county is available directly on `src.encounter.county`, this table was never joined anywhere.
- **`src.pain_assessment`** — pain scoring is an IM/primary care concern; no psychiatric BH KPI or tool uses it.
- **`src.drug_procedure_mapping`** — HCPCS billing code mapping for drugs; purely administrative, no clinical relevance to the BH dashboard.
- **`src.allergies`** — allergy tracking has no connection to any BH KPI, assessment, or MCP tool.
- **`src.assessment`** — generic EHR flowsheet catch-all; all clinical instruments have dedicated staging tables (phq9, gad7, cssrs, dla20).

### Column naming standardization

- **`src.person`** — all columns converted from PascalCase to snake_case; `DurableKey` → `person_id`, `PrimaryCareProviderDurableKey` → `primary_care_provider_id`.
- **`src.allergies`** — mixed-case columns standardized to snake_case; `su_id` → `person_id`, date key columns lowercased.
- **`src.ZipCodeList`** — table renamed to `src.zip_codes`; all columns lowercased.
- **`src.pain_assessment`** — `su_id` → `person_id`, `staff_id` → `employee_id`.
- **`src.drug`** — `su_id` → `person_id`, `name` → `drug_name`.
- **`src.prescriptions`** — `su_id` → `person_id`, `name` → `drug_name`.
- **`src.inpatient`** — `patient_id` → `person_id`.
- **`src.diagnosis`** — inlined `category` column into `CREATE TABLE`; removed trailing `ALTER TABLE ADD COLUMN`.
- **`src.gad7`** — added `accepted_flg` for consistency with other assessment tables.
- **`ensure_schema.py`** — aligned all `src.*` table definitions with the above; updated `_SRC_TABLES` RLS list.

## 2026-03-19

- Renamed source tables to neutral `src.*` names.
- Updated matching index names.
- Aligned standalone SQL schema files in `source/` with neutral table naming.
- Standardized source-table references for future synthetic data work under MindForge.

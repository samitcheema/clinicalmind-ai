# Revision history of Grady Source Tables

## 2025-06-03

- `grady_encounter` changes:
  - Added new column `appointment_date_time` to track appointment dates and times.

## 2025-05-29

- `grady_person` changes:
  - Added `Sex` column as a third option to deduce gender.

## 2025-04-04

- `grady_procedure` changes:
  - Adding columns related to procedure codes to `grady_procedure` for MIPS measurement calculation.
  - Pulling in procedure events along with procedure order.
  - Removed join to `ProcedureOrderTemplateDim` and instead utilize `ProcedureDim` to align with `ProcedureEventFact` table.

## 2025-04-01

- Refactor `grady_encounter`:
- Removal of join with `PatientDim`(derived from `grady_person`), `HospitalAdmissionFact`(EncounterFact already takes these into account based on the hospital departments we're tracking)
- Replacing `LEFT JOIN` with `INNER JOIN` (no orphaned records were found)
- Renaming CTEs to snake_case for conformity
- Added new source table to derive Provider information for future use
- Changed order of table creation to only pull in active patients into `grady_person`.
- Fixed some aliasing to be capitalized.

## 2025-03-26

- Adding columns `drug_class` and `drug_route` to prescriptions table for MIPS measurement calculations. Removing join with `grady_person` and replacing with `grady_encounter`

## 2025-03-19

- Adding `pos_key` and `pos_name` columns to `grady_encounter` table to derive Place of Service.

## 2025-03-14

- Adding `discharge_instant` column to `grady_encounter` table to signify discharge date and time component.

## 2025-03-12

- Remove `how_difficult` column from `assessment_phq9` as its not needed.

## 2025-03-04

- Introduce `is_crisis_department` flag to `src.grady_departments` to identify crisis managing departments.

## 2025-02-27

- Removed newly created `src.grady_drug_ra` and moving everything into a single master table. Prod ETL is having issues reading new table(Just a speculation).

## 2025-02-26

- Removing join to `drugs_of_interest` table from `src.grady_drug`
- Recreated `src.grady_drug` to only capture `drug_id` and `drug_name` for our current use case
- Generate separate source table `src.grady_drug_ra` for RA ingestion, containing patient medication data filtered on start date to a lookback period of 1 year.

## 2025-02-04

- Introduced new source table `src.treatment_plan` to derive additional treatment plan data for Grady patients. Added missing `OBJECT_ID` check on `src_treatment_plan`.

## 2025-01-30

- Introduced new column `prescribing_provider_name` to `prescriptions` table

## 2025-01-24

- Introduced new column `isCIS` to `encounter` table

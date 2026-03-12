"""
ClinicalMind AI — SQL Adapter (Phase 2 stub)

Replace this file to connect to the real SQL database.
Implements the same interface as mock_adapter.py — no server.py changes needed.

Expected schema tables:
  mast_processing.encounter
  mast_processing.assessment_phq9 / assessment_gad7 / assessment_whodas / assessment_ssrs
  mast_processing.contact
  mast_processing.crisis_event
  output.su          (KPI columns)
  output.su_staff    (provider assignments)

Usage:
  1. pip install pyodbc  (or asyncpg / pymysql / etc.)
  2. Set env vars: DB_SERVER, DB_DATABASE, DB_USER, DB_PASSWORD
  3. In server.py change:  from adapter.mock_adapter import ...
                       to: from adapter.sql_adapter  import ...

TODO: Implement each function by querying the appropriate tables.
      Return shapes must match mock_adapter.py exactly.
"""

# import os
# import pyodbc
#
# _conn = pyodbc.connect(
#     f"DRIVER={{ODBC Driver 18 for SQL Server}};"
#     f"SERVER={os.environ['DB_SERVER']};"
#     f"DATABASE={os.environ['DB_DATABASE']};"
#     f"UID={os.environ['DB_USER']};"
#     f"PWD={os.environ['DB_PASSWORD']};"
#     "Encrypt=yes;TrustServerCertificate=no;"
# )


def _not_implemented(fn: str):
    raise NotImplementedError(
        f"SQL adapter method '{fn}' is not yet implemented. "
        "See adapter/sql_adapter.py for the implementation guide."
    )


def get_patients(risk_level=None, county=None, provider=None):
    _not_implemented("get_patients")

def get_patient_detail(patient_id: str):
    _not_implemented("get_patient_detail")

def get_high_risk_patients(risk_type=None):
    _not_implemented("get_high_risk_patients")

def get_kpi_compliance(kpi_name=None):
    _not_implemented("get_kpi_compliance")

def get_overdue_assessments(assessment_type=None):
    _not_implemented("get_overdue_assessments")

def get_crisis_events(window_days=28):
    _not_implemented("get_crisis_events")

def get_disengaged_patients(threshold_days=30):
    _not_implemented("get_disengaged_patients")

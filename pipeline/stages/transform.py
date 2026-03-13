"""
Stage 2 — Transform

Convert raw FHIR R4 bundles into canonical patient dicts using the
two-path transform_fhir module:
  • _meta fast path  — bundles produced by generate_fhir.py
  • Full FHIR parse  — real Synthea output or any external FHIR source

Input:  list of FHIR bundle dicts
Output: list of canonical patient dicts + StageResult
"""
from __future__ import annotations



import os
import sys
import time

_PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PIPELINE_DIR not in sys.path:
    sys.path.insert(0, _PIPELINE_DIR)

from transform_fhir import transform_bundles
from pipeline_run import StageResult


def run(bundles: list[dict]) -> tuple[list[dict], StageResult]:
    """
    Transform FHIR R4 bundles → canonical patient dicts.

    Returns:
        patients: list of patient dicts
        result:   StageResult
    """
    t0 = time.perf_counter()

    try:
        patients = transform_bundles(bundles)

        # Count how many used the fast path vs full parse
        fast = sum(1 for b in bundles if b.get("_meta"))
        parsed = len(bundles) - fast

        result = StageResult(
            name="transform",
            status="ok",
            records_in=len(bundles),
            records_out=len(patients),
            duration_secs=time.perf_counter() - t0,
            metadata={"fast_path": fast, "full_parse": parsed},
        )

    except Exception as exc:
        result = StageResult(
            name="transform",
            status="failed",
            records_in=len(bundles),
            duration_secs=time.perf_counter() - t0,
            error=str(exc),
        )
        patients = []

    return patients, result

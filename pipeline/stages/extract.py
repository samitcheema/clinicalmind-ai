"""
Stage 1 — Extract

Generate synthetic FHIR R4 bundles (via generate_fhir.py) or load a
pre-existing FHIR JSON file (e.g. real Synthea output).

Input:  pipeline config dict
Output: list of raw FHIR bundle dicts + StageResult
"""
from __future__ import annotations



import json
import os
import sys
import time

_PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PIPELINE_DIR not in sys.path:
    sys.path.insert(0, _PIPELINE_DIR)

from generate_fhir import generate_fhir_bundles
from pipeline_run import StageResult


def run(config: dict) -> tuple[list[dict], StageResult]:
    """
    Extract FHIR R4 bundles.

    Config keys:
        fhir_file (str | None): path to a FHIR JSON file; if absent, generate synthetic data
        count     (int):        number of synthetic patients (default 60)
        seed      (int):        RNG seed for reproducibility (default 42)

    Returns:
        bundles: list of FHIR bundle dicts
        result:  StageResult
    """
    t0 = time.perf_counter()

    fhir_file = config.get("fhir_file")
    count = int(config.get("count", 60))
    seed = int(config.get("seed", 42))

    try:
        if fhir_file:
            with open(fhir_file) as fh:
                raw = json.load(fh)
            bundles = raw if isinstance(raw, list) else [raw]
            source = f"file:{fhir_file}"
        else:
            bundles = generate_fhir_bundles(n=count, seed=seed)
            source = f"synthetic (n={count}, seed={seed})"

        result = StageResult(
            name="extract",
            status="ok",
            records_in=0,
            records_out=len(bundles),
            duration_secs=time.perf_counter() - t0,
            metadata={"source": source},
        )

    except Exception as exc:
        result = StageResult(
            name="extract",
            status="failed",
            duration_secs=time.perf_counter() - t0,
            error=str(exc),
        )
        bundles = []

    return bundles, result

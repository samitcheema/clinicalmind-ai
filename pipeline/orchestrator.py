#!/usr/bin/env python3
"""
ClinicalMind AI — Data Pipeline Orchestrator

Coordinates all ETL stages end-to-end:

  Stage 1  SCHEMA       Create tables if they don't exist (ensure_schema.py)
  Stage 2  EXTRACT      Generate synthetic FHIR R4 bundles (or load from file)
  Stage 3  TRANSFORM    FHIR bundles -> canonical patient dicts
  Stage 4  STANDARDIZE  Type coercion / validation / deduplication
  Stage 5  LOAD         Upsert all Supabase tables + clinic_stats aggregate
  Stage 6  RECORD RUN   Persist pipeline run metadata to pipeline_runs table

Usage:
  cd pipeline
  python orchestrator.py                      # 60 synthetic patients (default)
  python orchestrator.py --count 100          # 100 patients
  python orchestrator.py --fhir-file f.json   # load real Synthea FHIR output
  python orchestrator.py --dry-run            # full pipeline, no DB writes needed
  python orchestrator.py --seed 99            # reproducible run with custom RNG seed
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from dotenv import load_dotenv
from supabase import create_client, Client

from pipeline_run import PipelineRun, StageResult
import ensure_schema
import stages.extract     as stage_extract
import stages.transform   as stage_transform
import stages.standardize as stage_standardize
import stages.load        as stage_load

load_dotenv(os.path.join(_HERE, ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")

_TOTAL = 6
_WIDTH = 60


# -- Console output ------------------------------------------------------------

def _hr():
    print("-" * _WIDTH)

def _banner(run):
    print("=" * _WIDTH)
    print("  ClinicalMind AI -- Data Pipeline")
    print(f"  Run ID : {run.run_id}")
    cfg = {k: v for k, v in run.config.items() if v is not None and v is not False}
    print(f"  Config : {json.dumps(cfg, separators=(',', ':'))}")
    print("=" * _WIDTH)

def _stage_header(n, name):
    print(f"\n[{n}/{_TOTAL}]  {name.upper()}")
    _hr()

def _ok(msg, secs):
    print(f"  OK  {msg}  ({secs:.2f}s)")

def _fail(result):
    print(f"  FAILED ({result.duration_secs:.2f}s)")
    print(f"     {result.error}")

def _summary(run, stats):
    print("\n" + "=" * _WIDTH)
    label = "COMPLETE" if run.status == "success" else "FAILED"
    print(f"  Pipeline {label}  ({run.duration_secs:.2f}s total)")

    if stats and run.status == "success":
        print()
        print(f"  {'Run ID':<26}  {run.run_id}")
        print(f"  {'Patients loaded':<26}  {stats.get('total_patients', 0)}")
        print(f"  {'High risk':<26}  {stats.get('high_risk_count', 0)}")
        print(f"  {'Moderate risk':<26}  {stats.get('moderate_risk_count', 0)}")
        print(f"  {'Low risk':<26}  {stats.get('low_risk_count', 0)}")
        print(f"  {'KPI compliance (avg)':<26}  {stats.get('overall_kpi_compliance_pct', 0)}%")
        print(f"  {'Below KPI target':<26}  {stats.get('patients_below_kpi_target', 0)}")
        print(f"  {'Crisis events (28d)':<26}  {stats.get('crisis_events_28d', 0)}")
        print(f"  {'Disengaged patients':<26}  {stats.get('disengaged_patients_count', 0)}")
        print(f"  {'High-risk disengaged':<26}  {stats.get('high_risk_disengaged_count', 0)}")

    print()
    print(f"  {'Stage':<14}  {'Status':<8}  {'In':>6}  {'Out':>6}  {'Time':>7}")
    _hr()
    for s in run.stages:
        icon = "OK" if s.status == "ok" else ("--" if s.status == "skipped" else "XX")
        print(f"  {icon} {s.name:<13}  {s.status.upper():<8}  {s.records_in:>6}  {s.records_out:>6}  {s.duration_secs:>6.2f}s")
    print("=" * _WIDTH)


# -- Pipeline ------------------------------------------------------------------

def run_pipeline(config, client=None, database_url=""):
    """
    Execute all six pipeline stages in sequence.

    Args:
        config:       dict with keys: count, fhir_file, seed, dry_run
        client:       Supabase client (not required when dry_run=True)
        database_url: PostgreSQL URI for schema creation (not required when dry_run=True)

    Returns:
        Completed PipelineRun with all stage results attached.
    """
    run      = PipelineRun(config=config)
    dry      = bool(config.get("dry_run", False))
    stats    = None
    rejected = []

    _banner(run)

    # -- Stage 1: Schema -------------------------------------------------------
    _stage_header(1, "schema")

    if dry:
        print("  [dry-run]  schema check skipped")
        r1 = StageResult(name="schema", status="skipped", duration_secs=0.0)
    elif not database_url:
        print("  !  DATABASE_URL not set -- skipping schema check")
        print("     Tables must already exist, or add DATABASE_URL to pipeline/.env")
        r1 = StageResult(name="schema", status="skipped", duration_secs=0.0)
    else:
        r1 = ensure_schema.run(database_url)
        if r1.status == "ok":
            n  = r1.metadata.get("tables", 0)
            st = r1.metadata.get("statements", 0)
            _ok(f"{n} tables verified  |  {st} statements executed", r1.duration_secs)
        else:
            _fail(r1)
            run.add_stage(r1)
            run.finish("failed")
            _summary(run, None)
            return run

    run.add_stage(r1)

    # -- Stage 2: Extract ------------------------------------------------------
    _stage_header(2, "extract")
    bundles, r2 = stage_extract.run(config)
    run.add_stage(r2)

    if r2.status == "ok":
        _ok(f"{r2.records_out} bundles  |  source: {r2.metadata.get('source', '')}", r2.duration_secs)
    else:
        _fail(r2)
        run.finish("failed")
        _summary(run, None)
        return run

    # -- Stage 3: Transform ----------------------------------------------------
    _stage_header(3, "transform")
    patients_raw, r3 = stage_transform.run(bundles)
    run.add_stage(r3)

    if r3.status == "ok":
        fast   = r3.metadata.get("fast_path", 0)
        parsed = r3.metadata.get("full_parse", 0)
        _ok(f"{r3.records_out} patient dicts  |  fast-path: {fast}  full-parse: {parsed}", r3.duration_secs)
    else:
        _fail(r3)
        run.finish("failed")
        _summary(run, None)
        return run

    # -- Stage 4: Standardize --------------------------------------------------
    _stage_header(4, "standardize")
    patients, rejected, r4 = stage_standardize.run(patients_raw)
    run.add_stage(r4)

    if r4.status == "ok":
        n_rej   = r4.metadata.get("rejected", 0)
        n_dupes = r4.metadata.get("duplicates_removed", 0)
        _ok(f"{r4.records_out} valid  |  {n_rej} rejected  |  {n_dupes} dupes removed", r4.duration_secs)
        if rejected:
            print(f"  Rejected records (showing first {min(5, len(rejected))}):")
            for rec in rejected[:5]:
                print(f"    {rec['patient_id']}: {'; '.join(rec['errors'])}")
            if len(rejected) > 5:
                print(f"    ... and {len(rejected) - 5} more")
    else:
        _fail(r4)
        run.finish("failed")
        _summary(run, None)
        return run

    if not patients:
        print("\n  No valid records remain after standardization. Aborting.")
        run.finish("failed")
        _summary(run, None)
        return run

    # -- Stage 5: Load ---------------------------------------------------------
    _stage_header(5, "load")

    if dry:
        print("  [dry-run]  Supabase writes skipped -- row counts shown below:")

    if client is None and not dry:
        r5 = StageResult(
            name="load",
            status="failed",
            records_in=len(patients),
            error="No Supabase client. Provide credentials or use --dry-run.",
        )
        run.add_stage(r5)
        _fail(r5)
        run.finish("failed")
        _summary(run, None)
        return run

    stats, r5 = stage_load.run(client, patients, run.run_id, dry_run=dry)
    run.add_stage(r5)

    if r5.status == "ok":
        tc    = r5.metadata.get("table_counts", {})
        col_w = max((len(t) for t in tc), default=20) + 2
        for tbl, cnt in tc.items():
            marker = "[dry]" if dry else "     "
            print(f"  {marker}  {tbl:<{col_w}}  {cnt:>5} rows")
        _ok("all tables loaded", r5.duration_secs)
    else:
        _fail(r5)
        run.finish("failed")
        _summary(run, stats)
        return run

    # -- Stage 6: Record run ---------------------------------------------------
    _stage_header(6, "record run")
    t6 = time.perf_counter()
    run.finish("success")

    if not dry and client:
        try:
            run_row = {
                "run_id":              run.run_id,
                "started_at":          run.started_at.isoformat(),
                "completed_at":        run.completed_at.isoformat(),
                "status":              run.status,
                "config":              json.dumps(run.config),
                "records_extracted":   r2.records_out,
                "records_transformed": r3.records_out,
                "records_loaded":      r5.records_out,
                "records_rejected":    len(rejected),
                "stages":              json.dumps([s.to_dict() for s in run.stages]),
            }
            client.table("pipeline_runs").upsert([run_row], on_conflict="run_id").execute()
            _ok("run metadata persisted to pipeline_runs", time.perf_counter() - t6)
        except Exception as exc:
            print(f"  !  warning: could not persist run metadata: {exc}")
    else:
        print(f"  [dry-run]  run not persisted  ({time.perf_counter() - t6:.2f}s)")

    r6 = StageResult(name="record", status="ok", records_out=1, duration_secs=time.perf_counter() - t6)
    run.add_stage(r6)

    _summary(run, stats)
    return run


# -- Entry point ---------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ClinicalMind AI -- Data Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--count",     type=int,  default=60,   help="Synthetic patients to generate (default: 60)")
    parser.add_argument("--fhir-file", type=str,  default=None, help="Load real FHIR JSON instead of generating")
    parser.add_argument("--seed",      type=int,  default=42,   help="RNG seed for reproducible data (default: 42)")
    parser.add_argument("--dry-run",   action="store_true",     help="Run all stages without writing to the database")
    args = parser.parse_args()

    config = {
        "count":     args.count,
        "fhir_file": args.fhir_file,
        "seed":      args.seed,
        "dry_run":   args.dry_run,
    }

    client = None
    db_url = DATABASE_URL

    if not args.dry_run:
        if not SUPABASE_URL or not SUPABASE_KEY:
            sys.exit(
                "ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY not set.\n"
                "       Copy pipeline/.env.example -> pipeline/.env and fill in values.\n"
                "       Or use --dry-run to test without a database."
            )
        client = create_client(SUPABASE_URL, SUPABASE_KEY)

    result = run_pipeline(config, client, database_url=db_url)
    sys.exit(0 if result.status == "success" else 1)


if __name__ == "__main__":
    main()

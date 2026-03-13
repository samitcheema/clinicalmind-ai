#!/usr/bin/env python3
"""
ClinicalMind AI — Synthea FHIR Import

Loads real Synthea-generated FHIR R4 output into the ClinicalMind pipeline.

Synthea produces one JSON file per patient under its output/fhir/ directory.
This script:
  1. Reads all *.json files from a Synthea output directory
  2. Filters to Transaction bundles containing a Patient resource
  3. Writes a combined fhir_synthea.json array
  4. Runs the full orchestrator pipeline against it

Usage:
  # Generate Synthea data first (requires Java):
  #   java -jar synthea-with-dependencies.jar -p 60 --exporter.fhir.export true
  #   (output lands in synthea/output/fhir/)

  cd pipeline
  python import_synthea.py /path/to/synthea/output/fhir
  python import_synthea.py /path/to/synthea/output/fhir --dry-run
  python import_synthea.py /path/to/synthea/output/fhir --count 40 --seed 0

What Synthea covers (parsed by transform_fhir.py):
  - Patient demographics (name, DOB, address/county)
  - Practitioner
  - Condition (ICD-10 diagnosis)
  - PHQ-9 observations (LOINC 44261-6 + item LOINCs)
  - Encounters and care contacts

What defaults when absent from Synthea bundles:
  - GAD-7, WHODAS, C-SSRS    -> scores default to 0 / "Low" / False
  - KPI compliance            -> all KPIs default to overdue=True
  - Crisis events             -> empty list
  - Risk level                -> derived from PHQ-9 score + SI flag
  - Engagement flag           -> derived from days since last contact

These gaps reflect real-world EHR integration: Synthea models primary-care
workflows. The pipeline's transform stage handles missing data gracefully and
documents every default via the standardize stage's rejection log.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)


def load_synthea_dir(synthea_dir: str, max_count: int | None = None) -> list[dict]:
    """
    Read all FHIR JSON files from a Synthea output directory.

    Synthea writes one Bundle per patient. Each bundle has:
      "resourceType": "Bundle", "type": "transaction"
    Hospital information files (hospitalInformation*.json) are skipped —
    they contain Location/Organization resources, not patients.

    Returns a list of patient Bundle dicts.
    """
    if not os.path.isdir(synthea_dir):
        sys.exit(f"ERROR: directory not found: {synthea_dir}")

    files = sorted(
        f for f in os.listdir(synthea_dir)
        if f.endswith(".json") and not f.startswith("hospitalInformation")
                                 and not f.startswith("practitionerInformation")
    )

    if not files:
        sys.exit(f"ERROR: no patient JSON files found in {synthea_dir}")

    bundles = []
    skipped = 0
    for fname in files:
        path = os.path.join(synthea_dir, fname)
        try:
            with open(path) as fh:
                raw = json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"  ! skipping {fname}: {exc}")
            skipped += 1
            continue

        # Accept single bundle or list
        candidates = raw if isinstance(raw, list) else [raw]

        for bundle in candidates:
            if not isinstance(bundle, dict):
                continue
            entries = bundle.get("entry", [])
            # Only include bundles that have at least one Patient resource
            has_patient = any(
                e.get("resource", {}).get("resourceType") == "Patient"
                for e in entries
            )
            if has_patient:
                bundles.append(bundle)
                if max_count and len(bundles) >= max_count:
                    break

        if max_count and len(bundles) >= max_count:
            break

    print(f"  Loaded {len(bundles)} patient bundles  ({skipped} files skipped)")
    return bundles


def main():
    parser = argparse.ArgumentParser(
        description="Import Synthea FHIR output into the ClinicalMind pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "synthea_dir",
        help="Path to Synthea output/fhir directory (contains per-patient .json files)",
    )
    parser.add_argument("--count",   type=int, default=None, help="Max patients to import")
    parser.add_argument("--seed",    type=int, default=42,   help="RNG seed (unused for file input, passed to orchestrator)")
    parser.add_argument("--dry-run", action="store_true",    help="Run pipeline without writing to the database")
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Path to write combined FHIR JSON (default: pipeline/fhir_synthea.json)",
    )
    args = parser.parse_args()

    out_path = args.out or os.path.join(_HERE, "fhir_synthea.json")

    print("ClinicalMind AI — Synthea Import")
    print("=" * 50)
    print(f"  Source   : {args.synthea_dir}")
    print(f"  Out file : {out_path}")
    print(f"  Dry run  : {args.dry_run}")
    print("-" * 50)

    # Step 1 — collect bundles from Synthea directory
    print("\n[1/2]  COLLECT SYNTHEA BUNDLES")
    print("-" * 50)
    bundles = load_synthea_dir(args.synthea_dir, max_count=args.count)

    if not bundles:
        sys.exit("ERROR: no valid patient bundles found.")

    # Step 2 — write combined JSON so orchestrator can read it as --fhir-file
    with open(out_path, "w") as fh:
        json.dump(bundles, fh)
    print(f"  Combined file written: {out_path}  ({os.path.getsize(out_path):,} bytes)")

    # Step 3 — run the orchestrator against the combined file
    print("\n[2/2]  RUNNING PIPELINE")
    print("-" * 50)

    from dotenv import load_dotenv
    load_dotenv(os.path.join(_HERE, ".env"))

    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    database_url = os.environ.get("DATABASE_URL", "")

    config = {
        "fhir_file": out_path,
        "count":     len(bundles),
        "seed":      args.seed,
        "dry_run":   args.dry_run,
    }

    client = None
    if not args.dry_run:
        if not supabase_url or not supabase_key:
            sys.exit(
                "ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY not set.\n"
                "       Copy pipeline/.env.example -> pipeline/.env and fill in values.\n"
                "       Or use --dry-run to test without a database."
            )
        from supabase import create_client
        client = create_client(supabase_url, supabase_key)

    from orchestrator import run_pipeline
    result = run_pipeline(config, client, database_url=database_url)
    sys.exit(0 if result.status == "success" else 1)


if __name__ == "__main__":
    main()

# ClinicalMind AI

A behavioral health data pipeline with an AI query layer — ingests FHIR R4 patient data from Synthea, normalizes it into a PostgreSQL schema, and exposes it to Claude via the Model Context Protocol so clinicians can ask questions.

**Live demo:** `https://samitcheema.github.io/clinicalmind-ai/`

---

## What It Does

1. **ETL pipeline** ingests [Synthea](https://github.com/synthetichealth/synthea)-generated FHIR R4 bundles, parses 15+ resource types, and loads normalized clinical data into Supabase
2. **MCP server** wraps the database with 7 typed tools that Claude calls based on the question — no dashboards, no SQL
3. **Browser demo** on GitHub Pages, served through a Cloudflare Worker proxy, lets anyone interact with live data using their own Anthropic API key

**Example queries:**
- *"Who are my highest-risk patients right now?"*
- *"Which patients have overdue SRA assessments?"*
- *"Were there any crisis events in the last 7 days?"*
- *"What's our KPI compliance rate for PHQ-9?"*
- *"Who hasn't had contact in over 30 days?"*

---

## Architecture

```
Synthea FHIR output (standard EHR-format bundles)
      │
      │  import_synthea.py
      ▼
┌─────────────────────────────────────────┐
│          6-Stage ETL Pipeline           │
│  1. Schema  — idempotent DDL + RLS      │
│  2. Extract — load FHIR bundles         │
│  3. Transform — FHIR R4 → patient dicts │
│  4. Standardize — validate + dedupe     │
│  5. Load  — upsert 12 Supabase tables   │
│  6. Record — persist run audit log      │
└─────────────────────────────────────────┘
      │
      ▼
Supabase (PostgreSQL + RLS)
      │
      ├── Cloudflare Worker proxy ──► Browser dashboard (GitHub Pages)
      │
      └── MCP Server (FastMCP / stdio)
                │
                ▼
          Claude claude-opus-4-6
```

---

## ETL Pipeline

The pipeline (`pipeline/`) is the core of the project. Every stage is independently testable and supports `--dry-run` for full execution without database writes.

### Stages

| Stage | File | Description |
|-------|------|-------------|
| Schema | `ensure_schema.py` | CREATE IF NOT EXISTS DDL for all 12 tables; RLS policies via psycopg2 |
| Extract | `stages/extract.py` | Load FHIR JSON from file or generate synthetic bundles |
| Transform | `transform_fhir.py` | FHIR R4 → canonical patient dicts; parses Patient, Encounter, Observation (LOINC), Condition (ICD-10-CM), Practitioner |
| Standardize | `stages/standardize.py` | Type coercion, clinical validation (score ranges, SI flags), deduplication |
| Load | `stages/load.py` | Upsert patients/providers, DELETE+INSERT for assessments/encounters/KPIs, refresh `clinic_stats` aggregate |
| Record | `orchestrator.py` | Persist run metadata to `pipeline_runs` audit table |

### Real FHIR Data (Synthea)

The pipeline ingests standards-compliant FHIR R4 format, exercising the full parse path on every record (`fast-path: 0, full-parse: 64`):

```bash
# Generate 100 patients with FHIR R4 output
java -jar synthea-with-dependencies.jar -p 100 --exporter.fhir.export true

# Import into the pipeline
cd pipeline
python import_synthea.py /path/to/synthea/output/fhir --dry-run  # test first
python import_synthea.py /path/to/synthea/output/fhir            # load to Supabase
```

**What Synthea covers** (parsed by `transform_fhir.py`):
- Patient demographics — name, DOB, address/county
- Practitioners — extracted from Encounter participant NPI references
- Conditions — ICD-10-CM diagnosis codes
- PHQ-9 observations — LOINC `44261-6` + item LOINCs
- Encounters and care contacts

**What defaults when absent** (behavioral health data Synthea doesn't model):
- GAD-7, WHODAS, C-SSRS → scores default to 0 / "Low" / False
- KPI compliance → all 7 KPIs default to overdue
- Crisis events → empty list
- Risk level → derived from PHQ-9 score + SI flag

### Database Schema

12 tables in Supabase with row-level security:

| Table | Notes |
|-------|-------|
| `providers` | Seeded from hardcoded list + NPI-derived from Synthea encounters |
| `patients` | Core PHI table — service_role only |
| `assessments_phq9/gad7/whodas/ssrs` | Per-assessment history |
| `encounters` | Inpatient/outpatient visits |
| `contacts` | Care contacts with days-since |
| `crisis_events` | 7-day and 28-day crisis flags |
| `kpi_compliance` | 7 behavioral health KPIs per patient |
| `clinic_stats` | De-identified aggregate — anon-readable for dashboard |
| `pipeline_runs` | Full audit log: per-stage record counts, run ID, duration |

### Running the Pipeline

```bash
cd pipeline
cp .env.example .env      # add SUPABASE_URL, SUPABASE_SERVICE_KEY, DATABASE_URL

pip install -r requirements.txt

python orchestrator.py --dry-run          # 60 synthetic patients, no DB writes
python orchestrator.py --count 100        # 100 synthetic patients → Supabase
python import_synthea.py /path/to/fhir   # Synthea FHIR data → Supabase
```

---

## MCP Server

The MCP server (`mcp-server/`) wraps the Supabase data with 7 tools that Claude invokes based on the clinical question.

### Why MCP Instead of RAG or Prompt Injection?

| Approach | Token cost | Stale data risk | Auditability |
|----------|-----------|-----------------|--------------|
| Inject all patients in system prompt | ~50k tokens | High | None |
| RAG (vector search) | Low | Medium | Partial |
| **MCP tool calls (this project)** | **Only what's needed** | **None (live fetch)** | **Full** |

Every tool call is structured — arguments in, typed response out. Claude never touches data it didn't explicitly request.

### Tools

| Tool | Description |
|------|-------------|
| `get_patients` | Patient list with optional filters (risk level, county, provider) |
| `get_patient_detail` | Full clinical record for one patient |
| `get_high_risk_patients` | Patients flagged by PHQ-9, SSRS, or recent crisis |
| `get_kpi_compliance` | Cohort-wide KPI completion vs 75% target |
| `get_overdue_assessments` | Patients past their assessment due dates |
| `get_crisis_events` | Crisis episodes within a configurable date window (default: 28 days) |
| `get_disengaged_patients` | No contact beyond a configurable threshold (default: 30 days) |

### Setup

```bash
cd mcp-server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "clinicalmind": {
      "command": "/path/to/clinicalmind-ai/mcp-server/.venv/bin/python",
      "args": ["/path/to/clinicalmind-ai/mcp-server/server.py"]
    }
  }
}
```

---

## Browser Demo

The demo at `docs/index.html` is served via GitHub Pages. It calls the Anthropic API through a **Cloudflare Worker proxy** (`worker/src/index.js`) which also proxies Supabase REST API requests — keeping credentials server-side and adding CORS headers.

The demo implements all 7 MCP tools as JavaScript functions against the live Supabase dataset.

---

## Project Structure

```
clinicalmind-ai/
├── pipeline/
│   ├── orchestrator.py        # 6-stage pipeline coordinator (CLI entry point)
│   ├── import_synthea.py      # Synthea FHIR directory → pipeline
│   ├── transform_fhir.py      # FHIR R4 bundle → canonical patient dict
│   ├── ensure_schema.py       # Idempotent DDL + RLS via psycopg2
│   ├── generate_fhir.py       # Synthetic FHIR bundle generator
│   ├── pipeline_run.py        # PipelineRun + StageResult dataclasses
│   ├── stages/
│   │   ├── extract.py
│   │   ├── standardize.py
│   │   └── load.py
│   ├── requirements.txt
│   └── .env.example
├── mcp-server/
│   ├── server.py              # FastMCP server — all 7 tool definitions
│   ├── adapter/
│   │   ├── mock_adapter.py
│   │   └── sql_adapter.py
│   └── data/mock_data.py
├── worker/
│   ├── src/index.js           # Cloudflare Worker — Supabase + Claude API proxy
│   └── wrangler.toml
└── docs/
    └── index.html             # Browser demo (GitHub Pages)
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI | Claude (`claude-opus-4-6`) via Anthropic API |
| MCP framework | [FastMCP](https://github.com/jlowin/fastmcp) (Python, stdio) |
| ETL | Python — psycopg2, supabase-py, python-dotenv |
| FHIR data | [Synthea](https://github.com/synthetichealth/synthea) — FHIR R4 bundles |
| Database | Supabase (PostgreSQL 15+) with row-level security |
| Edge proxy | Cloudflare Workers |
| Frontend | Vanilla JS — GitHub Pages |

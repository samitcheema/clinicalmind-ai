# Repo Cleanup Design

**Date:** 2026-03-21
**Scope:** Repository hygiene + targeted code quality audit
**Out of scope:** worker/, mcp-server/, source SQL files

---

## 1. Repository Hygiene

### .gitignore additions
- `.superpowers/` — Claude Code brainstorm artifacts; not project code
- `.wrangler/` — Wrangler cache at repo root (only `worker/.wrangler/` was excluded before)

### Tracked file review
- `docs/assets/` (compiled JS/CSS) — intentionally tracked for GitHub Pages; leave as-is
- `synthea-with-dependencies.jar` and `synthea_out/` — already gitignored, local workspace clutter only; no git action needed

---

## 2. Frontend Audit (`frontend/src/`)

Scan all files for and remove:
- Unused imports
- Dead code and commented-out blocks
- Stray `console.log` statements
- Utility functions in `frontend/src/utils/` that are defined but never called anywhere

No restructuring. Changes stay within existing files.

**Files in scope:**
- `frontend/src/App.jsx`
- `frontend/src/ThemeContext.jsx`
- `frontend/src/components/` (all)
- `frontend/src/utils/` (all)
- `frontend/src/index.css`, `frontend/src/main.jsx`

---

## 3. Pipeline Audit (`pipeline/`)

Scan all Python scripts for and remove:
- Unused imports
- Dead code and commented-out blocks
- Debug-only `print` statements (preserve intentional logging)
- Functions defined but never called within the pipeline

**Files in scope:**
- `pipeline/orchestrator.py`
- `pipeline/pipeline_run.py`
- `pipeline/ensure_schema.py`
- `pipeline/import_synthea.py`
- `pipeline/transform_fhir.py`
- `pipeline/seed.py`
- `pipeline/seed_mock.py`
- `pipeline/generate_fhir.py`
- `pipeline/stages/extract.py`
- `pipeline/stages/load.py`
- `pipeline/stages/standardize.py`
- `pipeline/stages/transform.py`

**Approach:** `seed_mock.py` and `generate_fhir.py` are treated as standalone utilities — remove internal dead code only, do not restructure or remove the scripts themselves.

---

## Success Criteria

- `.gitignore` covers `.superpowers/` and root `.wrangler/`
- No unused imports remain in frontend or pipeline files
- No dead/commented-out code blocks remain
- No stray `console.log` / debug `print` calls remain
- All existing functionality is preserved (no behavioral changes)

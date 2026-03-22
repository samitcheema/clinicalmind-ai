# Repo Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove clutter from .gitignore, strip dead imports/code from the frontend and pipeline, with no behavioral changes.

**Architecture:** Three independent cleanup passes — repo hygiene, frontend audit, pipeline audit — each committed separately. No restructuring of files; all changes are within-file removals.

**Tech Stack:** Git, React/Vite (JSX), Python 3

**Spec:** `docs/superpowers/specs/2026-03-21-repo-cleanup-design.md`

**Out of scope (do not touch):** `worker/`, `mcp-server/`, `pipeline/supabase_schema.sql`, `source/`

---

## Pre-flight

Verify the frontend builds without errors before making any changes:

```bash
cd frontend && npm run build 2>&1 | tail -5
```

Expected: exit 0. If the build fails, stop and report before proceeding.

---

## Task 1: Fix .gitignore

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Add the two missing entries**

Open `.gitignore`. The file currently has a `# Wrangler` section containing only `worker/.wrangler/`. Add two new entries — append them at the end of the file, or under the `# Wrangler` section:

```
# Claude Code / superpowers artifacts
.superpowers/

# Wrangler cache at repo root (worker/.wrangler/ already excluded above)
.wrangler/
```

- [ ] **Step 2: Verify git status no longer shows them as untracked**

```bash
git status --short
```

Expected: `.superpowers/` and `.wrangler/` no longer appear as `??`.

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: add .superpowers/ and .wrangler/ to .gitignore"
```

---

## Task 2: Frontend — Remove dead imports and unused exports

**Pre-confirmed dead code (found during planning):**

| File | Line | Issue |
|------|------|-------|
| `frontend/src/components/Dashboard.jsx` | 3 | `fmtDate` imported but never called in this file |
| `frontend/src/utils/dataTransform.js` | 6 | `RISK_ORDER` exported but never imported by any other file |
| `frontend/src/utils/tools.js` | 1 | `PHQ9_ITEMS` imported but never used within `tools.js` |

**Important:** `PHQ9_ITEMS` is a live export in `dataTransform.js` (line 7) — it is used by `PatientDetail.jsx`. Only the *import* of `PHQ9_ITEMS` in `tools.js` is dead. Never remove the `PHQ9_ITEMS` export from `dataTransform.js`.

**Files:**
- Modify: `frontend/src/components/Dashboard.jsx`
- Modify: `frontend/src/utils/dataTransform.js`
- Modify: `frontend/src/utils/tools.js`

- [ ] **Step 1: Fix Dashboard.jsx — remove unused `fmtDate` import**

In `Dashboard.jsx`, line 3 currently reads:
```js
import { offsetDate, TODAY, fmtDate } from '../utils/mockGenerators.js';
```

Change it to:
```js
import { offsetDate, TODAY } from '../utils/mockGenerators.js';
```

`fmtDate` is used in other components (PatientDetail, EncounterTimeline) but not in Dashboard. This is a within-file change only.

- [ ] **Step 2: Fix dataTransform.js — remove unused `RISK_ORDER` export**

In `dataTransform.js`, line 6 is:
```js
export const RISK_ORDER  = { High:0, Moderate:1, Low:2 };
```

Delete that line entirely. Line 7 (`export const PHQ9_ITEMS = [...]`) must remain — it is used by `PatientDetail.jsx`.

- [ ] **Step 3: Fix tools.js — remove unused `PHQ9_ITEMS` import**

In `tools.js`, line 1 currently reads:
```js
import { KPI_NAMES, PHQ9_ITEMS } from './dataTransform.js';
```

Change it to:
```js
import { KPI_NAMES } from './dataTransform.js';
```

This removes only the *import* in `tools.js`. The `PHQ9_ITEMS` export in `dataTransform.js` is untouched.

- [ ] **Step 4: Scan remaining frontend files for console.logs**

```bash
grep -rn "console\." frontend/src/
```

Expected: no output. If any hits appear, inspect each one. Remove any that are debug-style (`console.log(data)`, `console.log('here')`, etc.). Preserve any that are the sole user-visible error reporter in a utility function.

- [ ] **Step 5: Scan for commented-out code blocks**

```bash
grep -rn "//.*=\|// *function\|// *import\|// *return\|// *if " frontend/src/components/ frontend/src/utils/ | grep -v "node_modules"
```

Review any hits. Explanatory comments (e.g. `// PHQ-9 item scores: derive from total if item_scores unavailable`) should be kept. Commented-out code blocks should be removed.

- [ ] **Step 6: Verify build passes**

```bash
cd frontend && npm run build 2>&1 | tail -10
```

Expected: exit 0, no errors. If the build fails, revert and diagnose before proceeding.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/Dashboard.jsx \
        frontend/src/utils/dataTransform.js \
        frontend/src/utils/tools.js
git commit -m "chore: remove dead imports and unused export from frontend"
```

---

## Task 3: Pipeline — Remove dead code and debug prints

**Pattern note:** Five pipeline files share the same cosmetic issue — a double blank line after `from __future__ import annotations` (PEP 8 expects one blank line before stdlib imports). These are `pipeline_run.py`, `stages/extract.py`, `stages/transform.py`, `stages/standardize.py`, and `stages/load.py`. Each step below addresses this in one file.

**Files:**
- Modify: `pipeline/pipeline_run.py`
- Modify: `pipeline/stages/extract.py`
- Modify: `pipeline/stages/transform.py`
- Modify: `pipeline/stages/standardize.py`
- Modify: `pipeline/stages/load.py`
- Audit (modify if needed): `pipeline/ensure_schema.py`, `pipeline/transform_fhir.py`, `pipeline/import_synthea.py`, `pipeline/seed.py`, `pipeline/seed_mock.py`, `pipeline/generate_fhir.py`, `pipeline/stages/__init__.py`

### 3a: pipeline_run.py

- [ ] **Step 1: Fix double blank line in pipeline_run.py**

Lines 8–13 currently look like:
```python
from __future__ import annotations


import uuid
```

Remove one blank line so it becomes:
```python
from __future__ import annotations

import uuid
```

- [ ] **Step 2: Check if `PipelineRun.stage()` is called anywhere**

```bash
grep -rn "\.stage(" pipeline/ --include="*.py"
```

Expected: no output. Empty result confirms no callers exist and the method is safe to remove. If callers ARE found outside `pipeline_run.py`, leave the method in place.

If no callers: remove the method (approximately lines 75–76):
```python
def stage(self, name: str) -> StageResult | None:
    return next((s for s in self.stages if s.name == name), None)
```

If there are callers outside `pipeline_run.py`, leave it.

- [ ] **Step 3: Check if `PipelineRun.to_dict()` is called anywhere**

Note: `StageResult.to_dict()` IS called (as `s.to_dict()` in `orchestrator.py`). This step is about `PipelineRun.to_dict()` specifically.

```bash
grep -rn "run\.to_dict\b" pipeline/ --include="*.py"
```

Expected: no output. Empty result confirms `PipelineRun.to_dict()` is dead (note: `s.to_dict()` calls in `orchestrator.py` are `StageResult.to_dict()`, not this method). If callers ARE found, leave the method in place.

If no callers: `PipelineRun.to_dict()` is dead. Remove it (approximately lines 78–86):
```python
def to_dict(self) -> dict:
    return {
        "run_id":        self.run_id,
        "started_at":    self.started_at.isoformat(),
        "completed_at":  self.completed_at.isoformat() if self.completed_at else None,
        "status":        self.status,
        "config":        self.config,
        "stages":        [s.to_dict() for s in self.stages],
    }
```

If there are callers, leave it.

### 3b: Stage files — fix double blank lines

All four stage files have the same issue: one extra blank line after `from __future__ import annotations`.

- [ ] **Step 4: Fix extract.py**

Change:
```python
from __future__ import annotations



import json
```
To:
```python
from __future__ import annotations

import json
```

- [ ] **Step 5: Fix transform.py**

Change:
```python
from __future__ import annotations



import os
```
To:
```python
from __future__ import annotations

import os
```

- [ ] **Step 6: Fix standardize.py**

Change:
```python
from __future__ import annotations



import os
```
To:
```python
from __future__ import annotations

import os
```

- [ ] **Step 7: Fix load.py**

Change:
```python
from __future__ import annotations



import json
```
To:
```python
from __future__ import annotations

import json
```

### 3c: Audit remaining pipeline files

- [ ] **Step 8: Scan for debug print() calls**

```bash
grep -rn "^\s*print(" pipeline/ensure_schema.py pipeline/transform_fhir.py pipeline/import_synthea.py pipeline/seed.py pipeline/seed_mock.py pipeline/generate_fhir.py pipeline/stages/__init__.py 2>/dev/null
```

**Expected result:** All print() calls found here will be in standalone CLI entry-point scripts and are exempt under the spec's logging heuristic (they are the sole user-visible progress indicator). If you find any bare `print(some_variable)` or `print(result)` debug-style calls that are not user-facing messages, remove those. If everything found looks like intentional status output, no changes needed.

Note: `orchestrator.py` print() calls are all intentional console output — do not modify `orchestrator.py` in this step.

- [ ] **Step 9: Scan for unused imports in remaining pipeline files**

```bash
grep -n "^import \|^from " pipeline/ensure_schema.py pipeline/transform_fhir.py pipeline/import_synthea.py pipeline/seed.py pipeline/seed_mock.py pipeline/generate_fhir.py
```

For each import found, verify it is used in the file body:
```bash
# Example — replace MODULE with each import name found above
grep -n "MODULE" pipeline/<filename>.py | grep -v "^.*:.*import"
```

Remove any import with zero usage hits in the file body.

- [ ] **Step 10: Scan for commented-out code blocks in pipeline files**

```bash
grep -n "^\s*#\s*[a-z].*=\|^\s*#\s*def \|^\s*#\s*return \|^\s*#\s*if " pipeline/ensure_schema.py pipeline/transform_fhir.py pipeline/import_synthea.py pipeline/seed.py pipeline/seed_mock.py pipeline/generate_fhir.py pipeline/stages/__init__.py 2>/dev/null
```

Review hits. Section dividers (e.g. `# ── Helpers ───`) and explanatory comments should be kept. Commented-out code blocks should be removed.

- [ ] **Step 11: Scan for unused functions in remaining pipeline files**

```bash
grep -n "^def " pipeline/ensure_schema.py pipeline/transform_fhir.py pipeline/import_synthea.py pipeline/seed.py pipeline/seed_mock.py pipeline/generate_fhir.py
```

For each function found, check if it is called anywhere in the pipeline:
```bash
# Example — replace FUNCNAME with each function name
grep -rn "FUNCNAME(" pipeline/ --include="*.py"
```

Remove functions with zero call sites outside their own definition. Be conservative — if a function looks like a public entry point (e.g. called from orchestrator.py or import_synthea.py) or is documented in the module docstring, leave it.

- [ ] **Step 12: Commit pipeline cleanup**

```bash
git add pipeline/pipeline_run.py \
        pipeline/stages/extract.py \
        pipeline/stages/transform.py \
        pipeline/stages/standardize.py \
        pipeline/stages/load.py
# Add any additional pipeline files that were modified
git commit -m "chore: remove dead code, fix blank lines in pipeline"
```

---

## Task 4: Final verification

- [ ] **Step 1: Frontend build is clean**

```bash
cd frontend && npm run build 2>&1 | tail -5
```

Expected: exit 0.

- [ ] **Step 2: No stray console.logs remain**

```bash
grep -rn "console\." frontend/src/
```

Expected: no output.

- [ ] **Step 3: No stray debug prints remain**

```bash
grep -rn "^\s*print(" pipeline/ --include="*.py" | grep -v "orchestrator"
```

Review any remaining hits — all should be intentional status messages in standalone utility scripts.

- [ ] **Step 4: .gitignore covers both directories**

```bash
git status --short | grep -E "superpowers|wrangler"
```

Expected: no output (neither directory appears as untracked).

- [ ] **Step 5: Exclusion zones untouched**

```bash
git diff HEAD -- worker/ mcp-server/ pipeline/supabase_schema.sql source/
```

Expected: no output (no changes in any exclusion zone).

- [ ] **Step 6: Final commit if any loose ends**

If any files were cleaned in steps 8–11 above but not yet committed:
```bash
git add -p  # stage selectively
git commit -m "chore: pipeline audit — remove unused imports and dead code"
```

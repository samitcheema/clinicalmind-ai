# Frontend Enhancement Design — ClinicalMind AI
**Date:** 2026-03-18
**Status:** Approved

---

## Overview

Redesign the ClinicalMind AI frontend dashboard with a dark "Clinical Command Center" theme, fixed sidebar navigation, enhanced stat cards with sparkline trends, SVG progress rings for KPI compliance, and an improved patient table with risk badges and inline KPI status indicators. Also removes all references to the 75% KPI compliance target.

---

## 1. KPI Compliance Target Removal

Remove the `KPI_TARGET = 75` constant and all references from:

- `dataTransform.js` — delete `KPI_TARGET` export
- `Dashboard.jsx` — remove `Target: {KPI_TARGET}%` sub-label on stat card; remove `.kpi-target-tick` element from KPI bars
- `tools.js` — remove `meets_target` and `target_pct` fields from `getKpiCompliance()` return value; remove `KPI_TARGET` import
- `ChatPane.jsx` — remove "meets the 75% target" language from system prompt and suggested prompts
- `index.css` — remove `.kpi-target-tick` rule

The KPI panel title changes from "KPI Compliance vs 75% Target" to "KPI Compliance".

---

## 2. Design System — Dark Theme

Replace the current light theme CSS variables with a dark palette:

| Token | Value | Purpose |
|---|---|---|
| `--bg` | `#0f172a` | Page background |
| `--surface` | `#1e293b` | Card/panel background |
| `--surface-2` | `#0d1526` | Sidebar/topbar background |
| `--border` | `#334155` | Borders |
| `--text` | `#f8fafc` | Primary text |
| `--text-2` | `#cbd5e1` | Secondary text |
| `--text-3` | `#94a3b8` | Labels/captions |
| `--text-4` | `#475569` | Muted/disabled |

Status colors (unchanged): `--red: #ef4444`, `--amber: #f59e0b`, `--green: #22c55e`, `--primary: #3b82f6`.

---

## 3. Layout — Fixed Sidebar

Replace the current tab-based navigation (Dashboard / Patients / AI Chat) with a fixed left sidebar (200px wide).

**Sidebar structure:**
- Logo mark (`CM` monogram in blue gradient, 32×32px) + wordmark
- Nav section "MAIN": Dashboard (active state), Patients (with overdue badge count), AI Assistant
- Nav section "REPORTS": KPI Summary, Crisis Log
- Footer: live status dot + "Updated now" timestamp

**Active nav item:** `#1e3a8a` background, `#93c5fd` text, blue dot.
**Sidebar background:** `#0d1526`, right border `1px solid #334155`.

The main area retains a topbar (site title + subtitle + Supabase status pill + date pill).

---

## 4. Stat Cards — Sparklines & Trend Indicators

Each of the 4 stat cards gains:

1. **Icon area** (34×34px rounded square with 15% opacity tinted background)
2. **Trend badge** (top-right): directional arrow + delta value + period label (e.g. "↑ 3 wk", "↑ 4% mo")
3. **Sparkline** (SVG polyline, full width, 20px tall, 60% opacity) at the bottom of each card

Cards keep their colored bottom border stripe (3px gradient). The `.sc-sub` line on the KPI compliance card changes from "Target: 75%" to "overall across all KPIs".

---

## 5. KPI Panel — Progress Rings

Replace the horizontal bar chart rows with a 3-column grid of SVG circular progress rings (one per KPI, 7 total — last row has 1 item spanning).

Each ring:
- 52×52px SVG, `r=20`, `stroke-width=5`
- Track color: `#1e3a4a` (dark teal)
- Fill: green (`#22c55e`) if compliant, amber (`#f59e0b`) if below — driven by the same overdue logic as before, just without any target comparison
- Centered percentage label inside the ring
- KPI name label below

Panel header retains an "avg%" badge (green pill) showing overall compliance.

---

## 6. Patient Table — Risk Badges & KPI Dots

**Columns:** Patient (name), Risk, Diagnosis, KPI Status, Last Contact, Provider.

**Risk column:** Replace plain text with colored pill badges:
- High: red background tint + `● High`
- Moderate: amber background tint + `● Moderate`
- Low: green background tint + `● Low`

**KPI Status column:** 7 small squares (6×6px, `border-radius: 1px`) — one per KPI, green if compliant, red if overdue.

**Last Contact column:** Color-coded recency text — green if ≤7d, amber if 8–30d, default muted if older.

**Table styling:** Dark rows on `#1e293b` background, `#0f172a` hover, thin `#1e293b` row separators. Header labels in small-caps `#475569`.

---

## 7. Files Changed

| File | Change |
|---|---|
| `frontend/src/index.css` | Full dark theme rewrite; sidebar, sparkline, ring, badge styles added; `kpi-target-tick` removed |
| `frontend/src/App.jsx` | Replace tab nav with sidebar layout shell |
| `frontend/src/components/Header.jsx` | Fold into sidebar/topbar — or remove if sidebar replaces it |
| `frontend/src/components/Dashboard.jsx` | Stat cards with sparklines; KPI rings panel; remove target tick & label |
| `frontend/src/components/PatientTable.jsx` | Risk badges, KPI dot grid, contact recency coloring |
| `frontend/src/utils/dataTransform.js` | Remove `KPI_TARGET` export |
| `frontend/src/utils/tools.js` | Remove `meets_target` / `target_pct` from KPI tool response |
| `frontend/src/components/ChatPane.jsx` | Remove 75% target language from system prompt |

---

## 8. Out of Scope

- PatientDetail modal — no changes this iteration
- EncounterTimeline — no changes this iteration
- Backend / Supabase schema — no changes
- New data sources or API endpoints

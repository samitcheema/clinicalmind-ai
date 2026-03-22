# IM Dashboard Routing — Design Spec

**Date:** 2026-03-22
**Status:** Approved
**Scope:** Frontend only — React routing, provider identity, IM dashboard panel

---

## Goal

Route providers to specialty-specific dashboards based on who is logged in. BH providers see the existing behavioral health dashboard. IM providers see a new internal medicine dashboard with disease panel views. No real authentication — a mock provider picker establishes identity.

---

## Architecture Overview

### New dependency

`react-router-dom` v6 added to `frontend/package.json`. Replaces the manual `activeView` state-switching in `App.jsx` with declarative `<Routes>`.

### Provider identity

A `ProviderContext` (mirrors `ThemeContext`) wraps the entire app and exposes:

```js
{ provider, setProvider, clearProvider }
// provider shape: { provider_id, name, specialty, team } | null
```

Persisted to `localStorage` as `cm_provider` (JSON). On mount, `ProviderContext` reads `localStorage`; if a valid entry exists, the picker is skipped.

### Route table

```
/            →  redirect to /dashboard
/dashboard   →  <BHDashboard> if specialty === "BH"
             →  <IMDashboard> if specialty === "IM"
/patients    →  <PatientTable> filtered by selected provider's specialty
/chat        →  <ChatPane> (IM tool definitions registered alongside BH)
```

---

## Provider Picker

**Component:** `frontend/src/components/ProviderPicker.jsx`

Rendered as a full-screen overlay in `App.jsx` whenever `provider` is `null`. Dismissed only by completing both steps — no close button.

### Step 1 — Specialty

Two large clickable cards:
- 🧠 **Behavioral Health** — subtitle: team names (ACT-1, ACT-2, CSP-1)
- 🏥 **Internal Medicine** — subtitle: team name (IM-1)

Clicking a card advances to Step 2. A "← Back" link in Step 2 returns to Step 1.

### Step 2 — Provider

Shows only providers whose `specialty` matches the Step 1 selection. Provider list is hardcoded from the mock data (6 BH providers, 2 IM providers). Each card shows name and team. Clicking a card:
1. Calls `setProvider({ provider_id, name, specialty, team })`
2. Saves to `localStorage` as `cm_provider` (underscore, consistent with `cm_api_key`)
3. Dismisses the overlay

### Switch provider

`Topbar.jsx` gains a small "👤 Dr. Name · switch" element. Clicking "switch" calls `clearProvider()`, which clears `localStorage` and sets `provider` to `null`, re-showing the picker.

---

## BHDashboard

**File:** `frontend/src/components/BHDashboard.jsx`

The existing `Dashboard.jsx` is renamed to `BHDashboard.jsx`. No logic changes — this is a rename only. `App.jsx` import is updated accordingly. `Dashboard.jsx` is deleted.

---

## IMDashboard

**File:** `frontend/src/components/IMDashboard.jsx`

### Data source

IM data is served from a new JavaScript mock module `frontend/src/utils/imMockData.js` that mirrors the Python `im_mock_data.py` structure. This module exports:

```js
export function getImPatients({ risk_level, condition, provider } = {}) { ... }
export function getImPatientDetail(patient_id) { ... }
// returns the full patient object matching patient_id, or null if not found
// return shape is identical to individual items returned by getImPatients()
export function getChronicDiseasePanel(condition) { ... }  // "diabetes" | "ckd" | "hypertension"
export function getPreventiveCareGaps(gap_type = null) { ... }
```

These functions operate on the same patient data shape as the Python adapter and are called directly in the component (no HTTP call). The data is hardcoded — 12 IM patients matching the Python mock exactly.

`IMDashboard` calls all three `getChronicDiseasePanel` variants and `getImPatients` on mount using these local JS functions. Loading state shows a spinner; error state shows an error message.

### Stat cards (top row, 3 cards)

| Card | Value | Source |
|------|-------|--------|
| High Risk | Count of patients with `risk_level === "High"` | `getImPatients({ risk_level: "High" })` |
| A1c Outliers | Count of patients with latest A1c > 8.0 | `getChronicDiseasePanel("diabetes")` |
| Care Gaps | Count of patients with ≥ 1 overdue item | `getPreventiveCareGaps()` |

### Disease panels (three columns)

**Diabetes panel** — calls `getChronicDiseasePanel("diabetes")`
- Lists patients with A1c > 8.0
- Shows: patient name, latest A1c value, trend arrow (↑ if last reading higher than prior, ↓ lower, → same)
- Sorted by A1c descending

**CKD panel** — calls `getChronicDiseasePanel("ckd")`
- Lists patients with eGFR slope ≤ −3 units/year
- Shows: patient name, eGFR slope (e.g. "−8/yr"), trend arrow (always ↓ for this panel)
- Sorted by slope ascending (worst first)

**Hypertension panel** — calls `getChronicDiseasePanel("hypertension")`
- Lists patients with latest systolic > 140
- Shows: patient name, latest BP reading (e.g. "162/98")
- Sorted by systolic descending

### Patient interaction

Clicking a patient name is a no-op in this iteration. No detail view for IM patients yet.

---

## Topbar Changes

`Topbar.jsx` gains two changes:

1. **Provider name + switch link** — "👤 Dr. Name · switch" rendered in the right section. Reads from `ProviderContext`. Clicking "switch" calls `clearProvider()`.

2. **Dynamic subtitle** — the hardcoded `"Westchester County · ACT + CSP Programs"` subtitle is replaced with a specialty-aware value:
   - BH: `"Westchester County · ACT + CSP Programs"`
   - IM: `"Westchester County · Internal Medicine"`
   - No provider selected: `"Westchester County"`

---

## Sidebar Changes

`Sidebar.jsx` changes:

1. Replace `onNavigate(view)` calls with `<NavLink to="/dashboard">`, `<NavLink to="/patients">`, `<NavLink to="/chat">`. Active styling uses NavLink's `className` callback.

2. **Overdue badge guard** — the badge currently iterates `patients` and reads `p.kpis[k].overdue`. For IM providers, `kpis` does not exist on patient objects. Add a specialty check: only compute and show the overdue badge when `provider.specialty === "BH"`. For IM providers, omit the badge entirely.

---

## PatientTable Changes

`PatientTable.jsx` reads `provider` from `ProviderContext`:
- `specialty === "BH"` → renders the existing BH patient list (from `App.jsx` patients state, unchanged)
- `specialty === "IM"` → renders IM patients from `getImPatients()` in `imMockData.js`

The component does not accept a `specialty` prop — it reads directly from context.

---

## Chat Tool Changes (`tools.js`)

`tools.js` gains 4 new IM tool definitions alongside the existing 7 BH definitions. Tool definitions are Claude API tool schemas (name, description, input_schema).

`runTool(name, input, patients)` gains 4 new cases. IM tool cases call the corresponding functions from `imMockData.js` directly — they do not use the `patients` argument (IM data is self-contained in `imMockData.js`):

| Tool name | `runTool` dispatches to |
|-----------|------------------------|
| `get_im_patients` | `getImPatients(input)` |
| `get_im_patient_detail` | `getImPatientDetail(input.patient_id)` — add this export to `imMockData.js` |
| `get_chronic_disease_panel` | `getChronicDiseasePanel(input.condition)` |
| `get_preventive_care_gaps` | `getPreventiveCareGaps(input.gap_type)` |

Both BH and IM tools are always registered — Claude uses whichever is contextually appropriate.

---

## Files Changed

| Action | File | What |
|--------|------|------|
| Create | `src/components/ProviderPicker.jsx` | Two-step specialty + provider picker overlay |
| Rename | `src/components/Dashboard.jsx` → `src/components/BHDashboard.jsx` | Name only, no logic change |
| Create | `src/components/IMDashboard.jsx` | IM dashboard with 3 disease panels |
| Create | `src/ProviderContext.jsx` | Provider identity context + localStorage persistence |
| Create | `src/utils/imMockData.js` | JS mirror of Python IM mock adapter (4 exported functions) |
| Modify | `src/App.jsx` | Add BrowserRouter, Routes, ProviderContext; remove activeView state |
| Modify | `src/components/Sidebar.jsx` | Replace onNavigate with NavLink; guard BH-only overdue badge |
| Modify | `src/components/Topbar.jsx` | Add provider name + switch link; dynamic specialty subtitle |
| Modify | `src/components/PatientTable.jsx` | Read from ProviderContext; filter by specialty |
| Modify | `src/utils/tools.js` | Add 4 IM tool definitions + runTool cases |
| Modify | `package.json` | Add react-router-dom dependency |

---

## Out of Scope

- Real authentication (Supabase auth, passwords, sessions)
- IM patient detail view (clicking a patient name)
- Provider-filtered chat (AI assistant sees all tools regardless of specialty)
- Any backend changes (MCP server, Cloudflare Worker, Supabase schema)

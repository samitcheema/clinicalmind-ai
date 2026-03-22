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
2. Saves to `localStorage`
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

### Stat cards (top row, 3 cards)

| Card | Value | Source |
|------|-------|--------|
| High Risk | Count of patients with `risk_level === "High"` | `get_im_patients({ risk_level: "High" })` |
| A1c Outliers | Count of patients with latest A1c > 8.0 | `get_chronic_disease_panel("diabetes")` |
| Care Gaps | Count of patients with ≥ 1 overdue item | `get_preventive_care_gaps()` |

### Disease panels (three columns)

**Diabetes panel** — calls `get_chronic_disease_panel("diabetes")`
- Lists patients with A1c > 8.0
- Shows: patient name, latest A1c value, trend arrow (↑ if last reading higher than prior, ↓ lower, → same)
- Sorted by A1c descending

**CKD panel** — calls `get_chronic_disease_panel("ckd")`
- Lists patients with eGFR slope ≤ −3 units/year
- Shows: patient name, eGFR slope (e.g. "−8/yr"), trend arrow (always ↓ for this panel)
- Sorted by slope ascending (worst first)

**Hypertension panel** — calls `get_chronic_disease_panel("hypertension")`
- Lists patients with latest systolic > 140
- Shows: patient name, latest BP reading (e.g. "162/98")
- Sorted by systolic descending

### Data loading

`IMDashboard` calls all three `get_chronic_disease_panel` variants and `get_im_patients` on mount via the existing Cloudflare Workers proxy (`dataTransform.js`). Loading state shows a spinner; error state shows a message.

### Patient interaction

Clicking a patient name is a no-op in this iteration. No detail view for IM patients yet.

---

## PatientTable Changes

`PatientTable.jsx` gains a specialty filter: when `provider.specialty === "IM"`, it renders IM patients from `get_im_patients()`; when `"BH"`, it renders the existing BH patient list. The component accepts a `specialty` prop (or reads from `ProviderContext` directly).

---

## Chat Tool Changes

`tools.js` gains 4 new IM tool definitions alongside the existing 7 BH definitions:

| Tool | Description |
|------|-------------|
| `get_im_patients` | IM patient panel, optional filters: risk_level, condition, provider |
| `get_im_patient_detail` | Full record for one IM patient |
| `get_chronic_disease_panel` | Outliers for diabetes / ckd / hypertension |
| `get_preventive_care_gaps` | Patients overdue for preventive care items |

`runTool()` routes these calls to the corresponding IM adapter functions. Both BH and IM tools are always registered — Claude uses whichever is contextually appropriate.

---

## Files Changed

| Action | File | What |
|--------|------|------|
| Create | `src/components/ProviderPicker.jsx` | Two-step specialty + provider picker overlay |
| Rename | `src/components/Dashboard.jsx` → `src/components/BHDashboard.jsx` | Name only, no logic change |
| Create | `src/components/IMDashboard.jsx` | IM dashboard with 3 disease panels |
| Create | `src/ProviderContext.jsx` | Provider identity context + localStorage persistence |
| Modify | `src/App.jsx` | Add BrowserRouter, Routes, ProviderContext; remove activeView state |
| Modify | `src/components/Sidebar.jsx` | Replace onNavigate with NavLink |
| Modify | `src/components/Topbar.jsx` | Add provider name + switch link |
| Modify | `src/components/PatientTable.jsx` | Filter by provider specialty |
| Modify | `src/utils/tools.js` | Add 4 IM tool definitions to runTool |
| Modify | `package.json` | Add react-router-dom dependency |

---

## Out of Scope

- Real authentication (Supabase auth, passwords, sessions)
- IM patient detail view (clicking a patient name)
- Provider-filtered chat (AI assistant sees all tools regardless of specialty)
- Any backend changes (MCP server, Cloudflare Worker, Supabase schema)

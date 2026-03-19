# Frontend Enhancement Design — ClinicalMind AI
**Date:** 2026-03-18
**Status:** Approved

---

## Overview

Redesign the ClinicalMind AI frontend dashboard with a dark "Clinical Command Center" theme, fixed sidebar navigation, enhanced stat cards with sparkline trends, SVG progress rings for KPI compliance, and an improved patient table with risk badges and inline KPI status indicators. Also removes all references to the 75% KPI compliance target.

---

## 1. KPI Compliance Target Removal

Remove `KPI_TARGET = 75` from `dataTransform.js` and every reference across the codebase:

| File | What to remove |
|---|---|
| `dataTransform.js` | Delete the `KPI_TARGET` export constant |
| `Dashboard.jsx` | Remove `KPI_TARGET` from the import line; remove `Target: {KPI_TARGET}%` from stat card `.sc-sub`; remove `<div className="kpi-target-tick" />` from KPI bar rows; change panel title from "KPI Compliance vs 75% Target" to "KPI Compliance"; replace `kpiColor = overallPct >= KPI_TARGET ? 'green' : 'amber'` with `kpiColor = overdueTotal === 0 ? 'green' : 'amber'`; the KPI bar loop (`const cls = pct >= KPI_TARGET ? 'meets' : 'below'`) is removed entirely as Section 5 replaces bars with rings |
| `tools.js` | Remove `KPI_TARGET` import; in `getKpiCompliance()` remove `meets_target` from both `by_kpi[n]` and the top-level return object, remove `overall_meets_target` and `target_pct` from the returned object; update the `TOOL_DEFS` description string from "Returns KPI completion rates vs 75% target." to "Returns KPI completion rates for each KPI." |
| `ChatPane.jsx` | In the system prompt remove the sentence "Note whether KPI compliance meets the 75% target"; keep the suggested prompt "What's our overall KPI compliance?" — it remains valid since `get_kpi_compliance` is unchanged |
| `index.css` | Delete the `.kpi-target-tick` rule block; delete `.kpi-bar-fill.meets`, `.kpi-bar-fill.below`, `.kpi-pct.meets`, `.kpi-pct.below` rules (replaced by ring CSS); delete old `.risk-badge.High/.Moderate/.Low` rules (replaced by `.risk-pill`) |

**KPI color rule going forward (no target):** A ring is green if `overdue === 0` for that KPI, amber if `overdue > 0`. The overall stat card is green if `overdueTotal === 0`, amber otherwise.

**Pre-existing bug (out of scope):** `Dashboard.jsx` `computeStats()` references `cutoff28` which is currently undeclared — this bug exists before this change and is not introduced by this work. Leave it unchanged.

---

## 2. Design System — Dark Theme

Replace all CSS custom properties in `index.css` `:root` with:

| Token | Value | Purpose |
|---|---|---|
| `--bg` | `#0f172a` | Page background |
| `--surface` | `#1e293b` | Card / panel background |
| `--surface-2` | `#0d1526` | Sidebar + topbar background |
| `--border` | `#334155` | Borders |
| `--border-light` | `#1e293b` | Row separators (intentionally same hex as `--surface`; kept as a separate token so it can diverge later) |
| `--text` | `#f8fafc` | Primary text |
| `--text-2` | `#cbd5e1` | Secondary text |
| `--text-3` | `#94a3b8` | Labels / captions |
| `--text-4` | `#475569` | Muted / disabled |
| `--ring-track` | `#1e3a4a` | SVG ring track (defined token, not a magic number) |
| `--primary` | `#3b82f6` | Interactive blue |
| `--primary-dark` | `#1d4ed8` | Hover blue |
| `--primary-900` | `#1e3a8a` | Active nav background |
| `--red` | `#ef4444` | High risk / urgent |
| `--red-dark` | `#dc2626` | Stripe gradient end |
| `--red-bg` | `rgba(239,68,68,0.15)` | Risk badge tint |
| `--amber` | `#f59e0b` | Warning / moderate |
| `--amber-dark` | `#d97706` | Stripe gradient end |
| `--amber-bg` | `rgba(245,158,11,0.15)` | Risk badge tint |
| `--green` | `#22c55e` | Compliant / success |
| `--green-dark` | `#16a34a` | Stripe gradient end |
| `--green-bg` | `rgba(34,197,94,0.15)` | Ring/badge tint |
| `--blue-bg` | `rgba(59,130,246,0.15)` | Blue icon tint |
| `--shadow-sm` | `0 1px 3px rgba(0,0,0,0.3)` | Card shadow |
| `--shadow` | `0 4px 6px rgba(0,0,0,0.4)` | Elevated shadow |
| `--radius` | `12px` | Card border radius |

---

## 3. App Shell — Sidebar Layout

**Delete `Header.jsx`** — fully replaced by `Sidebar.jsx` + `Topbar.jsx`.

In `App.jsx`, replace the current tab-based layout with:

```
<div className="app-shell">         {/* display:flex; height:100vh; overflow:hidden */}
  <Sidebar activeView={activeView} onNavigate={setActiveView} patients={patients} />
  <div className="main-area">       {/* flex:1; display:flex; flex-direction:column; overflow:hidden */}
    <Topbar status={status} />
    <div className="content-scroll"> {/* flex:1; overflow-y:auto; padding:16px 20px; background:var(--bg) */}
      {activeView === 'dashboard' && <Dashboard patients={patients} loading={loading} />}
      {activeView === 'patients'  && <PatientTable patients={patients} />}
      {activeView === 'chat'      && <ChatPane patients={patients} apiKey={apiKey} onNeedKey={() => setShowApiSetup(true)} />}
    </div>
  </div>
  {showApiSetup && <ApiSetupModal ... />}  {/* existing modal, dark-themed — see note below */}
</div>
```

`activeView` replaces `activeTab`. Default: `'dashboard'`.

**API key check:** In `Sidebar.jsx`, the "AI Assistant" nav item click handler:
```js
onClick={() => { if (!apiKey) { onNeedKey(); } else { onNavigate('chat'); } }}
```
`onNeedKey` is passed from `App.jsx` as `() => setShowApiSetup(true)` — same logic as current `handleTabChange`.

**API setup modal styles** (`index.css` `.api-setup`, `.api-input`, `.api-btn`, `.api-note`): update background to `var(--surface)`, text to `var(--text)`, input border to `var(--border)`, button to `var(--primary)`. Keep the modal overlay structure unchanged.

**Remove:** `<footer className="footer">` element from `App.jsx` and all `.footer` CSS rules from `index.css`.

### `Sidebar.jsx` — imports and CSS class names

Required imports:
```js
import { KPI_NAMES } from '../utils/dataTransform';
```

### `Sidebar.jsx` — CSS class names and rules

```css
.sidebar            { width:200px; flex-shrink:0; background:var(--surface-2); border-right:1px solid var(--border); display:flex; flex-direction:column; padding:20px 0; }
.sidebar-logo       { display:flex; align-items:center; gap:10px; padding:0 16px 24px; border-bottom:1px solid var(--border); }
.logo-mark          { width:32px; height:32px; background:linear-gradient(135deg,var(--primary),var(--primary-dark)); border-radius:8px; font-size:14px; font-weight:800; color:white; display:flex; align-items:center; justify-content:center; }
.logo-text          { font-size:12px; font-weight:700; color:var(--text); }
.logo-sub           { font-size:10px; color:var(--text-4); }
.sidebar-nav        { padding:16px 8px; flex:1; }
.nav-section-label  { font-size:9px; font-weight:600; color:var(--text-4); letter-spacing:1px; padding:0 8px; margin:12px 0 6px; display:block; }
.nav-item           { display:flex; align-items:center; gap:10px; padding:9px 10px; border-radius:8px; color:var(--text-4); font-size:12px; cursor:pointer; margin-bottom:2px; }
.nav-item.active    { background:var(--primary-900); color:#93c5fd; }
.nav-item.disabled  { cursor:default; opacity:0.4; pointer-events:none; }
.nav-dot            { width:8px; height:8px; border-radius:50%; background:var(--border); flex-shrink:0; }
.nav-item.active .nav-dot { background:var(--primary); box-shadow:0 0 0 3px rgba(59,130,246,0.2); }
.nav-badge          { margin-left:auto; background:var(--red); color:white; font-size:9px; font-weight:700; border-radius:10px; padding:1px 5px; }
.sidebar-footer     { padding:12px 16px; border-top:1px solid var(--border); font-size:10px; color:var(--text-4); display:flex; align-items:center; gap:6px; }
.status-dot         { width:6px; height:6px; border-radius:50%; background:var(--green); flex-shrink:0; }
```

**Nav structure:**

Section "MAIN":
- Dashboard → `onNavigate('dashboard')`
- Patients → `onNavigate('patients')` + `.nav-badge` showing `patients.filter(p => KPI_NAMES.some(k => p.kpis[k].overdue)).length`
- AI Assistant → `onNavigate('chat')` with apiKey check (see above)

Section "REPORTS":
- KPI Summary → `.nav-item.disabled`, no `onClick`
- Crisis Log → `.nav-item.disabled`, no `onClick`

Footer: `<div className="status-dot" />` + `"Live · Updated now"` (static string).

### `Topbar.jsx` — props and styles

Props: `{ status }` where `status = { state: 'ok'|'loading'|'error', msg: string }` — same object currently passed to `Header.jsx`.

```css
.topbar       { background:var(--surface-2); border-bottom:1px solid var(--border); padding:12px 20px; display:flex; align-items:center; justify-content:space-between; }
.topbar-left  { }
.topbar-title { font-size:15px; font-weight:700; color:var(--text); }
.topbar-sub   { font-size:11px; color:var(--text-4); margin-top:1px; }
.topbar-right { display:flex; align-items:center; gap:10px; }
.badge-pill   { background:var(--surface); border:1px solid var(--border); border-radius:20px; padding:4px 10px; font-size:10px; color:var(--text-3); display:flex; align-items:center; gap:5px; }
```

Left: title "Clinical Dashboard" + subtitle "Westchester County · ACT + CSP Programs".
Right: status pill (green dot + `status.msg`) + date pill (e.g. "Mar 18, 2026").

---

## 4. Stat Cards — Trend Badges & Sparklines

### Trend badge (top-right)

Static placeholder strings per card:

| Card | Text | Class |
|---|---|---|
| Total Patients | `↑ 3 wk` | `.trend-up` |
| High Risk | `— same` | `.trend-neutral` |
| Crisis 7D | `↓ 1 7d` | `.trend-down` |
| KPI Compliance | `↑ 4% mo` | `.trend-up` |

```css
.sc-trend       { font-size:10px; font-weight:600; display:flex; align-items:center; gap:2px; }
.trend-up       { color:var(--green); }
.trend-down     { color:var(--red); }
.trend-neutral  { color:var(--amber); }
```

### Sparkline (bottom of card)

Decorative static SVG, not data-driven. Fixed `points` per card:

| Card | SVG points (viewBox 0 0 120 20) |
|---|---|
| Total Patients | `0,15 20,13 40,14 60,10 80,11 100,8 120,6` |
| High Risk | `0,10 20,8 40,12 60,9 80,11 100,8 120,9` |
| Crisis 7D | `0,12 20,14 40,10 60,13 80,8 100,11 120,8` |
| KPI Compliance | `0,14 20,13 40,12 60,11 80,10 100,9 120,7` |

```css
.sc-sparkline { display:block; width:100%; height:20px; margin-top:8px; }
/* polyline: stroke = card accent color, stroke-width:1.5, opacity:0.6, fill:none */
```

### Icon area

`.sc-icon` becomes a 34×34px flex-center `<div>` with rounded corners. Background uses per-card tint token:

| Card | `background` |
|---|---|
| Total Patients | `var(--blue-bg)` |
| High Risk | `var(--red-bg)` |
| Crisis 7D | `var(--amber-bg)` |
| KPI Compliance | `var(--green-bg)` |

Emoji content (👥 ⚠️ 🚨 📋) unchanged.

```css
.sc-icon { width:34px; height:34px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:16px; flex-shrink:0; }
```

### Card bottom stripe

Replace current `::before` left-border stripe with `::after` bottom stripe:

```css
.stat-card::after { content:''; position:absolute; bottom:0; left:0; right:0; height:3px; border-radius:0 0 var(--radius) var(--radius); }
.stat-card.blue::after  { background:linear-gradient(90deg,var(--primary),var(--primary-dark)); }
.stat-card.red::after   { background:linear-gradient(90deg,var(--red),var(--red-dark)); }
.stat-card.amber::after { background:linear-gradient(90deg,var(--amber),var(--amber-dark)); }
.stat-card.green::after { background:linear-gradient(90deg,var(--green),var(--green-dark)); }
```

The `.sc-sub` for the KPI compliance card changes from `Target: {KPI_TARGET}%` to `overall across all KPIs`.

---

## 5. KPI Panel — SVG Progress Rings

Replace `.kpi-row` bar chart with a 3-column grid of SVG circular progress rings.

**Grid — 7th item centering:**
```css
.kpi-rings { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; justify-items:center; }
.kpi-ring-item:last-child { grid-column:2; grid-row:3; }
```

**`s` is the `computeStats(patients)` return value** — declared at the top of the `Dashboard` component as `const s = useMemo(() => computeStats(patients), [patients])` (already done in the current code; reference it the same way).

**Per-ring JSX:**
```jsx
{KPI_NAMES.map(k => {
  const { pct, overdue } = s.kpiStats[k];
  return (
    <div key={k} className="kpi-ring-item">
      <div className="ring-wrap">
        <svg width="52" height="52" viewBox="0 0 52 52">
          <circle cx="26" cy="26" r="20" fill="none" stroke="var(--ring-track)" strokeWidth="5"/>
          <circle cx="26" cy="26" r="20" fill="none"
            stroke={overdue === 0 ? 'var(--green)' : 'var(--amber)'}
            strokeWidth="5"
            strokeDasharray="125.6"
            strokeDashoffset={125.6 * (1 - pct / 100)}
            strokeLinecap="round"
            transform="rotate(-90 26 26)"/>
        </svg>
        <div className={`ring-pct ${overdue === 0 ? 'green' : 'amber'}`}>{pct}%</div>
      </div>
      <div className="ring-label">{KPI_DISPLAY[k]}</div>
    </div>
  );
})}
```

**CSS:**
```css
.kpi-ring-item  { display:flex; flex-direction:column; align-items:center; gap:4px; }
.ring-wrap      { position:relative; width:52px; height:52px; }
.ring-pct       { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:700; }
.ring-pct.green { color:var(--green); }
.ring-pct.amber { color:var(--amber); }
.ring-label     { font-size:9px; color:var(--text-4); font-weight:600; text-align:center; }
.panel-avg      { font-size:10px; background:var(--green-bg); color:var(--green); border-radius:4px; padding:2px 8px; font-weight:600; }
```

---

## 6. Patient Table — Risk Badges, KPI Dots, Recency

**Total columns: 7** — expand-chevron · Patient · Risk · Diagnosis · KPI Status · Last Contact · Provider. Two columns (PHQ-9, SSRS) are replaced by two new columns (Diagnosis, KPI Status), so the count stays at 7 and `colSpan={7}` on the detail/no-data rows requires no change — but note this is a column swap, not an unchanged layout.

**Sort state:** Change initial sort from `{ col:'phq9', dir:'desc' }` to `{ col:'name', dir:'asc' }`. Sortable columns and their sort expressions:

| Sort key | Expression |
|---|---|
| `name` | `p.name` (string, alphabetical) |
| `contact` | `p.days_since_last_contact ?? Infinity` (numeric, ascending = most recent first when `dir:'asc'`) |
| `overdue` | `KPI_NAMES.filter(k => p.kpis[k].overdue).length` (numeric) |

Remove `phq9` and `ssrs` from the sort switch. Risk and Diagnosis columns are not sortable.

**PHQ-9 and SSRS columns:** Removed from the main table. Remain visible in the PatientDetail expanded row (no changes to PatientDetail).

**Diagnosis value:** `p.diagnosis` string field.

### Risk badge

```jsx
<span className={`risk-pill ${p.risk_level.toLowerCase()}`}>● {p.risk_level}</span>
```

```css
.risk-pill          { display:inline-flex; align-items:center; gap:4px; font-size:9px; font-weight:700; border-radius:4px; padding:2px 7px; }
.risk-pill.high     { background:var(--red-bg); color:var(--red); }
.risk-pill.moderate { background:var(--amber-bg); color:var(--amber); }
.risk-pill.low      { background:var(--green-bg); color:var(--green); }
```

### KPI dot grid

```jsx
<div className="kpi-dot-row">
  {KPI_NAMES.map(k => (
    <div key={k} className={`kpi-sq ${p.kpis[k].overdue ? 'ov' : 'ok'}`} title={KPI_DISPLAY[k]} />
  ))}
</div>
```

```css
.kpi-dot-row { display:flex; gap:2px; }
.kpi-sq      { width:6px; height:6px; border-radius:1px; }
.kpi-sq.ok   { background:var(--green); }
.kpi-sq.ov   { background:var(--red); }
```

### Last Contact recency

| `days_since_last_contact` | Class | Color |
|---|---|---|
| ≤ 7 | `.contact-recent` | `var(--green)` |
| 8 – 30 | `.contact-warn` | `var(--amber)` |
| > 30 | `.contact-crit` | `var(--red)` |
| `null` | — | `var(--text-4)` |

Display: `"{n}d ago"` or `"—"` if null.

### Table dark styles

```css
table          { width:100%; border-collapse:collapse; }
thead th       { font-size:9px; font-weight:600; color:var(--text-4); letter-spacing:0.8px; padding:10px 16px; border-bottom:1px solid var(--border); text-align:left; }
tbody tr       { border-bottom:1px solid var(--border-light); cursor:pointer; }
tbody tr:hover { background:var(--bg); }
tbody td       { padding:10px 16px; font-size:11px; color:var(--text-2); }
.td-name       { font-weight:600; color:var(--text); }
```

---

## 7. Files Changed

| File | Change |
|---|---|
| `frontend/src/index.css` | Full dark token rewrite; sidebar/topbar/ring/badge/dot styles added; remove `.kpi-target-tick`, `.kpi-bar-fill.meets/below`, `.kpi-pct.meets/below`, `.tab-bar`, `.header`, `.footer`, `.risk-badge` (old), `.api-setup/*` dark-themed replacements |
| `frontend/src/App.jsx` | Replace tab nav + `<Header>` + `<footer>` with `app-shell` + `<Sidebar>` + `<Topbar>`; rename `activeTab`→`activeView`; move apiKey check into sidebar click handler |
| `frontend/src/components/Header.jsx` | **Delete** |
| `frontend/src/components/Sidebar.jsx` | **New file** |
| `frontend/src/components/Topbar.jsx` | **New file** |
| `frontend/src/components/Dashboard.jsx` | Stat cards: sparklines + trend badges + icon tints + bottom stripe; KPI panel: rings replacing bars; remove all `KPI_TARGET` references including import |
| `frontend/src/components/PatientTable.jsx` | Replace columns; risk-pill; kpi-dot-row; contact recency; change initial sort to `{col:'name',dir:'asc'}`; update sort keys |
| `frontend/src/utils/dataTransform.js` | Remove `KPI_TARGET` export |
| `frontend/src/utils/tools.js` | Remove `KPI_TARGET`; remove `meets_target`/`target_pct` from tool output; update description |
| `frontend/src/components/ChatPane.jsx` | Remove "Note whether KPI compliance meets the 75% target" from system prompt |

---

## 8. Known Regressions & Out of Scope

- **PatientDetail dark theme:** `PatientDetail.jsx` uses light-theme inline styles. With the global dark theme applied, the detail panel will appear with light backgrounds — this is a known visual regression, deferred to a follow-up iteration.
- **Mobile layout:** 200px fixed sidebar is desktop-only. Mobile breakpoints are future work.
- **Real sparkline/trend data:** Static decorative values this iteration.
- **REPORTS nav items** (KPI Summary, Crisis Log): disabled placeholders, future iteration.
- **Pre-existing `cutoff28` bug** in `computeStats()`: out of scope for this change.

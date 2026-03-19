# Frontend Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign ClinicalMind AI frontend with a dark Clinical Command Center theme — fixed sidebar, KPI progress rings, sparkline stat cards, risk badges, and removal of the 75% KPI compliance target.

**Architecture:** Replace the tab-based `App.jsx` layout with a fixed sidebar shell. New `Sidebar.jsx` and `Topbar.jsx` components replace `Header.jsx`. `Dashboard.jsx` gets sparklines + SVG progress rings. `PatientTable.jsx` gets new columns, risk-pill badges, and KPI dot grids. All CSS variables rewritten for dark theme.

**Tech Stack:** React 18, Vite 5, vanilla CSS custom properties (no UI library), Supabase.

---

## File Map

| Action | File | Responsibility |
|---|---|---|
| Modify | `frontend/src/index.css` | Dark token rewrite + all new component styles |
| Modify | `frontend/src/App.jsx` | Replace tab shell with sidebar shell |
| **Delete** | `frontend/src/components/Header.jsx` | Replaced by Sidebar + Topbar |
| **Create** | `frontend/src/components/Sidebar.jsx` | Fixed nav sidebar |
| **Create** | `frontend/src/components/Topbar.jsx` | Top bar with status + date |
| Modify | `frontend/src/components/Dashboard.jsx` | KPI rings, sparklines, trend badges |
| Modify | `frontend/src/components/PatientTable.jsx` | New columns, badges, dot grid, sort |
| Modify | `frontend/src/utils/dataTransform.js` | Remove `KPI_TARGET` export |
| Modify | `frontend/src/utils/tools.js` | Remove target fields from KPI tool |
| Modify | `frontend/src/components/ChatPane.jsx` | Remove 75% target language from system prompt |

---

## Task 1: Remove KPI Target from Data Layer

Cleanest first — no visual impact, just data.

**Files:**
- Modify: `frontend/src/utils/dataTransform.js`
- Modify: `frontend/src/utils/tools.js`
- Modify: `frontend/src/components/ChatPane.jsx`

- [ ] **Step 1: Remove `KPI_TARGET` export from dataTransform.js**

Open `frontend/src/utils/dataTransform.js`. Find and delete the line:
```js
export const KPI_TARGET = 75;
```

- [ ] **Step 2: Remove `KPI_TARGET` from tools.js**

Open `frontend/src/utils/tools.js`. Make these changes:

a) Remove `KPI_TARGET` from the import at the top:
```js
// Before:
import { KPI_NAMES, KPI_DISPLAY, KPI_TARGET } from './dataTransform';
// After:
import { KPI_NAMES, KPI_DISPLAY } from './dataTransform';
```

b) In `getKpiCompliance()`, remove `meets_target` from the per-KPI object:
```js
// Before:
by_kpi[n] = { total, compliant, overdue, compliance_pct, meets_target: compliance_pct >= KPI_TARGET };
// After:
by_kpi[n] = { total, compliant, overdue, compliance_pct };
```

c) Remove `overall_meets_target` and `target_pct` from the returned object:
```js
// Before:
return { overall_compliance_pct: overallPct, overall_meets_target: overallPct >= KPI_TARGET, target_pct: KPI_TARGET, total_patients, by_kpi };
// After:
return { overall_compliance_pct: overallPct, total_patients, by_kpi };
```

d) Update the `TOOL_DEFS` description for `get_kpi_compliance`:
```js
// Before:
description: 'Returns KPI completion rates vs 75% target.'
// After:
description: 'Returns KPI completion rates for each KPI.'
```

- [ ] **Step 3: Remove 75% target language from ChatPane.jsx**

Open `frontend/src/components/ChatPane.jsx`. In the system prompt string, find and delete the sentence:
```
Note whether KPI compliance meets the 75% target.
```
Leave all other system prompt content unchanged.

- [ ] **Step 4: Verify dev server starts without errors**

```bash
cd frontend && npm run dev
```
Expected: Server starts, no console errors about `KPI_TARGET` being undefined.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/utils/dataTransform.js frontend/src/utils/tools.js frontend/src/components/ChatPane.jsx
git commit -m "feat: remove KPI 75% compliance target from data layer and prompts"
```

---

## Task 2: Rewrite CSS Design Tokens (Dark Theme)

Replaces all `:root` tokens. No component changes yet — this will visually break the UI temporarily until Task 3+.

**Files:**
- Modify: `frontend/src/index.css`

- [ ] **Step 1: Replace the `:root` block**

Open `frontend/src/index.css`. Replace the entire `:root { ... }` block with:

```css
:root {
  --bg:           #0f172a;
  --surface:      #1e293b;
  --surface-2:    #0d1526;
  --border:       #334155;
  --border-light: #1e293b; /* intentionally same as --surface; separate token for future divergence */
  --text:         #f8fafc;
  --text-2:       #cbd5e1;
  --text-3:       #94a3b8;
  --text-4:       #475569;
  --ring-track:   #1e3a4a;
  --primary:      #3b82f6;
  --primary-dark: #1d4ed8;
  --primary-900:  #1e3a8a;
  --red:          #ef4444;
  --red-dark:     #dc2626;
  --red-bg:       rgba(239,68,68,0.15);
  --amber:        #f59e0b;
  --amber-dark:   #d97706;
  --amber-bg:     rgba(245,158,11,0.15);
  --green:        #22c55e;
  --green-dark:   #16a34a;
  --green-bg:     rgba(34,197,94,0.15);
  --blue-bg:      rgba(59,130,246,0.15);
  --shadow-sm:    0 1px 3px rgba(0,0,0,0.3);
  --shadow:       0 4px 6px rgba(0,0,0,0.4);
  --radius:       12px;
}
```

- [ ] **Step 2: Remove stale CSS rules**

In `index.css`, delete the following rule blocks entirely (they are replaced in later tasks):
- `.kpi-target-tick { ... }`
- `.kpi-bar-fill.meets { ... }` and `.kpi-bar-fill.below { ... }`
- `.kpi-pct.meets { ... }` and `.kpi-pct.below { ... }`
- `.risk-badge { ... }`, `.risk-badge.High { ... }`, `.risk-badge.Moderate { ... }`, `.risk-badge.Low { ... }`
- `.tab-bar { ... }` and all `.tab-btn { ... }` rules
- `.header { ... }` and all `.header-*` rules
- `.footer { ... }`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/index.css
git commit -m "feat: dark theme CSS tokens and remove stale rules"
```

---

## Task 3: Create Sidebar.jsx

**Files:**
- Create: `frontend/src/components/Sidebar.jsx`

- [ ] **Step 1: Create the file**

Create `frontend/src/components/Sidebar.jsx`:

```jsx
import { KPI_NAMES } from '../utils/dataTransform';

export default function Sidebar({ activeView, onNavigate, onNeedKey, apiKey, patients }) {
  const overdueBadge = patients
    ? patients.filter(p => KPI_NAMES.some(k => p.kpis[k].overdue)).length
    : 0;

  function handleChat() {
    if (!apiKey) { onNeedKey(); } else { onNavigate('chat'); }
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-mark">CM</div>
        <div>
          <div className="logo-text">ClinicalMind</div>
          <div className="logo-sub">Clinical AI</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <span className="nav-section-label">MAIN</span>
        <div
          className={`nav-item${activeView === 'dashboard' ? ' active' : ''}`}
          onClick={() => onNavigate('dashboard')}
        >
          <div className="nav-dot" />
          Dashboard
        </div>
        <div
          className={`nav-item${activeView === 'patients' ? ' active' : ''}`}
          onClick={() => onNavigate('patients')}
        >
          <div className="nav-dot" />
          Patients
          {overdueBadge > 0 && <span className="nav-badge">{overdueBadge}</span>}
        </div>
        <div
          className={`nav-item${activeView === 'chat' ? ' active' : ''}`}
          onClick={handleChat}
        >
          <div className="nav-dot" />
          AI Assistant
        </div>

        <span className="nav-section-label">REPORTS</span>
        <div className="nav-item disabled">
          <div className="nav-dot" />
          KPI Summary
        </div>
        <div className="nav-item disabled">
          <div className="nav-dot" />
          Crisis Log
        </div>
      </nav>

      <div className="sidebar-footer">
        <div className="status-dot" />
        Live · Updated now
      </div>
    </aside>
  );
}
```

- [ ] **Step 2: Add Sidebar CSS to index.css**

Append to `frontend/src/index.css`:

```css
/* ── Sidebar ─────────────────────────────────────────── */
.sidebar { width:200px; flex-shrink:0; background:var(--surface-2); border-right:1px solid var(--border); display:flex; flex-direction:column; padding:20px 0; }
.sidebar-logo { display:flex; align-items:center; gap:10px; padding:0 16px 24px; border-bottom:1px solid var(--border); }
.logo-mark { width:32px; height:32px; background:linear-gradient(135deg,var(--primary),var(--primary-dark)); border-radius:8px; font-size:14px; font-weight:800; color:white; display:flex; align-items:center; justify-content:center; }
.logo-text { font-size:12px; font-weight:700; color:var(--text); }
.logo-sub  { font-size:10px; color:var(--text-4); }
.sidebar-nav { padding:16px 8px; flex:1; }
.nav-section-label { font-size:9px; font-weight:600; color:var(--text-4); letter-spacing:1px; padding:0 8px; margin:12px 0 6px; display:block; }
.nav-item { display:flex; align-items:center; gap:10px; padding:9px 10px; border-radius:8px; color:var(--text-4); font-size:12px; cursor:pointer; margin-bottom:2px; }
.nav-item.active { background:var(--primary-900); color:#93c5fd; }
.nav-item.disabled { cursor:default; opacity:0.4; pointer-events:none; }
.nav-dot { width:8px; height:8px; border-radius:50%; background:var(--border); flex-shrink:0; }
.nav-item.active .nav-dot { background:var(--primary); box-shadow:0 0 0 3px rgba(59,130,246,0.2); }
.nav-badge { margin-left:auto; background:var(--red); color:white; font-size:9px; font-weight:700; border-radius:10px; padding:1px 5px; }
.sidebar-footer { padding:12px 16px; border-top:1px solid var(--border); font-size:10px; color:var(--text-4); display:flex; align-items:center; gap:6px; }
.status-dot { width:6px; height:6px; border-radius:50%; background:var(--green); flex-shrink:0; }
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/Sidebar.jsx frontend/src/index.css
git commit -m "feat: add Sidebar component with dark nav, badge, disabled reports"
```

---

## Task 4: Create Topbar.jsx

**Files:**
- Create: `frontend/src/components/Topbar.jsx`

- [ ] **Step 1: Create the file**

Create `frontend/src/components/Topbar.jsx`:

```jsx
export default function Topbar({ status }) {
  const date = new Date().toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' });
  const isOk = status?.state === 'ok';

  return (
    <div className="topbar">
      <div className="topbar-left">
        <div className="topbar-title">Clinical Dashboard</div>
        <div className="topbar-sub">Westchester County · ACT + CSP Programs</div>
      </div>
      <div className="topbar-right">
        <div className="badge-pill">
          <span style={{ color: isOk ? 'var(--green)' : 'var(--amber)' }}>●</span>
          {status?.msg || 'Connecting…'}
        </div>
        <div className="badge-pill">{date}</div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Add Topbar CSS to index.css**

Append to `frontend/src/index.css`:

```css
/* ── Topbar ──────────────────────────────────────────── */
.topbar       { background:var(--surface-2); border-bottom:1px solid var(--border); padding:12px 20px; display:flex; align-items:center; justify-content:space-between; }
.topbar-left  { }
.topbar-title { font-size:15px; font-weight:700; color:var(--text); }
.topbar-sub   { font-size:11px; color:var(--text-4); margin-top:1px; }
.topbar-right { display:flex; align-items:center; gap:10px; }
.badge-pill   { background:var(--surface); border:1px solid var(--border); border-radius:20px; padding:4px 10px; font-size:10px; color:var(--text-3); display:flex; align-items:center; gap:5px; }
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/Topbar.jsx frontend/src/index.css
git commit -m "feat: add Topbar component with status pill and date"
```

---

## Task 5: Rewire App.jsx — Sidebar Shell

**Files:**
- Modify: `frontend/src/App.jsx`
- Delete: `frontend/src/components/Header.jsx`

- [ ] **Step 1: Update App.jsx imports**

At the top of `frontend/src/App.jsx`, replace the `Header` import with `Sidebar` and `Topbar`:

```js
// Remove:
import Header from './components/Header';
// Add:
import Sidebar from './components/Sidebar';
import Topbar  from './components/Topbar';
```

- [ ] **Step 2: Replace tab state with activeView**

Find `const [tab, setTab] = useState('dashboard')` and rename:
```js
const [activeView, setActiveView] = useState('dashboard');
```

Update all references to `tab` and `setTab` throughout `App.jsx` to `activeView` and `setActiveView`.

Remove the `handleTabChange` function entirely. The Sidebar handles navigation and the API key check directly via `onNeedKey` prop.

- [ ] **Step 3: Replace the JSX layout**

Replace the current return JSX (the `<div className="app">` block containing `<Header>`, `.tab-bar`, tab panels, and `<footer>`) with:

```jsx
return (
  <div className="app-shell">
    <Sidebar
      activeView={activeView}
      onNavigate={setActiveView}
      onNeedKey={() => setShowApiSetup(true)}
      apiKey={apiKey}
      patients={patients}
    />
    <div className="main-area">
      <Topbar status={status} />
      <div className="content-scroll">
        {activeView === 'dashboard' && <Dashboard patients={patients} loading={loading} />}
        {activeView === 'patients'  && <PatientTable patients={patients} />}
        {activeView === 'chat'      && (
          <ChatPane
            patients={patients}
            apiKey={apiKey}
            onNeedKey={() => setShowApiSetup(true)}
          />
        )}
      </div>
    </div>
    {showApiSetup && (
      /* PASTE THE EXISTING showApiSetup JSX BLOCK HERE VERBATIM */
      /* It currently lives outside the tab nav in App.jsx. Move it here. */
      /* Do NOT use this comment literally — replace with the real JSX from the file. */
    )}
  </div>
);
```

> **Note:** Open the current `App.jsx` and find the `{showApiSetup && ( ... )}` block. Copy it exactly and paste it in place of the comment placeholder above. Do not rewrite or simplify it. The modal overlay should appear on top of the new shell layout just as it did before.

- [ ] **Step 4: Add app-shell CSS to index.css**

Append to `frontend/src/index.css`:

```css
/* ── App shell ───────────────────────────────────────── */
.app-shell     { display:flex; height:100vh; overflow:hidden; background:var(--bg); }
.main-area     { flex:1; display:flex; flex-direction:column; overflow:hidden; }
.content-scroll{ flex:1; overflow-y:auto; padding:16px 20px; background:var(--bg); }
```

Also update the existing `.api-setup` styles in `index.css` for the dark theme:
```css
.api-setup   { background:var(--surface); color:var(--text); border:1px solid var(--border); }
.api-input   { background:var(--bg); color:var(--text); border:1px solid var(--border); }
.api-btn     { background:var(--primary); color:white; }
.api-note    { color:var(--text-4); }
```

- [ ] **Step 5: Delete Header.jsx**

```bash
rm frontend/src/components/Header.jsx
```

- [ ] **Step 6: Verify in browser**

```bash
cd frontend && npm run dev
```

Open http://localhost:5173. Expected: dark sidebar on left, topbar across top, dashboard content in main area. No console errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/App.jsx frontend/src/index.css
git rm frontend/src/components/Header.jsx
git commit -m "feat: replace tab nav with sidebar shell, delete Header"
```

---

## Task 6: Enhance Dashboard — Stat Cards

**Files:**
- Modify: `frontend/src/components/Dashboard.jsx`
- Modify: `frontend/src/index.css`

- [ ] **Step 1: Remove KPI_TARGET from Dashboard.jsx import**

In `frontend/src/components/Dashboard.jsx`, remove `KPI_TARGET` from the import line:
```js
// Before:
import { KPI_NAMES, KPI_DISPLAY, KPI_TARGET } from '../utils/dataTransform';
// After:
import { KPI_NAMES, KPI_DISPLAY } from '../utils/dataTransform';
```

- [ ] **Step 2: Fix kpiColor logic**

Find `const kpiColor = s.overallPct >= KPI_TARGET ? 'green' : 'amber'` and replace:
```js
const overdueTotal = KPI_NAMES.reduce((sum, k) => sum + s.kpiStats[k].overdue, 0);
const kpiColor = overdueTotal === 0 ? 'green' : 'amber';
```

Note: `computeStats()` does not return `overdueTotal` directly — derive it from `s.kpiStats` as above.

- [ ] **Step 3: Add CARD_META constant**

At the top of the Dashboard component (after the imports), add:

```js
const CARD_META = {
  patients:   { trend:'↑ 3 wk',  trendCls:'trend-up',      sparkPts:'0,15 20,13 40,14 60,10 80,11 100,8 120,6', stroke:'var(--primary)' },
  high_risk:  { trend:'— same',  trendCls:'trend-neutral',  sparkPts:'0,10 20,8 40,12 60,9 80,11 100,8 120,9',  stroke:'var(--red)'     },
  crisis_7d:  { trend:'↓ 1 7d',  trendCls:'trend-down',    sparkPts:'0,12 20,14 40,10 60,13 80,8 100,11 120,8', stroke:'var(--amber)'   },
  kpi:        { trend:'↑ 4% mo', trendCls:'trend-up',      sparkPts:'0,14 20,13 40,12 60,11 80,10 100,9 120,7', stroke:'var(--green)'   },
};
```

- [ ] **Step 4: Rewrite the four stat card JSX blocks**

Replace each `.stat-card` JSX block with the new pattern. Example for the Patients card (repeat for each):

**`computeStats()` returns:** `{ total, byRisk: { High, Moderate, Low }, kpiStats, overallPct, activeCrisis, alerts }`

Use these actual fields in the stat card JSX:

```jsx
<div className="stat-card blue">
  <div className="sc-top">
    <div className="sc-icon" style={{ background:'var(--blue-bg)' }}>👥</div>
    <span className={`sc-trend ${CARD_META.patients.trendCls}`}>{CARD_META.patients.trend}</span>
  </div>
  <div className="sc-label">TOTAL PATIENTS</div>
  <div className="sc-value">{s.total}</div>
  <div className="sc-sub">{s.byRisk.High} high · {s.byRisk.Moderate} moderate</div>
  <svg className="sc-sparkline" viewBox="0 0 120 20" preserveAspectRatio="none">
    <polyline points={CARD_META.patients.sparkPts}
      fill="none" stroke={CARD_META.patients.stroke} strokeWidth="1.5" opacity="0.6"/>
  </svg>
</div>

<div className="stat-card red">
  <div className="sc-top">
    <div className="sc-icon" style={{ background:'var(--red-bg)' }}>⚠️</div>
    <span className={`sc-trend ${CARD_META.high_risk.trendCls}`}>{CARD_META.high_risk.trend}</span>
  </div>
  <div className="sc-label">HIGH RISK</div>
  <div className="sc-value" style={{ color:'var(--red)' }}>{s.byRisk.High}</div>
  <div className="sc-sub">{s.alerts.filter(a => a.level === 'red').length} need review</div>
  <svg className="sc-sparkline" viewBox="0 0 120 20" preserveAspectRatio="none">
    <polyline points={CARD_META.high_risk.sparkPts}
      fill="none" stroke={CARD_META.high_risk.stroke} strokeWidth="1.5" opacity="0.6"/>
  </svg>
</div>

<div className="stat-card amber">
  <div className="sc-top">
    <div className="sc-icon" style={{ background:'var(--amber-bg)' }}>🚨</div>
    <span className={`sc-trend ${CARD_META.crisis_7d.trendCls}`}>{CARD_META.crisis_7d.trend}</span>
  </div>
  <div className="sc-label">CRISIS EVENTS (7D)</div>
  <div className="sc-value" style={{ color:'var(--amber)' }}>{s.activeCrisis}</div>
  <div className="sc-sub">active unresolved events</div>
  <svg className="sc-sparkline" viewBox="0 0 120 20" preserveAspectRatio="none">
    <polyline points={CARD_META.crisis_7d.sparkPts}
      fill="none" stroke={CARD_META.crisis_7d.stroke} strokeWidth="1.5" opacity="0.6"/>
  </svg>
</div>

<div className={`stat-card ${kpiColor}`}>
  <div className="sc-top">
    <div className="sc-icon" style={{ background:'var(--green-bg)' }}>📋</div>
    <span className={`sc-trend ${CARD_META.kpi.trendCls}`}>{CARD_META.kpi.trend}</span>
  </div>
  <div className="sc-label">KPI COMPLIANCE</div>
  <div className={`sc-value ${kpiColor}`}>{s.overallPct}%</div>
  <div className="sc-sub">overall across all KPIs</div>
  <svg className="sc-sparkline" viewBox="0 0 120 20" preserveAspectRatio="none">
    <polyline points={CARD_META.kpi.sparkPts}
      fill="none" stroke={CARD_META.kpi.stroke} strokeWidth="1.5" opacity="0.6"/>
  </svg>
</div>
```

- [ ] **Step 5: Update stat card CSS in index.css**

Find the existing `.stat-card` rules and replace/update:

```css
/* ── Stat cards ──────────────────────────────────────── */
.stat-grid    { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:16px; }
.stat-card    { background:var(--surface); border-radius:var(--radius); padding:16px; border:1px solid var(--border); position:relative; overflow:hidden; }
.stat-card::after { content:''; position:absolute; bottom:0; left:0; right:0; height:3px; border-radius:0 0 var(--radius) var(--radius); }
.stat-card.blue::after  { background:linear-gradient(90deg,var(--primary),var(--primary-dark)); }
.stat-card.red::after   { background:linear-gradient(90deg,var(--red),var(--red-dark)); }
.stat-card.amber::after { background:linear-gradient(90deg,var(--amber),var(--amber-dark)); }
.stat-card.green::after { background:linear-gradient(90deg,var(--green),var(--green-dark)); }
.sc-top    { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:10px; }
.sc-icon   { width:34px; height:34px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:16px; flex-shrink:0; }
.sc-trend  { font-size:10px; font-weight:600; display:flex; align-items:center; gap:2px; }
.trend-up      { color:var(--green); }
.trend-down    { color:var(--red); }
.trend-neutral { color:var(--amber); }
.sc-label  { font-size:10px; color:var(--text-4); font-weight:600; letter-spacing:0.3px; margin-bottom:4px; }
.sc-value  { font-size:26px; font-weight:800; color:var(--text); line-height:1; margin-bottom:4px; }
.sc-sub    { font-size:10px; color:var(--text-4); }
.sc-sparkline { display:block; width:100%; height:20px; margin-top:8px; }
```

- [ ] **Step 6: Verify cards render**

```bash
cd frontend && npm run dev
```

Open http://localhost:5173. Expected: 4 dark stat cards with sparklines and trend badges in the dashboard.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/Dashboard.jsx frontend/src/index.css
git commit -m "feat: stat cards with sparklines, trend badges, dark theme"
```

---

## Task 7: Replace KPI Bars with Progress Rings

**Files:**
- Modify: `frontend/src/components/Dashboard.jsx`
- Modify: `frontend/src/index.css`

- [ ] **Step 1: Replace the KPI panel JSX in Dashboard.jsx**

Find the `<div className="panel">` block that contains `.kpi-row` elements and replace the entire inner content with:

```jsx
<div className="panel">
  <div className="panel-header">
    <span className="panel-title">KPI COMPLIANCE</span>
    <span className="panel-avg">{s.overallPct}% avg</span>
  </div>
  <div className="kpi-rings">
    {KPI_NAMES.map((k, i) => {
      const { pct, overdue } = s.kpiStats[k];
      const circumference = 125.6;
      const offset = circumference * (1 - pct / 100);
      const isLast = i === KPI_NAMES.length - 1;
      return (
        <div key={k} className={`kpi-ring-item${isLast ? ' last' : ''}`}>
          <div className="ring-wrap">
            <svg width="52" height="52" viewBox="0 0 52 52">
              <circle cx="26" cy="26" r="20" fill="none" stroke="var(--ring-track)" strokeWidth="5"/>
              <circle cx="26" cy="26" r="20" fill="none"
                stroke={overdue === 0 ? 'var(--green)' : 'var(--amber)'}
                strokeWidth="5"
                strokeDasharray={circumference}
                strokeDashoffset={offset}
                strokeLinecap="round"
                transform="rotate(-90 26 26)"/>
            </svg>
            <div className={`ring-pct ${overdue === 0 ? 'green' : 'amber'}`}>{pct}%</div>
          </div>
          <div className="ring-label">{KPI_DISPLAY[k]}</div>
        </div>
      );
    })}
  </div>
</div>
```

> **Note:** `s.kpiStats[k].overdue` is the count of patients with that KPI overdue (from `computeStats()`). If the existing field is named differently (e.g. `kpiStats[k].overdueCount`), use the actual field name.

- [ ] **Step 2: Add KPI rings CSS to index.css**

Append to `frontend/src/index.css`:

```css
/* ── KPI rings ───────────────────────────────────────── */
.panel-header   { display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; }
.panel-title    { font-size:11px; font-weight:700; color:var(--text-3); letter-spacing:0.5px; }
.panel-avg      { font-size:10px; background:var(--green-bg); color:var(--green); border-radius:4px; padding:2px 8px; font-weight:600; }
.kpi-rings      { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; justify-items:center; }
.kpi-ring-item  { display:flex; flex-direction:column; align-items:center; gap:4px; }
.kpi-ring-item.last { grid-column:2; grid-row:3; }
.ring-wrap      { position:relative; width:52px; height:52px; }
.ring-pct       { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:700; }
.ring-pct.green { color:var(--green); }
.ring-pct.amber { color:var(--amber); }
.ring-label     { font-size:9px; color:var(--text-4); font-weight:600; text-align:center; }
```

- [ ] **Step 3: Verify rings render**

```bash
cd frontend && npm run dev
```

Expected: KPI panel shows 7 progress rings in a 3-column grid (3 / 3 / 1 centered).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/Dashboard.jsx frontend/src/index.css
git commit -m "feat: KPI progress rings replacing bar chart, avg badge"
```

---

## Task 8: Rewrite PatientTable — New Columns, Badges, Sort

**Files:**
- Modify: `frontend/src/components/PatientTable.jsx`
- Modify: `frontend/src/index.css`

- [ ] **Step 1: Update initial sort state**

In `frontend/src/components/PatientTable.jsx`, find:
```js
const [sort, setSort] = useState({ col:'phq9', dir:'desc' });
```
Change to:
```js
const [sort, setSort] = useState({ col:'name', dir:'asc' });
```

- [ ] **Step 2: Update the sort function**

Find the sort/comparison logic (the `sorted` derivation using the `sort.col` switch). Replace the switch cases with:

```js
const sorted = [...patients].sort((a, b) => {
  let av, bv;
  switch (sort.col) {
    case 'name':
      av = a.name?.toLowerCase() ?? '';
      bv = b.name?.toLowerCase() ?? '';
      break;
    case 'contact':
      av = a.days_since_last_contact ?? Infinity;
      bv = b.days_since_last_contact ?? Infinity;
      break;
    case 'overdue':
      av = KPI_NAMES.filter(k => a.kpis[k].overdue).length;
      bv = KPI_NAMES.filter(k => b.kpis[k].overdue).length;
      break;
    default:
      return 0;
  }
  if (av < bv) return sort.dir === 'asc' ? -1 : 1;
  if (av > bv) return sort.dir === 'asc' ?  1 : -1;
  return 0;
});
```

Also add `KPI_NAMES` to the import from `dataTransform` if not already there.

- [ ] **Step 3: Rewrite the table header**

Replace the `<thead>` block with:

```jsx
<thead>
  <tr>
    <th style={{ width:28 }}></th>
    <th className={sort.col==='name'?'sort-active':''} onClick={()=>handleSort('name')}>PATIENT</th>
    <th>RISK</th>
    <th>DIAGNOSIS</th>
    <th className={sort.col==='overdue'?'sort-active':''} onClick={()=>handleSort('overdue')}>KPI STATUS</th>
    <th className={sort.col==='contact'?'sort-active':''} onClick={()=>handleSort('contact')}>LAST CONTACT</th>
    <th>PROVIDER</th>
  </tr>
</thead>
```

- [ ] **Step 4: Rewrite the patient row JSX**

Replace the `<tr>` inside `sorted.map(p => ...)` (main patient row, not the detail expand row) with:

```jsx
<tr key={p.id} onClick={() => toggleExpand(p.id)}>
  <td style={{ textAlign:'center', color:'var(--text-4)', fontSize:10 }}>
    {expanded === p.id ? '▼' : '▶'}
  </td>
  <td className="td-name">{p.name}</td>
  <td>
    <span className={`risk-pill ${p.risk_level?.toLowerCase()}`}>● {p.risk_level}</span>
  </td>
  <td style={{ color:'var(--text-3)', fontSize:11 }}>{p.diagnosis || '—'}</td>
  <td>
    <div className="kpi-dot-row">
      {KPI_NAMES.map(k => (
        <div key={k} className={`kpi-sq ${p.kpis[k].overdue ? 'ov' : 'ok'}`} title={KPI_DISPLAY[k]} />
      ))}
    </div>
  </td>
  <td>
    {p.days_since_last_contact == null
      ? <span style={{ color:'var(--text-4)' }}>—</span>
      : <span className={
          p.days_since_last_contact <= 7  ? 'contact-recent' :
          p.days_since_last_contact <= 30 ? 'contact-warn'   : 'contact-crit'
        }>{p.days_since_last_contact}d ago</span>
    }
  </td>
  <td style={{ color:'var(--text-4)', fontSize:11 }}>{p.provider || '—'}</td>
</tr>
```

Update `colSpan` on the detail/no-data rows from whatever it currently is to `7`.

- [ ] **Step 5: Add new table CSS to index.css**

Append to `frontend/src/index.css`:

```css
/* ── Patient table ───────────────────────────────────── */
table          { width:100%; border-collapse:collapse; }
thead th       { font-size:9px; font-weight:600; color:var(--text-4); letter-spacing:0.8px; padding:10px 16px; border-bottom:1px solid var(--border); text-align:left; cursor:default; }
thead th.sort-active { color:var(--primary); cursor:pointer; }
thead th[onclick] { cursor:pointer; }
tbody tr       { border-bottom:1px solid var(--border-light); cursor:pointer; }
tbody tr:hover { background:var(--bg); }
tbody td       { padding:10px 16px; font-size:11px; color:var(--text-2); }
.td-name       { font-weight:600; color:var(--text); }

.risk-pill          { display:inline-flex; align-items:center; gap:4px; font-size:9px; font-weight:700; border-radius:4px; padding:2px 7px; }
.risk-pill.high     { background:var(--red-bg);   color:var(--red);   }
.risk-pill.moderate { background:var(--amber-bg); color:var(--amber); }
.risk-pill.low      { background:var(--green-bg); color:var(--green); }

.kpi-dot-row { display:flex; gap:2px; }
.kpi-sq      { width:6px; height:6px; border-radius:1px; }
.kpi-sq.ok   { background:var(--green); }
.kpi-sq.ov   { background:var(--red);   }

.contact-recent { color:var(--green); }
.contact-warn   { color:var(--amber); }
.contact-crit   { color:var(--red);   }
```

- [ ] **Step 6: Verify table renders**

```bash
cd frontend && npm run dev
```

Expected: Patient table shows new columns — Risk pills (colored), Diagnosis text, 7 KPI dots per row, contact recency coloring.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/PatientTable.jsx frontend/src/index.css
git commit -m "feat: patient table with risk pills, KPI dot grid, contact recency, updated sort"
```

---

## Task 9: Build and Smoke Test

- [ ] **Step 1: Run the Vite build**

```bash
cd frontend && npm run build
```

Expected: Build succeeds with no errors. Output goes to `../docs/` (per `vite.config.js`).

- [ ] **Step 2: Manual smoke test — Dashboard**

Open http://localhost:5173 (or re-run `npm run dev`). Check:
- [ ] Dark sidebar visible on left with 5 nav items (3 active, 2 disabled/faded)
- [ ] "Patients" badge shows correct count of patients with ≥1 overdue KPI
- [ ] Topbar shows "Clinical Dashboard" title, status pill, date
- [ ] 4 stat cards visible with sparklines and trend badges
- [ ] KPI panel shows 7 rings (3 / 3 / 1 layout), no "75% target" anywhere
- [ ] Clicking Dashboard / Patients / AI Assistant in sidebar switches views

- [ ] **Step 3: Manual smoke test — Patient Table**

Click "Patients" in sidebar:
- [ ] Table shows columns: (chevron) · Patient · Risk · Diagnosis · KPI Status · Last Contact · Provider
- [ ] Risk column shows colored pills (● High, ● Moderate, ● Low)
- [ ] KPI Status shows 7 small colored squares per row
- [ ] Last Contact shows colored "Xd ago" text
- [ ] Clicking a patient row expands the PatientDetail panel
- [ ] Clicking column headers for Patient / KPI Status / Last Contact sorts

- [ ] **Step 4: Manual smoke test — AI Assistant**

Click "AI Assistant" in sidebar:
- [ ] If no API key: API key prompt appears
- [ ] If API key set: Chat pane loads with no mentions of "75% target"

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: frontend enhancement complete — dark theme, sidebar, rings, badges"
```

---

## Known Regressions (deferred)

- **PatientDetail modal** uses light-theme inline styles and will render with light backgrounds against the dark page — visual regression, deferred to follow-up.
- **Mobile layout** — 200px fixed sidebar breaks narrow screens. Deferred.
- **Sparkline / trend data** — static decorative values; real delta calculations deferred.
- **KPI Summary / Crisis Log** nav items — disabled placeholders; content deferred.

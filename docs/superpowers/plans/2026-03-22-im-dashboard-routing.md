# IM Dashboard Routing — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Route BH providers to the existing dashboard and IM providers to a new disease-panel dashboard, gated by a two-step mock provider picker.

**Architecture:** Add `react-router-dom` v6 for URL-based routing. A new `ProviderContext` (mirrors `ThemeContext`) stores the selected provider in `localStorage`. A `ProviderPicker` overlay gates entry. `Dashboard.jsx` is renamed to `BHDashboard.jsx`; a new `IMDashboard.jsx` renders three chronic disease panels from a JS mock data module (`imMockData.js`) that mirrors the Python IM adapter.

**Tech Stack:** React 18, Vite, react-router-dom v6, Vitest (unit tests for `imMockData.js`), no other new dependencies.

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `frontend/package.json` | Add `react-router-dom`, `vitest` |
| Create | `frontend/src/ProviderContext.jsx` | Provider identity context + localStorage |
| Create | `frontend/src/utils/imMockData.js` | JS mirror of Python IM adapter — 4 exported functions |
| Create | `frontend/src/utils/imMockData.test.js` | Vitest unit tests for imMockData.js |
| Create | `frontend/src/components/ProviderPicker.jsx` | Two-step specialty + provider picker overlay |
| Rename | `frontend/src/components/Dashboard.jsx` → `BHDashboard.jsx` | Name only, no logic change |
| Create | `frontend/src/components/IMDashboard.jsx` | IM dashboard: 3 stat cards + 3 disease panels |
| Modify | `frontend/src/App.jsx` | BrowserRouter, Routes, ProviderContext, ProviderPicker |
| Modify | `frontend/src/components/Sidebar.jsx` | NavLink routing, BH-only overdue badge guard |
| Modify | `frontend/src/components/Topbar.jsx` | Dynamic subtitle, provider name + switch link |
| Modify | `frontend/src/components/PatientTable.jsx` | Specialty-aware data source + column guard |
| Modify | `frontend/src/utils/tools.js` | 4 IM tool defs + runTool cases |

---

## Task 1: Install dependencies and configure Vitest

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/vite.config.js` (add test config)

- [ ] **Step 1: Install react-router-dom and vitest**

```bash
cd frontend
npm install react-router-dom
npm install -D vitest
```

- [ ] **Step 2: Add test script and vitest config to package.json**

In `frontend/package.json`, add `"test": "vitest run"` to scripts:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build && touch ../docs/.nojekyll",
    "preview": "vite preview",
    "test": "vitest run"
  }
}
```

- [ ] **Step 3: Add vitest config to vite.config.js**

Read the existing `vite.config.js` first. Add a `test` block:

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'node',
  },
})
```

- [ ] **Step 4: Verify vitest runs (no tests yet)**

```bash
cd frontend && npm test
```

Expected: `No test files found` or `0 tests`.

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vite.config.js
git commit -m "chore: add react-router-dom and vitest"
```

---

## Task 2: Create ProviderContext

**Files:**
- Create: `frontend/src/ProviderContext.jsx`

Pattern: mirror `frontend/src/ThemeContext.jsx` exactly — same structure, different state.

- [ ] **Step 1: Write ProviderContext.jsx**

```jsx
// frontend/src/ProviderContext.jsx
import { createContext, useContext, useState } from 'react';

const ProviderContext = createContext(null);

const STORAGE_KEY = 'cm_provider';

function loadStored() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function ProviderProvider({ children }) {
  const [provider, setProviderState] = useState(loadStored);

  function setProvider(p) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(p));
    setProviderState(p);
  }

  function clearProvider() {
    localStorage.removeItem(STORAGE_KEY);
    setProviderState(null);
  }

  return (
    <ProviderContext.Provider value={{ provider, setProvider, clearProvider }}>
      {children}
    </ProviderContext.Provider>
  );
}

export function useProvider() {
  const ctx = useContext(ProviderContext);
  if (!ctx) throw new Error('useProvider must be used inside ProviderProvider');
  return ctx;
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/ProviderContext.jsx
git commit -m "feat: add ProviderContext with localStorage persistence"
```

---

## Task 3: Create imMockData.js

**Files:**
- Create: `frontend/src/utils/imMockData.js`
- Create: `frontend/src/utils/imMockData.test.js`

Write the failing tests first, then implement. The 12 patient records must exactly mirror `mcp-server/data/im_mock_data.py` — translate each Python dict to a JS object literal, converting Python `True`/`False` to `true`/`false`.

- [ ] **Step 1: Write failing tests**

```js
// frontend/src/utils/imMockData.test.js
import { describe, it, expect } from 'vitest';
import {
  getImPatients,
  getImPatientDetail,
  getChronicDiseasePanel,
  getPreventiveCareGaps,
} from './imMockData.js';

describe('getImPatients', () => {
  it('returns all 12 patients unfiltered', () => {
    const result = getImPatients();
    expect(result.length).toBe(12);
    expect(result.every(p => p.specialty === 'IM')).toBe(true);
  });

  it('filters by risk_level High — returns 4', () => {
    const result = getImPatients({ risk_level: 'High' });
    expect(result.length).toBe(4);
    expect(result.every(p => p.risk_level === 'High')).toBe(true);
  });

  it('filters by condition diabetes — returns 6', () => {
    const result = getImPatients({ condition: 'diabetes' });
    expect(result.length).toBeGreaterThan(0);
    expect(result.every(p =>
      p.conditions.some(c => c.toLowerCase().includes('diabetes'))
    )).toBe(true);
  });

  it('filters by provider PROV007', () => {
    const result = getImPatients({ provider: 'PROV007' });
    expect(result.length).toBeGreaterThan(0);
    expect(result.every(p => p.provider_id === 'PROV007')).toBe(true);
  });
});

describe('getImPatientDetail', () => {
  it('returns patient for known ID', () => {
    const result = getImPatientDetail('IM001');
    expect(result).not.toBeNull();
    expect(result.patient_id).toBe('IM001');
    expect(result.a1c_history.length).toBe(4);
  });

  it('returns null for unknown ID', () => {
    expect(getImPatientDetail('UNKNOWN')).toBeNull();
  });
});

describe('getChronicDiseasePanel', () => {
  it('diabetes returns patients with latest A1c > 8.0', () => {
    const result = getChronicDiseasePanel('diabetes');
    expect(result.length).toBeGreaterThan(0);
    result.forEach(p => {
      const latest = p.a1c_history.at(-1).value;
      expect(latest).toBeGreaterThan(8.0);
    });
  });

  it('ckd returns patients with eGFR slope <= -3/yr', () => {
    const result = getChronicDiseasePanel('ckd');
    expect(result.length).toBeGreaterThan(0);
  });

  it('hypertension returns patients with latest systolic > 140', () => {
    const result = getChronicDiseasePanel('hypertension');
    expect(result.length).toBeGreaterThan(0);
    result.forEach(p => {
      const latest = p.bp_history.at(-1).systolic;
      expect(latest).toBeGreaterThan(140);
    });
  });
});

describe('getPreventiveCareGaps', () => {
  it('returns only patients with at least one overdue item', () => {
    const result = getPreventiveCareGaps();
    expect(result.length).toBeGreaterThan(0);
    result.forEach(p => {
      const hasOverdue = p.preventive_care.some(item => item.overdue);
      expect(hasOverdue).toBe(true);
    });
  });

  it('filters by gap_type flu_vaccine', () => {
    const result = getPreventiveCareGaps('flu_vaccine');
    result.forEach(p => {
      const fluItem = p.preventive_care.find(item => item.item_name === 'flu_vaccine');
      expect(fluItem?.overdue).toBe(true);
    });
  });
});
```

- [ ] **Step 2: Run tests — verify they all fail**

```bash
cd frontend && npm test
```

Expected: all tests fail with `Cannot find module './imMockData.js'`.

- [ ] **Step 3: Implement imMockData.js**

The patient array must be translated from `mcp-server/data/im_mock_data.py`. Open that file and translate each of the 12 Python dicts to a JS object literal (Python `True` → `true`, Python `False` → `false`, Python `None` → `null`). The structure for each patient is:

```js
{
  patient_id: "IM001",
  name: "Robert Fitzgerald",
  date_of_birth: "1958-04-12",
  specialty: "IM",
  conditions: ["Type 2 Diabetes (E11.9)", "Hypertension (I10)", "Dyslipidemia (E78.5)"],
  county: "Westchester",
  provider_id: "PROV007",
  provider_name: "Dr. Linda Park",
  risk_level: "High",
  a1c_history: [{ date: "2025-03-01", value: 7.8 }, /* ... */],
  egfr_history: [{ date: "2025-01-01", value: 58 }, /* ... */],
  bp_history: [{ date: "2025-06-01", systolic: 148, diastolic: 88 }, /* ... */],
  cholesterol_history: [{ date: "2025-06-01", ldl: 148, hdl: 36, total: 218 }],
  medications: ["Metformin 1000mg", /* ... */],
  preventive_care: [
    { item_name: "flu_vaccine", last_date: "2025-09-15", due_date: "2026-09-15", overdue: false },
    { item_name: "colonoscopy", last_date: "2021-03-10", due_date: "2031-03-10", overdue: false },
    /* ... */
  ],
}
```

Helper functions and exports:

```js
// frontend/src/utils/imMockData.js

const IM_PATIENTS = [
  // ... (12 patient objects translated from im_mock_data.py)
];

// Returns annualized eGFR slope using least-squares regression over all history entries.
// Returns null if fewer than 2 entries.
function eGFRSlope(egfr_history) {
  if (!egfr_history || egfr_history.length < 2) return null;
  const pts = egfr_history.map(e => ({
    t: new Date(e.date).getFullYear() + new Date(e.date).getMonth() / 12,
    v: e.value,
  }));
  const n = pts.length;
  const sumT  = pts.reduce((s, p) => s + p.t, 0);
  const sumV  = pts.reduce((s, p) => s + p.v, 0);
  const sumTT = pts.reduce((s, p) => s + p.t * p.t, 0);
  const sumTV = pts.reduce((s, p) => s + p.t * p.v, 0);
  const denom = n * sumTT - sumT * sumT;
  if (denom === 0) return null;
  return (n * sumTV - sumT * sumV) / denom;
}

export function getImPatients({ risk_level, condition, provider } = {}) {
  let pts = IM_PATIENTS;
  if (risk_level) pts = pts.filter(p => p.risk_level === risk_level);
  if (condition)  pts = pts.filter(p =>
    p.conditions.some(c => c.toLowerCase().includes(condition.toLowerCase()))
  );
  if (provider)   pts = pts.filter(p =>
    p.provider_id === provider || p.provider_name?.toLowerCase().includes(provider.toLowerCase())
  );
  return pts;
}

export function getImPatientDetail(patient_id) {
  return IM_PATIENTS.find(p => p.patient_id === patient_id) ?? null;
}

export function getChronicDiseasePanel(condition) {
  switch (condition) {
    case 'diabetes':
      return IM_PATIENTS.filter(p => {
        const latest = p.a1c_history?.at(-1)?.value;
        return latest != null && latest > 8.0;
      });
    case 'ckd':
      return IM_PATIENTS.filter(p => {
        const slope = eGFRSlope(p.egfr_history);
        return slope != null && slope <= -3;
      });
    case 'hypertension':
      return IM_PATIENTS.filter(p => {
        const latest = p.bp_history?.at(-1)?.systolic;
        return latest != null && latest > 140;
      });
    default:
      return [];
  }
}

export function getPreventiveCareGaps(gap_type = null) {
  return IM_PATIENTS.filter(p => {
    const items = gap_type
      ? p.preventive_care.filter(item => item.item_name === gap_type)
      : p.preventive_care;
    return items.some(item => item.overdue);
  });
}
```

- [ ] **Step 4: Run tests — verify all pass**

```bash
cd frontend && npm test
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/utils/imMockData.js frontend/src/utils/imMockData.test.js
git commit -m "feat: add JS IM mock data module with 4 query functions"
```

---

## Task 4: Create ProviderPicker

**Files:**
- Create: `frontend/src/components/ProviderPicker.jsx`

- [ ] **Step 1: Write ProviderPicker.jsx**

```jsx
// frontend/src/components/ProviderPicker.jsx
import { useState } from 'react';
import { useProvider } from '../ProviderContext';

const BH_PROVIDERS = [
  { provider_id: 'PROV001', name: 'Dr. Emma Chen',       team: 'ACT-1', specialty: 'BH' },
  { provider_id: 'PROV002', name: 'Dr. Marcus Williams', team: 'ACT-1', specialty: 'BH' },
  { provider_id: 'PROV003', name: 'Dr. Priya Sharma',    team: 'ACT-2', specialty: 'BH' },
  { provider_id: 'PROV004', name: "Dr. James O'Brien",   team: 'ACT-2', specialty: 'BH' },
  { provider_id: 'PROV005', name: 'Dr. Sarah Nakamura',  team: 'CSP-1', specialty: 'BH' },
  { provider_id: 'PROV006', name: 'Dr. Robert Kim',      team: 'CSP-1', specialty: 'BH' },
];

const IM_PROVIDERS = [
  { provider_id: 'PROV007', name: 'Dr. Linda Park',   team: 'IM-1', specialty: 'IM' },
  { provider_id: 'PROV008', name: 'Dr. Ahmed Hassan', team: 'IM-1', specialty: 'IM' },
];

export default function ProviderPicker() {
  const { setProvider } = useProvider();
  const [specialty, setSpecialty] = useState(null);

  const providers = specialty === 'BH' ? BH_PROVIDERS : IM_PROVIDERS;

  return (
    <div className="provider-picker-overlay">
      <div className="provider-picker">
        <div className="picker-logo">
          <div className="logo-text" style={{ fontSize: '20px' }}>ClinicalMind</div>
          <div className="logo-sub">Select your profile to continue</div>
        </div>

        {!specialty ? (
          <>
            <h2 className="picker-heading">Choose your specialty</h2>
            <div className="picker-cards">
              <div className="picker-card" onClick={() => setSpecialty('BH')}>
                <div className="picker-card-icon">🧠</div>
                <div className="picker-card-title">Behavioral Health</div>
                <div className="picker-card-sub">ACT-1 · ACT-2 · CSP-1</div>
              </div>
              <div className="picker-card" onClick={() => setSpecialty('IM')}>
                <div className="picker-card-icon">🏥</div>
                <div className="picker-card-title">Internal Medicine</div>
                <div className="picker-card-sub">IM-1</div>
              </div>
            </div>
          </>
        ) : (
          <>
            <h2 className="picker-heading">
              <button className="picker-back" onClick={() => setSpecialty(null)}>← Back</button>
              Choose your provider
            </h2>
            <div className="picker-provider-list">
              {providers.map(p => (
                <div key={p.provider_id} className="picker-provider-card" onClick={() => setProvider(p)}>
                  <div className="picker-provider-name">{p.name}</div>
                  <div className="picker-provider-sub">{p.team} · {p.provider_id}</div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Add picker CSS to index.css**

Open `frontend/src/index.css`. Append these styles at the end:

```css
/* ── Provider Picker ─────────────────────────────────────────────────────── */
.provider-picker-overlay {
  position: fixed; inset: 0;
  background: var(--bg);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.provider-picker {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 40px;
  width: 480px;
  max-width: 95vw;
}
.picker-logo { text-align: center; margin-bottom: 28px; }
.picker-heading {
  font-size: 15px; font-weight: 600; color: var(--text-1);
  margin: 0 0 16px; display: flex; align-items: center; gap: 10px;
}
.picker-back {
  background: none; border: none; color: var(--text-3);
  cursor: pointer; font-size: 13px; padding: 0;
}
.picker-cards { display: flex; gap: 12px; }
.picker-card {
  flex: 1; background: var(--bg); border: 1px solid var(--border);
  border-radius: 8px; padding: 20px; cursor: pointer; text-align: center;
  transition: border-color 0.15s;
}
.picker-card:hover { border-color: var(--primary); }
.picker-card-icon { font-size: 28px; margin-bottom: 8px; }
.picker-card-title { font-size: 14px; font-weight: 600; color: var(--text-1); }
.picker-card-sub { font-size: 11px; color: var(--text-3); margin-top: 4px; }
.picker-provider-list { display: flex; flex-direction: column; gap: 8px; }
.picker-provider-card {
  background: var(--bg); border: 1px solid var(--border);
  border-radius: 8px; padding: 12px 16px; cursor: pointer;
  transition: border-color 0.15s;
}
.picker-provider-card:hover { border-color: var(--primary); }
.picker-provider-name { font-size: 14px; font-weight: 600; color: var(--text-1); }
.picker-provider-sub { font-size: 11px; color: var(--text-3); margin-top: 2px; }
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ProviderPicker.jsx frontend/src/index.css
git commit -m "feat: add ProviderPicker two-step overlay"
```

---

## Task 5: Rename Dashboard → BHDashboard

**Files:**
- Rename: `frontend/src/components/Dashboard.jsx` → `frontend/src/components/BHDashboard.jsx`

- [ ] **Step 1: Copy file with new name**

```bash
cp frontend/src/components/Dashboard.jsx frontend/src/components/BHDashboard.jsx
```

- [ ] **Step 2: Delete old file**

```bash
rm frontend/src/components/Dashboard.jsx
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/BHDashboard.jsx frontend/src/components/Dashboard.jsx
git commit -m "refactor: rename Dashboard to BHDashboard"
```

---

## Task 6: Create IMDashboard

**Files:**
- Create: `frontend/src/components/IMDashboard.jsx`

- [ ] **Step 1: Write IMDashboard.jsx**

```jsx
// frontend/src/components/IMDashboard.jsx
import { useMemo } from 'react';
import {
  getImPatients,
  getChronicDiseasePanel,
  getPreventiveCareGaps,
} from '../utils/imMockData.js';

// Returns ↑ / ↓ / → based on the last two values in a history array
function trendArrow(history, valueKey = 'value') {
  if (!history || history.length < 2) return '→';
  const last = history.at(-1)[valueKey];
  const prev = history.at(-2)[valueKey];
  if (last > prev) return '↑';
  if (last < prev) return '↓';
  return '→';
}

// Annualized eGFR slope — intentionally duplicated from imMockData.js to keep the
// dashboard self-contained. This version rounds to one decimal for display; do NOT
// extract to a shared util — it would couple the display component to the data module.
function eGFRSlope(egfr_history) {
  if (!egfr_history || egfr_history.length < 2) return null;
  const pts = egfr_history.map(e => ({
    t: new Date(e.date).getFullYear() + new Date(e.date).getMonth() / 12,
    v: e.value,
  }));
  const n = pts.length;
  const sumT  = pts.reduce((s, p) => s + p.t, 0);
  const sumV  = pts.reduce((s, p) => s + p.v, 0);
  const sumTT = pts.reduce((s, p) => s + p.t * p.t, 0);
  const sumTV = pts.reduce((s, p) => s + p.t * p.v, 0);
  const denom = n * sumTT - sumT * sumT;
  if (denom === 0) return null;
  return Math.round(((n * sumTV - sumT * sumV) / denom) * 10) / 10;
}

function StatCard({ label, value, color }) {
  return (
    <div className="stat-card" style={{ borderLeftColor: `var(--${color})` }}>
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ color: `var(--${color})` }}>{value}</div>
    </div>
  );
}

function DiseasePanel({ title, rows, emptyMsg }) {
  return (
    <div className="disease-panel">
      <div className="panel-title">{title}</div>
      {rows.length === 0 ? (
        <div className="panel-empty">{emptyMsg}</div>
      ) : (
        <table className="panel-table">
          <tbody>
            {rows.map((row, i) => (
              <tr key={i}>
                <td className="panel-name">{row.name}</td>
                <td className="panel-metric">{row.metric}</td>
                <td className="panel-trend">{row.trend}</td>
                <td className={`panel-risk risk-${row.risk_level?.toLowerCase()}`}>{row.risk_level}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default function IMDashboard() {
  const data = useMemo(() => {
    const highRisk   = getImPatients({ risk_level: 'High' });
    const diabetics  = getChronicDiseasePanel('diabetes')
      .sort((a, b) => (b.a1c_history.at(-1)?.value ?? 0) - (a.a1c_history.at(-1)?.value ?? 0));
    const ckd        = getChronicDiseasePanel('ckd')
      .sort((a, b) => (eGFRSlope(a.egfr_history) ?? 0) - (eGFRSlope(b.egfr_history) ?? 0));
    const hypertensive = getChronicDiseasePanel('hypertension')
      .sort((a, b) => (b.bp_history.at(-1)?.systolic ?? 0) - (a.bp_history.at(-1)?.systolic ?? 0));
    const gaps       = getPreventiveCareGaps();
    return { highRisk, diabetics, ckd, hypertensive, gaps };
  }, []);

  const diabetesRows = data.diabetics.map(p => ({
    name:      p.name,
    metric:    `A1c ${p.a1c_history.at(-1)?.value}`,
    trend:     trendArrow(p.a1c_history),
    risk_level: p.risk_level,
  }));

  const ckdRows = data.ckd.map(p => {
    const slope = eGFRSlope(p.egfr_history);
    return {
      name:      p.name,
      metric:    slope != null ? `${slope}/yr` : '—',
      trend:     '↓',
      risk_level: p.risk_level,
    };
  });

  const htRows = data.hypertensive.map(p => {
    const bp = p.bp_history.at(-1);
    return {
      name:      p.name,
      metric:    bp ? `${bp.systolic}/${bp.diastolic}` : '—',
      trend:     trendArrow(p.bp_history, 'systolic'),
      risk_level: p.risk_level,
    };
  });

  return (
    <div className="dashboard-pane">
      <div className="dash-inner">
        <div className="stats-row">
          <StatCard label="High Risk"    value={data.highRisk.length}      color="red"     />
          <StatCard label="A1c > 8.0"   value={data.diabetics.length}     color="amber"   />
          <StatCard label="Care Gaps"   value={data.gaps.length}          color="primary" />
        </div>

        <div className="disease-panels">
          <DiseasePanel
            title="🩸 Diabetes — A1c > 8.0"
            rows={diabetesRows}
            emptyMsg="No patients with A1c > 8.0"
          />
          <DiseasePanel
            title="🫘 CKD — eGFR slope ≤ −3/yr"
            rows={ckdRows}
            emptyMsg="No patients with declining kidney function"
          />
          <DiseasePanel
            title="💗 Hypertension — systolic > 140"
            rows={htRows}
            emptyMsg="No patients with uncontrolled hypertension"
          />
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Add disease panel CSS to index.css**

Append to `frontend/src/index.css`:

```css
/* ── IM Disease Panels ───────────────────────────────────────────────────── */
.disease-panels {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
  margin-top: 20px;
}
.disease-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px 16px;
}
.panel-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-2);
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.panel-empty { font-size: 12px; color: var(--text-3); }
.panel-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.panel-table tr { border-bottom: 1px solid var(--border); }
.panel-table tr:last-child { border-bottom: none; }
.panel-table td { padding: 5px 4px; }
.panel-name  { color: var(--text-1); font-weight: 500; }
.panel-metric { color: var(--text-2); font-variant-numeric: tabular-nums; }
.panel-trend  { color: var(--text-3); width: 20px; text-align: center; }
.panel-risk   { width: 64px; text-align: right; font-size: 10px; font-weight: 600; }
.risk-high     { color: var(--red); }
.risk-moderate { color: var(--amber); }
.risk-low      { color: var(--green); }
```

- [ ] **Step 3: Verify tests still pass**

```bash
cd frontend && npm test
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/IMDashboard.jsx frontend/src/index.css
git commit -m "feat: add IMDashboard with three disease panels"
```

---

## Task 7: Wire React Router and ProviderContext in App.jsx

**Files:**
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: Rewrite App.jsx**

```jsx
// frontend/src/App.jsx
import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Topbar  from './components/Topbar';
import BHDashboard from './components/BHDashboard.jsx';
import IMDashboard from './components/IMDashboard.jsx';
import PatientTable from './components/PatientTable.jsx';
import ChatPane from './components/ChatPane.jsx';
import ProviderPicker from './components/ProviderPicker.jsx';
import { ThemeProvider } from './ThemeContext';
import { ProviderProvider, useProvider } from './ProviderContext';
import { loadPatients } from './utils/dataTransform.js';

function AppShell() {
  const { provider } = useProvider();
  const [patients, setPatients] = useState([]);
  const [status, setStatus] = useState({ state: 'loading', msg: 'Loading data…' });
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('cm_api_key') || '');
  const [showApiSetup, setShowApiSetup] = useState(false);

  useEffect(() => {
    loadPatients()
      .then(pts => { setPatients(pts); setStatus({ state: 'ok', msg: `${pts.length} patients loaded` }); })
      .catch(() => setStatus({ state: 'error', msg: 'Data unavailable' }));
  }, []);

  function handleSaveKey(key) {
    localStorage.setItem('cm_api_key', key);
    setApiKey(key);
    setShowApiSetup(false);
  }

  if (!provider) return <ProviderPicker />;

  const DashboardComponent = provider.specialty === 'IM' ? IMDashboard : BHDashboard;

  return (
    <div className="app-shell">
      <Sidebar
        onNeedKey={() => setShowApiSetup(true)}
        apiKey={apiKey}
        patients={patients}
      />
      <div className="main-area">
        <Topbar status={status} />
        {showApiSetup && (
          <div className="api-setup">
            <label htmlFor="api-input">Anthropic API Key</label>
            <input
              id="api-input"
              type="password"
              className="api-input"
              placeholder="sk-ant-..."
              defaultValue={apiKey}
              onKeyDown={e => e.key === 'Enter' && handleSaveKey(e.target.value.trim())}
            />
            <button className="api-btn" onClick={e => handleSaveKey(e.target.previousElementSibling.value.trim())}>Connect</button>
            <button className="api-btn" style={{background:'transparent',border:'1px solid var(--border)',color:'var(--text-3)'}} onClick={() => setShowApiSetup(false)}>✕</button>
            <span className="api-note">Stored in your browser only</span>
          </div>
        )}
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={
            <div className="content-scroll">
              {/* IMDashboard takes no props — it reads from imMockData.js directly.
          BHDashboard uses patients + loading. Extra props are ignored by React. */}
      <DashboardComponent patients={patients} loading={status.state === 'loading'} />
            </div>
          } />
          <Route path="/patients" element={
            <div className="content-scroll">
              <PatientTable patients={patients} />
            </div>
          } />
          <Route path="/chat" element={
            <ChatPane patients={patients} apiKey={apiKey} onNeedKey={() => setShowApiSetup(true)} />
          } />
        </Routes>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <ProviderProvider>
        <BrowserRouter>
          <AppShell />
        </BrowserRouter>
      </ProviderProvider>
    </ThemeProvider>
  );
}
```

- [ ] **Step 2: Verify tests still pass**

```bash
cd frontend && npm test
```

Expected: all tests pass.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.jsx
git commit -m "feat: wire React Router, ProviderContext, and ProviderPicker in App"
```

---

## Task 8: Update Sidebar

**Files:**
- Modify: `frontend/src/components/Sidebar.jsx`

- [ ] **Step 1: Rewrite Sidebar.jsx**

Replace `onNavigate` prop and `activeView` state with `NavLink`. Guard the overdue badge to BH only.

```jsx
// frontend/src/components/Sidebar.jsx
import { NavLink } from 'react-router-dom';
import { KPI_NAMES } from '../utils/dataTransform';
import { useProvider } from '../ProviderContext';

export default function Sidebar({ onNeedKey, apiKey, patients }) {
  const { provider } = useProvider();

  const overdueBadge = provider?.specialty === 'BH' && patients?.length
    ? patients.filter(p => KPI_NAMES.some(k => p.kpis?.[k]?.overdue)).length
    : 0;

  function handleChat(e) {
    if (!apiKey) { e.preventDefault(); onNeedKey(); }
  }

  const navCls = ({ isActive }) => `nav-item${isActive ? ' active' : ''}`;

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-mark">
          <svg viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
            <line x1="11" y1="2.5" x2="5"  y2="7"  stroke="white" strokeWidth="0.7" strokeOpacity="0.4"/>
            <line x1="11" y1="2.5" x2="17" y2="7"  stroke="white" strokeWidth="0.7" strokeOpacity="0.4"/>
            <line x1="5"  y1="7"  x2="11" y2="11" stroke="white" strokeWidth="0.7" strokeOpacity="0.4"/>
            <line x1="17" y1="7"  x2="11" y2="11" stroke="white" strokeWidth="0.7" strokeOpacity="0.4"/>
            <line x1="5"  y1="7"  x2="4"  y2="12" stroke="white" strokeWidth="0.7" strokeOpacity="0.4"/>
            <line x1="17" y1="7"  x2="18" y2="12" stroke="white" strokeWidth="0.7" strokeOpacity="0.4"/>
            <line x1="11" y1="11" x2="4"  y2="12" stroke="white" strokeWidth="0.7" strokeOpacity="0.4"/>
            <line x1="11" y1="11" x2="18" y2="12" stroke="white" strokeWidth="0.7" strokeOpacity="0.4"/>
            <circle cx="11" cy="2.5" r="1.4" fill="white" fillOpacity="0.9"/>
            <circle cx="5"  cy="7"   r="1.1" fill="white" fillOpacity="0.7"/>
            <circle cx="17" cy="7"   r="1.1" fill="white" fillOpacity="0.7"/>
            <circle cx="11" cy="11"  r="2.2" fill="white"/>
            <circle cx="4"  cy="12"  r="1.1" fill="white" fillOpacity="0.7"/>
            <circle cx="18" cy="12"  r="1.1" fill="white" fillOpacity="0.7"/>
            <path d="M2 18 L5 18 L6.5 15.5 L8 20.5 L9.5 17 L11 18 L15 18 L16.5 15.5 L18 20.5 L19.5 17 L20 18"
                  stroke="white" strokeWidth="0.95" strokeLinecap="round" strokeLinejoin="round" strokeOpacity="0.85"/>
          </svg>
        </div>
        <div>
          <div className="logo-text">ClinicalMind</div>
          <div className="logo-sub">Clinical AI</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <span className="nav-section-label">MAIN</span>
        <NavLink to="/dashboard" className={navCls}>
          <div className="nav-dot" />
          Dashboard
        </NavLink>
        <NavLink to="/patients" className={navCls}>
          <div className="nav-dot" />
          Patients
          {overdueBadge > 0 && <span className="nav-badge">{overdueBadge}</span>}
        </NavLink>
        <NavLink to="/chat" className={navCls} onClick={handleChat}>
          <div className="nav-dot" />
          AI Assistant
        </NavLink>

        <span className="nav-section-label">REPORTS</span>
        <div className="nav-item disabled"><div className="nav-dot" />KPI Summary</div>
        <div className="nav-item disabled"><div className="nav-dot" />Crisis Log</div>
      </nav>

      <div className="sidebar-footer">
        <div className="status-dot" />
        Live · Updated now
      </div>
    </aside>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/Sidebar.jsx
git commit -m "feat: replace Sidebar onNavigate with NavLink, guard BH badge"
```

---

## Task 9: Update Topbar

**Files:**
- Modify: `frontend/src/components/Topbar.jsx`

- [ ] **Step 1: Rewrite Topbar.jsx**

```jsx
// frontend/src/components/Topbar.jsx
import { useTheme } from '../ThemeContext';
import { useProvider } from '../ProviderContext';

const THEME_CYCLE = { system: 'light', light: 'dark', dark: 'system' };
const THEME_ICON  = { system: '🖥', light: '☀️', dark: '🌙' };

const SUBTITLES = {
  BH: 'Westchester County · ACT + CSP Programs',
  IM: 'Westchester County · Internal Medicine',
  default: 'Westchester County',
};

export default function Topbar({ status }) {
  const date = new Date().toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' });
  const isOk = status?.state === 'ok';
  const { theme, setTheme } = useTheme();
  const { provider, clearProvider } = useProvider();

  const subtitle = SUBTITLES[provider?.specialty] ?? SUBTITLES.default;

  return (
    <div className="topbar">
      <div className="topbar-left">
        <div className="topbar-title">Clinical Dashboard</div>
        <div className="topbar-sub">{subtitle}</div>
      </div>
      <div className="topbar-right">
        {provider && (
          <div className="badge-pill">
            👤 {provider.name}
            <button
              onClick={clearProvider}
              style={{ background:'none', border:'none', color:'var(--text-3)', cursor:'pointer', marginLeft:'6px', fontSize:'11px' }}
            >
              switch
            </button>
          </div>
        )}
        <button
          className="badge-pill"
          onClick={() => setTheme(THEME_CYCLE[theme])}
          title={`Theme: ${theme}`}
          style={{ cursor:'pointer', fontSize:'13px', minWidth:'28px', textAlign:'center' }}
        >
          {THEME_ICON[theme]}
        </button>
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

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/Topbar.jsx
git commit -m "feat: add provider name + switch link and dynamic subtitle to Topbar"
```

---

## Task 10: Update PatientTable

**Files:**
- Modify: `frontend/src/components/PatientTable.jsx`

`PatientTable` currently takes a `patients` prop from `App.jsx` and uses KPI-specific sort logic. For IM providers, we need IM patient data and different columns.

- [ ] **Step 1: Read the full PatientTable.jsx**

Read `frontend/src/components/PatientTable.jsx` in full before editing.

- [ ] **Step 2: Add ProviderContext import and specialty branch at the top**

At the top of `PatientTable.jsx`, add the import:

```jsx
import { useProvider } from '../ProviderContext';
import { getImPatients } from '../utils/imMockData.js';
```

- [ ] **Step 3: Update the component to branch on specialty**

Inside the component, before the existing `filtered` useMemo, add:

```jsx
const { provider } = useProvider();
const isIM = provider?.specialty === 'IM';

// For IM providers, source data from imMockData instead of BH patients prop
const activePatients = isIM ? getImPatients() : patients;
```

Replace all references to `patients` in the `filtered` useMemo with `activePatients`.

- [ ] **Step 4: Guard the KPI sort column**

In the `sort` switch, guard the `overdue` case so it only runs for BH patients (IM patients have no `kpis` field):

```js
case 'overdue':
  va = isIM ? 0 : KPI_NAMES.filter(k => a.kpis?.[k]?.overdue).length;
  vb = isIM ? 0 : KPI_NAMES.filter(k => b.kpis?.[k]?.overdue).length;
  break;
```

- [ ] **Step 5: Render IM-appropriate columns**

In the `<thead>` and `<tbody>`, branch on `isIM`:

For IM: show columns — Patient name, Conditions (joined), Risk Level, Provider
For BH: keep the existing KPI Status + Last Contact columns

```jsx
<thead>
  <tr>
    <th style={{width:32}} className="no-sort"></th>
    <SortTh col="name">Patient</SortTh>
    {isIM
      ? <><th>Conditions</th><th>Risk</th></>
      : <><th>Diagnosis</th><SortTh col="overdue">KPI Status</SortTh><SortTh col="contact">Last Contact</SortTh></>
    }
    <th>Provider</th>
  </tr>
</thead>
```

For IM rows, show a simplified non-expandable row:

```jsx
{isIM ? filtered.map(p => (
  <tr key={p.patient_id}>
    <td></td>
    <td className="pt-name">{p.name}</td>
    <td style={{fontSize:'11px',color:'var(--text-3)'}}>{p.conditions.slice(0,2).join(', ')}</td>
    <td><span className={`risk-badge risk-${p.risk_level?.toLowerCase()}`}>{p.risk_level}</span></td>
    <td style={{fontSize:'12px'}}>{p.provider_name}</td>
  </tr>
)) : /* existing BH rows */}
```

- [ ] **Step 6: Update patient count display**

The `{filtered.length} of {patients.length}` count should use `activePatients.length`:

```jsx
<span className="pt-count">{filtered.length} of {activePatients.length} patients</span>
```

- [ ] **Step 7: Verify tests pass**

```bash
cd frontend && npm test
```

Expected: all tests pass.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/components/PatientTable.jsx
git commit -m "feat: PatientTable reads ProviderContext for specialty-aware data and columns"
```

---

## Task 11: Add IM tools to tools.js

**Files:**
- Modify: `frontend/src/utils/tools.js`

- [ ] **Step 1: Add IM imports to tools.js**

At the top of `frontend/src/utils/tools.js`, add:

```js
import {
  getImPatients,
  getImPatientDetail,
  getChronicDiseasePanel,
  getPreventiveCareGaps,
} from './imMockData.js';
```

- [ ] **Step 2: Add 4 IM cases to runTool**

In the `runTool` switch, add before the `default` case:

```js
case 'get_im_patients':
  return getImPatients(input);
case 'get_im_patient_detail':
  return getImPatientDetail(input.patient_id) ?? { error: `No IM patient found: ${input.patient_id}` };
case 'get_chronic_disease_panel':
  return { condition: input.condition, patients: getChronicDiseasePanel(input.condition) };
case 'get_preventive_care_gaps':
  return { patients: getPreventiveCareGaps(input.gap_type ?? null) };
```

- [ ] **Step 3: Add IM tool definitions to TOOL_DEFS**

After the existing `TOOL_DEFS` array, add:

```js
export const IM_TOOL_DEFS = [
  {
    name: 'get_im_patients',
    description: 'Returns the IM patient panel with chronic disease summary data. Filter by risk level, condition, or provider.',
    input_schema: {
      type: 'object',
      properties: {
        risk_level: { type: 'string', enum: ['High', 'Moderate', 'Low'] },
        condition:  { type: 'string', enum: ['diabetes', 'ckd', 'hypertension'] },
        provider:   { type: 'string', description: 'Provider ID (e.g. PROV007) or name fragment' },
      },
    },
  },
  {
    name: 'get_im_patient_detail',
    description: 'Returns the full IM record for one patient — lab histories, medications, and preventive care status.',
    input_schema: {
      type: 'object',
      properties: { patient_id: { type: 'string' } },
      required: ['patient_id'],
    },
  },
  {
    name: 'get_chronic_disease_panel',
    description: 'Returns IM patients with poorly controlled chronic disease metrics. diabetes = A1c > 8.0; ckd = eGFR slope ≤ −3/yr; hypertension = systolic BP > 140.',
    input_schema: {
      type: 'object',
      properties: { condition: { type: 'string', enum: ['diabetes', 'ckd', 'hypertension'] } },
      required: ['condition'],
    },
  },
  {
    name: 'get_preventive_care_gaps',
    description: 'Returns IM patients overdue for preventive care. Options: flu_vaccine, colonoscopy, mammogram, eye_exam_diabetic, microalbumin, foot_exam_diabetic.',
    input_schema: {
      type: 'object',
      properties: {
        gap_type: {
          type: 'string',
          enum: ['flu_vaccine', 'colonoscopy', 'mammogram', 'eye_exam_diabetic', 'microalbumin', 'foot_exam_diabetic'],
        },
      },
    },
  },
];
```

- [ ] **Step 4: Update ChatPane to merge tool defs**

Read `frontend/src/components/ChatPane.jsx`. Find where `TOOL_DEFS` is imported/used. Update to merge BH and IM defs:

```js
import { TOOL_DEFS, IM_TOOL_DEFS, runTool } from '../utils/tools.js';
// ...
const allTools = [...TOOL_DEFS, ...IM_TOOL_DEFS];
// pass allTools wherever TOOL_DEFS was used in the API call
```

- [ ] **Step 5: Verify tests pass**

```bash
cd frontend && npm test
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/utils/tools.js frontend/src/components/ChatPane.jsx
git commit -m "feat: add 4 IM tool definitions and runTool cases"
```

---

## Final Verification

- [ ] **Run the dev server and smoke test**

```bash
cd frontend && npm run dev
```

Verify manually:
1. App opens to the ProviderPicker overlay
2. Selecting BH → pick Dr. Emma Chen → see BH dashboard, BH patients, overdue badge visible
3. Click "switch" in Topbar → picker reappears
4. Select IM → pick Dr. Linda Park → see IM dashboard with 3 disease panels, no badge in sidebar
5. Patients view shows IM patient list with Conditions + Risk columns
6. AI Assistant works (chat opens, no crashes)
7. Refresh retains the selected provider (localStorage)

- [ ] **Run all tests one final time**

```bash
cd frontend && npm test
```

Expected: all tests pass.

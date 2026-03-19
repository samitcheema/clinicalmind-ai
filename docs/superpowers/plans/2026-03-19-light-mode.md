# Light Mode Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a warm-neutral light mode with system-preference detection and a manual toggle button in the topbar.

**Architecture:** CSS custom properties drive all colors; a `[data-theme="light"]` block on `<html>` overrides the palette. A `ThemeContext` React context manages `'system' | 'light' | 'dark'` state, sets the attribute as a side effect, and persists to `localStorage`. A toggle button in the topbar cycles through the three states.

**Tech Stack:** React 18, Vite, vanilla CSS custom properties, no test framework.

---

### Task 1: CSS — fix hardcoded values and add light palette

**Files:**
- Modify: `frontend/src/index.css`

No test framework exists; verify visually by running the dev server (`npm run dev` from `frontend/`) and checking both themes.

- [ ] **Step 1: Fix `body` hardcoded background and color**

In `frontend/src/index.css`, replace lines 3–9:

```css
/* BEFORE */
body {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  background: #f0f4f8;
  color: #0f172a;
  font-size: 14px;
  line-height: 1.5;
}

/* AFTER */
body {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
  line-height: 1.5;
}
```

- [ ] **Step 2: Fix `.tl-dot` hardcoded white border**

Find `.tl-dot` (around line 295) and change `border: 2px solid white` to `border: 2px solid var(--surface)`:

```css
/* BEFORE */
.tl-dot {
  position: absolute;
  left: -19px;
  top: 3px;
  width: 10px; height: 10px;
  border-radius: 50%;
  border: 2px solid white;
  box-shadow: 0 0 0 1.5px currentColor;
}

/* AFTER */
.tl-dot {
  position: absolute;
  left: -19px;
  top: 3px;
  width: 10px; height: 10px;
  border-radius: 50%;
  border: 2px solid var(--surface);
  box-shadow: 0 0 0 1.5px currentColor;
}
```

- [ ] **Step 3: Add `[data-theme="light"]` override block**

Insert this block immediately after the closing `}` of the `:root` block (after line 38):

```css
[data-theme="light"] {
  --bg:           #f5f4f2;
  --surface:      #fdfcfb;
  --surface-2:    #ece9e4;
  --border:       #d6d0c8;
  --border-light: #ece9e4;
  --text:         #1e1a16;
  --text-2:       #3d3530;
  --text-3:       #7a6f66;
  --text-4:       #a8a097;
  --ring-track:   #e8e2da;
  --shadow-sm:    0 1px 3px rgba(0,0,0,0.08);
  --shadow:       0 4px 6px rgba(0,0,0,0.10);
}
```

- [ ] **Step 4: Verify manually**

Run the dev server: `cd frontend && npm run dev`

Open the app in a browser. In DevTools console, run:
```js
document.documentElement.setAttribute('data-theme', 'light')
```
Expected: the UI switches to warm neutral light colors — warm off-white cards, warm gray background, dark text. No white-on-white elements visible in the EncounterTimeline dot rings.

Remove the attribute to verify dark mode still works:
```js
document.documentElement.removeAttribute('data-theme')
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/index.css
git commit -m "feat: add light mode CSS palette and fix hardcoded colors"
```

---

### Task 2: ThemeContext — theme state, persistence, system preference

**Files:**
- Create: `frontend/src/ThemeContext.jsx`

- [ ] **Step 1: Create ThemeContext.jsx**

Create `frontend/src/ThemeContext.jsx` with this content:

```jsx
import { createContext, useContext, useEffect, useState } from 'react';

const ThemeContext = createContext(null);

function getSystemTheme() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(
    () => localStorage.getItem('cm-theme') || 'system'
  );

  const effectiveTheme = theme === 'system' ? getSystemTheme() : theme;

  useEffect(() => {
    if (effectiveTheme === 'light') {
      document.documentElement.setAttribute('data-theme', 'light');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
  }, [effectiveTheme]);

  useEffect(() => {
    if (theme !== 'system') return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => {
      // Re-render to pick up new system preference
      setThemeState('system');
    };
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [theme]);

  function setTheme(next) {
    localStorage.setItem('cm-theme', next);
    setThemeState(next);
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme, effectiveTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used inside ThemeProvider');
  return ctx;
}
```

- [ ] **Step 2: Verify the context logic mentally**

Check these three scenarios before continuing:

1. Fresh load, no `localStorage` value → `theme = 'system'`, `effectiveTheme` = whatever the OS is → correct `data-theme` attribute set or absent.
2. User sets `theme = 'light'` → `localStorage` updated, `data-theme="light"` added, system listener removed.
3. User sets `theme = 'system'` → listener re-added, attribute follows OS again.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/ThemeContext.jsx
git commit -m "feat: add ThemeContext with system preference and localStorage persistence"
```

---

### Task 3: App.jsx — wrap in ThemeProvider

**Files:**
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: Import ThemeProvider and wrap the return**

At the top of `frontend/src/App.jsx`, add the import after the existing imports:

```jsx
import { ThemeProvider } from './ThemeContext';
```

Then wrap the entire return value of `App()` in `<ThemeProvider>`:

```jsx
return (
  <ThemeProvider>
    <div className="app-shell">
      {/* ... all existing JSX unchanged ... */}
    </div>
  </ThemeProvider>
);
```

- [ ] **Step 2: Verify the app still loads**

The dev server should still be running. Reload the browser. Expected: app loads normally, no console errors. The theme should follow your OS preference automatically (dark if your OS is dark, light if OS is light).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.jsx
git commit -m "feat: wrap app in ThemeProvider"
```

---

### Task 4: Topbar — add theme toggle button

**Files:**
- Modify: `frontend/src/components/Topbar.jsx`

- [ ] **Step 1: Update Topbar to use the toggle**

Replace the entire contents of `frontend/src/components/Topbar.jsx` with:

```jsx
import { useTheme } from '../ThemeContext';

const THEME_CYCLE = { system: 'light', light: 'dark', dark: 'system' };
const THEME_ICON  = { system: '🖥', light: '☀️', dark: '🌙' };

export default function Topbar({ status }) {
  const date = new Date().toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' });
  const isOk = status?.state === 'ok';
  const { theme, setTheme } = useTheme();

  return (
    <div className="topbar">
      <div className="topbar-left">
        <div className="topbar-title">Clinical Dashboard</div>
        <div className="topbar-sub">Westchester County · ACT + CSP Programs</div>
      </div>
      <div className="topbar-right">
        <button
          className="badge-pill"
          onClick={() => setTheme(THEME_CYCLE[theme])}
          title={`Theme: ${theme}`}
          style={{ cursor: 'pointer', background: 'none', border: '1px solid var(--border)', fontSize: '13px' }}
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

- [ ] **Step 2: Verify the toggle works end-to-end**

In the browser:

1. Click the toggle once → icon changes from 🖥 to ☀️, UI switches to light mode (warm neutral palette).
2. Click again → icon changes to 🌙, UI switches to dark mode.
3. Click again → icon changes to 🖥, UI follows OS preference.
4. Set to light mode, reload the page → still in light mode (persisted via `localStorage`).
5. Open DevTools → Application → Local Storage → confirm `cm-theme` key exists with the correct value.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/Topbar.jsx
git commit -m "feat: add theme toggle button to topbar"
```

---

### Done

All four tasks complete. The light mode feature is fully implemented:

- Warm neutral light palette applied via CSS variable overrides
- System preference followed by default, persisted manual override
- Toggle button in the topbar cycling system → light → dark → system

# Light Mode Design Spec
**Date:** 2026-03-19
**Project:** ClinicalMind AI — Frontend

---

## Overview

Add a light/dark theme system to the ClinicalMind AI clinical dashboard. The app currently has a hardcoded dark theme using CSS custom properties. This spec covers adding a warm-neutral light palette, a system-preference-aware theme context, and a manual toggle in the topbar.

---

## Requirements

- Follow the OS/system `prefers-color-scheme` by default (no user action required)
- Allow manual override via a toggle button in the topbar
- Persist the manual override to `localStorage` across sessions
- Warm neutral light palette (not cool/sterile)
- Status colors (red, amber, green, blue primary) unchanged — they work on both themes

---

## Architecture

### Approach: CSS `data-theme` attribute + React context

The `data-theme="light"` attribute is set on `document.documentElement`. A `[data-theme="light"]` CSS block in `index.css` overrides the color variables. A `ThemeContext` in React manages state and side effects.

This approach fits the existing vanilla CSS architecture with no new dependencies.

---

## 1. CSS Changes (`frontend/src/index.css`)

Add a `[data-theme="light"]` override block after the existing `:root` block. All other CSS rules remain unchanged — they reference variables and automatically pick up the overrides.

### Light palette (warm neutral)

| Variable | Light value | Dark value (current) |
|---|---|---|
| `--bg` | `#f5f4f2` | `#0f172a` |
| `--surface` | `#fdfcfb` | `#1e293b` |
| `--surface-2` | `#ece9e4` | `#0d1526` |
| `--border` | `#d6d0c8` | `#334155` |
| `--border-light` | `#ece9e4` | `#1e293b` |
| `--text` | `#1e1a16` | `#f8fafc` |
| `--text-2` | `#3d3530` | `#cbd5e1` |
| `--text-3` | `#7a6f66` | `#94a3b8` |
| `--text-4` | `#a8a097` | `#475569` |
| `--ring-track` | `#e8e2da` | `#1e3a4a` |
| `--shadow-sm` | `0 1px 3px rgba(0,0,0,0.08)` | `0 1px 3px rgba(0,0,0,0.3)` |
| `--shadow` | `0 4px 6px rgba(0,0,0,0.10)` | `0 4px 6px rgba(0,0,0,0.4)` |

Unchanged in both themes: `--primary`, `--primary-dark`, `--primary-900`, `--red`, `--red-dark`, `--red-bg`, `--amber`, `--amber-dark`, `--amber-bg`, `--green`, `--green-dark`, `--green-bg`, `--blue-bg`, `--radius`.

---

## 2. ThemeContext (`frontend/src/ThemeContext.jsx`)

A React context + provider that manages theme state.

**State:** `theme` — `'system' | 'light' | 'dark'`. Initialized from `localStorage` key `cm-theme`, defaulting to `'system'`.

**Derived value:** `effectiveTheme` — resolves `'system'` to `'light'` or `'dark'` by reading `window.matchMedia('(prefers-color-scheme: dark)')`.

**Side effects:**
- On `effectiveTheme` change: set/remove `data-theme="light"` on `document.documentElement` (dark is the default, so only `light` needs the attribute)
- While `theme === 'system'`: add a `matchMedia` change listener to re-resolve `effectiveTheme` when OS preference changes; clean up on unmount or when theme changes away from `'system'`
- On `setTheme`: persist new value to `localStorage`

**Exports:** `ThemeProvider` (wraps children), `useTheme()` hook returning `{ theme, setTheme, effectiveTheme }`.

---

## 3. Toggle Button (`frontend/src/components/Topbar.jsx`)

**Placement:** Right side of the topbar, to the left of the existing badge pills.

**Behavior:** Clicking cycles through `system → light → dark → system`.

**Icon:** Shows the *current effective mode* with a small indicator for system-following:
- Effective dark + system: 🖥 (system following dark)
- Effective light + system: 🖥 (system following light)
- Manual dark: 🌙
- Manual light: ☀️

**Styling:** Matches the existing `.badge-pill` style (same height, same border radius). No separate new CSS class needed unless the pill style needs minor adjustment for an icon-only button.

---

## 4. App Integration (`frontend/src/App.jsx`)

Wrap the top-level JSX return in `<ThemeProvider>`. No other changes to `App.jsx`.

---

## Files Changed

| File | Change |
|---|---|
| `frontend/src/index.css` | Add `[data-theme="light"]` variable override block |
| `frontend/src/ThemeContext.jsx` | New file — context, provider, hook |
| `frontend/src/components/Topbar.jsx` | Import `useTheme`, add toggle button |
| `frontend/src/App.jsx` | Wrap in `<ThemeProvider>` |

---

## Out of Scope

- Per-component theme customization
- More than two themes (light/dark)
- Any backend or API changes

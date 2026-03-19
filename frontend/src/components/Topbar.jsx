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
          style={{ cursor: 'pointer', fontSize: '13px', minWidth: '28px', textAlign: 'center' }}
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

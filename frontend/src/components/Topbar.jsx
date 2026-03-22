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

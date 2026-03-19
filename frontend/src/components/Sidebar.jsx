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

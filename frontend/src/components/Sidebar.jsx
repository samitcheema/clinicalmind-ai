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

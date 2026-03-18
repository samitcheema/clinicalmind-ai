export default function Header({ status }) {
  const date = new Date().toLocaleDateString('en-US', { weekday:'short', month:'short', day:'numeric', year:'numeric' });
  const badgeCls = `status-badge ${status.state === 'error' ? 'error' : status.state === 'ok' ? 'ok' : ''}`;
  return (
    <header className="header">
      <div className="header-logo">🧠</div>
      <div>
        <div className="header-title">ClinicalMind AI</div>
        <div className="header-sub">Behavioral Health Decision Support</div>
      </div>
      <div className="header-right">
        <span className="header-date">{date}</span>
        <span className={badgeCls}>{status.msg}</span>
      </div>
    </header>
  );
}

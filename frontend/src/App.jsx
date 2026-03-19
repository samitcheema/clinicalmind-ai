import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Topbar  from './components/Topbar';
import Dashboard from './components/Dashboard.jsx';
import PatientTable from './components/PatientTable.jsx';
import ChatPane from './components/ChatPane.jsx';
import { loadPatients } from './utils/dataTransform.js';

export default function App() {
  const [patients, setPatients] = useState([]);
  const [status, setStatus] = useState({ state: 'loading', msg: 'Loading data…' });
  const [activeView, setActiveView] = useState('dashboard');
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
        {activeView === 'chat' ? (
          <ChatPane
            patients={patients}
            apiKey={apiKey}
            onNeedKey={() => setShowApiSetup(true)}
          />
        ) : (
          <div className="content-scroll">
            {activeView === 'dashboard' && <Dashboard patients={patients} loading={status.state === 'loading'} />}
            {activeView === 'patients'  && <PatientTable patients={patients} />}
          </div>
        )}
      </div>
    </div>
  );
}

import { useState, useEffect } from 'react';
import Header from './components/Header.jsx';
import Dashboard from './components/Dashboard.jsx';
import ChatPane from './components/ChatPane.jsx';
import { loadPatients } from './utils/dataTransform.js';

export default function App() {
  const [patients, setPatients] = useState([]);
  const [status, setStatus] = useState({ state: 'loading', msg: 'Loading data…' });
  const [tab, setTab] = useState('dashboard');
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

  function handleTabChange(t) {
    setTab(t);
    if (t === 'chat' && !apiKey) setShowApiSetup(true);
    if (t === 'dashboard') setShowApiSetup(false);
  }

  return (
    <div className="app">
      <Header status={status} />
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
          <span className="api-note">Stored in your browser only</span>
        </div>
      )}
      <nav className="tab-nav">
        <button className={`tab-btn ${tab==='dashboard'?'active':''}`} onClick={() => handleTabChange('dashboard')}>📊 Dashboard</button>
        <button className={`tab-btn ${tab==='chat'?'active':''}`} onClick={() => handleTabChange('chat')}>💬 AI Chat</button>
      </nav>
      <div className="content">
        {tab === 'dashboard'
          ? <Dashboard patients={patients} loading={status.state==='loading'} />
          : <ChatPane patients={patients} apiKey={apiKey} onNeedKey={() => setShowApiSetup(true)} />
        }
      </div>
      <footer className="footer">
        <a href="https://github.com/samitcheema/clinicalmind-ai" target="_blank" rel="noreferrer">GitHub</a>
        {' · Synthetic data only · Not for clinical use'}
      </footer>
    </div>
  );
}

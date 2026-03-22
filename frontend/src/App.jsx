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
              {/* IMDashboard takes no props — reads from imMockData.js directly.
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

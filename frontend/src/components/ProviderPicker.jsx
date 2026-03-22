// frontend/src/components/ProviderPicker.jsx
import { useState } from 'react';
import { useProvider } from '../ProviderContext';

const BH_PROVIDERS = [
  { provider_id: 'PROV001', name: 'Dr. Emma Chen',       team: 'ACT-1', specialty: 'BH' },
  { provider_id: 'PROV002', name: 'Dr. Marcus Williams', team: 'ACT-1', specialty: 'BH' },
  { provider_id: 'PROV003', name: 'Dr. Priya Sharma',    team: 'ACT-2', specialty: 'BH' },
  { provider_id: 'PROV004', name: "Dr. James O'Brien",   team: 'ACT-2', specialty: 'BH' },
  { provider_id: 'PROV005', name: 'Dr. Sarah Nakamura',  team: 'CSP-1', specialty: 'BH' },
  { provider_id: 'PROV006', name: 'Dr. Robert Kim',      team: 'CSP-1', specialty: 'BH' },
];

const IM_PROVIDERS = [
  { provider_id: 'PROV007', name: 'Dr. Linda Park',   team: 'IM-1', specialty: 'IM' },
  { provider_id: 'PROV008', name: 'Dr. Ahmed Hassan', team: 'IM-1', specialty: 'IM' },
];

export default function ProviderPicker() {
  const { setProvider } = useProvider();
  const [specialty, setSpecialty] = useState(null);

  const providers = specialty === 'BH' ? BH_PROVIDERS : IM_PROVIDERS;

  return (
    <div className="provider-picker-overlay">
      <div className="provider-picker">
        <div className="picker-logo">
          <div className="logo-text" style={{ fontSize: '20px' }}>ClinicalMind</div>
          <div className="logo-sub">Select your profile to continue</div>
        </div>

        {!specialty ? (
          <>
            <h2 className="picker-heading">Choose your specialty</h2>
            <div className="picker-cards">
              <div className="picker-card" onClick={() => setSpecialty('BH')}>
                <div className="picker-card-icon">🧠</div>
                <div className="picker-card-title">Behavioral Health</div>
                <div className="picker-card-sub">ACT-1 · ACT-2 · CSP-1</div>
              </div>
              <div className="picker-card" onClick={() => setSpecialty('IM')}>
                <div className="picker-card-icon">🏥</div>
                <div className="picker-card-title">Internal Medicine</div>
                <div className="picker-card-sub">IM-1</div>
              </div>
            </div>
          </>
        ) : (
          <>
            <h2 className="picker-heading">
              <button className="picker-back" onClick={() => setSpecialty(null)}>← Back</button>
              Choose your provider
            </h2>
            <div className="picker-provider-list">
              {providers.map(p => (
                <div key={p.provider_id} className="picker-provider-card" onClick={() => setProvider(p)}>
                  <div className="picker-provider-name">{p.name}</div>
                  <div className="picker-provider-sub">{p.team} · {p.provider_id}</div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

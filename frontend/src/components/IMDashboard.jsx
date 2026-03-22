// frontend/src/components/IMDashboard.jsx
import { useMemo } from 'react';
import {
  getImPatients,
  getChronicDiseasePanel,
  getPreventiveCareGaps,
} from '../utils/imMockData.js';

// Returns ↑ / ↓ / → based on the last two values in a history array
function trendArrow(history, valueKey = 'value') {
  if (!history || history.length < 2) return '→';
  const last = history.at(-1)[valueKey];
  const prev = history.at(-2)[valueKey];
  if (last > prev) return '↑';
  if (last < prev) return '↓';
  return '→';
}

// Annualized eGFR slope — intentionally local to keep display separate from data module.
// Rounds to one decimal for display; imMockData.js keeps the raw value for filtering.
function eGFRSlope(egfr_history) {
  if (!egfr_history || egfr_history.length < 2) return null;
  const pts = egfr_history.map(e => {
    const d = new Date(e.date);
    return { t: d.getUTCFullYear() + d.getUTCMonth() / 12, v: e.value };
  });
  const n = pts.length;
  const sumT  = pts.reduce((s, p) => s + p.t, 0);
  const sumV  = pts.reduce((s, p) => s + p.v, 0);
  const sumTT = pts.reduce((s, p) => s + p.t * p.t, 0);
  const sumTV = pts.reduce((s, p) => s + p.t * p.v, 0);
  const denom = n * sumTT - sumT * sumT;
  if (denom === 0) return null;
  return Math.round(((n * sumTV - sumT * sumV) / denom) * 10) / 10;
}

function StatCard({ label, value, color }) {
  return (
    <div className="stat-card" style={{ borderLeftColor: `var(--${color})` }}>
      <div className="sc-label">{label}</div>
      <div className="sc-value" style={{ color: `var(--${color})` }}>{value}</div>
    </div>
  );
}

function DiseasePanel({ title, rows, emptyMsg }) {
  return (
    <div className="disease-panel">
      <div className="panel-title">{title}</div>
      {rows.length === 0 ? (
        <div className="panel-empty">{emptyMsg}</div>
      ) : (
        <table className="panel-table">
          <tbody>
            {rows.map((row, i) => (
              <tr key={i}>
                <td className="panel-name">{row.name}</td>
                <td className="panel-metric">{row.metric}</td>
                <td className="panel-trend">{row.trend}</td>
                <td className={`panel-risk risk-${row.risk_level?.toLowerCase()}`}>{row.risk_level}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default function IMDashboard() {
  const data = useMemo(() => {
    const highRisk   = getImPatients({ risk_level: 'High' });
    const diabetics  = getChronicDiseasePanel('diabetes')
      .sort((a, b) => (b.a1c_history.at(-1)?.value ?? 0) - (a.a1c_history.at(-1)?.value ?? 0));
    const ckd        = getChronicDiseasePanel('ckd')
      .sort((a, b) => (eGFRSlope(a.egfr_history) ?? 0) - (eGFRSlope(b.egfr_history) ?? 0));
    const hypertensive = getChronicDiseasePanel('hypertension')
      .sort((a, b) => (b.bp_history.at(-1)?.systolic ?? 0) - (a.bp_history.at(-1)?.systolic ?? 0));
    const gaps       = getPreventiveCareGaps();
    return { highRisk, diabetics, ckd, hypertensive, gaps };
  }, []);

  const diabetesRows = data.diabetics.map(p => ({
    name:      p.name,
    metric:    `A1c ${p.a1c_history.at(-1)?.value}`,
    trend:     trendArrow(p.a1c_history),
    risk_level: p.risk_level,
  }));

  const ckdRows = data.ckd.map(p => {
    const slope = eGFRSlope(p.egfr_history);
    return {
      name:      p.name,
      metric:    slope != null ? `${slope}/yr` : '—',
      trend:     '↓',
      risk_level: p.risk_level,
    };
  });

  const htRows = data.hypertensive.map(p => {
    const bp = p.bp_history.at(-1);
    return {
      name:      p.name,
      metric:    bp ? `${bp.systolic}/${bp.diastolic}` : '—',
      trend:     trendArrow(p.bp_history, 'systolic'),
      risk_level: p.risk_level,
    };
  });

  return (
    <div className="dashboard-pane">
      <div className="dash-inner">
        <div className="stat-grid">
          <StatCard label="High Risk"    value={data.highRisk.length}      color="red"     />
          <StatCard label="A1c > 8.0"   value={data.diabetics.length}     color="amber"   />
          <StatCard label="Care Gaps"   value={data.gaps.length}          color="primary" />
        </div>

        <div className="disease-panels">
          <DiseasePanel
            title="🩸 Diabetes — A1c > 8.0"
            rows={diabetesRows}
            emptyMsg="No patients with A1c > 8.0"
          />
          <DiseasePanel
            title="🫘 CKD — eGFR slope ≤ −3/yr"
            rows={ckdRows}
            emptyMsg="No patients with declining kidney function"
          />
          <DiseasePanel
            title="💗 Hypertension — systolic > 140"
            rows={htRows}
            emptyMsg="No patients with uncontrolled hypertension"
          />
        </div>
      </div>
    </div>
  );
}

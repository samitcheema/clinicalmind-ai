import { useMemo } from 'react';
import { KPI_NAMES, KPI_DISPLAY } from '../utils/dataTransform.js';
import { offsetDate, TODAY } from '../utils/mockGenerators.js';
import PatientTable from './PatientTable.jsx';

const CARD_META = {
  patients:   { trend:'↑ 3 wk',  trendCls:'trend-up',      sparkPts:'0,15 20,13 40,14 60,10 80,11 100,8 120,6', stroke:'var(--primary)' },
  crisis_7d:  { trend:'↓ 1 7d',  trendCls:'trend-down',    sparkPts:'0,12 20,14 40,10 60,13 80,8 100,11 120,8', stroke:'var(--amber)'   },
  kpi:        { trend:'↑ 4% mo', trendCls:'trend-up',      sparkPts:'0,14 20,13 40,12 60,11 80,10 100,9 120,7', stroke:'var(--green)'   },
};

function computeStats(patients) {
  const total = patients.length;
  if (!total) return null;
  const kpiStats = {};
  for (const k of KPI_NAMES) {
    const overdue = patients.filter(p=>p.kpis[k].overdue).length;
    kpiStats[k] = { compliant:total-overdue, overdue, pct:Math.round((total-overdue)/total*100) };
  }
  const totalKpis = total*KPI_NAMES.length;
  const overdueTotal = KPI_NAMES.reduce((s,k)=>s+kpiStats[k].overdue,0);
  const overallPct = Math.round((totalKpis-overdueTotal)/totalKpis*100);

  const cutoff7 = offsetDate(TODAY,-7);
  const cutoff28 = offsetDate(TODAY, -28);
  const activeCrisis = patients.filter(p=>p.crisis_events.some(e=>e.date>=cutoff7&&!e.resolved)).length;

  const alerts = [];
  for (const p of patients) {
    if (p.phq9.si_present || p.ssrs.risk_level==='High')
      alerts.push({ name:p.name, reason:p.phq9.si_present?'Suicidal ideation present':'SSRS High risk', level:'red', id:p.id });
    else if (p.crisis_events.some(e=>e.date>=cutoff28&&!e.resolved))
      alerts.push({ name:p.name, reason:'Unresolved crisis event (28d)', level:'red', id:p.id });
    else if (p.phq9.score>=15)
      alerts.push({ name:p.name, reason:`PHQ-9 score ${p.phq9.score} (Severe)`, level:'amber', id:p.id });
  }

  return { total, kpiStats, overdueTotal, overallPct, activeCrisis, alerts };
}

export default function BHDashboard({ patients, loading }) {
  const s = useMemo(() => computeStats(patients), [patients]);

  if (loading || !s) {
    return (
      <div className="dashboard-pane">
        <div className="dash-inner" style={{textAlign:'center',padding:'60px',color:'#94a3b8'}}>
          {loading ? 'Loading patient data…' : 'No data available'}
        </div>
      </div>
    );
  }

  const overdueTotal = s.overdueTotal;
  const kpiColor = overdueTotal === 0 ? 'green' : 'amber';

  return (
    <div className="dashboard-pane">
      <div className="dash-inner">

        {/* Stat Cards */}
        <div className="stat-grid">
          <div className="stat-card blue">
            <div className="sc-top">
              <div className="sc-icon" style={{ background:'var(--blue-bg)' }}>👥</div>
              <span className={`sc-trend ${CARD_META.patients.trendCls}`}>{CARD_META.patients.trend}</span>
            </div>
            <div className="sc-label">TOTAL PATIENTS</div>
            <div className="sc-value">{s.total}</div>
            <div className="sc-sub">{s.activeCrisis} active crisis events</div>
            <svg className="sc-sparkline" viewBox="0 0 120 20" preserveAspectRatio="none">
              <polyline points={CARD_META.patients.sparkPts} fill="none" stroke={CARD_META.patients.stroke} strokeWidth="1.5" opacity="0.6"/>
            </svg>
          </div>

          <div className="stat-card amber">
            <div className="sc-top">
              <div className="sc-icon" style={{ background:'var(--amber-bg)' }}>🚨</div>
              <span className={`sc-trend ${CARD_META.crisis_7d.trendCls}`}>{CARD_META.crisis_7d.trend}</span>
            </div>
            <div className="sc-label">CRISIS EVENTS (7D)</div>
            <div className="sc-value" style={{ color:'var(--amber)' }}>{s.activeCrisis}</div>
            <div className="sc-sub">active unresolved events</div>
            <svg className="sc-sparkline" viewBox="0 0 120 20" preserveAspectRatio="none">
              <polyline points={CARD_META.crisis_7d.sparkPts} fill="none" stroke={CARD_META.crisis_7d.stroke} strokeWidth="1.5" opacity="0.6"/>
            </svg>
          </div>

          <div className={`stat-card ${kpiColor}`}>
            <div className="sc-top">
              <div className="sc-icon" style={{ background: kpiColor === 'green' ? 'var(--green-bg)' : 'var(--amber-bg)' }}>📋</div>
              <span className={`sc-trend ${CARD_META.kpi.trendCls}`}>{CARD_META.kpi.trend}</span>
            </div>
            <div className="sc-label">KPI COMPLIANCE</div>
            <div className={`sc-value ${kpiColor}`}>{s.overallPct}%</div>
            <div className="sc-sub">overall across all KPIs</div>
            <svg className="sc-sparkline" viewBox="0 0 120 20" preserveAspectRatio="none">
              <polyline points={CARD_META.kpi.sparkPts} fill="none" stroke={CARD_META.kpi.stroke} strokeWidth="1.5" opacity="0.6"/>
            </svg>
          </div>
        </div>

        {/* Mid Row */}
        <div className="mid-row">
          {/* KPI Panel */}
          <div className="panel">
            <div className="panel-title">KPI Compliance</div>
            {KPI_NAMES.map(k => {
              const { pct, compliant, overdue } = s.kpiStats[k];
              const barColor = overdue === 0 ? 'var(--green)' : pct >= 50 ? 'var(--amber)' : 'var(--red)';
              return (
                <div key={k} className="kpi-bar-item">
                  <div className="kpi-bar-header">
                    <span className="kpi-bar-label">{KPI_DISPLAY[k]}</span>
                    <span className="kpi-bar-pct">{pct}% <small>({compliant}/{compliant + overdue})</small></span>
                  </div>
                  <div className="kpi-bar-track">
                    <div className="kpi-bar-fill" style={{ width:`${pct}%`, background: barColor }} />
                  </div>
                </div>
              );
            })}
            <div className="panel-avg">
              Avg <strong>{s.overallPct}%</strong> across {KPI_NAMES.length} KPIs
            </div>
          </div>

          {/* Alerts Panel */}
          <div className="panel">
            <div className="panel-title">⚠️ Priority Alerts</div>
            {s.alerts.length === 0
              ? <div style={{color:'#94a3b8',fontSize:'12px'}}>No active alerts</div>
              : s.alerts.slice(0,6).map((a,i) => (
                <div key={i} className="alert-item">
                  <div className={`alert-dot ${a.level}`} />
                  <div>
                    <div className="alert-name">{a.name}</div>
                    <div className="alert-reason">{a.reason}</div>
                  </div>
                </div>
              ))
            }
          </div>
        </div>

        {/* Patient Table */}
        <div className="panel" style={{marginBottom:20}}>
          <PatientTable patients={patients} />
        </div>

      </div>
    </div>
  );
}

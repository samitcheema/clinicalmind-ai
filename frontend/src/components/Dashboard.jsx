import { useMemo } from 'react';
import { KPI_NAMES, KPI_DISPLAY } from '../utils/dataTransform.js';
import { offsetDate, TODAY, fmtDate } from '../utils/mockGenerators.js';
import PatientTable from './PatientTable.jsx';

const CARD_META = {
  patients:   { trend:'↑ 3 wk',  trendCls:'trend-up',      sparkPts:'0,15 20,13 40,14 60,10 80,11 100,8 120,6', stroke:'var(--primary)' },
  high_risk:  { trend:'— same',  trendCls:'trend-neutral',  sparkPts:'0,10 20,8 40,12 60,9 80,11 100,8 120,9',  stroke:'var(--red)'     },
  crisis_7d:  { trend:'↓ 1 7d',  trendCls:'trend-down',    sparkPts:'0,12 20,14 40,10 60,13 80,8 100,11 120,8', stroke:'var(--amber)'   },
  kpi:        { trend:'↑ 4% mo', trendCls:'trend-up',      sparkPts:'0,14 20,13 40,12 60,11 80,10 100,9 120,7', stroke:'var(--green)'   },
};

function computeStats(patients) {
  const total = patients.length;
  if (!total) return null;
  const byRisk = { High:0, Moderate:0, Low:0 };
  for (const p of patients) byRisk[p.risk_level] = (byRisk[p.risk_level]||0)+1;

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

  return { total, byRisk, kpiStats, overdueTotal, overallPct, activeCrisis, alerts };
}

export default function Dashboard({ patients, loading }) {
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
            <div className="sc-sub">{s.byRisk.High} high · {s.byRisk.Moderate} moderate</div>
            <svg className="sc-sparkline" viewBox="0 0 120 20" preserveAspectRatio="none">
              <polyline points={CARD_META.patients.sparkPts} fill="none" stroke={CARD_META.patients.stroke} strokeWidth="1.5" opacity="0.6"/>
            </svg>
          </div>

          <div className="stat-card red">
            <div className="sc-top">
              <div className="sc-icon" style={{ background:'var(--red-bg)' }}>⚠️</div>
              <span className={`sc-trend ${CARD_META.high_risk.trendCls}`}>{CARD_META.high_risk.trend}</span>
            </div>
            <div className="sc-label">HIGH RISK</div>
            <div className="sc-value" style={{ color:'var(--red)' }}>{s.byRisk.High}</div>
            <div className="sc-sub">{s.alerts.filter(a => a.level === 'red').length} need review</div>
            <svg className="sc-sparkline" viewBox="0 0 120 20" preserveAspectRatio="none">
              <polyline points={CARD_META.high_risk.sparkPts} fill="none" stroke={CARD_META.high_risk.stroke} strokeWidth="1.5" opacity="0.6"/>
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
            <div className="kpi-ring-grid">
              {KPI_NAMES.map(k => {
                const { pct, compliant, overdue } = s.kpiStats[k];
                const r = 20;
                const circ = 2 * Math.PI * r; // 125.66
                const offset = circ - (pct / 100) * circ;
                const ringColor = overdue === 0 ? 'var(--green)' : pct >= 50 ? 'var(--amber)' : 'var(--red)';
                return (
                  <div key={k} className="kpi-ring-item">
                    <svg viewBox="0 0 52 52" className="kpi-ring-svg">
                      <circle cx="26" cy="26" r={r} fill="none" stroke="var(--ring-track)" strokeWidth="4" />
                      <circle
                        cx="26" cy="26" r={r}
                        fill="none"
                        stroke={ringColor}
                        strokeWidth="4"
                        strokeLinecap="round"
                        strokeDasharray={`${circ} ${circ}`}
                        strokeDashoffset={offset}
                        transform="rotate(-90 26 26)"
                      />
                      <text x="26" y="30" textAnchor="middle" fontSize="9" fontWeight="700" fill="var(--text)">{pct}%</text>
                    </svg>
                    <div className="kpi-ring-label">{KPI_DISPLAY[k]}</div>
                    <div className="kpi-ring-sub">{compliant}/{compliant + overdue}</div>
                  </div>
                );
              })}
            </div>
            <div className="panel-avg">
              Avg <strong>{s.overallPct}%</strong> across {KPI_NAMES.length} KPIs
            </div>
          </div>

          {/* Risk Panel */}
          <div className="panel">
            <div className="panel-title">Risk Distribution</div>
            {['High','Moderate','Low'].map(r => {
              const cnt = s.byRisk[r]||0;
              const pct = Math.round(cnt/s.total*100);
              return (
                <div key={r} className="risk-item">
                  <div className="risk-item-header">
                    <span className={`risk-lbl ${r}`}>{r}</span>
                    <span className="risk-cnt">{cnt} <small style={{color:'#94a3b8',fontWeight:400}}>({pct}%)</small></span>
                  </div>
                  <div className="risk-bar">
                    <div className={`risk-bar-fill ${r}`} style={{width:`${pct}%`}} />
                  </div>
                </div>
              );
            })}
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

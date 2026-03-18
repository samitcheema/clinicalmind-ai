import { useMemo } from 'react';
import { KPI_NAMES, KPI_DISPLAY, KPI_TARGET } from '../utils/dataTransform.js';
import { offsetDate, TODAY, fmtDate } from '../utils/mockGenerators.js';
import PatientTable from './PatientTable.jsx';

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

  return { total, byRisk, kpiStats, overallPct, activeCrisis, alerts };
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

  const kpiColor = s.overallPct >= KPI_TARGET ? 'green' : 'amber';
  const crisisColor = s.activeCrisis > 0 ? 'red' : 'green';

  return (
    <div className="dashboard-pane">
      <div className="dash-inner">

        {/* Stat Cards */}
        <div className="stat-cards">
          <div className="stat-card blue">
            <span className="sc-icon">👥</span>
            <div className="sc-label">Total Patients</div>
            <div className="sc-value">{s.total}</div>
            <div className="sc-sub">Active caseload</div>
          </div>
          <div className="stat-card red">
            <span className="sc-icon">⚠️</span>
            <div className="sc-label">High Risk</div>
            <div className={`sc-value ${s.byRisk.High>0?'red':''}`}>{s.byRisk.High}</div>
            <div className="sc-sub">{Math.round(s.byRisk.High/s.total*100)}% of caseload</div>
          </div>
          <div className={`stat-card ${kpiColor}`}>
            <span className="sc-icon">📋</span>
            <div className="sc-label">KPI Compliance</div>
            <div className={`sc-value ${kpiColor}`}>{s.overallPct}%</div>
            <div className="sc-sub">Target: {KPI_TARGET}%</div>
          </div>
          <div className={`stat-card ${crisisColor}`}>
            <span className="sc-icon">🚨</span>
            <div className="sc-label">Active Crisis</div>
            <div className={`sc-value ${crisisColor}`}>{s.activeCrisis}</div>
            <div className="sc-sub">Admitted to crisis unit</div>
          </div>
        </div>

        {/* Mid Row */}
        <div className="mid-row">
          {/* KPI Panel */}
          <div className="panel">
            <div className="panel-title">KPI Compliance vs 75% Target</div>
            {KPI_NAMES.map(k => {
              const pct = s.kpiStats[k].pct;
              const cls = pct >= KPI_TARGET ? 'meets' : 'below';
              return (
                <div key={k} className="kpi-row">
                  <span className="kpi-name">{KPI_DISPLAY[k]}</span>
                  <div className="kpi-bar-outer">
                    <div className="kpi-bar-bg">
                      <div className={`kpi-bar-fill ${cls}`} style={{width:`${pct}%`}} />
                    </div>
                    <div className="kpi-target-tick" />
                  </div>
                  <span className={`kpi-pct ${cls}`}>{pct}%</span>
                </div>
              );
            })}
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

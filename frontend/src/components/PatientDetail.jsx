import { KPI_NAMES, KPI_DISPLAY, PHQ9_ITEMS } from '../utils/dataTransform.js';
import { daysBetween } from '../utils/tools.js';
import { fmtDate, TODAY } from '../utils/mockGenerators.js';
import EncounterTimeline from './EncounterTimeline.jsx';

const CSSRS_ITEMS = [
  { label:'Wish to be Dead',    key:'wish_dead'          },
  { label:'Suicidal Thoughts',  key:'suicidal_thoughts'  },
  { label:'Suicidal Intent',    key:'suicidal_intent'    },
  { label:'Intent with Plan',   key:'suicidal_with_plan' },
  { label:'With Method',        key:'suicidal_method'    },
  { label:'History of Attempt', key:'history_suicide'    },
];

export default function PatientDetail({ patient: p }) {
  const days = daysBetween(p.last_contact_date);
  const daysLbl = days >= 999 ? 'Unknown' : `${days}d ago`;

  const age = p.dob
    ? Math.floor((new Date(TODAY) - new Date(p.dob)) / 31557600000) + 'y'
    : '—';

  // PHQ-9 item scores: derive from total if item_scores unavailable
  const phqItems = PHQ9_ITEMS.map((label, i) => {
    const raw = p.phq9.items?.[i];
    const score = raw != null ? Math.round(raw) : (i===8&&p.phq9.si_present ? 1 : Math.min(3, Math.round(p.phq9.score / 9 * (3 - i * 0.15))));
    return { label, score: Math.max(0, Math.min(3, score)) };
  });

  const ci = p.cssrs_items || {};

  return (
    <div className="detail-panel">
      {/* Header */}
      <div className="detail-header">
        <div>
          <div className="dh-name">{p.name}</div>
          <div className="dh-meta">
            {p.id} · DOB: {fmtDate(p.dob)} ({age}) · {p.county} · {p.service_type} · Provider: {p.provider}
          </div>
        </div>
        <div className="dh-badges">
          <span className={`risk-badge ${p.risk_level}`}>{p.risk_level} Risk</span>
          <span className={`ssrs-badge ${p.ssrs.risk_level}`}>SSRS {p.ssrs.risk_level}</span>
          {p.phq9.si_present && <span className="si-badge">⚠ SI Present</span>}
        </div>
      </div>

      {/* Left Column */}
      <div>
        {/* Score Pills */}
        <div className="score-row">
          {[
            { label:'PHQ-9', val:p.phq9.score, sub:p.phq9.score>=15?'Severe':p.phq9.score>=10?'Moderate':p.phq9.score>=5?'Mild':'Minimal', cls:p.phq9.score>=15||p.phq9.si_present?'hi':p.phq9.score>=10?'mod':'' },
            { label:'GAD-7', val:p.gad7.score, sub:p.gad7.severity||'—', cls:'' },
            { label:'WHODAS', val:p.whodas.score, sub:p.whodas.level||'—', cls:'' },
            { label:'Last Contact', val:daysLbl, sub:p.last_contact_date||'—', cls:'', small:true },
          ].map(s => (
            <div key={s.label} className="score-pill">
              <div className="score-pill-label">{s.label}</div>
              <div className={`score-pill-value${s.cls?' '+s.cls:''}${s.small?' ':''}`} style={s.small?{fontSize:'14px'}:{}}>{s.val}</div>
              <div className="score-pill-sub">{s.sub}</div>
            </div>
          ))}
        </div>

        {/* PHQ-9 Items */}
        <div className="section-title">PHQ-9 Item Breakdown</div>
        <div className="phq-items">
          {phqItems.map(({ label, score }) => (
            <div key={label} className="phq-item">
              <span className="phq-item-label">{label}</span>
              <div className="phq-item-bar"><div className={`phq-item-fill s${score}`} /></div>
              <span className="phq-item-score">{score}</span>
            </div>
          ))}
        </div>

        {/* C-SSRS */}
        <div className="section-title">C-SSRS Items</div>
        <div className="cssrs-grid">
          {CSSRS_ITEMS.map(({ label, key }) => {
            const val = ci[key] || 'No';
            return (
              <div key={key} className={`cssrs-item${val==='Yes'?' yes':''}`}>
                <span className="cssrs-label">{label}</span>
                <span className="cssrs-val">{val}</span>
              </div>
            );
          })}
        </div>

        {/* KPI Grid */}
        <div className="section-title">KPI Compliance</div>
        <div className="kpi-detail-grid">
          {KPI_NAMES.map(k => (
            <div key={k} className={`kdi${p.kpis[k].overdue?' overdue':''}`}>
              <span className="kdi-name">{KPI_DISPLAY[k]}</span>
              <div className="kdi-status">{p.kpis[k].overdue ? '❌' : '✅'}</div>
              <div className="kdi-date">{p.kpis[k].due_date || '—'}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Right Column */}
      <div>
        {/* Encounter Timeline */}
        <div className="section-title">Encounter Timeline</div>
        <div style={{maxHeight:220,overflowY:'auto',paddingRight:4,marginBottom:16}}>
          <EncounterTimeline encounters={p.encounters || []} />
        </div>

        {/* Medications */}
        <div className="section-title">Active Medications</div>
        <div className="med-list" style={{marginBottom:16}}>
          {(p.medications||[]).length === 0
            ? <div style={{color:'#94a3b8',fontSize:'12px'}}>No medications on file</div>
            : (p.medications||[]).map((m,i) => (
              <div key={i} className="med-item">
                <div style={{flex:1}}>
                  <div className="med-name">{m.name}</div>
                  <div className="med-dosage">{m.dosage}</div>
                </div>
                <span className="med-class">{m.drug_class}</span>
              </div>
            ))
          }
        </div>

        {/* Diagnoses */}
        <div className="section-title">Diagnoses</div>
        <div className="diag-list">
          {(p.diagnoses||[]).length === 0
            ? <div style={{color:'#94a3b8',fontSize:'12px'}}>No diagnoses on file</div>
            : (p.diagnoses||[]).map((d,i) => (
              <div key={i} className="diag-item">
                <span className="diag-code">{d.code}</span>
                <div>
                  <div className="diag-desc">{d.desc}</div>
                  <div className="diag-cat">{d.category} · Since {fmtDate(d.start_date)}</div>
                </div>
              </div>
            ))
          }
        </div>
      </div>
    </div>
  );
}

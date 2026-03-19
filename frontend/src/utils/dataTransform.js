import { hashStr, mkRand, generateEncounters, generateDiagnoses, generateMedications, generateCSSRS } from './mockGenerators.js';
import { getMockPatients } from './mockSeeds.js';

export const KPI_NAMES   = ['bha','sra','aims','whodas','phq9','beh_tp','beh_csp'];
export const KPI_DISPLAY = { bha:'BHA', sra:'SRA', aims:'AIMS', whodas:'WHODAS', phq9:'PHQ-9', beh_tp:'BEH-TP', beh_csp:'BEH-CSP' };
export const RISK_ORDER  = { High:0, Moderate:1, Low:2 };
export const PHQ9_ITEMS  = ['Interest','Feeling Hopeless','Trouble Sleeping','Feeling Tired','Poor Appetite','Feeling Bad','Trouble Concentrating','Moving Slowly','Better Off Dead'];

function _latest(arr) {
  if (!arr?.length) return {};
  return arr.slice().sort((a,b) => (b.assessment_date||'') > (a.assessment_date||'') ? 1 : -1)[0];
}

export function transformPatient(row) {
  const phq9   = _latest(row.assessments_phq9);
  const gad7   = _latest(row.assessments_gad7);
  const whodas = _latest(row.assessments_whodas);
  const ssrs   = _latest(row.assessments_ssrs);

  const kpiMap = {};
  for (const k of KPI_NAMES) {
    const m = (row.kpi_compliance||[]).find(r=>r.kpi_name===k)||{};
    kpiMap[k] = { last_completed:m.last_completed||null, due_date:m.due_date||null, overdue:!!m.overdue };
  }

  const prov = row.providers || {};
  const p = {
    id:                row.patient_id,
    name:              row.name,
    dob:               row.date_of_birth,
    county:            row.county || '',
    service_type:      row.service_type || '',
    diagnosis:         row.diagnosis || '',
    provider:          prov.name || row.provider_id || '',
    team:              prov.team || '',
    risk_level:        row.risk_level || 'Low',
    last_contact_date: row.last_contact_date || null,
    phq9: { score: phq9.total_score||0, si_present:!!phq9.suicidal_ideation, date:phq9.assessment_date||null, items:phq9.item_scores||[] },
    gad7: { score: gad7.total_score||0, severity:gad7.severity||'', date:gad7.assessment_date||null },
    whodas: { score: whodas.total_score||0, level:whodas.disability_level||'', date:whodas.assessment_date||null },
    ssrs: { risk_level:ssrs.risk_level||'Low', plan_present:!!ssrs.plan, method_present:!!ssrs.method, intent:!!ssrs.intent, ideation:!!ssrs.suicidal_ideation, history:!!ssrs.history_attempt, date:ssrs.assessment_date||null },
    crisis_events: (row.crisis_events||[]).map(e=>({ date:e.crisis_date, type:e.crisis_type, resolved:!e.within_28_days })),
    kpis: kpiMap,
  };

  const rand = mkRand(hashStr(p.id || p.name || 'x'));
  p.encounters  = generateEncounters(p, rand);
  p.diagnoses   = generateDiagnoses(p, rand);
  p.medications = generateMedications(p, rand);
  p.cssrs_items = generateCSSRS(p, rand);
  return p;
}

export const PROXY = 'https://clinicalmind-ai.samitcheema.workers.dev/';

export async function loadPatients() {
  const select = [
    '*',
    'providers(name,team)',
    'assessments_phq9(assessment_date,total_score,suicidal_ideation,severity,item_scores)',
    'assessments_gad7(assessment_date,total_score,severity)',
    'assessments_whodas(assessment_date,total_score,disability_level)',
    'assessments_ssrs(assessment_date,suicidal_ideation,ideation_intensity,intent,plan,method,history_attempt,risk_level)',
    'kpi_compliance(kpi_name,last_completed,due_date,overdue)',
    'crisis_events(event_id,crisis_date,crisis_type,within_7_days,within_28_days,days_since)',
  ].join(',');

  try {
    const res = await fetch(`${PROXY}supabase/patients?select=${select}&order=patient_id`, { headers: { Accept:'application/json' } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const rows = await res.json();
    if (rows.length > 0) return rows.map(transformPatient);
  } catch (_) { /* fall through to demo data */ }

  return getMockPatients();
}

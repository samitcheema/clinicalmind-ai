import { KPI_NAMES, KPI_TARGET, PHQ9_ITEMS } from './dataTransform.js';
import { TODAY, offsetDate } from './mockGenerators.js';

export function daysBetween(dateStr) {
  if (!dateStr) return 999;
  return Math.round((new Date(TODAY) - new Date(dateStr)) / 86400000);
}

export function getPatients(patients, { risk_level, county, provider } = {}) {
  let pts = patients;
  if (risk_level) pts = pts.filter(p=>p.risk_level===risk_level);
  if (county)     pts = pts.filter(p=>p.county.toLowerCase().includes(county.toLowerCase()));
  if (provider)   pts = pts.filter(p=>p.provider.toLowerCase().includes(provider.toLowerCase()));
  return { total:pts.length, filters:{risk_level:risk_level||null,county:county||null,provider:provider||null},
    patients:pts.map(p=>({ id:p.id,name:p.name,risk_level:p.risk_level,county:p.county,provider:p.provider,phq9_score:p.phq9.score,si_present:p.phq9.si_present,last_contact_date:p.last_contact_date,days_since_contact:daysBetween(p.last_contact_date),open_crisis_events:p.crisis_events.filter(e=>!e.resolved).length })) };
}

export function getPatientDetail(patients, { patient_id } = {}) {
  const p = patients.find(x=>x.id===patient_id);
  if (!p) return { error:`Patient ${patient_id} not found` };
  return { ...p, days_since_contact:daysBetween(p.last_contact_date) };
}

export function getPatientHistory(patients, { patient_id, lookback_days=365 } = {}) {
  const p = patients.find(x=>x.id===patient_id);
  if (!p) return { error:`Patient ${patient_id} not found` };
  const cutoffStr = offsetDate(TODAY, -lookback_days);
  const encs = p.encounters.filter(e=>e.date>=cutoffStr);
  return { patient_id:p.id, name:p.name, diagnoses:p.diagnoses, medications:p.medications, cssrs_detail:p.cssrs_items, encounters:encs, total_encounters:encs.length, pes_count:encs.filter(e=>e.isPES).length, cis_count:encs.filter(e=>e.isCIS).length, no_show_count:encs.filter(e=>e.status==='No Show').length, completed_count:encs.filter(e=>e.status==='Completed').length };
}

export function getHighRiskPatients(patients, { risk_type } = {}) {
  let pts;
  if (risk_type==='phq9')    pts = patients.filter(p=>p.phq9.score>=15||p.phq9.si_present);
  else if (risk_type==='ssrs')   pts = patients.filter(p=>p.ssrs.risk_level==='High'||p.ssrs.plan_present||p.ssrs.method_present);
  else if (risk_type==='crisis') pts = patients.filter(p=>p.crisis_events.some(e=>!e.resolved));
  else pts = patients.filter(p=>p.risk_level==='High');
  return { total:pts.length, risk_type:risk_type||'all', patients:pts.map(p=>({ id:p.id,name:p.name,risk_level:p.risk_level,provider:p.provider,phq9_score:p.phq9.score,si_present:p.phq9.si_present,ssrs_risk:p.ssrs.risk_level,ssrs_plan:p.ssrs.plan_present,ssrs_method:p.ssrs.method_present,open_crisis_events:p.crisis_events.filter(e=>!e.resolved),last_contact_date:p.last_contact_date })) };
}

export function getKpiCompliance(patients, { kpi_name } = {}) {
  const by_kpi = {};
  for (const n of KPI_NAMES) {
    const overdue = patients.filter(p=>p.kpis[n].overdue).length;
    by_kpi[n] = { total:patients.length,compliant:patients.length-overdue,overdue,compliance_pct:Math.round((patients.length-overdue)/patients.length*100),meets_target:Math.round((patients.length-overdue)/patients.length*100)>=KPI_TARGET };
  }
  const totalKpis=patients.length*KPI_NAMES.length, overdueTotal=KPI_NAMES.reduce((s,n)=>s+by_kpi[n].overdue,0);
  const overallPct=Math.round((totalKpis-overdueTotal)/totalKpis*100);
  const result={overall_compliance_pct:overallPct,overall_meets_target:overallPct>=KPI_TARGET,target_pct:KPI_TARGET,total_patients:patients.length};
  if (kpi_name){result.kpi=kpi_name;result.stats=by_kpi[kpi_name.toLowerCase()];}
  else{result.by_kpi=by_kpi;}
  return result;
}

export function getOverdueAssessments(patients, { assessment_type } = {}) {
  const names=assessment_type?[assessment_type.toLowerCase()]:KPI_NAMES;
  const result=[];
  for (const p of patients) {
    const overdue=names.filter(n=>p.kpis[n].overdue).map(n=>({kpi:n.toUpperCase().replace('_','-'),last_completed:p.kpis[n].last_completed,due_date:p.kpis[n].due_date,days_overdue:daysBetween(p.kpis[n].due_date)}));
    if (overdue.length) result.push({id:p.id,name:p.name,risk_level:p.risk_level,provider:p.provider,overdue_assessments:overdue});
  }
  return {total_patients_with_overdue:result.length,assessment_type:assessment_type||'all',patients:result};
}

export function getCrisisEvents(patients, { window_days=28 } = {}) {
  const cutoffStr=offsetDate(TODAY,-window_days);
  const events=[];
  for (const p of patients) for (const e of p.crisis_events) if(e.date>=cutoffStr) events.push({patient_id:p.id,patient_name:p.name,provider:p.provider,risk_level:p.risk_level,event_date:e.date,event_type:e.type,resolved:e.resolved,days_ago:daysBetween(e.date)});
  events.sort((a,b)=>b.event_date.localeCompare(a.event_date));
  return{window_days,cutoff_date:cutoffStr,total_events:events.length,unresolved_events:events.filter(e=>!e.resolved).length,events};
}

export function getDisengagedPatients(patients, { threshold_days=30 } = {}) {
  const pts=patients.map(p=>({...p,days_since_contact:daysBetween(p.last_contact_date)})).filter(p=>p.days_since_contact>threshold_days).sort((a,b)=>b.days_since_contact-a.days_since_contact);
  return{threshold_days,total_disengaged:pts.length,patients:pts.map(p=>({id:p.id,name:p.name,risk_level:p.risk_level,provider:p.provider,last_contact_date:p.last_contact_date,days_since_contact:p.days_since_contact}))};
}

export function runTool(name, input, patients) {
  switch(name) {
    case 'get_patients':            return getPatients(patients, input);
    case 'get_patient_detail':      return getPatientDetail(patients, input);
    case 'get_patient_history':     return getPatientHistory(patients, input);
    case 'get_high_risk_patients':  return getHighRiskPatients(patients, input);
    case 'get_kpi_compliance':      return getKpiCompliance(patients, input);
    case 'get_overdue_assessments': return getOverdueAssessments(patients, input);
    case 'get_crisis_events':       return getCrisisEvents(patients, input);
    case 'get_disengaged_patients': return getDisengagedPatients(patients, input);
    default: return { error:`Unknown tool: ${name}` };
  }
}

export const TOOL_DEFS = [
  { name:'get_patients', description:'Returns the patient list with summary clinical data.', input_schema:{type:'object',properties:{risk_level:{type:'string',enum:['High','Moderate','Low']},county:{type:'string'},provider:{type:'string'}}}},
  { name:'get_patient_detail', description:'Returns the full clinical record for one patient.', input_schema:{type:'object',properties:{patient_id:{type:'string'}},required:['patient_id']}},
  { name:'get_patient_history', description:'Returns complete encounter timeline, diagnoses, medications, and C-SSRS breakdown. Use when asked about patient history, past visits, medications.', input_schema:{type:'object',properties:{patient_id:{type:'string'},lookback_days:{type:'integer',description:'Days to look back, default 365'}},required:['patient_id']}},
  { name:'get_high_risk_patients', description:'Returns high-risk patients — PHQ-9 ≥15 or SI, SSRS High, or unresolved crisis.', input_schema:{type:'object',properties:{risk_type:{type:'string',enum:['phq9','ssrs','crisis']}}}},
  { name:'get_kpi_compliance', description:'Returns KPI completion rates vs 75% target.', input_schema:{type:'object',properties:{kpi_name:{type:'string',enum:['bha','sra','aims','whodas','phq9','beh_tp','beh_csp']}}}},
  { name:'get_overdue_assessments', description:'Returns patients with overdue assessments.', input_schema:{type:'object',properties:{assessment_type:{type:'string',enum:['bha','sra','aims','whodas','phq9','beh_tp','beh_csp']}}}},
  { name:'get_crisis_events', description:'Returns crisis episodes within a lookback window. Default: 28 days.', input_schema:{type:'object',properties:{window_days:{type:'integer'}}}},
  { name:'get_disengaged_patients', description:'Returns patients with no contact beyond threshold. Default: 30 days.', input_schema:{type:'object',properties:{threshold_days:{type:'integer'}}}},
];

export const TODAY = new Date().toISOString().split('T')[0];

export function hashStr(s) {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = Math.imul(31, h) + s.charCodeAt(i) | 0;
  return Math.abs(h);
}

export function mkRand(seed) {
  let s = (seed | 1) >>> 0;
  return () => { s ^= s << 13; s ^= s >> 17; s ^= s << 5; return (s >>> 0) / 4294967296; };
}

export function offsetDate(base, days) {
  const d = new Date(base);
  d.setDate(d.getDate() + days);
  return d.toISOString().split('T')[0];
}

export function fmtDate(d) {
  if (!d) return '—';
  const [y, m, dd] = d.split('-');
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  return `${months[parseInt(m)-1]} ${parseInt(dd)}, ${y}`;
}

const ENC_TYPES = [
  { type:'Outpatient',          dept:'BH Ambulatory Clinic',    isPES:false,isCIS:false, color:'blue'   },
  { type:'Outpatient',          dept:'NBH Outpatient',           isPES:false,isCIS:false, color:'blue'   },
  { type:'Phone Contact',       dept:'Care Management',          isPES:false,isCIS:false, color:'slate'  },
  { type:'Treatment Plan',      dept:'BH Care Coordination',     isPES:false,isCIS:false, color:'green'  },
  { type:'Crisis Intervention', dept:'GHS Crisis Interv Svcs',  isPES:false,isCIS:true,  color:'amber'  },
  { type:'PES Visit',           dept:'GHS Emergency',            isPES:true, isCIS:false, color:'red'    },
  { type:'Inpatient',           dept:'BH Inpatient Unit',        isPES:false,isCIS:false, color:'purple' },
];
const STATUSES = ['Completed','Completed','Completed','Completed','Completed','No Show','Canceled','Reschedule'];

export function generateEncounters(p, rand) {
  const riskBase = p.risk_level === 'High' ? 10 : p.risk_level === 'Moderate' ? 7 : 4;
  const count = riskBase + Math.floor(rand() * 4);
  const list = [];

  for (const ce of (p.crisis_events || [])) {
    list.push({ date:ce.date, type:'PES Visit', dept:'GHS Emergency', isPES:true, isCIS:false, color:'red', status:'Completed', provider:p.provider });
  }
  if (p.last_contact_date) {
    list.push({ date:p.last_contact_date, type:'Outpatient', dept:'BH Ambulatory Clinic', isPES:false, isCIS:false, color:'blue', status:'Completed', provider:p.provider });
  }

  const typeWeights = p.risk_level==='High' ? [3,2,2,2,2,1,1] : p.risk_level==='Moderate' ? [4,2,2,2,1,0,0] : [5,3,2,2,0,0,0];
  function pickType() {
    const total = typeWeights.reduce((a,b)=>a+b,0);
    let r = rand() * total;
    for (let i = 0; i < ENC_TYPES.length; i++) { r -= typeWeights[i]; if (r <= 0) return ENC_TYPES[i]; }
    return ENC_TYPES[0];
  }

  const today = new Date(TODAY);
  while (list.length < count) {
    const daysBack = 30 + Math.floor(rand() * 480);
    const d = new Date(today); d.setDate(d.getDate() - daysBack);
    const dateStr = d.toISOString().split('T')[0];
    if (list.some(e => e.date === dateStr)) continue;
    const et = pickType();
    list.push({ date:dateStr, type:et.type, dept:et.dept, isPES:et.isPES, isCIS:et.isCIS, color:et.color, status:STATUSES[Math.floor(rand()*STATUSES.length)], provider:p.provider });
  }
  return list.sort((a,b) => b.date.localeCompare(a.date));
}

const DIAG_MAP = {
  'Major Depressive': [{ code:'F33.1', desc:'Major depressive disorder, recurrent, moderate', category:'Psychiatric Diagnosis' },{ code:'F41.1', desc:'Generalized anxiety disorder', category:'Psychiatric Diagnosis' }],
  'Schizophrenia':    [{ code:'F20.9', desc:'Schizophrenia, unspecified', category:'Psychosis' },{ code:'F17.210', desc:'Nicotine dependence, cigarettes, uncomplicated', category:'Psychiatric Diagnosis' }],
  'Bipolar':          [{ code:'F31.81', desc:'Bipolar II disorder', category:'Psychiatric Diagnosis' },{ code:'F41.1', desc:'Generalized anxiety disorder', category:'Psychiatric Diagnosis' }],
  'PTSD':             [{ code:'F43.11', desc:'Post-traumatic stress disorder, chronic', category:'Psychiatric Diagnosis' },{ code:'F32.1', desc:'Major depressive disorder, single episode, moderate', category:'Psychiatric Diagnosis' }],
  'Anxiety':          [{ code:'F41.1', desc:'Generalized anxiety disorder', category:'Psychiatric Diagnosis' },{ code:'F40.10', desc:'Social phobia, unspecified', category:'Psychiatric Diagnosis' }],
  'Schizoaffective':  [{ code:'F25.0', desc:'Schizoaffective disorder, bipolar type', category:'Psychosis' },{ code:'F10.20', desc:'Alcohol dependence, uncomplicated', category:'Substance Use High' }],
};

export function generateDiagnoses(p, rand) {
  const key = Object.keys(DIAG_MAP).find(k => p.diagnosis && p.diagnosis.includes(k));
  const base = key ? DIAG_MAP[key] : [{ code:'F32.9', desc:'Major depressive disorder, unspecified', category:'Psychiatric Diagnosis' },{ code:'F41.9', desc:'Anxiety disorder, unspecified', category:'Psychiatric Diagnosis' }];
  const diags = base.map((d,i) => ({ ...d, start_date: offsetDate(TODAY, -(180+i*90+Math.floor(rand()*180))) }));
  if (p.phq9?.score >= 15 || p.phq9?.si_present) {
    diags.push({ code:'F33.2', desc:'Major depressive disorder, recurrent severe without psychosis', category:'Psychiatric Diagnosis', start_date: offsetDate(TODAY, -(30+Math.floor(rand()*60))) });
  }
  if (p.risk_level === 'High' && rand() > 0.5) {
    diags.push({ code:'F10.20', desc:'Alcohol dependence, uncomplicated', category:'Substance Use High', start_date: offsetDate(TODAY, -(365+Math.floor(rand()*365))) });
  }
  return diags.slice(0, 4);
}

const MED_MAP = {
  'Major Depressive': [{ name:'Sertraline 100mg', drug_class:'SSRI', dosage:'1 tablet daily', refills_remaining:3 },{ name:'Trazodone 50mg', drug_class:'Antidepressant', dosage:'1 tablet at bedtime', refills_remaining:2 }],
  'Schizophrenia':    [{ name:'Risperidone 4mg', drug_class:'Atypical Antipsychotic', dosage:'1 tablet twice daily', refills_remaining:2 },{ name:'Benztropine 1mg', drug_class:'Anticholinergic', dosage:'1 tablet daily', refills_remaining:3 }],
  'Bipolar':          [{ name:'Lithium 300mg', drug_class:'Mood Stabilizer', dosage:'3 capsules twice daily', refills_remaining:1 },{ name:'Quetiapine 200mg', drug_class:'Atypical Antipsychotic', dosage:'1 tablet at bedtime', refills_remaining:2 }],
  'PTSD':             [{ name:'Sertraline 50mg', drug_class:'SSRI', dosage:'1 tablet daily', refills_remaining:3 },{ name:'Prazosin 1mg', drug_class:'Alpha Blocker', dosage:'1 capsule at bedtime', refills_remaining:2 }],
  'Anxiety':          [{ name:'Escitalopram 20mg', drug_class:'SSRI', dosage:'1 tablet daily', refills_remaining:2 },{ name:'Buspirone 10mg', drug_class:'Anxiolytic', dosage:'1 tablet twice daily', refills_remaining:3 }],
  'Schizoaffective':  [{ name:'Olanzapine 10mg', drug_class:'Atypical Antipsychotic', dosage:'1 tablet daily', refills_remaining:1 },{ name:'Valproate 500mg', drug_class:'Mood Stabilizer', dosage:'1 tablet twice daily', refills_remaining:2 }],
};

export function generateMedications(p, rand) {
  const key = Object.keys(MED_MAP).find(k => p.diagnosis && p.diagnosis.includes(k));
  const base = key ? MED_MAP[key] : [{ name:'Sertraline 100mg', drug_class:'SSRI', dosage:'1 tablet daily', refills_remaining:2 }];
  return base.map((m,i) => ({ ...m, start_date: offsetDate(TODAY, -(90+i*30+Math.floor(rand()*180))) }));
}

export function generateCSSRS(p, rand) {
  const r = p.ssrs?.risk_level || 'Low';
  const plan = p.ssrs?.plan_present || false;
  const method = p.ssrs?.method_present || false;
  const si = p.phq9?.si_present || false;
  if (r === 'High' || si) return { wish_dead:'Yes', suicidal_thoughts:'Yes', suicidal_intent:plan?'Yes':'No', suicidal_with_plan:plan?'Yes':'No', suicidal_method:method?'Yes':'No', history_suicide:rand()>.5?'Yes':'No' };
  if (r === 'Moderate') return { wish_dead:'Yes', suicidal_thoughts:'Yes', suicidal_intent:'No', suicidal_with_plan:'No', suicidal_method:'No', history_suicide:rand()>.7?'Yes':'No' };
  return { wish_dead:rand()>.85?'Yes':'No', suicidal_thoughts:'No', suicidal_intent:'No', suicidal_with_plan:'No', suicidal_method:'No', history_suicide:'No' };
}

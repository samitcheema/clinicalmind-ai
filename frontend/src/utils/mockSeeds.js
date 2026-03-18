import {
  hashStr, mkRand, offsetDate, TODAY,
  generateEncounters, generateDiagnoses, generateMedications, generateCSSRS
} from './mockGenerators.js';

const KPI_NAMES = ['bha','sra','aims','whodas','phq9','beh_tp','beh_csp'];

const SEEDS = [
  { id:'P-001', name:'Marcus Johnson',    dob:'1985-03-14', county:'Fulton',    svc:'ACT',        dx:'Major Depressive Disorder', risk:'High',     phq:21, si:true,  gad:14, crisis:[{d:-8, t:'PES Visit'}],                                    lc:-12 },
  { id:'P-002', name:'Aisha Williams',    dob:'1991-07-22', county:'DeKalb',    svc:'CST',        dx:'Bipolar Disorder',          risk:'High',     phq:18, si:true,  gad:11, crisis:[{d:-21,t:'PES Visit'}],                                    lc:-18 },
  { id:'P-003', name:'Carlos Rivera',     dob:'1979-11-05', county:'Gwinnett',  svc:'CORE',       dx:'PTSD',                      risk:'Moderate', phq:12, si:false, gad:9,  crisis:[],                                                         lc:-25 },
  { id:'P-004', name:'Destiny Brown',     dob:'1994-02-18', county:'Clayton',   svc:'ACT',        dx:'Schizoaffective Disorder',  risk:'High',     phq:19, si:true,  gad:13, crisis:[{d:-5, t:'Crisis Intervention'},{d:-62,t:'PES Visit'}],    lc:-5  },
  { id:'P-005', name:'James Mitchell',    dob:'1967-08-30', county:'Cobb',      svc:'Outpatient', dx:'Anxiety Disorder',          risk:'Low',      phq:6,  si:false, gad:5,  crisis:[],                                                         lc:-14 },
  { id:'P-006', name:'Latoya Davis',      dob:'1988-04-12', county:'Fulton',    svc:'CORE',       dx:'Major Depressive Disorder', risk:'Moderate', phq:11, si:false, gad:8,  crisis:[],                                                         lc:-30 },
  { id:'P-007', name:'Robert Thompson',   dob:'1972-09-25', county:'DeKalb',    svc:'ACT',        dx:'Schizophrenia',             risk:'High',     phq:16, si:true,  gad:7,  crisis:[{d:-35,t:'PES Visit'}],                                    lc:-8  },
  { id:'P-008', name:'Tamara Wilson',     dob:'1995-12-03', county:'Fulton',    svc:'CST',        dx:'Bipolar Disorder',          risk:'Moderate', phq:10, si:false, gad:10, crisis:[],                                                         lc:-21 },
  { id:'P-009', name:'Kevin Harris',      dob:'1983-06-17', county:'Gwinnett',  svc:'Outpatient', dx:'Major Depressive Disorder', risk:'Low',      phq:5,  si:false, gad:4,  crisis:[],                                                         lc:-7  },
  { id:'P-010', name:'Nicole Clark',      dob:'1990-01-28', county:'Clayton',   svc:'ACT',        dx:'PTSD',                      risk:'High',     phq:17, si:true,  gad:12, crisis:[{d:-14,t:'PES Visit'},{d:-90,t:'PES Visit'}],              lc:-14 },
  { id:'P-011', name:'Isaiah Jackson',    dob:'1975-05-09', county:'Cobb',      svc:'CST',        dx:'Schizophrenia',             risk:'Moderate', phq:9,  si:false, gad:6,  crisis:[],                                                         lc:-42 },
  { id:'P-012', name:'Brittany White',    dob:'1997-10-14', county:'Fulton',    svc:'ACT',        dx:'Schizoaffective Disorder',  risk:'High',     phq:20, si:true,  gad:15, crisis:[{d:-3, t:'PES Visit'}],                                    lc:-3  },
  { id:'P-013', name:'DeShawn Martin',    dob:'1986-03-07', county:'DeKalb',    svc:'Outpatient', dx:'Anxiety Disorder',          risk:'Low',      phq:4,  si:false, gad:3,  crisis:[],                                                         lc:-10 },
  { id:'P-014', name:'Jasmine Anderson',  dob:'1993-08-21', county:'Gwinnett',  svc:'CORE',       dx:'Major Depressive Disorder', risk:'Moderate', phq:13, si:false, gad:10, crisis:[],                                                         lc:-35 },
  { id:'P-015', name:'Anthony Lewis',     dob:'1980-11-16', county:'Clayton',   svc:'CST',        dx:'Bipolar Disorder',          risk:'High',     phq:18, si:false, gad:12, crisis:[{d:-28,t:'Crisis Intervention'}],                          lc:-28 },
  { id:'P-016', name:'Maya Robinson',     dob:'1998-02-04', county:'Cobb',      svc:'Outpatient', dx:'PTSD',                      risk:'Low',      phq:7,  si:false, gad:6,  crisis:[],                                                         lc:-21 },
  { id:'P-017', name:'Christopher Scott', dob:'1977-07-11', county:'Fulton',    svc:'CORE',       dx:'Major Depressive Disorder', risk:'Moderate', phq:11, si:false, gad:8,  crisis:[],                                                         lc:-45 },
  { id:'P-018', name:'Tiffany Green',     dob:'1989-05-29', county:'DeKalb',    svc:'ACT',        dx:'Schizophrenia',             risk:'High',     phq:15, si:true,  gad:9,  crisis:[{d:-50,t:'PES Visit'}],                                    lc:-50 },
];

const PROVIDERS = [
  { name:'Dr. Sarah Chen',    team:'ACT Team A'       },
  { name:'Dr. Marcus Webb',   team:'CST Team B'       },
  { name:'Lisa Patel, LCSW',  team:'CORE Services'   },
  { name:'Dr. James Okoye',   team:'ACT Team B'       },
  { name:'Maria Santos, LPC', team:'Outpatient Clinic'},
];

function makeItems(score, si, rand) {
  const items = Array(9).fill(0);
  let rem = Math.max(0, score);
  if (si) { items[8] = rand() > 0.5 ? 3 : 2; rem -= items[8]; }
  for (let i = 0; i < 8 && rem > 0; i++) {
    const v = Math.min(3, Math.round(rand() * Math.min(rem, 3)));
    items[i] = v;
    rem -= v;
  }
  return items.map(v => Math.max(0, Math.min(3, v)));
}

function makeKPIs(rand) {
  const kpis = {};
  for (const k of KPI_NAMES) {
    const daysAgo = Math.floor(rand() * 180) + 10;
    const overdue = daysAgo > 90;
    kpis[k] = {
      last_completed: offsetDate(TODAY, -daysAgo),
      due_date:       offsetDate(TODAY, overdue ? -(daysAgo - 90) : (90 - daysAgo)),
      overdue,
    };
  }
  return kpis;
}

export function getMockPatients() {
  return SEEDS.map(s => {
    const rand    = mkRand(hashStr(s.id));
    const prov    = PROVIDERS[Math.floor(rand() * PROVIDERS.length)];
    const lc      = offsetDate(TODAY, s.lc);

    const p = {
      id:               s.id,
      name:             s.name,
      dob:              s.dob,
      county:           s.county,
      service_type:     s.svc,
      diagnosis:        s.dx,
      provider:         prov.name,
      team:             prov.team,
      risk_level:       s.risk,
      last_contact_date: lc,
      phq9: {
        score:      s.phq,
        si_present: s.si,
        date:       offsetDate(TODAY, -(Math.floor(rand() * 14) + 7)),
        items:      makeItems(s.phq, s.si, rand),
      },
      gad7: {
        score:    s.gad,
        severity: s.gad >= 15 ? 'Severe' : s.gad >= 10 ? 'Moderate' : s.gad >= 5 ? 'Mild' : 'Minimal',
        date:     offsetDate(TODAY, -(Math.floor(rand() * 14) + 7)),
      },
      whodas: {
        score: Math.floor(rand() * 30 + (s.risk==='High'?25 : s.risk==='Moderate'?12 : 3)),
        level: s.risk==='High' ? 'Severe' : s.risk==='Moderate' ? 'Moderate' : 'Mild',
        date:  offsetDate(TODAY, -(Math.floor(rand() * 30) + 14)),
      },
      ssrs: {
        risk_level:     s.risk,
        plan_present:   s.si && s.risk==='High' && rand() > 0.55,
        method_present: s.si && s.risk==='High' && rand() > 0.65,
        intent:         s.si && rand() > 0.72,
        ideation:       s.si,
        history:        s.risk==='High' && rand() > 0.45,
        date:           offsetDate(TODAY, -(Math.floor(rand() * 21) + 7)),
      },
      crisis_events: s.crisis.map(c => ({
        date:     offsetDate(TODAY, c.d),
        type:     c.t,
        resolved: c.d < -28,
      })),
      kpis: makeKPIs(rand),
    };

    p.encounters  = generateEncounters(p, rand);
    p.diagnoses   = generateDiagnoses(p, rand);
    p.medications = generateMedications(p, rand);
    p.cssrs_items = generateCSSRS(p, rand);

    return p;
  });
}

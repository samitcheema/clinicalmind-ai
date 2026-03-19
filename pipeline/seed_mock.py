#!/usr/bin/env python3
"""
ClinicalMind AI — Mock Data Seeder

Generates and inserts synthetic patient data into Supabase using the same
18 patient seeds and deterministic PRNG as the frontend mockSeeds.js.
The resulting data is consistent with what the dashboard displays in demo mode.

Usage:
    cd pipeline
    python seed_mock.py            # insert all 18 mock patients
    python seed_mock.py --clear    # wipe existing mock data first, then insert

Requires DATABASE_URL in pipeline/.env.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import sys
from datetime import date, timedelta

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

_HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_HERE, ".env"))

TODAY = date.today()


# ── Deterministic PRNG — mirrors mockGenerators.js ────────────────────────────

def hash_str(s: str) -> int:
    """Replicate JS hashStr() — djb2-style with Math.imul 32-bit wrap."""
    h = 0
    for c in s:
        h = ctypes.c_int32(ctypes.c_int32(31 * h).value + ord(c)).value
    return abs(h)


def mk_rand(seed: int):
    """Replicate JS mkRand() — xorshift32 PRNG seeded deterministically."""
    s = ctypes.c_uint32(seed | 1).value

    def rand() -> float:
        nonlocal s
        s = ctypes.c_uint32(s ^ (s << 13)).value
        s = ctypes.c_uint32(s ^ (s >> 17)).value
        s = ctypes.c_uint32(s ^ (s << 5)).value
        return s / 4_294_967_296.0

    return rand


def offset_date(base: date, days: int) -> date:
    return base + timedelta(days=days)


# ── Seed data — mirrors frontend/src/utils/mockSeeds.js ───────────────────────

SEEDS = [
    dict(id='P-001', name='Marcus Johnson',    dob='1985-03-14', county='Fulton',   svc='ACT',        dx='Major Depressive Disorder', risk='High',     phq=21, si=True,  gad=14, crisis=[dict(d=-8,  t='PES Visit')],                                      lc=-12),
    dict(id='P-002', name='Aisha Williams',    dob='1991-07-22', county='DeKalb',   svc='CST',        dx='Bipolar Disorder',          risk='High',     phq=18, si=True,  gad=11, crisis=[dict(d=-21, t='PES Visit')],                                      lc=-18),
    dict(id='P-003', name='Carlos Rivera',     dob='1979-11-05', county='Gwinnett', svc='CORE',       dx='PTSD',                      risk='Moderate', phq=12, si=False, gad=9,  crisis=[],                                                                 lc=-25),
    dict(id='P-004', name='Destiny Brown',     dob='1994-02-18', county='Clayton',  svc='ACT',        dx='Schizoaffective Disorder',  risk='High',     phq=19, si=True,  gad=13, crisis=[dict(d=-5,  t='Crisis Intervention'), dict(d=-62, t='PES Visit')], lc=-5),
    dict(id='P-005', name='James Mitchell',    dob='1967-08-30', county='Cobb',     svc='Outpatient', dx='Anxiety Disorder',          risk='Low',      phq=6,  si=False, gad=5,  crisis=[],                                                                 lc=-14),
    dict(id='P-006', name='Latoya Davis',      dob='1988-04-12', county='Fulton',   svc='CORE',       dx='Major Depressive Disorder', risk='Moderate', phq=11, si=False, gad=8,  crisis=[],                                                                 lc=-30),
    dict(id='P-007', name='Robert Thompson',   dob='1972-09-25', county='DeKalb',   svc='ACT',        dx='Schizophrenia',             risk='High',     phq=16, si=True,  gad=7,  crisis=[dict(d=-35, t='PES Visit')],                                      lc=-8),
    dict(id='P-008', name='Tamara Wilson',     dob='1995-12-03', county='Fulton',   svc='CST',        dx='Bipolar Disorder',          risk='Moderate', phq=10, si=False, gad=10, crisis=[],                                                                 lc=-21),
    dict(id='P-009', name='Kevin Harris',      dob='1983-06-17', county='Gwinnett', svc='Outpatient', dx='Major Depressive Disorder', risk='Low',      phq=5,  si=False, gad=4,  crisis=[],                                                                 lc=-7),
    dict(id='P-010', name='Nicole Clark',      dob='1990-01-28', county='Clayton',  svc='ACT',        dx='PTSD',                      risk='High',     phq=17, si=True,  gad=12, crisis=[dict(d=-14, t='PES Visit'), dict(d=-90, t='PES Visit')],           lc=-14),
    dict(id='P-011', name='Isaiah Jackson',    dob='1975-05-09', county='Cobb',     svc='CST',        dx='Schizophrenia',             risk='Moderate', phq=9,  si=False, gad=6,  crisis=[],                                                                 lc=-42),
    dict(id='P-012', name='Brittany White',    dob='1997-10-14', county='Fulton',   svc='ACT',        dx='Schizoaffective Disorder',  risk='High',     phq=20, si=True,  gad=15, crisis=[dict(d=-3,  t='PES Visit')],                                      lc=-3),
    dict(id='P-013', name='DeShawn Martin',    dob='1986-03-07', county='DeKalb',   svc='Outpatient', dx='Anxiety Disorder',          risk='Low',      phq=4,  si=False, gad=3,  crisis=[],                                                                 lc=-10),
    dict(id='P-014', name='Jasmine Anderson',  dob='1993-08-21', county='Gwinnett', svc='CORE',       dx='Major Depressive Disorder', risk='Moderate', phq=13, si=False, gad=10, crisis=[],                                                                 lc=-35),
    dict(id='P-015', name='Anthony Lewis',     dob='1980-11-16', county='Clayton',  svc='CST',        dx='Bipolar Disorder',          risk='High',     phq=18, si=False, gad=12, crisis=[dict(d=-28, t='Crisis Intervention')],                             lc=-28),
    dict(id='P-016', name='Maya Robinson',     dob='1998-02-04', county='Cobb',     svc='Outpatient', dx='PTSD',                      risk='Low',      phq=7,  si=False, gad=6,  crisis=[],                                                                 lc=-21),
    dict(id='P-017', name='Christopher Scott', dob='1977-07-11', county='Fulton',   svc='CORE',       dx='Major Depressive Disorder', risk='Moderate', phq=11, si=False, gad=8,  crisis=[],                                                                 lc=-45),
    dict(id='P-018', name='Tiffany Green',     dob='1989-05-29', county='DeKalb',   svc='ACT',        dx='Schizophrenia',             risk='High',     phq=15, si=True,  gad=9,  crisis=[dict(d=-50, t='PES Visit')],                                      lc=-50),
]

PROVIDERS = [
    dict(id='PROV-001', name='Dr. Sarah Chen',    team='ACT Team A'),
    dict(id='PROV-002', name='Dr. Marcus Webb',   team='CST Team B'),
    dict(id='PROV-003', name='Lisa Patel, LCSW',  team='CORE Services'),
    dict(id='PROV-004', name='Dr. James Okoye',   team='ACT Team B'),
    dict(id='PROV-005', name='Maria Santos, LPC', team='Outpatient Clinic'),
]

KPI_NAMES = ['bha', 'sra', 'aims', 'whodas', 'phq9', 'beh_tp', 'beh_csp']

MED_MAP = {
    'Major Depressive': [
        dict(name='Sertraline 100mg',    drug_class='SSRI',                   dosage='1 tablet daily',          refills_remaining=3, route='PO'),
        dict(name='Trazodone 50mg',      drug_class='Antidepressant',         dosage='1 tablet at bedtime',     refills_remaining=2, route='PO'),
    ],
    'Schizophrenia': [
        dict(name='Risperidone 4mg',     drug_class='Atypical Antipsychotic', dosage='1 tablet twice daily',    refills_remaining=2, route='PO'),
        dict(name='Benztropine 1mg',     drug_class='Anticholinergic',        dosage='1 tablet daily',          refills_remaining=3, route='PO'),
    ],
    'Bipolar': [
        dict(name='Lithium 300mg',       drug_class='Mood Stabilizer',        dosage='3 capsules twice daily',  refills_remaining=1, route='PO'),
        dict(name='Quetiapine 200mg',    drug_class='Atypical Antipsychotic', dosage='1 tablet at bedtime',     refills_remaining=2, route='PO'),
    ],
    'PTSD': [
        dict(name='Sertraline 50mg',     drug_class='SSRI',                   dosage='1 tablet daily',          refills_remaining=3, route='PO'),
        dict(name='Prazosin 1mg',        drug_class='Alpha Blocker',          dosage='1 capsule at bedtime',    refills_remaining=2, route='PO'),
    ],
    'Anxiety': [
        dict(name='Escitalopram 20mg',   drug_class='SSRI',                   dosage='1 tablet daily',          refills_remaining=2, route='PO'),
        dict(name='Buspirone 10mg',      drug_class='Anxiolytic',             dosage='1 tablet twice daily',    refills_remaining=3, route='PO'),
    ],
    'Schizoaffective': [
        dict(name='Olanzapine 10mg',     drug_class='Atypical Antipsychotic', dosage='1 tablet daily',          refills_remaining=1, route='PO'),
        dict(name='Valproate 500mg',     drug_class='Mood Stabilizer',        dosage='1 tablet twice daily',    refills_remaining=2, route='PO'),
    ],
}


# ── Data generation helpers ────────────────────────────────────────────────────

def pick_provider(rand) -> dict:
    return PROVIDERS[int(rand() * len(PROVIDERS))]


def make_phq9_items(score: int, si: bool, rand) -> list[int]:
    items = [0] * 9
    rem = max(0, score)
    if si:
        items[8] = 3 if rand() > 0.5 else 2
        rem -= items[8]
    for i in range(8):
        if rem <= 0:
            break
        v = min(3, round(rand() * min(rem, 3)))
        items[i] = v
        rem -= v
    return [max(0, min(3, v)) for v in items]


def make_kpis(rand) -> list[dict]:
    rows = []
    for k in KPI_NAMES:
        days_ago = int(rand() * 180) + 10
        overdue = days_ago > 90
        rows.append(dict(
            kpi_name=k,
            last_completed=offset_date(TODAY, -days_ago).isoformat(),
            due_date=offset_date(TODAY, -(days_ago - 90) if overdue else (90 - days_ago)).isoformat(),
            overdue=overdue,
        ))
    return rows


def make_meds(dx: str, rand) -> list[dict]:
    key = next((k for k in MED_MAP if k in dx), None)
    meds = MED_MAP[key] if key else [dict(
        name='Sertraline 100mg', drug_class='SSRI', dosage='1 tablet daily',
        refills_remaining=2, route='PO'
    )]
    result = []
    for i, m in enumerate(meds):
        start = offset_date(TODAY, -(90 + i * 30 + int(rand() * 180)))
        result.append(dict(
            medication_name=m['name'],
            drug_class=m['drug_class'],
            dosage=m['dosage'],
            refills_remaining=m['refills_remaining'],
            refills_authorized=m['refills_remaining'] + int(rand() * 3),
            route=m.get('route', 'PO'),
            status='active',
            start_date=start.isoformat(),
            end_date=offset_date(start, 90 + int(rand() * 180)).isoformat(),
            ordered_date=offset_date(start, -int(rand() * 7)).isoformat(),
            days_supply=30,
        ))
    return result


def gad_severity(score: int) -> str:
    if score >= 15:
        return 'Severe'
    if score >= 10:
        return 'Moderate'
    if score >= 5:
        return 'Mild'
    return 'Minimal'


def whodas_level(risk: str, rand) -> tuple[int, str]:
    base = 25 if risk == 'High' else 12 if risk == 'Moderate' else 3
    score = int(rand() * 30 + base)
    level = 'Severe' if risk == 'High' else 'Moderate' if risk == 'Moderate' else 'Mild'
    return score, level


# ── Database operations ────────────────────────────────────────────────────────

def clear_mock_data(cur) -> None:
    """Delete all rows that match mock patient IDs (safe for partial runs)."""
    pid_list = [s['id'] for s in SEEDS]
    placeholders = ','.join(['%s'] * len(pid_list))

    for table in ['kpi_compliance', 'assessments_phq9', 'assessments_gad7',
                  'assessments_whodas', 'assessments_ssrs', 'encounters',
                  'crisis_events', 'prescriptions']:
        cur.execute(f"DELETE FROM {table} WHERE patient_id IN ({placeholders})", pid_list)

    cur.execute(f"DELETE FROM patients WHERE patient_id IN ({placeholders})", pid_list)

    prov_list = [p['id'] for p in PROVIDERS]
    cur.execute(
        f"DELETE FROM providers WHERE provider_id IN ({','.join(['%s']*len(prov_list))})",
        prov_list
    )
    print("  Cleared existing mock data.")


def insert_providers(cur) -> None:
    psycopg2.extras.execute_values(
        cur,
        "INSERT INTO providers (provider_id, name, team) VALUES %s ON CONFLICT DO NOTHING",
        [(p['id'], p['name'], p['team']) for p in PROVIDERS],
    )
    print(f"  Inserted {len(PROVIDERS)} providers.")


def seed_patient(cur, s: dict) -> None:
    rand = mk_rand(hash_str(s['id']))
    prov = pick_provider(rand)
    lc = offset_date(TODAY, s['lc'])

    phq_score = s['phq']
    si = s['si']
    gad_score = s['gad']
    risk = s['risk']
    phq_date = offset_date(TODAY, -(int(rand() * 14) + 7))
    gad_date = offset_date(TODAY, -(int(rand() * 14) + 7))
    whodas_score, whodas_lvl = whodas_level(risk, rand)
    whodas_date = offset_date(TODAY, -(int(rand() * 30) + 14))
    ssrs_date = offset_date(TODAY, -(int(rand() * 21) + 7))
    plan = si and risk == 'High' and rand() > 0.55
    method = si and risk == 'High' and rand() > 0.65
    intent = si and rand() > 0.72
    history = risk == 'High' and rand() > 0.45

    # ── patients ──────────────────────────────────────────────────────────────
    cur.execute("""
        INSERT INTO patients (
            patient_id, name, date_of_birth, diagnosis, county, service_type,
            provider_id, risk_level, last_contact_date, days_since_last_contact,
            has_crisis_7d, has_crisis_28d
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (patient_id) DO NOTHING
    """, (
        s['id'], s['name'], s['dob'], s['dx'], s['county'], s['svc'],
        prov['id'], risk, lc.isoformat(), abs(s['lc']),
        any(c['d'] >= -7  for c in s['crisis']),
        any(c['d'] >= -28 for c in s['crisis']),
    ))

    # ── assessments_phq9 ─────────────────────────────────────────────────────
    items = make_phq9_items(phq_score, si, rand)
    severity = 'Severe' if phq_score >= 20 else 'Moderately Severe' if phq_score >= 15 else \
               'Moderate' if phq_score >= 10 else 'Mild' if phq_score >= 5 else 'Minimal'
    cur.execute("""
        INSERT INTO assessments_phq9 (patient_id, assessment_date, total_score,
            item_scores, suicidal_ideation, severity)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (s['id'], phq_date.isoformat(), phq_score,
          json.dumps(items), si, severity))

    # ── assessments_gad7 ─────────────────────────────────────────────────────
    cur.execute("""
        INSERT INTO assessments_gad7 (patient_id, assessment_date, total_score, severity)
        VALUES (%s,%s,%s,%s)
    """, (s['id'], gad_date.isoformat(), gad_score, gad_severity(gad_score)))

    # ── assessments_whodas ───────────────────────────────────────────────────
    cur.execute("""
        INSERT INTO assessments_whodas (patient_id, assessment_date, total_score, disability_level)
        VALUES (%s,%s,%s,%s)
    """, (s['id'], whodas_date.isoformat(), whodas_score, whodas_lvl))

    # ── assessments_ssrs ─────────────────────────────────────────────────────
    intensity = 3 if (risk == 'High' and si) else 2 if si else 1 if risk == 'Moderate' else 0
    cur.execute("""
        INSERT INTO assessments_ssrs (patient_id, assessment_date, suicidal_ideation,
            ideation_intensity, intent, plan, method, history_attempt, risk_level)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (s['id'], ssrs_date.isoformat(), si, intensity,
          intent, plan, method, history, risk))

    # ── crisis_events ────────────────────────────────────────────────────────
    for i, c in enumerate(s['crisis']):
        c_date = offset_date(TODAY, c['d'])
        days_since = abs(c['d'])
        cur.execute("""
            INSERT INTO crisis_events (event_id, patient_id, crisis_date, crisis_type,
                within_7_days, within_28_days, days_since)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT DO NOTHING
        """, (
            f"{s['id']}-CE-{i+1}", s['id'], c_date.isoformat(), c['t'],
            days_since <= 7, days_since <= 28, days_since,
        ))

    # ── kpi_compliance ───────────────────────────────────────────────────────
    kpis = make_kpis(rand)
    for k in kpis:
        cur.execute("""
            INSERT INTO kpi_compliance (patient_id, kpi_name, last_completed, due_date, overdue)
            VALUES (%s,%s,%s,%s,%s)
            ON CONFLICT (patient_id, kpi_name) DO UPDATE
                SET last_completed = EXCLUDED.last_completed,
                    due_date = EXCLUDED.due_date,
                    overdue = EXCLUDED.overdue
        """, (s['id'], k['kpi_name'], k['last_completed'], k['due_date'], k['overdue']))

    # ── prescriptions ────────────────────────────────────────────────────────
    meds = make_meds(s['dx'], rand)
    for m in meds:
        cur.execute("""
            INSERT INTO prescriptions (
                patient_id, medication_name, drug_class, status, dosage,
                route, days_supply, refills_authorized, refills_remaining,
                ordered_date, start_date, end_date, prescribing_provider_id,
                prescribing_provider_name
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            s['id'], m['medication_name'], m['drug_class'], m['status'], m['dosage'],
            m['route'], m['days_supply'], m['refills_authorized'], m['refills_remaining'],
            m['ordered_date'], m['start_date'], m['end_date'],
            prov['id'], prov['name'],
        ))


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description='Seed Supabase with mock patient data')
    parser.add_argument('--clear', action='store_true',
                        help='Delete existing mock data before inserting')
    args = parser.parse_args()

    db_url = os.environ.get('DATABASE_URL', '')
    if not db_url:
        sys.exit(
            'ERROR: DATABASE_URL not set.\n'
            '       Add it to pipeline/.env  (Supabase Dashboard → Settings →\n'
            '       Database → Connection string → URI format)'
        )

    print('ClinicalMind AI — Mock Data Seeder')
    print('=' * 38)

    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        if args.clear:
            clear_mock_data(cur)

        insert_providers(cur)

        for i, s in enumerate(SEEDS, 1):
            seed_patient(cur, s)
            print(f'  [{i:02d}/{len(SEEDS)}] {s["name"]} ({s["id"]}) — {s["risk"]} risk')

        conn.commit()
        print(f'\n✓  Seeded {len(SEEDS)} patients and {len(PROVIDERS)} providers successfully.')

    except Exception as exc:
        conn.rollback()
        print(f'\n✗  FAILED: {exc}')
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    main()

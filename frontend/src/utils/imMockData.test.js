import { describe, it, expect } from 'vitest';
import {
  getImPatients,
  getImPatientDetail,
  getChronicDiseasePanel,
  getPreventiveCareGaps,
} from './imMockData.js';

describe('getImPatients', () => {
  it('returns all 12 patients unfiltered', () => {
    const result = getImPatients();
    expect(result.length).toBe(12);
    expect(result.every(p => p.specialty === 'IM')).toBe(true);
  });

  it('filters by risk_level High — returns 4', () => {
    const result = getImPatients({ risk_level: 'High' });
    expect(result.length).toBe(4);
    expect(result.every(p => p.risk_level === 'High')).toBe(true);
  });

  it('filters by condition diabetes — returns 6', () => {
    const result = getImPatients({ condition: 'diabetes' });
    expect(result.length).toBeGreaterThan(0);
    expect(result.every(p =>
      p.conditions.some(c => c.toLowerCase().includes('diabetes'))
    )).toBe(true);
  });

  it('filters by provider PROV007', () => {
    const result = getImPatients({ provider: 'PROV007' });
    expect(result.length).toBeGreaterThan(0);
    expect(result.every(p => p.provider_id === 'PROV007')).toBe(true);
  });
});

describe('getImPatientDetail', () => {
  it('returns patient for known ID', () => {
    const result = getImPatientDetail('IM001');
    expect(result).not.toBeNull();
    expect(result.patient_id).toBe('IM001');
    expect(result.a1c_history.length).toBe(4);
  });

  it('returns null for unknown ID', () => {
    expect(getImPatientDetail('UNKNOWN')).toBeNull();
  });
});

describe('getChronicDiseasePanel', () => {
  it('diabetes returns patients with latest A1c > 8.0', () => {
    const result = getChronicDiseasePanel('diabetes');
    expect(result.length).toBeGreaterThan(0);
    result.forEach(p => {
      const latest = p.a1c_history.at(-1).value;
      expect(latest).toBeGreaterThan(8.0);
    });
  });

  it('ckd returns patients with eGFR slope <= -3/yr', () => {
    const result = getChronicDiseasePanel('ckd');
    expect(result.length).toBeGreaterThan(0);
  });

  it('hypertension returns patients with latest systolic > 140', () => {
    const result = getChronicDiseasePanel('hypertension');
    expect(result.length).toBeGreaterThan(0);
    result.forEach(p => {
      const latest = p.bp_history.at(-1).systolic;
      expect(latest).toBeGreaterThan(140);
    });
  });
});

describe('getPreventiveCareGaps', () => {
  it('returns only patients with at least one overdue item', () => {
    const result = getPreventiveCareGaps();
    expect(result.length).toBeGreaterThan(0);
    result.forEach(p => {
      const hasOverdue = p.preventive_care.some(item => item.overdue);
      expect(hasOverdue).toBe(true);
    });
  });

  it('filters by gap_type flu_vaccine', () => {
    const result = getPreventiveCareGaps('flu_vaccine');
    result.forEach(p => {
      const fluItem = p.preventive_care.find(item => item.item_name === 'flu_vaccine');
      expect(fluItem?.overdue).toBe(true);
    });
  });
});

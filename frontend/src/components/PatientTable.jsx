import { useState, useMemo } from 'react';
import { KPI_NAMES, KPI_DISPLAY } from '../utils/dataTransform.js';
import { daysBetween } from '../utils/tools.js';
import PatientDetail from './PatientDetail.jsx';
import { useProvider } from '../ProviderContext';
import { getImPatients } from '../utils/imMockData.js';

export default function PatientTable({ patients }) {
  const { provider } = useProvider();
  const isIM = provider?.specialty === 'IM';

  const [search, setSearch] = useState('');
  const [sort, setSort] = useState({ col:'name', dir:'asc' });
  const [expanded, setExpanded] = useState(new Set());

  // For IM providers, source data from imMockData instead of the BH patients prop
  const activePatients = useMemo(
    () => (isIM ? getImPatients() : patients),
    [isIM, patients]
  );

  function toggleExpand(id) {
    setExpanded(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function handleSort(col) {
    setSort(prev => ({
      col,
      dir: prev.col === col ? (prev.dir === 'asc' ? 'desc' : 'asc') : (col === 'name' ? 'asc' : 'desc')
    }));
  }

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    const idKey = isIM ? 'patient_id' : 'id';
    const providerKey = isIM ? 'provider_name' : 'provider';
    let pts = activePatients.filter(p => {
      if (q && !p.name.toLowerCase().includes(q) && !p[idKey]?.toLowerCase().includes(q) && !p[providerKey]?.toLowerCase().includes(q)) return false;
      return true;
    });
    return pts.slice().sort((a,b) => {
      let va, vb;
      switch(sort.col) {
        case 'name':    va=a.name;          vb=b.name;          break;
        case 'contact': va=a.last_contact_date||'';      vb=b.last_contact_date||'';     break;
        case 'overdue':
          va = isIM ? 0 : KPI_NAMES.filter(k => a.kpis?.[k]?.overdue).length;
          vb = isIM ? 0 : KPI_NAMES.filter(k => b.kpis?.[k]?.overdue).length;
          break;
        default: va=0; vb=0;
      }
      const cmp = typeof va==='string' ? va.localeCompare(vb) : (va-vb);
      return sort.dir==='asc' ? cmp : -cmp;
    });
  }, [activePatients, search, sort, isIM]);

  function SortTh({ col, children }) {
    const isSorted = sort.col === col;
    return (
      <th className={`sortable${isSorted?' sort-'+sort.dir:''}`} onClick={() => handleSort(col)}>
        {children}
      </th>
    );
  }

  return (
    <>
      <div className="table-controls">
        <input
          type="search"
          className="pt-search"
          placeholder="Search by name, ID, or provider…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <span className="pt-count">{filtered.length} of {activePatients.length} patients</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th style={{width:32}} className="no-sort"></th>
              <SortTh col="name">Patient</SortTh>
              {isIM
                ? <><th>Conditions</th><th>Risk Level</th></>
                : <><th>Diagnosis</th><SortTh col="overdue">KPI Status</SortTh><SortTh col="contact">Last Contact</SortTh></>
              }
              <th>Provider</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr className="no-data"><td colSpan={isIM ? 5 : 6}>No patients match the current filter.</td></tr>
            ) : isIM ? filtered.map(p => (
              <tr key={p.patient_id}>
                <td></td>
                <td>
                  <span className="pt-name">{p.name}</span>
                  <span className="pt-id">{p.patient_id}</span>
                </td>
                <td style={{fontSize:'11px',color:'var(--text-3)'}}>{p.conditions.slice(0,2).join(', ')}</td>
                <td><span className={`risk-badge risk-${p.risk_level?.toLowerCase()}`}>{p.risk_level}</span></td>
                <td style={{fontSize:'12px'}}>{p.provider_name}</td>
              </tr>
            )) : filtered.map(p => {
              const isExp = expanded.has(p.id);
              const days = daysBetween(p.last_contact_date);
              const daysCls = days>60?'days-crit':days>30?'days-warn':'days-ok';
              const daysLbl = days>=999?'Unknown':`${days}d ago`;
              return [
                <tr
                  key={p.id}
                  className={`patient-row${isExp?' expanded':''}`}
                  onClick={() => toggleExpand(p.id)}
                >
                  <td onClick={e => e.stopPropagation()}>
                    <button
                      className="expand-btn"
                      onClick={() => toggleExpand(p.id)}
                      aria-label={isExp ? 'Collapse patient' : 'Expand patient'}
                      aria-expanded={isExp}
                    >{isExp?'▼':'▶'}</button>
                  </td>
                  <td>
                    <span className="pt-name">{p.name}</span>
                    <span className="pt-id">{p.id}</span>
                  </td>
                  <td className="diag-cell">
                    {p.diagnoses && p.diagnoses.length > 0
                      ? p.diagnoses.map(d => d.code).join(', ')
                      : '—'}
                  </td>
                  <td>
                    <div className="kpi-dot-row">
                      {KPI_NAMES.map(k => (
                        <span
                          key={k}
                          className={`kpi-dot ${p.kpis[k]?.overdue ? 'kpi-dot-red' : 'kpi-dot-green'}`}
                          title={`${KPI_DISPLAY[k]}: ${p.kpis[k]?.overdue ? 'overdue' : 'compliant'}`}
                        />
                      ))}
                    </div>
                  </td>
                  <td><span className={daysCls}>{daysLbl}</span></td>
                  <td className="provider-cell">{p.provider}</td>
                </tr>,
                isExp && (
                  <tr key={`detail-${p.id}`} className="detail-row">
                    <td colSpan={6}>
                      <PatientDetail patient={p} />
                    </td>
                  </tr>
                )
              ];
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}

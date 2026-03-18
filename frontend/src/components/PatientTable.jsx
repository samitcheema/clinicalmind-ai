import { useState, useMemo } from 'react';
import { KPI_NAMES } from '../utils/dataTransform.js';
import { daysBetween } from '../utils/tools.js';
import PatientDetail from './PatientDetail.jsx';

export default function PatientTable({ patients }) {
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState({ col:'phq9', dir:'desc' });
  const [expanded, setExpanded] = useState(new Set());

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
    let pts = patients.filter(p => {
      if (q && !p.name.toLowerCase().includes(q) && !p.id.toLowerCase().includes(q) && !p.provider.toLowerCase().includes(q)) return false;
      return true;
    });
    return pts.slice().sort((a,b) => {
      let va, vb;
      switch(sort.col) {
        case 'name':    va=a.name;          vb=b.name;          break;
        case 'phq9':    va=a.phq9.score;    vb=b.phq9.score;    break;
        case 'contact': va=a.last_contact_date||'';      vb=b.last_contact_date||'';     break;
        case 'overdue': va=KPI_NAMES.filter(k=>a.kpis[k].overdue).length;
                        vb=KPI_NAMES.filter(k=>b.kpis[k].overdue).length; break;
        default: va=0; vb=0;
      }
      const cmp = typeof va==='string' ? va.localeCompare(vb) : (va-vb);
      return sort.dir==='asc' ? cmp : -cmp;
    });
  }, [patients, search, riskFilter, sort]);

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
        <span className="pt-count">{filtered.length} of {patients.length} patients</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th style={{width:32}} className="no-sort"></th>
              <SortTh col="name">Patient</SortTh>
              <th>Provider</th>
              <SortTh col="phq9">PHQ-9</SortTh>
              <th>SSRS</th>
              <SortTh col="contact">Last Contact</SortTh>
              <SortTh col="overdue">Overdue KPIs</SortTh>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr className="no-data"><td colSpan={7}>No patients match the current filter.</td></tr>
            ) : filtered.map(p => {
              const isExp = expanded.has(p.id);
              const days = daysBetween(p.last_contact_date);
              const daysCls = days>60?'days-crit':days>30?'days-warn':'days-ok';
              const daysLbl = days>=999?'Unknown':`${days}d ago`;
              const phqCls = p.phq9.score>=15||p.phq9.si_present?'high':p.phq9.score>=10?'mod':'';
              const phqLbl = p.phq9.score+(p.phq9.si_present?' ⚠':'');
              const overdueCnt = KPI_NAMES.filter(k=>p.kpis[k].overdue).length;
              return [
                <tr
                  key={p.id}
                  className={`patient-row${isExp?' expanded':''}`}
                  onClick={() => toggleExpand(p.id)}
                >
                  <td onClick={e => e.stopPropagation()}>
                    <button className="expand-btn" onClick={() => toggleExpand(p.id)}>{isExp?'▼':'▶'}</button>
                  </td>
                  <td>
                    <span className="pt-name">{p.name}</span>
                    <span className="pt-id">{p.id}</span>
                  </td>
                  <td>{p.provider}</td>
                  <td><span className={`phq-score ${phqCls}`}>{phqLbl}</span></td>
                  <td><span className={`ssrs-badge ${p.ssrs.risk_level}`}>{p.ssrs.risk_level}</span></td>
                  <td><span className={daysCls}>{daysLbl}</span></td>
                  <td>
                    {overdueCnt>0
                      ? <span className="overdue-count">{overdueCnt}</span>
                      : <span className="overdue-zero">—</span>
                    }
                  </td>
                </tr>,
                isExp && (
                  <tr key={`detail-${p.id}`} className="detail-row">
                    <td colSpan={7}>
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

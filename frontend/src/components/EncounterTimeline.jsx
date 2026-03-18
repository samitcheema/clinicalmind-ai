import { fmtDate } from '../utils/mockGenerators.js';

export default function EncounterTimeline({ encounters }) {
  if (!encounters?.length) return <div style={{color:'#94a3b8',fontSize:'12px'}}>No encounters recorded</div>;
  return (
    <div className="timeline">
      {encounters.slice(0,15).map((e,i) => {
        const statusCls = e.status?.replace(' ','-') || 'Completed';
        return (
          <div key={i} className="tl-event">
            <div className={`tl-dot ${e.color||'blue'}`} />
            <div className="tl-header">
              <span className="tl-date">{fmtDate(e.date)}</span>
              <span className={`tl-type ${e.color||'blue'}`}>{e.type}</span>
              <span className={`tl-status ${statusCls}`}>{e.status}</span>
            </div>
            <div className="tl-dept">{e.dept}</div>
          </div>
        );
      })}
    </div>
  );
}

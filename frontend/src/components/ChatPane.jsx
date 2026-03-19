import { useState, useRef, useEffect } from 'react';
import { TOOL_DEFS, runTool } from '../utils/tools.js';
import { PROXY } from '../utils/dataTransform.js';
import { TODAY } from '../utils/mockGenerators.js';

const MODEL = 'claude-opus-4-6';
const SYSTEM = `You are ClinicalMind AI, a clinical decision support assistant for behavioral health case managers. You have access to tools that query a live synthetic patient cohort.

All data is as of ${TODAY}. Always call a tool to get accurate data — never guess.

When responding:
- Be concise and clinically relevant
- Use bullet points or short lists for multiple patients
- Always cite specific scores, dates, and days
- Flag urgent items clearly (unresolved crisis events, SSRS High, PHQ-9 ≥15)
- When asked about patient history or past visits, use get_patient_history`;

const TOOL_LABELS = {
  get_patients:            () => 'Querying patient list',
  get_patient_detail:      i  => `Getting details: ${i.patient_id}`,
  get_patient_history:     i  => `Loading history: ${i.patient_id}`,
  get_high_risk_patients:  i  => i.risk_type ? `High-risk filter: ${i.risk_type}` : 'Fetching high-risk patients',
  get_kpi_compliance:      i  => i.kpi_name ? `KPI compliance: ${i.kpi_name.toUpperCase()}` : 'Checking KPI compliance',
  get_overdue_assessments: i  => i.assessment_type ? `Overdue: ${i.assessment_type.toUpperCase()}` : 'Finding overdue assessments',
  get_crisis_events:       i  => `Crisis events (${i.window_days||28}d window)`,
  get_disengaged_patients: i  => `Disengaged >${i.threshold_days||30} days`,
};

const SUGGESTIONS = [
  "Who are my highest-risk patients?",
  "Any crisis events in the last 7 days?",
  "What's our overall KPI compliance?",
  "Which patients have overdue SRA assessments?",
  "Show me PAT001's full clinical history",
  "Who hasn't had contact in over 30 days?",
];

function fmt(text) {
  function esc(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  const lines = esc(text).split('\n');
  const out = [];
  let inList = false;
  for (const line of lines) {
    if (inList && !/^\d+\.\s/.test(line.trim())) { out.push('</ol>'); inList = false; }
    let l = line.replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>').replace(/`(.*?)`/g,'<code>$1</code>');
    if (/^#{1,3}\s/.test(l)) l = `<h3>${l.replace(/^#{1,3}\s/,'')}</h3>`;
    else if (/^\d+\.\s/.test(l.trim())) {
      if (!inList) { out.push('<ol>'); inList = true; }
      l = `<li>${l.replace(/^\d+\.\s/,'')}</li>`;
    } else if (/^[-•]\s/.test(l)) l = '• ' + l.slice(2);
    out.push(l);
  }
  if (inList) out.push('</ol>');
  return out.join('<br>').replace(/<br>(<\/?[ohl])/g,'$1').replace(/(<\/[oli]>)<br>/g,'$1');
}

export default function ChatPane({ patients, apiKey, onNeedKey }) {
  const [messages, setMessages] = useState([]);   // { role, text } | { type:'tool', label } | { type:'typing' } | { type:'error', text }
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior:'smooth' }); }, [messages]);

  async function callClaude(msgs) {
    if (!apiKey) { onNeedKey(); throw new Error('No API key'); }
    const res = await fetch(PROXY, {
      method:'POST',
      headers:{'content-type':'application/json','x-api-key':apiKey,'anthropic-version':'2023-06-01','anthropic-dangerous-allow-browser':'true'},
      body:JSON.stringify({ model:MODEL, max_tokens:1024, system:SYSTEM, tools:TOOL_DEFS, messages:msgs })
    });
    if (!res.ok) { const err=await res.json().catch(()=>({})); throw new Error(err?.error?.message||`HTTP ${res.status}`); }
    return res.json();
  }

  async function send(text) {
    const userText = text || input.trim();
    if (!userText || busy) return;
    if (!apiKey) { onNeedKey(); return; }

    setBusy(true);
    setInput('');
    setShowSuggestions(false);
    setMessages(prev => [...prev, { role:'user', text:userText }, { type:'typing' }]);

    const msgs = [...history, { role:'user', content:userText }];
    try {
      while (true) {
        const resp = await callClaude(msgs);
        msgs.push({ role:'assistant', content:resp.content });
        if (resp.stop_reason === 'end_turn') {
          const replyText = resp.content.find(b=>b.type==='text')?.text || '';
          setMessages(prev => {
            const filtered = prev.filter(m=>m.type!=='typing'&&m.type!=='tool');
            return [...filtered, { role:'assistant', text:replyText }];
          });
          setHistory(prev => {
            const next = [...prev, { role:'user', content:userText }, { role:'assistant', content:replyText }];
            return next.length > 20 ? next.slice(-20) : next;
          });
          break;
        }
        if (resp.stop_reason === 'tool_use') {
          const toolUses = resp.content.filter(b=>b.type==='tool_use');
          const toolResults = [];
          for (const tu of toolUses) {
            const label = (TOOL_LABELS[tu.name]||((()=>tu.name)))(tu.input);
            setMessages(prev => { const f=prev.filter(m=>m.type!=='typing'); return [...f, { type:'tool', label }, { type:'typing' }]; });
            toolResults.push({ type:'tool_result', tool_use_id:tu.id, content:JSON.stringify(runTool(tu.name,tu.input,patients)) });
          }
          msgs.push({ role:'user', content:toolResults });
        }
      }
    } catch(err) {
      setMessages(prev => [...prev.filter(m=>m.type!=='typing'), { type:'error', text:err.message }]);
    } finally {
      setBusy(false);
      inputRef.current?.focus();
    }
  }

  function handleKey(e) { if (e.key==='Enter'&&!e.shiftKey) { e.preventDefault(); send(); } }
  function handleResize(e) { e.target.style.height='auto'; e.target.style.height=Math.min(e.target.scrollHeight,120)+'px'; }

  return (
    <div className="chat-pane">
      <div className="chat-main">
        <div className="messages">
          {messages.length === 0 && (
            <div className="welcome">
              <div className="welcome-icon">🧠</div>
              <h2>ClinicalMind AI</h2>
              <p>Ask questions about your patient caseload, clinical history, and care gaps.<br/>
              <small style={{color:'#94a3b8',fontSize:'11px'}}>Requires Anthropic API key · Synthetic dataset · Not real patient data</small></p>
            </div>
          )}
          {messages.map((m, i) => {
            if (m.type === 'typing') return (
              <div key={i} className="typing">
                <div className="dots"><span/><span/><span/></div>
                <span>Thinking…</span>
              </div>
            );
            if (m.type === 'tool') return (
              <div key={i} className="tool-chip">
                <div className="tool-chip-dot"/>
                <span>🔧 {m.label}</span>
              </div>
            );
            if (m.type === 'error') return (
              <div key={i} className="error-msg">Error: {m.text}</div>
            );
            return (
              <div key={i} className={`msg ${m.role}`}>
                <div className="avatar">{m.role==='user'?'👤':'🧠'}</div>
                <div className="bubble" dangerouslySetInnerHTML={{ __html: fmt(m.text) }} />
              </div>
            );
          })}
          <div ref={messagesEndRef} />
        </div>

        {showSuggestions && (
          <div className="suggestions">
            {SUGGESTIONS.map((s,i) => (
              <button key={i} className="chip" onClick={() => send(s)}>{s}</button>
            ))}
          </div>
        )}

        <div className="input-area">
          <textarea
            ref={inputRef}
            className="msg-input"
            rows={1}
            placeholder="Ask about your patients…"
            value={input}
            onChange={e => { setInput(e.target.value); handleResize(e); }}
            onKeyDown={handleKey}
            disabled={busy}
          />
          <button className="send-btn" onClick={() => send()} disabled={busy}>&#10148;</button>
        </div>
      </div>
    </div>
  );
}

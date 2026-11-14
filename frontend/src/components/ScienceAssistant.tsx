import { useState } from 'react';
import { api } from '../api';
import type { MissionSite } from '../missionSites';

type Evidence = { id: string; title: string; date: string; published?: string; instrument?: string; sol?: number | null; summary: string; url: string; credit?: string; limitations?: string; retrieval_score?: number };
type Answer = { answer: string; evidence: Evidence[]; mode: string; caution: string; model?: string; generation_note?: string };
const PROMPTS = [
  'What evidence supports groundwater activity in the boxwork region?',
  'What did Curiosity observe in the sandy hollows and ridges?',
  'What are the nodules and which instrument imaged them?',
  'Which Curiosity observations should be inspected for boxwork morphology?'
];

export default function ScienceAssistant({ missionSite }: { missionSite: MissionSite }) {
  const [question, setQuestion] = useState(PROMPTS[0]);
  const [result, setResult] = useState<Answer | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const ask = async (q = question) => {
    setBusy(true); setError('');
    try { const answer = await api.askScience(q); setResult(answer); }
    catch (err) { setError(err instanceof Error ? err.message : 'Science retrieval failed'); }
    finally { setBusy(false); }
  };
  return <div className="science-content science-assistant">
    <div className="panel-title"><span className="eyebrow">EVIDENCE-GROUNDED SCIENCE ASSISTANT</span><h3>Ask the archive</h3><p>Answers are assembled from a curated NASA/JPL evidence set. Each statement links to its original source.</p></div>
    {missionSite.id !== 'gale' && <div className="science-caution">The bundled evidence set currently focuses on Curiosity / Gale Crater boxwork. It is not yet a site-specific science catalogue for {missionSite.region}. Use the Data tab for live PDS and ODE searches around this selected site.</div>}
    <textarea className="science-question" value={question} onChange={(e) => setQuestion(e.target.value)} rows={4} aria-label="Question for the Mars science assistant"/>
    <button className="package-button" onClick={() => void ask()} disabled={busy || !question.trim()}>{busy ? 'RETRIEVING EVIDENCE…' : 'ASK MARSCOPE'}</button>
    <div className="prompt-list"><span className="eyebrow">SUGGESTED QUESTIONS</span>{PROMPTS.map((prompt) => <button key={prompt} onClick={() => { setQuestion(prompt); void ask(prompt); }}>{prompt}</button>)}</div>
    {error && <div className="error-banner">{error}</div>}
    {result && <div className="assistant-answer"><div className="archive-section-head"><b>RETRIEVED RESPONSE</b><span className="connected-tag">{result.mode.replace(/_/g, ' ').toUpperCase()}{result.model ? ` · ${result.model}` : ''}</span></div><div className="answer-copy">{result.answer.split('\n\n').map((paragraph, i) => <p key={i}>{paragraph}</p>)}</div><div className="science-caution">{result.caution}{result.generation_note ? ` Generation fallback: ${result.generation_note}` : ''}</div><div className="target-list-head"><span className="eyebrow">SOURCE EVIDENCE</span><span className="demo-tag">{result.evidence.length} RECORDS</span></div>{result.evidence.map((item) => <div className="evidence-card" key={item.id}><b>{item.title}</b><small>{item.instrument || 'Archive documentation'} · {item.date}{item.sol ? ` · Sol ${item.sol}` : ''}</small><p>{item.summary}</p>{item.limitations && <small className="muted-copy">Limitations: {item.limitations}</small>}<a href={item.url} target="_blank" rel="noreferrer">OPEN NASA / JPL SOURCE ↗</a></div>)}</div>}
  </div>;
}

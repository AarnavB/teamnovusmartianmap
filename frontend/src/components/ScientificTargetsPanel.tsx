import { useMemo, useState } from 'react';
import type { Point, Target, TerrainData } from '../types';

type Props = {
  terrain: TerrainData | null;
  customTargets: Target[];
  selectedIds: string[];
  scores: Record<string, number>;
  start: Point;
  onTargetsChange: (targets: Target[]) => void;
  onSelectedChange: (ids: string[]) => void;
  onScoresChange: (scores: Record<string, number>) => void;
  onSetDestination: (point: Point) => void;
};

const MAX_OBJECTIVES = 5;
const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));

function scoreTarget(target: Target, terrain: TerrainData, start: Point, relevance: number, scienceWeight: number, accessWeight: number) {
  const x = Math.round(target.x);
  const y = Math.round(target.y);
  const inBounds = x >= 0 && y >= 0 && x < terrain.width && y < terrain.height;
  if (!inBounds) return { score: 0, accessibility: 0, slope: null as number | null, raster: null as number | null, blocked: true };

  const slopeValue = terrain.slope_deg?.[y]?.[x];
  const slope = typeof slopeValue === 'number' && Number.isFinite(slopeValue) ? slopeValue : null;
  const blocked = terrain.obstacle?.[y]?.[x] === true || terrain.valid_mask?.[y]?.[x] === false;
  const rasterValue = terrain.science_potential?.[y]?.[x];
  const raster = typeof rasterValue === 'number' && Number.isFinite(rasterValue) ? clamp(rasterValue * 100, 0, 100) : null;

  // A blocked or NoData cell cannot be recommended as a traverse objective.
  if (blocked) return { score: 0, accessibility: 0, slope, raster, blocked: true };

  const distance = Math.hypot(x - start.x, y - start.y) / Math.max(1, Math.hypot(terrain.width, terrain.height));
  const slopePenalty = slope === null ? 0.35 : clamp(slope / 45, 0, 1);
  const accessibility = clamp(100 * (1 - slopePenalty * 0.62 - distance * 0.22), 0, 100);
  const denominator = Math.max(0.01, scienceWeight + accessWeight);
  const score = Math.round((relevance * scienceWeight + accessibility * accessWeight) / denominator);
  return { score, accessibility: Math.round(accessibility), slope, raster, blocked: false };
}

export default function ScientificTargetsPanel({
  terrain, customTargets, selectedIds, scores, start, onTargetsChange, onSelectedChange, onScoresChange, onSetDestination,
}: Props) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('Geological');
  const [x, setX] = useState(20);
  const [y, setY] = useState(20);
  const [scienceWeight, setScienceWeight] = useState(0.7);
  const [accessWeight, setAccessWeight] = useState(0.3);
  const [formError, setFormError] = useState('');

  const candidates = useMemo(() => {
    const byId = new Map<string, Target>();
    [...(terrain?.targets ?? []), ...customTargets].forEach((target) => byId.set(target.id, target));
    return [...byId.values()];
  }, [terrain?.targets, customTargets]);

  const ranked = useMemo(() => {
    if (!terrain) return [];
    return candidates.map((target) => {
      const tx = Math.round(target.x);
      const ty = Math.round(target.y);
      const inBounds = tx >= 0 && ty >= 0 && tx < terrain.width && ty < terrain.height;
      const cellScore = inBounds ? terrain.science_potential?.[ty]?.[tx] : undefined;
      const defaultRelevance = typeof cellScore === 'number' && Number.isFinite(cellScore)
        ? clamp(Math.round(cellScore * 100), 0, 100)
        : 0;
      const relevance = scores[target.id] ?? defaultRelevance;
      return { target, relevance, ...scoreTarget(target, terrain, start, relevance, scienceWeight, accessWeight) };
    }).sort((a, b) => b.score - a.score);
  }, [terrain, candidates, scores, start, scienceWeight, accessWeight]);

  const addTarget = () => {
    if (!terrain || !name.trim()) return;
    const tx = Math.round(x);
    const ty = Math.round(y);
    if (tx < 0 || ty < 0 || tx >= terrain.width || ty >= terrain.height) {
      setFormError('Coordinates must remain inside the loaded terrain grid.');
      return;
    }
    if (terrain.obstacle?.[ty]?.[tx] === true || terrain.valid_mask?.[ty]?.[tx] === false) {
      setFormError('That cell is blocked or marked NoData. Choose another grid cell.');
      return;
    }
    const target: Target = {
      id: `operator-${Date.now().toString(36)}`,
      name: name.trim(),
      x: tx,
      y: ty,
      description: description.trim() || 'Operator-defined point of interest.',
      evidence_status: 'operator_added',
      science_category: category,
    };
    onTargetsChange([...customTargets, target]);
    onScoresChange({ ...scores, [target.id]: 60 });
    setName('');
    setDescription('');
    setFormError('');
  };

  const toggle = (id: string, blocked: boolean) => {
    if (selectedIds.includes(id)) {
      onSelectedChange(selectedIds.filter((item) => item !== id));
      return;
    }
    if (blocked || selectedIds.length >= MAX_OBJECTIVES) return;
    onSelectedChange([...selectedIds, id]);
  };

  return <section className="science-target-panel">
    <div className="science-panel-head">
      <span className="eyebrow">SCIENCE OPERATIONS</span>
      <h3>Scientific target prioritisation</h3>
      <p>Rank candidate stops against operator-assigned scientific relevance and DEM-derived accessibility. Selected objectives are passed to the route planner as ordered waypoints.</p>
    </div>
    {!terrain ? <div className="science-empty">Load a verified terrain DEM to inspect target candidates.</div> : <>
      <div className="science-priority-controls">
        <div><label>SCIENCE EMPHASIS <b>{Math.round(scienceWeight * 100)}%</b></label><input type="range" min="0" max="100" value={scienceWeight * 100} onChange={(event) => setScienceWeight(Number(event.target.value) / 100)}/></div>
        <div><label>ACCESSIBILITY EMPHASIS <b>{Math.round(accessWeight * 100)}%</b></label><input type="range" min="0" max="100" value={accessWeight * 100} onChange={(event) => setAccessWeight(Number(event.target.value) / 100)}/></div>
      </div>
      <div className="science-score-note">RELATIVE PRIORITY INDEX · heuristic decision aid, not a probability or scientific discovery confidence</div>
      <div className="science-objective-limit">{selectedIds.length}/{MAX_OBJECTIVES} route objectives selected. Reordering is determined by selection order.</div>
      {!ranked.length && <div className="science-empty">No imported scientific target candidates are included in this terrain response. Add an operator-defined point below; MARSCOPE labels it separately rather than presenting it as a discovered feature.</div>}
      <div className="science-target-list">{ranked.map((item, index) => {
        const selected = selectedIds.includes(item.target.id);
        const atLimit = !selected && selectedIds.length >= MAX_OBJECTIVES;
        return <article className={selected ? 'science-target selected' : 'science-target'} key={item.target.id}>
          <div className="science-target-top"><span className="science-rank">{String(index + 1).padStart(2, '0')}</span><div className="science-target-name"><strong>{item.target.name}</strong><small>{item.target.science_category.replace(/_/g, ' ')} · grid {item.target.x}, {item.target.y}</small></div><b className="science-target-score">{item.score}</b></div>
          <p>{item.target.description}</p>
          <div className="science-target-facts"><span>Evidence: {item.target.evidence_status.replace(/_/g, ' ')}</span><span>Slope: {item.slope === null ? 'N/A' : `${item.slope.toFixed(1)}°`}</span><span>Access index: {item.accessibility}</span></div>
          <label className="science-relevance-label">SCIENTIFIC RELEVANCE INPUT <b>{item.relevance}/100</b></label>
          <input className="science-relevance-slider" type="range" min="0" max="100" value={item.relevance} onChange={(event) => onScoresChange({ ...scores, [item.target.id]: Number(event.target.value) })}/>
          <div className="science-target-actions">
            <button onClick={() => toggle(item.target.id, item.blocked)} disabled={item.blocked || atLimit}>{selected ? 'REMOVE OBJECTIVE' : item.blocked ? 'CELL UNAVAILABLE' : atLimit ? 'MAX 5 SELECTED' : 'ADD OBJECTIVE'}</button>
            <button onClick={() => onSetDestination({ x: item.target.x, y: item.target.y })} disabled={item.blocked}>SET AS DESTINATION</button>
          </div>
          <small className="science-data-caveat">{item.blocked ? 'Target cell is blocked or marked NoData and cannot be selected for a traverse objective.' : item.raster === null ? 'No science-potential raster value at this cell; the relevance input is operator-assigned and is not a measured science score.' : `Science-potential layer index at cell: ${item.raster.toFixed(0)}/100 (layer index, not probability).`}{terrain.uncertainty?.[Math.round(item.target.y)]?.[Math.round(item.target.x)] !== undefined ? ' Uncertainty-layer value available for inspection.' : ' No cell-level uncertainty value supplied.'}</small>
        </article>;
      })}</div>
      <div className="science-custom-form">
        <div className="provenance-section-title"><span>ADD OPERATOR TARGET</span><b>MANUAL ENTRY</b></div>
        <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Target name"/>
        <textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="What should the science team inspect?"/>
        <select value={category} onChange={(event) => setCategory(event.target.value)}><option>Geological</option><option>Sedimentary</option><option>Layered outcrop</option><option>Mineralogical</option><option>Other</option></select>
        <div className="science-coordinate-inputs"><label>GRID X<input type="number" min="0" max={terrain.width - 1} value={x} onChange={(event) => setX(Number(event.target.value))}/></label><label>GRID Y<input type="number" min="0" max={terrain.height - 1} value={y} onChange={(event) => setY(Number(event.target.value))}/></label></div>
        {formError && <div className="science-form-error" role="alert">{formError}</div>}
        <button onClick={addTarget} disabled={!name.trim()}>ADD TARGET TO MAP</button>
        <small>Operator-added targets are stored in this page session and labelled separately from imported candidates.</small>
      </div>
    </>}
  </section>;
}

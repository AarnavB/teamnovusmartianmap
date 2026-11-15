import { useMemo, useState } from 'react';
import { api } from '../api';
import type { MissionConstraintsPayload, Point, Route, SensitivityResponse, TerrainData } from '../types';

type Props = {
  siteId: string;
  terrain: TerrainData | null;
  start: Point;
  goal: Point;
  maxSlope: number;
  constraints: MissionConstraintsPayload;
  selectedRoute: Route | null;
};

function overlapPercent(a: Point[], b: Point[]) {
  if (!a.length || !b.length) return null;
  const key = (point: Point) => `${point.x},${point.y}`;
  const aset = new Set(a.map(key));
  const bset = new Set(b.map(key));
  let common = 0;
  aset.forEach((point) => { if (bset.has(point)) common += 1; });
  return Math.round(100 * common / Math.max(1, new Set([...aset, ...bset]).size));
}

export default function RouteRobustnessPanel({
  siteId, terrain, start, goal, maxSlope, constraints, selectedRoute,
}: Props) {
  const [result, setResult] = useState<SensitivityResponse | null>(null);
  const [analyzedFor, setAnalyzedFor] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const analysisKey = [
    siteId, terrain?.id ?? '', start.x, start.y, goal.x, goal.y, maxSlope,
    selectedRoute?.id ?? '', selectedRoute?.path.map((point) => `${point.x}:${point.y}`).join(',') ?? '',
    constraints.eva_limit_minutes ?? '', constraints.energy_budget_wh ?? '',
    constraints.oxygen_budget_l ?? '', constraints.oxygen_consumption_lpm ?? '',
    constraints.carried_equipment_mass_kg ?? '', constraints.rest_interval_min ?? '',
  ].join('|');

  const currentResult = analyzedFor === analysisKey ? result : null;

  const summary = useMemo(() => {
    if (!currentResult || !selectedRoute) return null;
    const valid = currentResult.sweep.filter((item) => item.feasible && item.path.length > 0);
    const overlaps = valid.map((item) => overlapPercent(selectedRoute.path, item.path)).filter((value): value is number => value !== null);
    const distances = valid.map((item) => item.distance_m).filter((value): value is number => typeof value === 'number');
    return {
      valid: valid.length,
      total: currentResult.sweep.length,
      returnFeasible: valid.filter((item) => item.return_feasible).length,
      meanOverlap: overlaps.length ? Math.round(overlaps.reduce((sum, value) => sum + value, 0) / overlaps.length) : null,
      distanceSpread: distances.length > 1 ? Math.max(...distances) - Math.min(...distances) : null,
    };
  }, [currentResult, selectedRoute]);

  const runAnalysis = async () => {
    if (!terrain || !selectedRoute || loading) return;
    let values = [...new Set([maxSlope - 5, maxSlope, maxSlope + 5].map((value) => Math.max(5, Math.min(50, Number(value.toFixed(1))))) )].sort((a, b) => a - b);
    if (values.length < 3) values = [5, 25, 50];
    setLoading(true);
    setError('');
    setResult(null);
    setAnalyzedFor('');
    const stableConstraints = {
      max_slope_deg: maxSlope,
      eva_limit_minutes: constraints.eva_limit_minutes,
      energy_budget_wh: constraints.energy_budget_wh,
      oxygen_budget_l: constraints.oxygen_budget_l,
      oxygen_consumption_lpm: constraints.oxygen_consumption_lpm,
      carried_equipment_mass_kg: constraints.carried_equipment_mass_kg,
      rest_interval_min: constraints.rest_interval_min,
    };
    try {
      const response = await api.sensitivity(siteId, start, goal, stableConstraints, values);
      setResult(response);
      setAnalyzedFor(analysisKey);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sensitivity analysis failed');
    } finally {
      setLoading(false);
    }
  };

  return <section className="robustness-panel">
    <div className="robustness-head"><div><span className="eyebrow">ROUTE VALIDATION</span><h3>Robustness & sensitivity</h3><p>Re-runs the balanced planner under three nearby maximum-slope constraints on the active DEM.</p></div><span className="robustness-tag">SCENARIO SWEEP</span></div>
    <div className="robustness-controls"><span>Baseline maximum slope: <b>{maxSlope.toFixed(0)}°</b></span><button onClick={() => void runAnalysis()} disabled={!terrain || !selectedRoute || loading}>{loading ? 'EVALUATING SCENARIOS…' : currentResult ? 'RERUN ANALYSIS' : 'RUN ROBUSTNESS ANALYSIS'}</button></div>
    {loading && <div className="robustness-state">Evaluating the requested terrain-constraint scenarios. This may take longer on the hosted research API.</div>}
    {error && <div className="robustness-error">Sensitivity analysis unavailable: {error}</div>}
    {!loading && summary && <>
      <div className="robustness-kpis">
        <div><span>FEASIBLE SCENARIOS</span><strong>{summary.valid}/{summary.total}</strong></div>
        <div><span>RETURN FEASIBLE</span><strong>{summary.returnFeasible}/{summary.valid}</strong></div>
        <div><span>MEAN PATH OVERLAP</span><strong>{summary.meanOverlap === null ? 'N/A' : `${summary.meanOverlap}%`}</strong></div>
        <div><span>DISTANCE SPREAD</span><strong>{summary.distanceSpread === null ? 'N/A' : `${summary.distanceSpread.toFixed(0)} m`}</strong></div>
      </div>
      <div className="robustness-scenarios">{currentResult?.sweep.map((item) => {
        const overlap = overlapPercent(selectedRoute?.path ?? [], item.path);
        return <div className="robustness-scenario" key={item.value}>
          <div><b>{item.value.toFixed(0)}°</b><span>MAX SLOPE</span></div>
          <div className="robustness-track"><i style={{ width: `${item.feasible ? overlap ?? 0 : 0}%` }}/></div>
          <div className={item.feasible && item.return_feasible ? 'scenario-ok' : 'scenario-warn'}>{!item.feasible ? 'NO ROUTE' : item.return_feasible ? 'RETURN OK' : 'RETURN LIMIT'}</div>
          <small>{item.feasible ? `${item.distance_m?.toFixed(0) ?? '—'} m · ${overlap ?? '—'}% path overlap` : item.error ?? 'Infeasible'}</small>
        </div>;
      })}</div>
      <p className="robustness-footnote">{currentResult?.notice} Path overlap compares the selected route with the balanced-profile route produced by each backend slope scenario. This is a deterministic sensitivity sweep, not a probability of safety or a guarantee under unmodelled terrain conditions.</p>
    </>}
    {!loading && !currentResult && !error && <div className="robustness-state">{!terrain ? 'Load a verified DEM first.' : !selectedRoute ? 'Generate a route first.' : 'Run the scenario sweep when you want to evaluate this route. Results are tied to the current route and constraints.'}</div>}
  </section>;
}


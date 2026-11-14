import { useCallback, useEffect, useMemo, useState } from 'react';
import TerrainScene from './components/TerrainScene';
import { api } from './api';
import type { BenchmarkResult, DatasetRecord, PlanResponse, Point, ReplanResponse, Route, TerrainData } from './types';

type Layer = 'elevation' | 'slope' | 'roughness' | 'uncertainty' | 'science';
const INITIAL_START: Point = { x: 4, y: 5 };
const INITIAL_GOAL: Point = { x: 59, y: 56 };

const layerNames: { id: Layer; name: string; unit: string }[] = [
  { id: 'elevation', name: 'Elevation', unit: 'synthetic m' },
  { id: 'slope', name: 'Slope', unit: 'degrees' },
  { id: 'roughness', name: 'Roughness', unit: '0–1 index' },
  { id: 'uncertainty', name: 'Uncertainty', unit: '0–1 index' },
  { id: 'science', name: 'Science potential', unit: '0–1 index' },
];

function pointText(p: Point) { return `X ${String(p.x).padStart(2, '0')} / Y ${String(p.y).padStart(2, '0')}`; }
function closestTarget(terrain: TerrainData | null, point: Point) {
  if (!terrain?.targets.length) return null;
  return [...terrain.targets].sort((a, b) => Math.hypot(a.x - point.x, a.y - point.y) - Math.hypot(b.x - point.x, b.y - point.y))[0];
}

export default function App() {
  const [terrain, setTerrain] = useState<TerrainData | null>(null);
  const [datasets, setDatasets] = useState<DatasetRecord[]>([]);
  const [plan, setPlan] = useState<PlanResponse | null>(null);
  const [routes, setRoutes] = useState<Route[]>([]);
  const [selectedRoute, setSelectedRoute] = useState('B');
  const [start, setStart] = useState<Point>(INITIAL_START);
  const [goal, setGoal] = useState<Point>(INITIAL_GOAL);
  const [layer, setLayer] = useState<Layer>('elevation');
  const [viewMode, setViewMode] = useState<'3D' | '2D'>('3D');
  const [pickMode, setPickMode] = useState<'start' | 'goal' | null>(null);
  const [evaMode, setEvaMode] = useState(false);
  const [activeTab, setActiveTab] = useState<'planner' | 'science' | 'data'>('planner');
  const [maxSlope, setMaxSlope] = useState(22);
  const [evaMinutes, setEvaMinutes] = useState(180);
  const [loading, setLoading] = useState(true);
  const [planning, setPlanning] = useState(false);
  const [replanning, setReplanning] = useState(false);
  const [error, setError] = useState('');
  const [replanResult, setReplanResult] = useState<ReplanResponse | null>(null);
  const [benchmarkResults, setBenchmarkResults] = useState<BenchmarkResult[]>([]);
  const [benchmarking, setBenchmarking] = useState(false);
  const [addedObstacles, setAddedObstacles] = useState<Point[]>([]);
  const [status, setStatus] = useState('CONNECTING');

  useEffect(() => {
    let alive = true;
    Promise.all([api.terrain(), api.registry(), api.health()])
      .then(([terrainData, registry, health]) => {
        if (!alive) return;
        setTerrain(terrainData);
        setDatasets(registry.datasets);
        setStatus(health.status.toUpperCase());
      })
      .catch((err: Error) => {
        if (!alive) return;
        setError(`Backend unavailable: ${err.message}. Start the FastAPI server and refresh.`);
        setStatus('OFFLINE');
      })
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, []);

  const runPlan = useCallback(async (newStart = start, newGoal = goal) => {
    setPlanning(true);
    setError('');
    setReplanResult(null);
    setAddedObstacles([]);
    try {
      const result = await api.plan(newStart, newGoal, {
        max_slope_deg: maxSlope,
        max_temperature_c: -35,
        eva_limit_minutes: evaMinutes,
        energy_budget_wh: 180,
        return_reserve_fraction: 0.25,
        suit_mass_kg: 42,
        base_speed_mps: 0.65,
      });
      setPlan(result);
      setRoutes(result.routes);
      setSelectedRoute('B');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Route planning failed');
    } finally {
      setPlanning(false);
    }
  }, [start, goal, maxSlope, evaMinutes]);

  useEffect(() => {
    if (terrain && !plan && !planning && !error) void runPlan(INITIAL_START, INITIAL_GOAL);
  }, [terrain, plan, planning, error, runPlan]);

  const handlePick = useCallback((point: Point) => {
    if (!terrain) return;
    if (pickMode === 'start') setStart(point);
    if (pickMode === 'goal') setGoal(point);
    setPickMode(null);
  }, [pickMode, terrain]);

  const runBenchmark = async () => {
    setBenchmarking(true);
    setError('');
    try {
      const result = await api.benchmark(start, goal, {
        max_slope_deg: maxSlope, max_temperature_c: -35, eva_limit_minutes: evaMinutes,
        energy_budget_wh: 180, return_reserve_fraction: 0.25, suit_mass_kg: 42, base_speed_mps: 0.65,
      });
      setBenchmarkResults(result.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Benchmark failed');
    } finally { setBenchmarking(false); }
  };

  const injectObstacle = async () => {
    if (!plan) return;
    const selected = routes.find((route) => route.id === selectedRoute) ?? routes[1];
    if (!selected || selected.path.length < 5) return;
    const middle = selected.path[Math.floor(selected.path.length * 0.52)];
    const candidates = [middle, ...selected.path.slice(Math.max(1, Math.floor(selected.path.length * 0.52) - 3), Math.floor(selected.path.length * 0.52) + 4)];
    const obstacle = candidates.find((p) =>
      Math.hypot(p.x - start.x, p.y - start.y) > 3 &&
      Math.hypot(p.x - goal.x, p.y - goal.y) > 3 &&
      !addedObstacles.some((q) => q.x === p.x && q.y === p.y) &&
      !terrain?.obstacle[p.y][p.x]
    );
    if (!obstacle) {
      setError('Could not find a suitable cell on the route for the simulated obstacle.');
      return;
    }
    setReplanning(true);
    setError('');
    try {
      const result = await api.replan(plan.plan_id, obstacle);
      setReplanResult(result);
      setAddedObstacles(result.obstacles_added);
      setRoutes((previous) => previous.map((route) => route.profile === 'balanced'
        ? { ...route, path: result.path, metrics: result.metrics }
        : route));
      setSelectedRoute('B');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Adaptive replanning failed');
    } finally {
      setReplanning(false);
    }
  };

  const selected = routes.find((route) => route.id === selectedRoute) ?? routes[1] ?? routes[0];
  const closest = useMemo(() => closestTarget(terrain, start), [terrain, start]);
  const totalTime = selected?.metrics.duration_min ?? 0;

  if (loading) return <div className="boot-screen"><div className="boot-mark">M</div><div className="boot-title">MARSCOPE</div><div className="boot-sub">INITIALIZING PLANETARY SYSTEMS</div><div className="boot-bar"><span /></div></div>;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <div className="brand-mark">M</div>
          <div><div className="brand-name">MARSCOPE</div><div className="brand-tag">FROM ORBIT TO BOOTPRINT</div></div>
        </div>
        <div className="mission-crumb"><span className="crumb-dot" /> GALE CRATER <span>/</span> MOUNT SHARP <span>/</span> BOXWORK STUDY</div>
        <div className="top-status"><span className={`status-dot ${status === 'OK' ? 'online' : 'offline'}`} /> API {status} <span className="top-divider" /> <span className="mono">BUILD 0.1.0</span></div>
      </header>

      <main className="workspace">
        <section className="left-rail">
          <div className="rail-head"><span className="eyebrow">MISSION AREA</span><span className="live-chip">SIMULATION</span></div>
          <div className="location-card">
            <div className="planet-glyph">♂</div>
            <div className="location-copy"><strong>Mount Sharp</strong><span>Gale Crater · Mars</span></div>
            <div className="location-chevron">⌄</div>
          </div>
          <div className="section-kicker">MISSION PLANNING</div>
          <div className="field-stack">
            <div className="field-label"><span>01 / START POINT</span><button className={`tiny-action ${pickMode === 'start' ? 'active' : ''}`} onClick={() => setPickMode(pickMode === 'start' ? null : 'start')}>PICK ON MAP</button></div>
            <div className="coord-card"><span className="point-symbol start-symbol">A</span><div><b>{pointText(start)}</b><small>Grid reference · synthetic tile</small></div></div>
            <div className="field-label"><span>02 / DESTINATION</span><button className={`tiny-action ${pickMode === 'goal' ? 'active' : ''}`} onClick={() => setPickMode(pickMode === 'goal' ? null : 'goal')}>PICK ON MAP</button></div>
            <div className="coord-card"><span className="point-symbol goal-symbol">B</span><div><b>{pointText(goal)}</b><small>Grid reference · synthetic tile</small></div></div>
            {pickMode && <div className="pick-hint">Click a location on the terrain to set the {pickMode === 'start' ? 'start point' : 'destination'}.</div>}
          </div>

          <div className="field-stack mission-params">
            <div className="section-kicker">OPERATIONAL CONSTRAINTS</div>
            <div className="slider-row"><div><label>Maximum slope</label><b>{maxSlope}°</b></div><input type="range" min="10" max="35" value={maxSlope} onChange={(e) => setMaxSlope(Number(e.target.value))} /></div>
            <div className="slider-row"><div><label>EVA time budget</label><b>{evaMinutes} min</b></div><input type="range" min="60" max="300" step="15" value={evaMinutes} onChange={(e) => setEvaMinutes(Number(e.target.value))} /></div>
            <div className="constraint-note"><span className="lock-icon">⌑</span> Return reserve: 25% · Energy budget: 180 Wh (model assumptions)</div>
          </div>
          <button className="primary-button" onClick={() => void runPlan()} disabled={planning || !terrain}>
            {planning ? <><span className="spinner" /> COMPUTING ROUTES</> : <><span>⌁</span> GENERATE ROUTE OPTIONS</>}
          </button>
          <button className="ghost-button" onClick={() => { setStart(INITIAL_START); setGoal(INITIAL_GOAL); void runPlan(INITIAL_START, INITIAL_GOAL); }}>RESET MISSION GEOMETRY</button>

          <div className="rail-footnote"><span className="warning-icon">!</span><p>Research prototype only. Never use these paths as operational astronaut guidance.</p></div>
        </section>

        <section className="center-column">
          <div className="view-header">
            <div><div className="eyebrow">SURFACE RECONNAISSANCE</div><h1>Gale Crater <span>/</span> Mount Sharp</h1></div>
            <div className="view-actions"><div className="segmented"><button className={viewMode === '3D' ? 'selected' : ''} onClick={() => setViewMode('3D')}>3D TERRAIN</button><button className={viewMode === '2D' ? 'selected' : ''} onClick={() => setViewMode('2D')}>2D MAP</button></div><button className={`eva-toggle ${evaMode ? 'on' : ''}`} onClick={() => setEvaMode(!evaMode)}><span className="eva-dot" /> EVA MODE</button></div>
          </div>

          <div className="terrain-frame">
            {terrain && <TerrainScene terrain={terrain} routes={routes} selectedRoute={selectedRoute} start={start} goal={goal} obstacles={addedObstacles} layer={layer} viewMode={viewMode} pickMode={pickMode} onPick={handlePick} />}
            <div className="scene-top-left"><span className="scene-tag"><i /> TERRAIN MODEL</span><span className="scene-tag muted">SYNTHETIC / NOT GEOREFERENCED</span></div>
            <div className="scene-top-right"><span className="compass">N</span><span className="compass-line" /></div>
            <div className="scene-bottom-left"><span className="scale-bar"><i /></span><span>500 m <small>illustrative scale only</small></span></div>
            <div className="scene-bottom-right"><span className="view-caption">{viewMode === '3D' ? 'OBLIQUE VIEW' : 'PLAN VIEW'}</span><span className="zoom-hint">DRAG TO ORBIT · SCROLL TO ZOOM</span></div>
            {pickMode && <div className="map-pick-overlay">SELECT {pickMode === 'start' ? 'START POINT' : 'DESTINATION'} ON THE TERRAIN</div>}
          </div>

          <div className="layer-strip">
            <div className="layer-title"><span className="eyebrow">MAP LAYERS</span><span className="layer-count">{layerNames.length} AVAILABLE</span></div>
            <div className="layer-buttons">{layerNames.map((entry) => <button key={entry.id} className={layer === entry.id ? 'layer-button active' : 'layer-button'} onClick={() => setLayer(entry.id)}><span className={`layer-swatch swatch-${entry.id}`} />{entry.name}</button>)}</div>
            <div className="layer-metadata"><span>SOURCE <b>Deterministic synthetic fixture</b></span><span>DATE <b>Not an observation</b></span><span>GRID SPACING <b>{terrain?.cell_size_m ?? 8} m assumed</b></span><span>UNITS <b>{layerNames.find((entry) => entry.id === layer)?.unit}</b></span></div>
          </div>

          {evaMode ? (
            <div className="eva-panel">
              <div className="eva-panel-head"><div><span className="eyebrow">FIELD NAVIGATION INTERFACE</span><h2>EXTRAVEHICULAR ACTIVITY</h2></div><span className="eva-badge">SIMULATED</span></div>
              <div className="eva-grid">
                <div className="eva-stat"><span>CURRENT POSITION</span><strong>{pointText(start)}</strong><small>Grid reference · synthetic</small></div>
                <div className="eva-stat"><span>NEXT WAYPOINT</span><strong>{closest?.name ?? 'No target'}</strong><small>{closest ? `${Math.round(Math.hypot(closest.x - start.x, closest.y - start.y) * (terrain?.cell_size_m ?? 8))} m approx.` : 'No target selected'}</small></div>
                <div className="eva-stat"><span>ESTIMATED OUTBOUND</span><strong>{totalTime.toFixed(1)} min</strong><small>Illustrative model</small></div>
                <div className="eva-stat"><span>RETURN FEASIBILITY</span><strong className={selected?.metrics.return_feasible ? 'good' : 'bad'}>{selected?.metrics.return_feasible ? 'WITHIN BUDGET' : 'REVIEW LIMITS'}</strong><small>Reserve included in test</small></div>
              </div>
              <div className="eva-notice">Offline use is a planned capability, not implemented in this release. Cache packages, map tile manifests and signed mission plans are part of the next integration phase.</div>
            </div>
          ) : (
            <div className="route-section">
              <div className="section-heading"><div><span className="eyebrow">PATHFINDING ENGINE</span><h2>Route alternatives <span className="count-pill">{routes.length}</span></h2></div><div className="route-actions"><button className="text-action" onClick={() => void runBenchmark()} disabled={benchmarking || planning}>{benchmarking ? 'COMPARING…' : 'COMPARE BASELINES'}</button><button className="text-action" onClick={() => void injectObstacle()} disabled={!plan || replanning || !routes.length}>{replanning ? 'REPAIRING GRAPH…' : '＋ SIMULATE OBSTACLE'}</button></div></div>
              <div className="route-cards">
                {routes.map((route) => <button key={route.id} className={`route-card ${selectedRoute === route.id ? 'selected' : ''}`} onClick={() => setSelectedRoute(route.id)}>
                  <div className="route-card-top"><span className={`route-letter route-${route.id}`}>{route.id}</span><span className="route-status">{route.is_pareto ? 'PARETO' : 'ALTERNATIVE'}</span></div>
                  <strong>{route.name}</strong><p>{route.summary}</p>
                  <div className="route-metrics-mini"><span><b>{route.metrics.distance_m.toFixed(0)}</b> m</span><span><b>{route.metrics.duration_min.toFixed(1)}</b> min</span><span><b>{route.metrics.terrain_risk_pct.toFixed(0)}</b> risk</span></div>
                </button>)}
              </div>
              {benchmarkResults.length > 0 && <div className="benchmark-strip">
                <div className="benchmark-head"><b>BASELINE COMPARISON</b><small>Same synthetic grid · balanced scalar cost for A* and Dijkstra</small></div>
                {benchmarkResults.map((result) => <div className="benchmark-row" key={result.algorithm}><span>{result.algorithm.replace('_', ' ').toUpperCase()}</span><b>{result.distance_m.toFixed(0)} m</b><b>{result.runtime_ms.toFixed(2)} ms</b><small>{result.expanded_nodes.toLocaleString()} expanded</small></div>)}
                <small className="benchmark-warning">Synthetic-fixture timings only; not a claim of field or orbital-data performance.</small>
              </div>}
              {replanResult && <div className="repair-banner"><span className="repair-icon">↻</span><div><b>Incremental route repair complete</b><small>LPA* updated the selected route after a simulated obstacle. {replanResult.expanded_during_repair} nodes expanded during repair.</small></div><button onClick={() => setReplanResult(null)}>×</button></div>}
              {error && <div className="error-banner"><span>!</span>{error}</div>}
            </div>
          )}
        </section>

        <aside className="right-rail">
          <div className="right-tabs"><button className={activeTab === 'planner' ? 'active' : ''} onClick={() => setActiveTab('planner')}>ANALYTICS</button><button className={activeTab === 'science' ? 'active' : ''} onClick={() => setActiveTab('science')}>SCIENCE</button><button className={activeTab === 'data' ? 'active' : ''} onClick={() => setActiveTab('data')}>DATA</button></div>
          {activeTab === 'planner' && selected && <div className="analytics-content">
            <div className="analytics-head"><span className="eyebrow">SELECTED PROFILE</span><div className="selected-title"><span className={`route-letter route-${selected.id}`}>{selected.id}</span><h3>{selected.name}</h3></div></div>
            <div className="metric-hero"><div><span>TOTAL DISTANCE</span><strong>{selected.metrics.distance_m.toFixed(0)}<small>m</small></strong></div><div><span>TRAVEL TIME</span><strong>{selected.metrics.duration_min.toFixed(1)}<small>min</small></strong></div></div>
            <div className="metric-list">
              <MetricBar label="Terrain risk" value={selected.metrics.terrain_risk_pct} color="sand" />
              <MetricBar label="Environmental index (simulated)" value={selected.metrics.environment_risk_pct} color="cyan" />
              <MetricBar label="Radiation index (simulated)" value={selected.metrics.radiation_index_pct} color="gold" />
              <MetricBar label="Data uncertainty" value={selected.metrics.uncertainty_pct} color="yellow" />
              <MetricBar label="Scientific value" value={selected.metrics.scientific_value_pct} color="green" />
            </div>
            <div className="resource-block"><div className="resource-heading"><span className="eyebrow">RESOURCE MODEL</span><span className={`feasibility ${selected.metrics.return_feasible ? 'pass' : 'fail'}`}>{selected.metrics.return_feasible ? 'RETURN FEASIBLE' : 'LIMIT EXCEEDED'}</span></div><div className="resource-row"><span>Estimated energy</span><b>{selected.metrics.energy_wh.toFixed(1)} Wh</b></div><div className="resource-row"><span>Out-and-back time</span><b>{selected.metrics.return_time_estimate_min.toFixed(1)} min</b></div><div className="resource-row"><span>Out-and-back energy</span><b>{selected.metrics.return_energy_estimate_wh.toFixed(1)} Wh</b></div></div>
            <div className="algorithm-card"><div className="algorithm-head"><span className="algorithm-icon">ƒ</span><div><b>HYBRID MULTI-OBJECTIVE A*</b><small>Bounded Pareto label search</small></div></div><div className="algorithm-stats"><div><b>{selected.search.expanded_nodes.toLocaleString()}</b><small>Expanded</small></div><div><b>{selected.search.generated_labels.toLocaleString()}</b><small>Labels</small></div><div><b>{selected.search.pareto_labels_at_goal}</b><small>Goal labels</small></div></div></div>
            <p className="metric-foot">{selected.metrics.model_note}</p>
          </div>}

          {activeTab === 'science' && <div className="science-content">
            <div className="panel-title"><span className="eyebrow">GEOLOGICAL INVESTIGATION</span><h3>Ancient groundwater record</h3><p>NASA has documented boxwork ridges, sandy hollows and nearby buttes during Curiosity's Mount Sharp traverse.</p></div>
            <div className="science-feature"><div className="feature-kicker">NASA / JPL FIELD CONTEXT</div><strong>Curiosity on the Road to Boxwork Formations</strong><p>Mastcam panorama captured March 9, 2025, on Sol 4476. Gould Mesa showed possible first glimpses of boxwork structures from the rover's position.</p><a href="https://www.jpl.nasa.gov/images/pia26552-curiosity-on-the-road-to-boxwork-formations/" target="_blank" rel="noreferrer">OPEN ORIGINAL NASA/JPL IMAGE ↗</a></div>
            <div className="target-list-head"><span className="eyebrow">DEMO TARGETS</span><span className="demo-tag">SYNTHETIC</span></div>
            {terrain?.targets.map((target, i) => <div className="target-item" key={target.id}><span className="target-number">0{i + 1}</span><div><b>{target.name}</b><small>{target.description}</small><span className="target-id">{target.id} · {target.science_category}</span></div></div>)}
            <div className="science-caution">These three map targets are synthetic teaching points. They do not represent Curiosity waypoints, measured mineral deposits or published feature coordinates.</div>
          </div>}

          {activeTab === 'data' && <div className="data-content">
            <div className="panel-title"><span className="eyebrow">DATA REGISTRY</span><h3>Mission evidence</h3><p>Source-level metadata and integration status. Connected versus documented sources are distinguished.</p></div>
            {datasets.map((record) => <div className="dataset-row" key={record.id}><div className="dataset-top"><b>{record.name}</b><span className={record.implementation === 'DOCUMENTED_NOT_CONNECTED_IN_DEMO' ? 'doc-status' : 'not-status'}>{record.implementation === 'DOCUMENTED_NOT_CONNECTED_IN_DEMO' ? 'DOCUMENTED' : 'REFERENCE'}</span></div><small>{record.mission} · {record.instrument}</small><div className="dataset-detail">{record.resolution}</div><a href={record.url} target="_blank" rel="noreferrer">SOURCE RECORD ↗</a></div>)}
          </div>}
        </aside>
      </main>
      <footer className="app-footer"><span>© MARSCOPE RESEARCH PROTOTYPE</span><span>DATA STATUS: SYNTHETIC DEMONSTRATION TILE</span><span>NOT FOR OPERATIONAL USE</span></footer>
    </div>
  );
}

function MetricBar({ label, value, color }: { label: string; value: number; color: string }) {
  return <div className="metric-bar-row"><div className="metric-bar-label"><span>{label}</span><b>{value.toFixed(0)}%</b></div><div className="bar-track"><div className={`bar-fill ${color}`} style={{ width: `${Math.max(0, Math.min(100, value))}%` }} /></div></div>;
}

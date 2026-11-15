import type { Point, Route, Target, TerrainData } from '../types';

type Mode = 'desktop' | 'helmet' | 'minimal';
type Props = {
  mode: Mode; onModeChange: (mode: Mode) => void; onClose: () => void;
  siteName: string; terrain: TerrainData | null; route: Route | null; start: Point; goal: Point;
  currentPosition: Point; progressIndex: number; targets: Target[]; selectedTargetIds: string[];
  oxygenRemainingL: number; energyRemainingWh: number; evaMinutesRemaining: number;
};

function distance(a: Point, b: Point, cellSize: number) { return Math.hypot(a.x - b.x, a.y - b.y) * cellSize; }
function heading(a: Point, b: Point) {
  const deg = (Math.atan2(b.x - a.x, -(b.y - a.y)) * 180 / Math.PI + 360) % 360;
  const compass = ['N','NE','E','SE','S','SW','W','NW'];
  return { deg: Math.round(deg), text: compass[Math.round(deg / 45) % 8] };
}
function safe(value: number | undefined, digits = 0) { return typeof value === 'number' && Number.isFinite(value) ? value.toFixed(digits) : 'N/A'; }

export default function AstronautHud({
  mode, onModeChange, onClose, siteName, terrain, route, start, goal, currentPosition, progressIndex,
  targets, selectedTargetIds, oxygenRemainingL, energyRemainingWh, evaMinutesRemaining,
}: Props) {
  const path = route?.path ?? [];
  const next = path[Math.min(path.length - 1, Math.max(0, progressIndex + 1))] ?? goal;
  const bearing = heading(currentPosition, next);
  const cell = terrain?.cell_size_m ?? 1;
  const currentSlope = terrain?.slope_deg?.[currentPosition.y]?.[currentPosition.x];
  const currentElevation = terrain?.elevation_m?.[currentPosition.y]?.[currentPosition.x];
  const nearby = targets.filter((target) => selectedTargetIds.includes(target.id));
  const nearestScience = [...(nearby.length ? nearby : targets)].sort((a,b) => distance(currentPosition,a,cell)-distance(currentPosition,b,cell))[0];
  const targetDistance = nearestScience ? distance(currentPosition, nearestScience, cell) : null;
  const routePoints = path.map((point) => `${point.x},${terrain?.height ? terrain.height - point.y : point.y}`).join(' ');
  return <div className={`astronaut-hud-shell hud-${mode}`}>
    <div className="hud-topbar"><div className="hud-brand"><span className="hud-brand-mark">M</span><div><b>MARSCOPE / EVA VISOR</b><small>{siteName.toUpperCase()} · MISSION INTERFACE SIMULATION</small></div></div><div className="hud-mode-switch">{(['desktop','helmet','minimal'] as Mode[]).map((value) => <button key={value} className={mode === value ? 'active' : ''} onClick={() => onModeChange(value)}>{value.toUpperCase()}</button>)}</div><button className="hud-exit" onClick={onClose}>EXIT HUD ✕</button></div>
    <div className="hud-viewfinder">
      <div className="hud-horizon-line"/>
      <div className="hud-reticle"><i/><b/><span/></div>
      <div className="hud-heading"><small>HEADING</small><strong>{bearing.text} {bearing.deg.toString().padStart(3,'0')}°</strong><div className="hud-compass-ticks"><span>N</span><i/><span>NE</span><i/><span>E</span><i/><span>SE</span></div></div>
      <div className="hud-left-stack">
        <div className="hud-readout"><small>NEXT WAYPOINT</small><strong>WP-{String(Math.min(path.length, progressIndex + 2)).padStart(2,'0')}</strong><span>{distance(currentPosition,next,cell).toFixed(0)} m · {bearing.text}</span></div>
        <div className="hud-readout"><small>TERRAIN</small><strong>{currentSlope === undefined ? 'SLOPE N/A' : `${currentSlope.toFixed(1)}° SLOPE`}</strong><span>{currentElevation === undefined ? 'Elevation unavailable' : `${currentElevation.toFixed(1)} m elevation`}</span></div>
      </div>
      <div className="hud-right-stack">
        <div className="hud-readout"><small>SCIENCE OBJECTIVE</small><strong>{nearestScience?.name ?? 'NO TARGET SELECTED'}</strong><span>{targetDistance === null ? 'Select a science target' : `${targetDistance.toFixed(0)} m · operator priority`}</span></div>
        <div className="hud-readout hud-warning"><small>DATA QUALITY</small><strong>{terrain?.valid_mask?.[currentPosition.y]?.[currentPosition.x] === false ? 'NODATA CELL' : terrain?.uncertainty ? 'UNCERTAINTY LAYER' : 'LIMITED DATA'}</strong><span>Use caution where coverage or uncertainty is incomplete</span></div>
      </div>
      <div className="hud-route-map"><div><small>TRAVERSE CORRIDOR</small><b>{route?.name ?? 'NO ROUTE'}</b></div>{terrain && <svg viewBox={`0 0 ${terrain.width} ${terrain.height}`} preserveAspectRatio="none"><polyline points={routePoints}/><circle cx={currentPosition.x} cy={terrain.height-currentPosition.y} r="1.8"/><circle className="hud-goal" cx={goal.x} cy={terrain.height-goal.y} r="1.3"/></svg>}<small>{route ? `${route.path.length} path cells · ${safe(route.metrics.distance_m)} m planned` : 'Plan a route to populate the visor'}</small></div>
      <div className="hud-bottom-left"><span>POS</span><b>{currentPosition.x.toFixed(0)} / {currentPosition.y.toFixed(0)}</b><span>START</span><b>{start.x} / {start.y}</b></div>
      <div className="hud-bottom-right"><span>LINK</span><b className="hud-link">SIMULATED</b><span>MISSION STATE</span><b>PLANNING REHEARSAL</b></div>
      {mode !== 'minimal' && <div className="hud-resource-strip">
        <div><small>ENERGY RESERVE*</small><strong>{safe(energyRemainingWh)} Wh</strong></div>
        <div><small>O₂ RESERVE*</small><strong>{safe(oxygenRemainingL)} L</strong></div>
        <div><small>EVA TIME*</small><strong>{safe(evaMinutesRemaining)} min</strong></div>
        <div><small>ROUTE STATUS</small><strong>{route?.metrics.return_feasible ? 'RETURN FEASIBLE' : route ? 'CHECK RESERVE' : 'NOT PLANNED'}</strong></div>
      </div>}
    </div>
    <div className="hud-disclaimer">* Resource values are planner estimates / simulations, not live suit telemetry. This browser HUD is a research visualization and is not connected to astronaut hardware or certified navigation sensors.</div>
  </div>;
}


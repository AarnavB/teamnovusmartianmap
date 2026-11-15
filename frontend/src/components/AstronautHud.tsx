import type { Point, Route, Target, TerrainData } from '../types';

type Mode = 'desktop' | 'helmet' | 'minimal';
type Props = {
  mode: Mode; onModeChange: (mode: Mode) => void; onClose: () => void;
  onStart: () => void; onPause: () => void; onResume: () => void; onAdvance: () => void; onReset: () => void;
  isRunning: boolean; canRun: boolean; canAdvance: boolean; tourActive: boolean;
  siteName: string; terrain: TerrainData | null; route: Route | null; start: Point; goal: Point;
  currentPosition: Point; progressIndex: number; targets: Target[]; selectedTargetIds: string[];
  maxSlope: number; oxygenRemainingL: number; energyRemainingWh: number; evaMinutesRemaining: number;
  warnings: string[];
};

function distance(a: Point, b: Point, cellSize: number) { return Math.hypot(a.x - b.x, a.y - b.y) * cellSize; }
function pathDistance(path: Point[], cellSize: number) {
  return path.slice(1).reduce((sum, point, index) => sum + distance(path[index], point, cellSize), 0);
}
function heading(a: Point, b: Point) {
  const deg = (Math.atan2(b.x - a.x, -(b.y - a.y)) * 180 / Math.PI + 360) % 360;
  const compass = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
  return { deg: Math.round(deg), text: compass[Math.round(deg / 45) % 8] };
}
function safe(value: number | undefined, digits = 0) {
  return typeof value === 'number' && Number.isFinite(value) ? value.toFixed(digits) : 'N/A';
}
function nearestConstraint(terrain: TerrainData, point: Point, maxSlope: number, radius = 12) {
  const minX = Math.max(0, Math.floor(point.x - radius));
  const maxX = Math.min(terrain.width - 1, Math.ceil(point.x + radius));
  const minY = Math.max(0, Math.floor(point.y - radius));
  const maxY = Math.min(terrain.height - 1, Math.ceil(point.y + radius));
  let nearest: { distanceM: number; label: string; point: Point } | null = null;
  for (let y = minY; y <= maxY; y += 1) {
    for (let x = minX; x <= maxX; x += 1) {
      const isNoData = terrain.valid_mask?.[y]?.[x] === false;
      const slope = terrain.slope_deg?.[y]?.[x];
      const overSlope = (terrain.available_layers ?? []).includes('slope') && typeof slope === 'number' && slope > maxSlope;
      const blocked = terrain.obstacle?.[y]?.[x] === true;
      if (!isNoData && !overSlope && !blocked) continue;
      const distanceM = distance(point, { x, y }, terrain.cell_size_m);
      if (!nearest || distanceM < nearest.distanceM) {
        nearest = { distanceM, point: { x, y }, label: isNoData ? 'NO DATA COVERAGE' : overSlope ? 'ABOVE CONFIGURED SLOPE LIMIT' : 'PLANNER-BLOCKED CELL' };
      }
    }
  }
  return nearest;
}

export default function AstronautHud({
  mode, onModeChange, onClose, onStart, onPause, onResume, onAdvance, onReset,
  isRunning, canRun, canAdvance, tourActive, siteName, terrain, route, start, goal,
  currentPosition, progressIndex, targets, selectedTargetIds, maxSlope,
  oxygenRemainingL, energyRemainingWh, evaMinutesRemaining, warnings,
}: Props) {
  const path = route?.path ?? [];
  const safeIndex = path.length ? Math.min(Math.max(0, progressIndex), path.length - 1) : 0;
  const next = path[safeIndex + 1] ?? goal;
  const bearing = heading(currentPosition, next);
  const cell = terrain?.cell_size_m ?? 1;
  const currentX = Math.round(currentPosition.x);
  const currentY = Math.round(currentPosition.y);
  const inBounds = Boolean(terrain && currentX >= 0 && currentY >= 0 && currentX < terrain.width && currentY < terrain.height);
  const currentSlope = inBounds ? terrain?.slope_deg?.[currentY]?.[currentX] : undefined;
  const currentElevation = inBounds ? terrain?.elevation_m?.[currentY]?.[currentX] : undefined;
  const currentNoData = inBounds && terrain?.valid_mask?.[currentY]?.[currentX] === false;
  const uncertaintyAvailable = (terrain?.available_layers ?? []).includes('uncertainty') && Boolean(terrain?.uncertainty);
  const currentUncertainty = inBounds && uncertaintyAvailable ? terrain?.uncertainty?.[currentY]?.[currentX] : undefined;
  const localConstraint = terrain ? nearestConstraint(terrain, currentPosition, maxSlope) : null;
  const selectedTargets = targets.filter((target) => selectedTargetIds.includes(target.id));
  const targetPool = selectedTargets.length ? selectedTargets : targets;
  const nearestScience = [...targetPool].sort((a, b) => distance(currentPosition, a, cell) - distance(currentPosition, b, cell))[0];
  const targetDistance = nearestScience ? distance(currentPosition, nearestScience, cell) : null;
  const routePoints = path.map((point) => `${point.x},${terrain?.height ? terrain.height - point.y : point.y}`).join(' ');
  const progressPercent = path.length > 1 ? Math.round((safeIndex / (path.length - 1)) * 100) : 0;
  const remainingDistance = path.length > 1 ? pathDistance(path.slice(safeIndex), cell) : null;
  const currentDataLabel = currentNoData ? 'NODATA CELL' : uncertaintyAvailable
    ? currentUncertainty === undefined ? 'UNCERTAINTY VALUE N/A' : `UNCERTAINTY INDEX ${currentUncertainty.toFixed(3)}`
    : inBounds ? 'UNCERTAINTY NOT MAPPED' : 'POSITION OUTSIDE GRID';
  const hasRoute = path.length > 1;

  return (
    <div className={`astronaut-hud-shell hud-${mode}`} data-tour-active={tourActive || undefined}>
      <div className="hud-topbar">
        <div className="hud-brand"><span className="hud-brand-mark">M</span><div><b>MARSCOPE / EVA VISOR</b><small>{siteName.toUpperCase()} · ROUTE-CELL SIMULATION</small></div></div>
        <div className="hud-mode-switch" role="group" aria-label="HUD display mode">
          {(['desktop', 'helmet', 'minimal'] as Mode[]).map((value) => <button type="button" key={value} className={mode === value ? 'active' : ''} aria-pressed={mode === value} onClick={() => onModeChange(value)}>{value.toUpperCase()}</button>)}
        </div>
        <button className="hud-exit" type="button" onClick={onClose}>EXIT HUD <span aria-hidden="true">×</span></button>
      </div>

      <div className="hud-viewfinder">
        <div className="hud-console-grid">
          <section className="hud-side-column">
            <div className="hud-section-label">NAVIGATION FIX <span>GRID / IMPORTED DEM</span></div>
            <div className="hud-readout"><small>CURRENT POSITION</small><strong>{currentPosition.x.toFixed(1)} / {currentPosition.y.toFixed(1)}</strong><span>Grid coordinate · not a geographic fix</span></div>
            <div className="hud-readout"><small>DESTINATION</small><strong>{goal.x} / {goal.y}</strong><span>{distance(currentPosition, goal, cell).toFixed(0)} m straight-line grid distance</span></div>
            <div className="hud-readout"><small>NEXT ROUTE CELL</small><strong>{path.length ? `WP-${String(Math.min(path.length, safeIndex + 2)).padStart(2, '0')}` : 'NO ACTIVE ROUTE'}</strong><span>{hasRoute ? `${next.x} / ${next.y} · ${distance(currentPosition, next, cell).toFixed(0)} m` : 'Generate a route to populate this field'}</span></div>
            <div className="hud-readout"><small>LOCAL TERRAIN</small><strong>{currentSlope === undefined ? 'SLOPE N/A' : `${currentSlope.toFixed(1)}° SLOPE`}</strong><span>{currentElevation === undefined ? 'Elevation unavailable' : `${currentElevation.toFixed(1)} m elevation · imported layer`}</span></div>
          </section>

          <section className="hud-primary-column">
            <div className="hud-heading"><small>GRID BEARING / DERIVED</small><strong>{hasRoute ? `${bearing.text} ${bearing.deg.toString().padStart(3, '0')}°` : '— — —'}</strong><div className="hud-compass-ticks"><span>N</span><i /><span>NE</span><i /><span>E</span><i /><span>SE</span></div></div>
            <div className="hud-reticle"><i /><b /><span /></div>
            <div className="hud-route-map">
              <div><small>TRAVERSE CORRIDOR</small><b>{route?.name ?? 'NO ROUTE'}</b></div>
              {terrain && path.length > 1 ? (
                <svg viewBox={`0 0 ${terrain.width} ${terrain.height}`} preserveAspectRatio="none" role="img" aria-label="Selected route in terrain grid coordinates">
                  <polyline points={routePoints} />
                  <circle cx={currentPosition.x} cy={terrain.height - currentPosition.y} r="1.8" />
                  <circle className="hud-goal" cx={goal.x} cy={terrain.height - goal.y} r="1.3" />
                </svg>
              ) : <div className="hud-route-empty">ROUTE VISUALISATION UNAVAILABLE</div>}
              <div className="hud-route-metrics"><span>{path.length ? `${path.length} path cells` : 'No path cells'}</span><b>{remainingDistance === null ? 'N/A' : `${remainingDistance.toFixed(0)} m remaining`}</b></div>
            </div>
            <div className="hud-progress">
              <div><span>ROUTE PROGRESS</span><b>{path.length ? `${progressPercent}%` : 'N/A'}</b></div>
              <div className="hud-progress-track"><i style={{ width: `${progressPercent}%` }} /></div>
            </div>
            <div className="hud-grid-coordinates"><span>ORIGIN <b>{start.x} / {start.y}</b></span><span>DESTINATION <b>{goal.x} / {goal.y}</b></span></div>
          </section>

          <section className="hud-side-column hud-right-column">
            <div className="hud-section-label">SURFACE & SCIENCE <span>MAP-CONTEXT ONLY</span></div>
            <div className="hud-readout hud-warning"><small>NEAREST MAPPED CONSTRAINT · 12-CELL SEARCH</small><strong>{localConstraint?.label ?? 'NO FLAGGED CELL FOUND'}</strong><span>{localConstraint ? `${localConstraint.distanceM.toFixed(0)} m · grid ${localConstraint.point.x} / ${localConstraint.point.y}` : 'No flagged cell in this search window; this does not establish hazard-free terrain.'}</span></div>
            <div className="hud-readout"><small>SCIENCE OBJECTIVE</small><strong>{nearestScience?.name ?? 'NO TARGET SELECTED'}</strong><span>{targetDistance === null ? 'No geolocated science target is available' : `${targetDistance.toFixed(0)} m · target coordinate from loaded dataset`}</span></div>
            <div className="hud-readout"><small>DATA QUALITY AT POSITION</small><strong>{currentDataLabel}</strong><span>{uncertaintyAvailable ? 'Imported uncertainty layer index; not a safety probability.' : 'No spatial uncertainty layer is available for this mission dataset.'}</span></div>
            <div className="hud-readout hud-warning"><small>CONTEXTUAL WARNINGS</small><strong>{warnings.length ? `${warnings.length} MAPPED / MODEL WARNINGS` : 'NO CURRENT WARNINGS'}</strong><span>{warnings[0] ?? 'No warning is generated from the currently loaded route layers.'}</span></div>
          </section>
        </div>

        {mode !== 'minimal' && <div className="hud-resource-strip">
          <div><small>ENERGY RESERVE*</small><strong>{safe(energyRemainingWh)} Wh</strong><span>planner estimate</span></div>
          <div><small>O₂ RESERVE*</small><strong>{safe(oxygenRemainingL)} L</strong><span>planner estimate</span></div>
          <div><small>EVA TIME*</small><strong>{safe(evaMinutesRemaining)} min</strong><span>modelled clock</span></div>
          <div><small>ROUTE STATUS</small><strong>{route ? route.metrics.return_feasible ? 'MODEL WITHIN LIMITS' : 'REVIEW MODEL LIMITS' : 'NOT PLANNED'}</strong><span>not a safety certification</span></div>
        </div>}
      </div>

      <div className="hud-control-dock" role="group" aria-label="EVA simulation controls">
        <div className="hud-control-status"><i className={isRunning ? 'running' : 'paused'} /><span>{isRunning ? 'SIMULATION RUNNING' : progressIndex > 0 ? 'SIMULATION PAUSED' : 'SIMULATION READY'}</span></div>
        {!isRunning
          ? progressIndex === 0
            ? <button className="hud-control-primary" type="button" onClick={onStart} disabled={!canRun}>START SIMULATION <span>▶</span></button>
            : <button className="hud-control-primary" type="button" onClick={onResume} disabled={!canRun || !canAdvance}>RESUME SIMULATION <span>▶</span></button>
          : <button className="hud-control-primary" type="button" onClick={onPause}>PAUSE SIMULATION <span>Ⅱ</span></button>}
        <button type="button" onClick={onAdvance} disabled={!canAdvance}>ADVANCE ONE CELL <span>→</span></button>
        <button type="button" onClick={onReset} disabled={!hasRoute || (progressIndex === 0 && !isRunning)}>RESET TO ORIGIN <span>↺</span></button>
      </div>
      <div className="hud-disclaimer">* Oxygen, energy and time values are planner estimates / simulated values, not live suit telemetry. Position and bearing are derived from route-grid cells, not geographic localization. Constraint markers reflect only the loaded grid and configured slope threshold. This research visualization is not connected to astronaut hardware or certified navigation sensors.</div>
    </div>
  );
}

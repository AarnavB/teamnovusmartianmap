import { useState } from 'react';
import { api } from '../api';
import type { MissionConstraintsPayload, Point, SensitivityResponse, SensitivitySweepItem } from '../types';

interface Props {
  siteId: string;
  start: Point;
  goal: Point;
  currentMaxSlope: number;
  constraints: MissionConstraintsPayload;
  onPreviewPath?: (path: Point[], label: string) => void;
  onClose: () => void;
}

const DEFAULT_SLOPES = [14, 18, 22, 26, 30];

export default function SensitivityAnalysis({
  siteId,
  start,
  goal,
  currentMaxSlope,
  constraints,
  onPreviewPath,
  onClose,
}: Props) {
  const [slopes, setSlopes] = useState<number[]>(DEFAULT_SLOPES);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [data, setData] = useState<SensitivityResponse | null>(null);
  const [selectedSweepVal, setSelectedSweepVal] = useState<number | null>(null);

  const runSweep = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.sensitivity(siteId, start, goal, constraints, slopes);
      setData(res);
      // Automatically preview first feasible path
      const firstFeasible = res.sweep.find((s) => s.feasible);
      if (firstFeasible && onPreviewPath) {
        setSelectedSweepVal(firstFeasible.value);
        onPreviewPath(firstFeasible.path, `${firstFeasible.value}° slope limit`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sensitivity analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRowClick = (item: SensitivitySweepItem) => {
    if (!item.feasible || !item.path.length) return;
    setSelectedSweepVal(item.value);
    onPreviewPath?.(item.path, `Sensitivity route (${item.value}° limit)`);
  };

  return (
    <div className="sensitivity-modal">
      <div className="sensitivity-head">
        <div>
          <span className="eyebrow">MISSION SENSITIVITY SWEEP</span>
          <h3>Maximum Incline Sensitivity ({slopes.length} settings)</h3>
        </div>
        <button className="tiny-action" onClick={onClose}>✕ CLOSE</button>
      </div>

      <p className="sensitivity-intro">
        Evaluates how adjusting the maximum traversable slope angle alters path existence, detour distance,
        and mission resource consumption over the catalogued DEM.
      </p>

      <div className="sensitivity-controls">
        <div className="slope-pills">
          <label>SWEEP ANGLES:</label>
          {slopes.map((s) => (
            <span key={s} className={`slope-pill ${s === currentMaxSlope ? 'current' : ''}`}>
              {s}° {s === currentMaxSlope ? '(ACTIVE)' : ''}
            </span>
          ))}
        </div>
        <button className="primary-button sensitivity-run-btn" onClick={() => void runSweep()} disabled={loading}>
          {loading ? <><span className="spinner" /> COMPUTING SWEEP…</> : 'RUN SENSITIVITY ANALYSIS'}
        </button>
      </div>

      {error && <div className="error-banner"><span>!</span>{error}</div>}

      {data && (
        <div className="sensitivity-results">
          <table className="sensitivity-table">
            <thead>
              <tr>
                <th>SLOPE LIMIT</th>
                <th>FEASIBILITY</th>
                <th>DISTANCE</th>
                <th>TIME</th>
                <th>ENERGY</th>
                <th>TERRAIN RISK</th>
                <th>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {data.sweep.map((item) => {
                const isSelected = selectedSweepVal === item.value;
                const isCurrent = item.value === currentMaxSlope;
                return (
                  <tr
                    key={item.value}
                    className={`${isSelected ? 'selected-row' : ''} ${!item.feasible ? 'infeasible-row' : ''}`}
                    onClick={() => handleRowClick(item)}
                  >
                    <td>
                      <strong>{item.value}°</strong>
                      {isCurrent && <span className="current-indicator">ACTIVE</span>}
                    </td>
                    <td>
                      {item.feasible ? (
                        <span className="badge-pass">FEASIBLE</span>
                      ) : (
                        <span className="badge-fail">INFEASIBLE</span>
                      )}
                    </td>
                    <td>{item.distance_m ? `${item.distance_m.toFixed(0)} m` : '—'}</td>
                    <td>{item.duration_min ? `${item.duration_min.toFixed(1)} min` : '—'}</td>
                    <td>{item.energy_wh ? `${item.energy_wh.toFixed(1)} Wh` : '—'}</td>
                    <td>{item.terrain_risk_pct !== null ? `${item.terrain_risk_pct.toFixed(0)}%` : '—'}</td>
                    <td>
                      {item.feasible ? (
                        <button
                          className={`tiny-action ${isSelected ? 'active' : ''}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRowClick(item);
                          }}
                        >
                          {isSelected ? 'VIEWING' : 'OVERLAY'}
                        </button>
                      ) : (
                        <small className="infeasible-note" title={item.error}>
                          Slope barrier
                        </small>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          <div className="sensitivity-summary">
            <strong>Key Finding:</strong>{' '}
            {data.sweep.every((s) => s.feasible)
              ? `All tested slope thresholds [${slopes.join('°, ')}°] yield feasible routes. Lower slope limits force longer contour paths around craters.`
              : data.sweep.some((s) => !s.feasible)
              ? `Stricter slope limits (<${data.sweep.find((s) => s.feasible)?.value ?? 22}°) break connectivity due to continuous steep terrain bands. Increasing allowance restores connectivity.`
              : 'Sensitivity calculation completed.'}
          </div>
        </div>
      )}

      <div className="sensitivity-foot">
        <small>
          Notice: Hard physical constraints and return reserves are strictly maintained across every sweep.
          Higher slope limits increase terrain risk scores.
        </small>
      </div>
    </div>
  );
}

import { useMemo, useState } from 'react';
import type { Route, TerrainData } from '../types';

interface Props {
  terrain: TerrainData;
  route: Route | null;
  maxSlopeDeg: number;
}

interface ProfilePoint {
  index: number;
  x: number;
  y: number;
  distM: number;
  elevationM: number;
  slopeDeg: number;
  exceedsSlope: boolean;
}

export default function RouteProfileChart({ terrain, route, maxSlopeDeg }: Props) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const profile = useMemo(() => {
    if (!route || !route.path || route.path.length < 2) return null;
    const points: ProfilePoint[] = [];
    let cumDist = 0;
    let minElev = Infinity;
    let maxElev = -Infinity;
    let minSlope = Infinity;
    let maxSlope = -Infinity;
    let maxSlopeIdx = 0;
    let totalAscent = 0;
    let totalDescent = 0;
    let overSlopeDist = 0;

    const cellSize = terrain.cell_size_m || 25.0;

    for (let i = 0; i < route.path.length; i++) {
      const p = route.path[i];
      if (i > 0) {
        const prev = route.path[i - 1];
        const step = Math.hypot(p.x - prev.x, p.y - prev.y) * cellSize;
        cumDist += step;
      }
      const elev = terrain.elevation_m[p.y]?.[p.x] ?? 0;
      const slope = terrain.slope_deg[p.y]?.[p.x] ?? 0;

      if (i > 0) {
        const prevElev = points[i - 1].elevationM;
        const diff = elev - prevElev;
        if (diff > 0) totalAscent += diff;
        else totalDescent += Math.abs(diff);

        if (slope > maxSlopeDeg) {
          const prev = route.path[i - 1];
          overSlopeDist += Math.hypot(p.x - prev.x, p.y - prev.y) * cellSize;
        }
      }

      if (elev < minElev) minElev = elev;
      if (elev > maxElev) maxElev = elev;
      if (slope < minSlope) minSlope = slope;
      if (slope > maxSlope) {
        maxSlope = slope;
        maxSlopeIdx = i;
      }

      points.push({
        index: i,
        x: p.x,
        y: p.y,
        distM: cumDist,
        elevationM: elev,
        slopeDeg: slope,
        exceedsSlope: slope > maxSlopeDeg,
      });
    }

    return {
      points,
      totalDist: cumDist,
      minElev,
      maxElev: Math.max(maxElev, minElev + 1),
      minSlope,
      maxSlope,
      maxSlopeIdx,
      totalAscent,
      totalDescent,
      overSlopeDist,
      overSlopePct: cumDist > 0 ? (overSlopeDist / cumDist) * 100 : 0,
    };
  }, [route, terrain, maxSlopeDeg]);

  if (!profile || profile.points.length < 2) {
    return (
      <div className="profile-chart-empty">
        <small>Select or generate a route to view its elevation and slope profile.</small>
      </div>
    );
  }

  const { points, totalDist, minElev, maxElev, maxSlopeIdx, totalAscent, totalDescent, overSlopePct } = profile;

  // Chart dimensions
  const width = 560;
  const height = 170;
  const padLeft = 46;
  const padRight = 44;
  const padTop = 22;
  const padBottom = 26;
  const plotW = width - padLeft - padRight;
  const plotH = height - padTop - padBottom;

  const elevRange = Math.max(1, maxElev - minElev);
  const elevMargin = elevRange * 0.1;
  const plotMinElev = minElev - elevMargin;
  const plotMaxElev = maxElev + elevMargin;
  const plotElevRange = plotMaxElev - plotMinElev;

  const maxPlotSlope = Math.max(35, maxSlopeDeg + 5);

  const getX = (dist: number) => padLeft + (dist / Math.max(1, totalDist)) * plotW;
  const getYElev = (elev: number) => padTop + plotH - ((elev - plotMinElev) / plotElevRange) * plotH;
  const getYSlope = (slope: number) => padTop + plotH - (Math.min(slope, maxPlotSlope) / maxPlotSlope) * plotH;

  // Build SVG paths
  const elevPath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(p.distM).toFixed(1)} ${getYElev(p.elevationM).toFixed(1)}`).join(' ');
  const elevArea = `${elevPath} L ${getX(totalDist).toFixed(1)} ${(padTop + plotH).toFixed(1)} L ${padLeft.toFixed(1)} ${(padTop + plotH).toFixed(1)} Z`;
  const slopePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(p.distM).toFixed(1)} ${getYSlope(p.slopeDeg).toFixed(1)}`).join(' ');

  const slopeLimitY = getYSlope(maxSlopeDeg);
  const peakPoint = points[maxSlopeIdx];

  const activeHover = hoverIndex !== null ? points[hoverIndex] : null;

  return (
    <div className="profile-chart-card">
      <div className="profile-chart-head">
        <div>
          <span className="eyebrow">TERRAIN ALONG ROUTE</span>
          <h4>Elevation & Slope Profile</h4>
        </div>
        <div className="profile-chart-legend">
          <span className="legend-item"><span className="legend-line elev-line" /> Elevation (m)</span>
          <span className="legend-item"><span className="legend-line slope-line" /> Slope (deg)</span>
          <span className="legend-item"><span className="legend-line limit-line" /> Limit ({maxSlopeDeg}°)</span>
        </div>
      </div>

      <div className="profile-stats-row">
        <div className="profile-stat"><span>DISTANCE</span><strong>{totalDist.toFixed(0)} m</strong></div>
        <div className="profile-stat"><span>ELEVATION RANGE</span><strong>{minElev.toFixed(0)} m → {maxElev.toFixed(0)} m</strong><small>Δ {elevRange.toFixed(0)} m</small></div>
        <div className="profile-stat"><span>ASCENT / DESCENT</span><strong>+{totalAscent.toFixed(0)} m / -{totalDescent.toFixed(0)} m</strong></div>
        <div className="profile-stat">
          <span>PEAK SLOPE</span>
          <strong className={peakPoint.slopeDeg > maxSlopeDeg ? 'bad' : 'good'}>{peakPoint.slopeDeg.toFixed(1)}°</strong>
          <small>{overSlopePct > 0 ? `${overSlopePct.toFixed(1)}% exceeds limit` : 'All segments within limit'}</small>
        </div>
      </div>

      <div className="profile-svg-container">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="profile-svg"
          onMouseLeave={() => setHoverIndex(null)}
          onMouseMove={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const relX = ((e.clientX - rect.left) / rect.width) * width;
            if (relX >= padLeft && relX <= padLeft + plotW) {
              const targetDist = ((relX - padLeft) / plotW) * totalDist;
              // find nearest point
              let bestIdx = 0;
              let bestDiff = Infinity;
              for (let i = 0; i < points.length; i++) {
                const diff = Math.abs(points[i].distM - targetDist);
                if (diff < bestDiff) {
                  bestDiff = diff;
                  bestIdx = i;
                }
              }
              setHoverIndex(bestIdx);
            }
          }}
        >
          <defs>
            <linearGradient id="elevAreaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#467e71" stopOpacity="0.45" />
              <stop offset="100%" stopColor="#1e3430" stopOpacity="0.05" />
            </linearGradient>
            <linearGradient id="hazardAreaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#d85e45" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#d85e45" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          <line x1={padLeft} y1={padTop} x2={padLeft + plotW} y2={padTop} stroke="#2c3a3c" strokeDasharray="2 3" />
          <line x1={padLeft} y1={padTop + plotH * 0.5} x2={padLeft + plotW} y2={padTop + plotH * 0.5} stroke="#2c3a3c" strokeDasharray="2 3" />
          <line x1={padLeft} y1={padTop + plotH} x2={padLeft + plotW} y2={padTop + plotH} stroke="#3b4d4f" />

          {/* Elevation Area & Line */}
          <path d={elevArea} fill="url(#elevAreaGrad)" />
          <path d={elevPath} fill="none" stroke="#70e0c0" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />

          {/* Slope Line */}
          <path d={slopePath} fill="none" stroke="#e2a45b" strokeWidth="1.6" strokeDasharray="4 2" strokeLinejoin="round" />

          {/* Slope Limit Line */}
          <line
            x1={padLeft}
            y1={slopeLimitY}
            x2={padLeft + plotW}
            y2={slopeLimitY}
            stroke="#d85e45"
            strokeWidth="1.4"
            strokeDasharray="5 3"
          />

          {/* Highlight segments that exceed max slope */}
          {points.map((p, i) => {
            if (p.exceedsSlope && i > 0) {
              const prev = points[i - 1];
              return (
                <line
                  key={`seg-${i}`}
                  x1={getX(prev.distM)}
                  y1={getYElev(prev.elevationM)}
                  x2={getX(p.distM)}
                  y2={getYElev(p.elevationM)}
                  stroke="#e85b46"
                  strokeWidth="3.8"
                  strokeLinecap="round"
                />
              );
            }
            return null;
          })}

          {/* Start and Goal markers */}
          <circle cx={getX(0)} cy={getYElev(points[0].elevationM)} r="4" fill="#f4eee3" stroke="#14191b" strokeWidth="1.5" />
          <circle cx={getX(totalDist)} cy={getYElev(points[points.length - 1].elevationM)} r="4.5" fill="#f2a45b" stroke="#14191b" strokeWidth="1.5" />

          {/* Peak slope marker */}
          {peakPoint && (
            <g transform={`translate(${getX(peakPoint.distM)}, ${getYSlope(peakPoint.slopeDeg)})`}>
              <polygon points="0,-5 4,0 0,5 -4,0" fill="#d85e45" />
              <text x="6" y="3" fill="#e88978" fontSize="8" fontFamily="'DM Mono', monospace">
                {peakPoint.slopeDeg.toFixed(1)}°
              </text>
            </g>
          )}

          {/* Axis labels */}
          {/* Elevation ticks (left) */}
          <text x={padLeft - 6} y={padTop + 4} fill="#82a599" fontSize="8" textAnchor="end" fontFamily="'DM Mono', monospace">
            {plotMaxElev.toFixed(0)}m
          </text>
          <text x={padLeft - 6} y={padTop + plotH * 0.5 + 3} fill="#82a599" fontSize="8" textAnchor="end" fontFamily="'DM Mono', monospace">
            {((plotMinElev + plotMaxElev) / 2).toFixed(0)}m
          </text>
          <text x={padLeft - 6} y={padTop + plotH} fill="#82a599" fontSize="8" textAnchor="end" fontFamily="'DM Mono', monospace">
            {plotMinElev.toFixed(0)}m
          </text>

          {/* Slope ticks (right) */}
          <text x={padLeft + plotW + 6} y={padTop + 4} fill="#cda26f" fontSize="8" textAnchor="start" fontFamily="'DM Mono', monospace">
            {maxPlotSlope}°
          </text>
          <text x={padLeft + plotW + 6} y={slopeLimitY + 3} fill="#d85e45" fontSize="8" textAnchor="start" fontFamily="'DM Mono', monospace">
            {maxSlopeDeg}° LIM
          </text>
          <text x={padLeft + plotW + 6} y={padTop + plotH} fill="#cda26f" fontSize="8" textAnchor="start" fontFamily="'DM Mono', monospace">
            0°
          </text>

          {/* X Axis distance ticks */}
          <text x={padLeft} y={height - 8} fill="#728484" fontSize="8" textAnchor="middle" fontFamily="'DM Mono', monospace">
            0m
          </text>
          <text x={padLeft + plotW * 0.5} y={height - 8} fill="#728484" fontSize="8" textAnchor="middle" fontFamily="'DM Mono', monospace">
            {(totalDist * 0.5).toFixed(0)}m
          </text>
          <text x={padLeft + plotW} y={height - 8} fill="#728484" fontSize="8" textAnchor="middle" fontFamily="'DM Mono', monospace">
            {totalDist.toFixed(0)}m
          </text>

          {/* Interactive hover cursor */}
          {activeHover && (
            <g>
              <line
                x1={getX(activeHover.distM)}
                y1={padTop}
                x2={getX(activeHover.distM)}
                y2={padTop + plotH}
                stroke="#fff"
                strokeWidth="1"
                strokeDasharray="2 2"
                opacity="0.75"
              />
              <circle
                cx={getX(activeHover.distM)}
                cy={getYElev(activeHover.elevationM)}
                r="3.5"
                fill="#70e0c0"
                stroke="#14191b"
                strokeWidth="1"
              />
              <circle
                cx={getX(activeHover.distM)}
                cy={getYSlope(activeHover.slopeDeg)}
                r="3.5"
                fill="#e2a45b"
                stroke="#14191b"
                strokeWidth="1"
              />
            </g>
          )}
        </svg>

        {activeHover && (
          <div
            className="profile-tooltip"
            style={{
              left: `${Math.min(75, Math.max(15, (getX(activeHover.distM) / width) * 100))}%`,
            }}
          >
            <span>DIST: <b>{activeHover.distM.toFixed(0)} m</b></span>
            <span>ELEV: <b>{activeHover.elevationM.toFixed(1)} m</b></span>
            <span>SLOPE: <b className={activeHover.slopeDeg > maxSlopeDeg ? 'bad' : ''}>{activeHover.slopeDeg.toFixed(1)}°</b></span>
            <small>Grid cell ({activeHover.x}, {activeHover.y})</small>
          </div>
        )}
      </div>
      <div className="profile-chart-foot">
        <small>Elevation values are sampled from the catalogued DEM. Slopes are calculated using adjacent cell central differences.</small>
      </div>
    </div>
  );
}

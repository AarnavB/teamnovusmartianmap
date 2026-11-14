# Validation and test record

## Automated test suite

Run from the backend working directory:

```bash
cd backend
python -m pytest -q
```

Release 0.3.1 contains automated tests for:

- deterministic synthetic terrain and hard-blocked path avoidance;
- three route policy generation and mission resource rejection;
- objective multiplier validation and normalization;
- `N/A` metrics and disabled objective weights when science/environment/radiation layers are unavailable;
- LPA* obstacle repair;
- standard A*, Dijkstra and distance-only baselines;
- FastAPI health, official catalog, evidence and offline-cache status endpoints;
- validation errors returned as HTTP 422 rather than server errors;
- PDS Search API query construction and raw-response retention;
- Mars ODE instrument and bounding-box query parameters;
- WMTS GetCapabilities parsing, tile-matrix planning and offline cache-manifest inspection;
- conflicting temperature-band unit metadata rejection;
- PDS3 and PDS4 label inspection with byte/text preservation;
- REMS/RAD field mapping and archive-station data semantics;
- deterministic science retrieval / abstention;
- optional Responses API RAG request formation, `store:false` and extractive fallback;
- official archive download allow-list, redirect handling, byte preservation and SHA-256;
- Mars DEM and aligned-layer geospatial ingestion, including rejection of Earth/unknown-body CRS.

The final local backend test run for this source tree: **32 passed**. Run the command again after installing dependencies in the target environment; this is not a NASA or operational certification test.

## Baseline comparison

`POST /api/benchmark` runs three methods on the same active grid and configured hard constraints:

- Standard scalar A*: balanced route cost plus Euclidean distance heuristic.
- Dijkstra: same edge scalarization, zero heuristic.
- Distance-only: minimizes distance while respecting configured blocked cells and resource feasibility.

For positive edge costs, A* and Dijkstra should agree on their scalar objective cost. Any claim of efficiency must include machine, Python/package versions, grid dimensions, route endpoints, available layers, policy weights, label cap, runtime repetitions and path metrics. The synthetic benchmark is not evidence of performance on NASA products or Mars field conditions.

## Frontend verification

The frontend dependency install was attempted in the build environment but did not complete within the environment time limit; an offline install was also unavailable because the npm cache lacked required React type packages. Therefore a full Vite production build/browser verification is **not claimed** for this release. A TypeScript/TSX syntax-transpilation pass completed for all frontend source files in release 0.3.1, but that is not a substitute for static type checking or a browser test. Run `npm install && npm run build` in a network-enabled Node.js 20+ environment. The source is included in full.

## Required before serious scientific or operational claims

### Algorithm

- Compare A* costs with Dijkstra on random positive-cost grids.
- Test heuristic admissibility/consistency for all movement and weight configurations.
- Compare bounded Pareto output with exact tiny-grid frontier enumeration; quantify label-cap losses.
- Test disconnected grids, identical start/goal, all-no-go maps, blocked endpoints, corner cases, invalid numeric values and resource reserves.
- Compare every LPA* repair with fresh Dijkstra after random obstacle additions/removals and field updates.
- Include memory/time scaling for larger rasters and profile weights.

### Geospatial/science

- Verify source product ID, checksum, PDS label, SIS, instrument, target body and observation time.
- Confirm map footprint intersection with actual product corners/tie points.
- Validate coordinate conversion between source planetographic/planetocentric and east-/west-positive conventions.
- Validate CRS operations and round-trip tie points against authoritative metadata.
- Confirm elevation vertical datum, units, scale, NoData, pixel transform and effective native resolution.
- Compare slope and roughness calculations to a trusted geospatial implementation and propagate DEM uncertainty.
- Verify each auxiliary raster's physical meaning, calibration, native units and coverage before user normalization.
- Georegister rover images/records using source metadata and SPICE/localization; never infer rover position from a panorama title.
- Use actual temperature, wind, dust, pressure and radiation products with temporal semantics before incorporating them as operational fields.

### Human factors / EVA

- Replace illustrative speed, mass, energy, oxygen and rest equations with validated subsystem and mobility models.
- Have human-factors, suit systems, mission planning and planetary science experts define constraints and review the model.
- Perform uncertainty analysis, robust feasibility checks, communication loss and return-to-base contingencies.
- Conduct independent verification and validation. This prototype must not be used to navigate people.

## Reporting discipline

Never claim the route is safe, faster or more scientifically productive unless the claim is supported by a reproducible comparison on verified source data and reviewed assumptions. The fixture tests only software behavior against controlled synthetic inputs.

# Testing and validation plan

## Automated tests currently included

- Deterministic synthetic fixture generation and explicit synthetic status.
- Route start/goal integrity and hard-blocked-cell avoidance.
- Three objective profiles and metric range checks.
- Infeasible resource budgets rejected.
- LPA* route repair after injecting an obstacle on the prior path.

Run with:

```bash
cd backend
python -m pytest -q
```

## Baseline comparison endpoint

`POST /api/benchmark` executes three baselines over the same synthetic tile and the same hard constraints / return-reserve rules:

- **Standard scalar A***: balanced weighted edge cost and a distance heuristic.
- **Dijkstra**: same balanced scalar edge cost, zero heuristic.
- **Distance-only**: minimizes distance and treats terrain/science as non-objective costs, while still respecting the configured hard constraints and resource reserve.

The endpoint reports route length, modeled duration/energy, terrain risk, scientific value, runtime, expanded nodes and scalar objective. The UI can display the results. Runtime values depend on the current machine and synthetic seed; they are not prefilled or advertised as performance claims.

## Additional required tests before a serious demonstration

### Algorithm correctness

- Compare A* cost against Dijkstra cost on randomized small maps with positive edge costs.
- Prove / test heuristic admissibility and consistency for all allowed moves and profile weights.
- Exhaustively enumerate all simple routes on tiny grids and compare their exact Pareto frontier against the bounded-label search; quantify cap-induced losses.
- Confirm no negative, NaN or infinite edge values enter the queue.
- Test disconnected grids, start=goal, invalid endpoints, diagonal corner cases and all-nogo maps.
- Test LPA* repair against a fresh Dijkstra recomputation after random obstacle additions/removals. Compare path cost, not necessarily exact path geometry.
- Test repeated changes to the same region and changes adjacent to start/goal.

### Data / geospatial correctness

- Check source product identifiers and label checksums.
- Test planetocentric/planetographic conversion and east/west longitude handling.
- Test reprojection round trips on known tie points from the source products.
- Confirm source footprints overlap and pixel-to-ground distances match product labels.
- Test nodata masks, edge effects, vertical datum/body figure and resampling.
- Ensure derived slope units and elevation units are preserved.
- Propagate DEM uncertainty into slope/roughness and planner uncertainty.

### Operational model and UI

- Validate any locomotion model with human factors / spacesuit mobility specialists before claiming EVA time/energy estimates are predictive.
- Require sourced thermal, radiation and atmosphere thresholds before enabling them as real hard constraints.
- Test UI endpoint failures, server restart / plan-session expiry, mobile/responsive layouts and accessibility.
- Verify that the UI always shows layer source, acquisition time, resolution, units, uncertainty and the synthetic/live status.

## Benchmark reporting rules

Record machine CPU, Python version, grid dimensions, cell size, number of traversability masks, number of science targets, profile weights and label cap for each run. Report median and spread over repeated runs. Separate search time from I/O, raster loading and 3D rendering. Compare route metrics and constraint violations, not just elapsed time.

Never claim the MARSCOPE planner is faster, safer or scientifically better without reproducible benchmark results and validated source data. The synthetic fixture demonstrates algorithm behavior only.

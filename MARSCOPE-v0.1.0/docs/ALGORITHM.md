# Path-planning model

## 1. State space and movement graph

The demo uses a regular 8-connected grid. Each traversable cell is a state. Cardinal moves have length `cell_size`; diagonal moves have length `sqrt(2) * cell_size`. Diagonal corner-cutting is prohibited when either adjacent cardinal cell violates a hard constraint. The fixture's `cell_size_m = 8` is a synthetic assumption, not a measured pixel spacing at Mount Sharp.

For a real raster, graph resolution must be no finer than the effective trustworthy resolution of the data being used. Fine-resolution data can be used for local sub-windows; coarse orbital products remain contextual layers.

## 2. Hard constraints versus soft costs

A cell is rejected if any of the following holds:

- it is a known obstacle / no-go cell;
- its slope exceeds the configured maximum;
- its modeled temperature exceeds the configured maximum.

The planner also rejects a partial route if the accumulated outbound time or energy estimate would exceed half of the available budget after retaining the configured reserve. This encodes a conservative out-and-back budget, rather than treating return resources as a soft preference.

The demo does **not** set real-world limits for radiation dose, suit temperature, wind, pressure, dust, oxygen, communications or physiological workload. Its radiation/environment fields are dimensionless synthetic indices. Explicit wind-direction/speed and pressure layers are not implemented in this release. Those factors require mission-authorized values, trustworthy observations and validated subsystem models before they can become operational constraints.

## 3. Positive, normalized edge-cost vector

For edge `e`, let:

- `d_e` = ground distance in metres;
- `t_e` = estimated traversal seconds;
- `E_e` = illustrative energy proxy in Wh;
- `L_max` = maximum analysis-window path scale;
- `T_budget` = configured EVA time budget in seconds;
- `E_budget` = configured illustrative energy budget in Wh;
- `r_t`, `r_env`, `r_rad`, `u` = normalized terrain, environment, radiation-index and uncertainty values in `[0,1]`;
- `s` = science potential near the edge in `[0,1]`.

The edge objective vector is:

\[
q(e)=\left[
\frac{d_e}{L_{max}},
\frac{t_e}{T_{budget}},
\frac{E_e}{E_{budget}},
 r_t\frac{d_e}{L_{max}},
 r_{env}\frac{d_e}{L_{max}},
 r_{rad}\frac{d_e}{L_{max}},
 u\frac{d_e}{L_{max}},
 (1-s)\frac{d_e}{L_{max}}
\right]
\]

All terms are dimensionless and non-negative. A profile `p` has non-negative weights `w_p` whose sum is one. Its scalar priority contribution is:

\[
 c_p(e)=w_p^T q(e)
\]

Scientific value is handled as a **missed-opportunity cost**, `1-s`, rather than a negative reward edge. Passing close to a science target reduces that cost; it does not create a negative edge. This keeps the scalarized graph costs non-negative and preserves the standard A* assumptions.

### Illustrative locomotion / energy assumptions

The demo currently applies:

\[
 v_e = \frac{v_0}{(1+1.8\bar{slope}/slope_{max})(1+0.55\bar{roughness}+0.35\bar{regolith})}
\]

\[
 t_e=d_e/v_e
\]

\[
 E_e=d_e\cdot0.018\frac{Wh}{m}\cdot\frac{m_{suit}}{42kg}\cdot slopeFactor\cdot mobilityFactor
\]

These are engineering placeholders for controlled algorithm experiments, not measured Mars EVA performance. The speed coefficient, multipliers and energy coefficient must be replaced by validated human mobility / suit-system models and uncertainty ranges. Time and energy estimates should never be presented as physiological predictions.

## 4. Multi-objective A*

Every label stores its accumulated objective vector `g_vec(n)`. At each cell, a new label is discarded when an existing label is no worse in every objective and strictly better in at least one. Labels dominated by the new label are removed. This retains meaningful local trade-offs rather than collapsing all objectives to one score immediately.

For each displayed policy, a weighted scalar priority orders the open list. The heuristic is:

\[
 h_p(n)=w_{distance,p}\frac{D_{Euclidean}(n,goal)}{L_{max}}
\]

Other heuristic components are zero. Since every edge's distance contribution is at least the straight-line metric movement and every other objective contribution is non-negative, this is a lower bound on the scalarized remaining cost. It is consistent for the 8-connected metric grid.

The implementation retains at most seven Pareto labels per cell. This cap bounds memory and CPU use but can discard a globally useful nondominated label. Therefore this is a **bounded approximate Pareto A***, not a proof of exhaustive global Pareto optimality. Increase the cap, add epsilon-dominance policies and compare against exact small-grid enumeration before drawing scientific conclusions.

### Route profiles (weights sum to 1)

| Objective | Conservative | Balanced | Science-first |
|---|---:|---:|---:|
| Distance | 0.12 | 0.23 | 0.10 |
| Time | 0.06 | 0.12 | 0.06 |
| Energy | 0.07 | 0.13 | 0.06 |
| Terrain risk | 0.30 | 0.18 | 0.15 |
| Environmental risk | 0.12 | 0.11 | 0.08 |
| Radiation index | 0.08 | 0.08 | 0.08 |
| Uncertainty | 0.20 | 0.10 | 0.10 |
| Science opportunity cost | 0.05 | 0.05 | 0.37 |

These values are starting policy settings for a demonstrator, not calibrated astronaut preferences or safety standards. A real program must estimate them from mission requirements and conduct sensitivity analysis across ranges, not optimize for a single convenient weight vector.

## 5. Pareto comparison

The three returned paths are compared on:

- lower-is-better: distance, duration, energy, terrain risk, environmental index, radiation index and uncertainty;
- higher-is-better: scientific value.

A route is marked non-dominated if none of the other returned routes is at least as good on every displayed dimension and strictly better on one. This comparison applies to the three returned policy solutions, not to the complete feasible route space.

## 6. Adaptive replanning with LPA*

The balanced route has a separate LPA* state. For each node `u`, LPA* retains:

- `g(u)`: current best known path cost from the fixed start;
- `rhs(u)`: one-step lookahead cost, the minimum over predecessor `p` of `g(p) + c(p,u)`.

A node is locally consistent when `g(u) = rhs(u)`. After an obstacle update, the changed cell and its neighbours are updated, then the priority queue repairs inconsistent vertices until the goal is locally consistent. The demo keeps start and goal fixed. Moving-start D* Lite, dynamic environment prediction and multi-agent replanning are not part of this release. LPA* currently repairs the balanced scalar objective; its output is post-checked against the return time/energy budget. If it fails that check, the API must not present it as a feasible route. A fully resource-constrained incremental planner would expand the search state with discretized resource budgets or use a validated resource-constrained label-setting repair method.

## 7. Complexity and memory

Let `V` be grid cells, `E` the 8-connected edges (`E <= 8V`), and `K` the maximum number of retained labels per cell. A bounded-label search has an operational bound near `O(K E log(KV))` queue work, with `O(KV)` active label storage plus stale/dead label records and heap entries. Actual work depends on how much the objectives conflict and how often labels dominate one another. LPA* stores `g`, `rhs` and queue state in `O(V)` memory; a local update initially invalidates only the changed cell's local neighbourhood, although the consistency repair can propagate across much of the graph in the worst case.

## 8. Calibration / sensitivity plan

Before using real data:

1. Keep hard limits separate from weights. Do not allow a large science score to compensate for an unsafe cell.
2. Calibrate slope, roughness and material mobility costs against a human mobility analogue or validated locomotion model, including uncertainty bounds.
3. Model time-varying environmental constraints and use observation ages / forecast validity windows.
4. Express radiation as a traceable dose or dose-rate product with time integration and uncertainty, not a generic scalar index.
5. Normalize each soft objective against mission-defined scales, and publish the scale with every result.
6. Sweep each weight across a range and show which route decisions are stable or sensitive.
7. Test hard-limit threshold perturbations, missing data, conflicting sources and route return reserves.
8. Compare scalar A*, Dijkstra, distance-only and the bounded Pareto planner on reproducible maps; report runtime, expanded nodes, path metrics and constraint violations.

A weight set becomes defensible only after stakeholders document its derivation, validation evidence and acceptable operating envelope.

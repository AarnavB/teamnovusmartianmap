# Path-planning model (release 0.3.1)

## 1. Search state and movement graph

The current planner discretizes the active local raster as an 8-connected grid. A node is a traversable cell. Cardinal moves have metric length `cell_m`; diagonal moves have length `sqrt(2) * cell_m`. Diagonal movement is rejected if either adjacent cardinal cell is blocked (no corner cutting).

The graph resolution must not be finer than the effective resolution of the data that supports the planned decision. Interpolation can put data on a common grid; it cannot create new information. The default 64 × 64 fixture has an 8 m cell spacing as a simulation assumption only, no real Mars coordinates and no measured elevation.

## 2. Hard constraints and resource feasibility

Hard exclusions are evaluated before a move is admitted:

- cell is outside the grid or is a known blocked/NoData cell;
- slope exceeds the configured `max_slope_deg`;
- when a temperature layer is actually available, temperature exceeds the configured `max_temperature_c`;
- diagonal move would cut a corner between blocked cardinal cells.

Cumulative resource feasibility is also a hard search rule. Let `ρ` be `return_reserve_fraction`. Each partial outbound path must satisfy:

\[
\frac{t_{out}}{T_{EVA}} \leq \frac{1-\rho}{2},\quad
\frac{E_{out}}{E_{budget}} \leq \frac{1-\rho}{2},\quad
\frac{O_{out}}{O_{budget}} \leq \frac{1-\rho}{2}
\]

This reserves resources for a nominal return and a contingency fraction. It is only a simplified resource check; it does not simulate a detailed return path, airlock cycle, suit faults, reserve oxygen modes, communications or emergency procedures.

If a required auxiliary layer is absent, MARSCOPE does not silently treat it as measured zero risk. The corresponding soft objective is removed from normalized preference weights and the route metric displays `N/A`. An unavailable temperature layer is not used as a temperature hard constraint. The UI must be read together with the available-layer/provenance status.

## 3. Edge-cost vector

For edge `e`, define:

- `d_e`: ground distance in metres;
- `t_e`: modeled traversal time in seconds, including simple rest overhead;
- `E_e`: modeled energy proxy in Wh;
- `O_e`: modeled oxygen proxy in litres;
- `L_max`: `terrain.max_path_distance_m`, a normalizer derived from active grid extent;
- `T_budget`, `E_budget`, `O_budget`: user-configured illustrative budgets;
- `r_t`, `r_env`, `r_rad`, `u`, `s`: normalized terrain, environment, radiation, uncertainty and science fields in `[0,1]`.

The implementation accumulates this nine-component vector:

\[
q(e)=\left[
\frac{d_e}{L_{max}},
\frac{t_e}{T_{budget}},
\frac{E_e}{E_{budget}},
r_t\frac{d_e}{L_{max}},
r_{env}\frac{d_e}{L_{max}},
r_{rad}\frac{d_e}{L_{max}},
u\frac{d_e}{L_{max}},(1-s)\frac{d_e}{L_{max}},\frac{O_e}{O_{budget}}
\right]
\]

All terms are dimensionless and non-negative. Science is a **missed-opportunity cost** `(1-s)`, not a negative reward. A route that visits higher-science cells pays less opportunity cost, while every edge remains non-negative.

The profile-weighted edge contribution is:

\[
c_p(e)=w_p^T q(e),\quad w_{p,i}\geq0,\quad \sum_iw_{p,i}=1
\]

User-set multipliers adjust selected base preferences and the resulting weights are renormalized. Multipliers are preference controls, not calibrated scientific or mission weights. Hard constraints are not affected by them. When `science`, `atmosphere` or `radiation` layers are unavailable, their associated weights are set to zero before renormalization; uncertainty remains in the cost.

### Current base route profiles

| Objective | Conservative | Balanced | Science-first |
|---|---:|---:|---:|
| Distance | 0.1152 | 0.2208 | 0.0960 |
| Time | 0.0576 | 0.1152 | 0.0576 |
| Energy | 0.0672 | 0.1248 | 0.0576 |
| Terrain risk | 0.2880 | 0.1728 | 0.1440 |
| Environmental index | 0.1152 | 0.1056 | 0.0768 |
| Radiation index | 0.0768 | 0.0768 | 0.0768 |
| Uncertainty | 0.1920 | 0.0960 | 0.0960 |
| Science opportunity cost | 0.0480 | 0.0480 | 0.3552 |
| Oxygen | 0.0400 | 0.0400 | 0.0400 |

These are starting demonstration values. They are not sourced EVA preferences, NASA safety limits or calibrated mission parameters.

## 4. Illustrative traversal / resource model

For each edge, the current code uses average slope, roughness and regolith proxies at the edge endpoints:

\[
F_s=1+1.8\frac{\bar{slope}}{slope_{max}},\quad
F_m=1+0.55\bar{roughness}+0.35\bar{regolith}
\]

\[
F_{mass}=\frac{m_{suit}+m_{equipment}}{54.5\;kg},\quad
v_e=\frac{v_0}{F_sF_mF_{load}}
\]

\[
t_e=\frac{d_e}{v_e}\left(1+\frac{restDuration}{restInterval}\right),\quad
E_e=d_e(0.018\;Wh/m)F_{mass}F_sF_m
\]

\[
O_e=\frac{t_e}{60\;s/min}\;O_{consumption}
\]

The risk proxy is currently:

\[
r_t=clamp_{[0,1]}(0.50\frac{targetSlope}{slope_{max}}+0.30\bar{roughness}+0.20\bar{regolith})
\]

Environmental and radiation values are currently dimensionless relative indices, not physical weather variables or dose. These equations are research placeholders for algorithm experiments. They are not measured Mars human locomotion, suit power, life-support or physiological models. Roughness is a 3 × 3 local DEM standard deviation, not a validated rock-size/footing classifier.

## 5. Multi-objective A*

Every active label stores an accumulated objective vector `g_vec(n)`. At each cell, a new label is discarded when an existing label is no worse in every component and strictly better in at least one. Existing labels dominated by the new label are removed.

The priority queue orders labels using the current profile-weighted scalar cost and heuristic:

\[
f_p(n)=w_p^Tg_{vec}(n)+h_p(n)
\]

\[
h_p(n)=w_{distance,p}\frac{D_{Euclidean}(n,goal)}{L_{max}}
\]

All other heuristic components are zero. Since each edge's distance contribution is at least the Euclidean distance between adjacent cell centres and all other terms are non-negative, this is an admissible and consistent lower bound for the scalarized objective on the 8-connected metric grid. When the distance multiplier is zero, the heuristic is zero.

The implementation retains at most seven labels per cell. When the cap is hit, it drops the highest current scalar-score label. This bounds memory and runtime but can discard a useful nondominated label. This is a **bounded approximate Pareto A*** variant, not an exact enumeration of the global Pareto frontier. The three policy routes are representative solutions, not an exhaustive set of all possible non-dominated routes.

## 6. Metrics and Pareto comparison

Lower is better for distance, modeled duration, modeled energy, terrain risk, environment index, radiation index and uncertainty. Higher is better for science potential. Resource feasibility is shown separately. If an auxiliary layer is missing, its route metric is `null` and the UI displays `N/A`; it is not reported as 0%.

The comparison marks non-dominance only across the three routes returned by the three policy searches. It does not establish global Pareto optimality.

## 7. Incremental replanning with LPA*

The balanced route has a retained LPA* state for a fixed start and goal. For node `u`:

- `g(u)` is the current best known start-to-node cost;
- `rhs(u)` is the one-step lookahead value, `min_p(g(p)+c(p,u))` over predecessors;
- `u` is locally consistent when `g(u)=rhs(u)`.

After an obstacle or local field change on an already loaded layer, the changed cell and neighbours are updated, then the priority queue repairs inconsistent vertices until the goal is consistent. This avoids discarding all search state for every local change.

The current LPA* state is for a fixed start/goal and balanced scalarization. If a condition update would introduce a previously unavailable environmental/temperature/radiation layer, the API rejects it: the old search state was not weighted for that new layer. Load that layer and generate a fresh route set first. LPA* post-checks return-resource feasibility, but it is not yet an exact resource-constrained incremental multiobjective planner. A fully resource-constrained repair algorithm would include discretized resource state or use a validated resource-constrained label-setting repair.

## 8. Complexity and memory

Let `V` be grid cells, `E` the 8-connected edges (`E <= 8V`), and `K` the maximum retained labels per cell. Bounded-label search has an operational queue bound near `O(K E log(KV))`, with `O(KV)` active-label memory plus stale/dead label and heap records. Actual work depends on objective conflict, dominance and cap pressure. LPA* stores `g`, `rhs` and queue state in `O(V)` memory; a local change initially invalidates a cell and its neighbourhood, but consistency repair can propagate through much of the graph in the worst case.

## 9. Baselines and calibration

The benchmark endpoint compares on the same grid, hard constraints and resource reserve:

- scalar weighted A*;
- Dijkstra with the same balanced edge scalarization;
- distance-only shortest path, still respecting hard constraints/resource reserve.

A* and Dijkstra should agree on scalar optimal cost for each tested positive-cost graph. Runtime and route metrics must be measured locally; no speed or safety improvement is assumed.

Before any real-data or human-safety claim:

1. Validate Mars map projections, pixel registration, vertical units and footprint overlap with source-product tie points.
2. Test A* consistency and optimality against Dijkstra on randomized small positive-cost grids.
3. Compare bounded Pareto labels against exact tiny-grid enumeration to quantify cap-induced frontier loss.
4. Compare every LPA* obstacle update against fresh Dijkstra recomputation on the same changed graph.
5. Calibrate slope, roughness and mobility from validated analogue/human-factors data.
6. Replace environmental/radiation indices with traceable physical quantities and time integration where appropriate.
7. Run sensitivity sweeps on weights, hard limits, missing-data treatment and reserve policies.
8. Have mission systems and human-factors specialists independently review any operational model.

A route found by the prototype is a computational result on its supplied data; it is not an assertion of astronaut safety.

# Hackathon demonstration script (about 4 minutes)

## Opening: the problem

"Curiosity has spent years turning Mount Sharp into a scientific record. A future human team would need more than a shortest line between two points: it needs a route that accounts for mobility, uncertainty, resource budgets and the science worth investigating. MARSCOPE is a research prototype for that planning problem."

Immediately point out the **synthetic / not georeferenced** label. Explain that the prototype does not pretend its demo mesh is NASA terrain.

## Route policies

1. Keep the default start and destination and click **Generate Route Options**.
2. Show route A, B and C.
3. Select the Analytics panel and compare distance, time, energy, terrain risk, environment/radiation indices, uncertainty and scientific value.
4. Explain that the planner uses non-negative normalized edge objectives and a bounded set of non-dominated labels. Science is modeled as a positive missed-opportunity cost, not a negative reward.
5. Toggle the Science Potential layer and open the Science panel. Explain that the three targets are synthetic stand-ins; the panel links to actual NASA/JPL Curiosity boxwork context.

## Conventional path versus mission planning

1. Click **Compare Baselines**.
2. Compare standard weighted A*, Dijkstra and distance-only results on the same fixture.
3. Use the distance-only result to explain the trade-off: the shortest path may cross higher modeled risk and miss scientific targets. Do not describe this one synthetic sample as proof of general performance.

For the committed default seed and default endpoints, one observed reference run returned:

| Route | Distance | Mean terrain risk | Science value |
|---|---:|---:|---:|
| Conservative | 637.1 m | 45.5% | 0.0% |
| Balanced | 660.5 m | 40.8% | 16.9% |
| Science-first | 651.2 m | 43.6% | 18.4% |
| Distance-only baseline | 637.1 m | 46.8% | 0.8% |

These values are from the synthetic fixture only. The risk columns are mean route-segment indices, not real hazard probabilities or exposure estimates.

## Adaptive replanning

1. Keep or select balanced route B and click **Simulate Obstacle**.
2. Show the obstacle marker and the route update.
3. Explain LPA*: it retains `g` and `rhs` state and repairs the inconsistent region after edge costs change. The sample smoke test repaired the route with 650 additional node expansions; counts vary with route and terrain.
4. Point to the return-feasibility check. A simulated route is not a safety approval.

## EVA mode and close

Switch to EVA Mode. Demonstrate the compact location, next-target and return-budget cards.

Close with the data plan: connect a verified Gale CTX mosaic for regional context, a footprint-verified HiRISE local product, MOLA as regional elevation background, CRISM spectral evidence and Curiosity PDS observations only after matching their footprints, coordinate metadata and dates.

**Honesty line:** "MARSCOPE currently proves the planning workflow on reproducible synthetic data. The NASA archives are researched and registered, not yet ingested as aligned terrain layers. The next milestone is geospatial validation, not a claim of operational readiness."

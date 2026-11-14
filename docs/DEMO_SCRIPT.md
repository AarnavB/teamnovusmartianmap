# MARSCOPE hackathon demo script

## The story

“A future explorer needs to travel between two places near Mount Sharp while keeping a return reserve and investigating evidence of ancient groundwater. MARSCOPE shows how a planner can compare exploration priorities, and how archive provenance and unknown data affect the answer.”

## Demo sequence

1. **Establish the data truth.** Open the map and point out the `SYNTHETIC / NOT GEOREFERENCED` tag. State clearly that the default hills and targets are teaching data, not Curiosity coordinates.
2. **Show available layers.** Toggle elevation, slope, roughness, uncertainty and science on the synthetic tile. Point out the source, date, grid spacing and available-layer indicators.
3. **Set an expedition.** Choose start/destination cells and adjust slope, EVA time, oxygen, carried equipment, rest and objective preference multipliers.
4. **Generate three route policies.** Explain why conservative, balanced and science-first may differ. Inspect distance, illustrative time/energy/oxygen, risk, data uncertainty, science and return feasibility.
5. **Compare baselines.** Run scalar A*, Dijkstra and distance-only under the same hard constraints and compare path metrics and expanded nodes. Do not claim a universal speed or safety win.
6. **Adapt to a field update.** Inject a simulated obstacle or update a local available layer. Show LPA* repair and the explicit simulated-scenario label.
7. **Ask the science assistant.** Search a question about ridges, hollows or nodules. Open the NASA/JPL source cards and distinguish published interpretation from direct instrument observation. If the optional model is configured, explain that it receives only retrieved source records; otherwise show the extractive fallback.
8. **Open official archive access.** Search NASA PDS metadata or Mars ODE product footprints. Show the original product identifier, archive URL and footprint metadata. Explain that a product must overlap the actual study area.
9. **Inspect the label.** Upload a matching PDS3 `.LBL` or PDS4 `.XML`, review the projection/unit/time/instrument fields and original label hash.
10. **Preserve a product.** Optionally download a small official product file or cache a small Mars Trek WMTS region. State that WMTS imagery is not a DEM.
11. **Explain the real-data import gate.** Show the DEM unit confirmation and Mars ellipsoid check. Import a verified Mars GeoTIFF only when the original label supports the conversion. Add an auxiliary layer only with documented meaning, band and unit mapping.
12. **Offline handoff.** Export the offline review ZIP and show its manifest: plan, terrain, evidence, data catalog, labels, observations, official downloads and WMTS cache as available.

## Closing statement

“MARSCOPE is a research prototype with working archive discovery, provenance-aware import paths and a testable multi-objective planner. Its default terrain is synthetic. Before it can support real human exploration, it needs a footprint-verified local DEM and imagery stack, rover localization, physically calibrated environmental/radiation models, validated EVA mobility/resource models, and independent safety verification.”

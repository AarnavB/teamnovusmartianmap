# MARSCOPE 0.4.0 — From Orbit to Bootprint

**Evidence-to-Route Intelligence for Mars exploration research.**

MARSCOPE combines official NASA/JPL source discovery, a real Curiosity Mastcam panorama, a dual-provider Jev decision service (TypeSafe or OpenCode Console), and a research-grade terrain/pathfinding prototype. This release is designed to be easy to run locally: one launcher starts the Python science API, the TypeScript decision service, and the built React interface together.

> **Scientific boundary:** the Curiosity panorama and NASA archive services are real. The default 64×64 route-planning tile is still a synthetic, non-georeferenced fixture. MARSCOPE does not pretend that a rover photograph or orbital image is a DEM, a precise human-scale obstacle map, or a certified EVA route. Import a verified Mars DEM before interpreting route calculations geographically.

## Quick start

### Windows

1. Install **Python 3.11+** and **Node.js 22.15+ (or newer)**.
2. Extract the MARSCOPE 0.4.0 folder.
3. Double-click `RUN_MARSCOPE.bat`.
4. On first run, the launcher creates `.venv`, installs Python/Node packages, builds the UI, runs the TypeScript decision-policy tests, starts both APIs, and opens the browser.
5. Keep the terminal window open. Press `Ctrl+C` in that window to stop both services.

On first Windows launch, keep at least **1 GB free** on the project drive for npm extraction, cache files and the build. The launcher checks this before installing Node packages and removes incomplete `node_modules` folders after a failed install so a partial install is not mistaken for a complete one.

Or run from Git CMD:

```cmd
cd path\to\MARSCOPE_0.4.0
RUN_MARSCOPE.bat
```

### macOS / Linux

Install Python 3.11+ and Node.js 22.15+ (or newer), then run from the project root:

```bash
./run.sh
```

**First launch requires internet access** to install dependencies and to retrieve NASA/TypeSafe data. Subsequent launches reuse the local environments and installed packages. The interface is served from one local address: `http://127.0.0.1:8000`.

### What runs behind the single launcher

- React + Three.js is built once and served by the TypeScript Node server.
- The Node server starts FastAPI as a child process and proxies `/api/*` while preserving the request path.
- The TypeScript service handles Jev requests and keeps the Jev API key in memory for the individual request only.
- You do not need to open separate terminal windows or start separate backend/frontend commands.

## Jev setup: TypeSafe or OpenCode Console

Open **JEV INTEL** in the right-side panel. Choose an API provider from the dropdown:

- **OpenCode Console — Jev 1.13 Free:** paste an OpenCode Console personal API key. MARSCOPE calls `https://opencode.ai/inference/systemone/v1/systemone` with model `jev-1.13-free`. OpenCode currently lists this model as temporarily free; availability and access can change. Its key is different from a TypeSafe key.
- **TypeSafe — Jev 1.14.0:** paste a TypeSafe API key. MARSCOPE continues to use the official `@typesafe-ai/sdk` package.

The two provider options use the same MARSCOPE evidence rubric and deterministic review policy. One System One request is made per selected source (maximum four). OpenCode's free Jev integration currently supports the text-based evidence evaluation workflow. The separate experimental image Box annotation remains TypeSafe-only and uses `jev-preview`.

Keys are not saved in `.env`, browser storage, the decision audit, or project files. A key remains in the page's current memory and is sent to the local Node service only when an evaluation starts. The server forwards it to the selected provider over HTTPS. Switching providers clears the key; refreshing the page or pressing **FORGET** also clears it. MARSCOPE does not control provider account billing, usage, rate limits, or model availability.

The evidence workflow uses:

- **Choice:** supports / contradicts / contextual / insufficient.
- **Score:** relevance and novelty rubrics.
- **Noul:** a yes-probability judgment for a narrowly stated direct-support question.

Jev's confidence is not a calibrated probability that a response is correct. Noul values are not calibrated scientific posterior probabilities. Policy thresholds in this prototype are provisional triage rules; they must be calibrated on a human-labelled evaluation set before making scientific performance claims. Jev can influence the route cost weights used by the separate adaptive pathfinding workflow described below, but cannot edit route geometry, bypass a hard constraint, or make astronaut-safety decisions.
## Real NASA/JPL data in this release

### Curiosity Mastcam panorama — PIA26560

MARSCOPE displays the original NASA/JPL panorama **“Curiosity Views Boxwork Patterns at a Distance”**. The JPL page describes a mosaic stitched from 23 Mastcam images acquired on **22 May 2025, Sol 4536**. The image provides real visual context for the boxwork investigation. It is rover-local imagery and the source page does not provide the georeferenced footprint needed for route overlay.

- Original source: <https://www.jpl.nasa.gov/images/pia26560-curiosity-views-boxwork-patterns-at-a-distance/>
- Image credit: NASA/JPL-Caltech/MSSS

The curated evidence bundle also links additional Curiosity boxwork and nodule records and the PDS MSL archive documentation. The records preserve original source links and known limitations.

### Live archive discovery

Use **DATA → NASA data access** to query official services:

| Source | How MARSCOPE uses it | Boundary |
|---|---|---|
| [NASA PDS Search API](https://pds.nasa.gov/api/search/1/) | Search and resolve PDS4 product metadata | Search index coverage is not complete for every product; original archive labels remain authoritative |
| [Mars Orbital Data Explorer (ODE)](https://ode.rsl.wustl.edu/mars/) | Mars orbital product and spatial-footprint discovery across supported archives | Footprints and instrument/product codes are product-specific |
| [NASA Mars Trek WMTS](https://trek.nasa.gov/mars/) | Capabilities discovery and bounded tile caching | Rendered tiles are imagery, not calibrated DEM values |
| [HiRISE archive](https://www.uahirise.org/catalog/) | Discover high-resolution targeted observations via archive metadata | Coverage is discontinuous and product-specific |
| [CRISM archive](https://pds-geosciences.wustl.edu/missions/mro/crism/) | Discover spectral observations | Spectral products require calibration and wavelength/label interpretation |
| [MOLA archive](https://pds-geosciences.wustl.edu/missions/mgs/megdr.html) | Discover regional/global topography | Resolution and vertical datum vary by product |

The Mars Trek layer catalog includes the Gale Crater CTX regional mosaic `Gale_CTX_BlockAdj_dd`, the Curiosity-site HiRISE mosaic and global MOLA/HRSC context products. The WMTS `GetCapabilities` document is read to identify matrix sets, styles, tile templates and formats before caching. The Gale CTX mosaic is regional context; its imagery is not a substitute for a verified elevation model.

**NASA Worldview is not used as a Mars data feed.** It is Earth-focused and is only a possible UI design reference.

## What Jev does in the decision loop

1. The user states a scientific objective and working hypothesis.
2. MARSCOPE supplies up to four curated NASA/JPL evidence records, with source metadata and limitations, to Jev.
3. Jev returns structured Choice, Score and Noul judgments.
4. A deterministic TypeScript policy classifies each record as a supporting candidate, counter-evidence, investigate-further item, or human-review item.
5. The UI shows the model, rubric outputs, source link, policy rationale and geospatial-linkage status.
6. A local audit file records only the objective, hypothesis, evidence IDs and decisions. It never records the API key.

At present, none of the curated rover image records is marked as a verified georeferenced target. Therefore, evidence triage remains a scientific review queue and does **not** directly alter route planning. The separate Jev pathfinding workflow uses only the mission prompt, operational constraints and terrain layers already available to the planner; it does not use image-local boxes or unverified coordinates.


### Jev-weighted adaptive pathfinding

1. Open **JEV INTEL**, choose OpenCode Console or TypeSafe, and enter the corresponding API key. The key remains in page memory and is shared with the route planner until cleared or the page is refreshed.
2. Return to the planner and edit the **MISSION INTENT PROMPT** (maximum 600 characters). Describe the mission trade-offs you care about, such as lower terrain difficulty, lower uncertainty, shorter travel time or higher scientific value.
3. Select **GENERATE WITH JEV WEIGHTS** or **APPLY JEV WEIGHTS + REPLAN**. MARSCOPE calls Jev *before* Python pathfinding starts.
4. Jev uses **Choice** to select a strategic focus, **Score** to rate each available route objective from 0–3, and **Noul** to estimate each objective's relevance to the prompt. MARSCOPE derives a normalized weight vector with 90% Jev influence and a 10% strategic prior.
5. Python applies the vector directly to the balanced route's A* edge-cost scalarization, queue priorities and bounded Pareto-label pruning. The same vector is used by LPA* for incremental repairs. The balanced route is labelled **JEV-ADAPTIVE**; conservative and science-first retain their static profile vectors as comparison baselines (the shared manual multipliers can still fine-tune them). The UI displays the actual weights sent to the pathfinder.

Only objectives with available spatial data are weighted. Missing atmosphere, radiation or science layers are omitted rather than treated as measured zeros. Jev controls preferences, not hard limits: terrain blocking, slope/temperature constraints and return time/energy/oxygen checks remain deterministic. A failed or malformed Jev response does not silently fall back to a different Jev judgment; the prior plan remains in place. Without a key, static-profile A*/LPA* remains available.

The 90/10 weight-construction policy is an experimental design choice, not a calibrated optimum. The resulting weights are mission preferences, not probabilities of route success or safety. All route and resource calculations remain research-prototype estimates and must not be used as operational astronaut guidance.

## Route planning and geospatial import

The backend includes:

- Bounded multi-objective A* with conservative, balanced and science-first profiles.
- Hard slope/temperature/obstacle checks and return resource reserves.
- LPA* incremental repair for the balanced scalarization.
- A* / Dijkstra / distance-only benchmark endpoints.
- Explicitly synthetic demo terrain for controlled algorithm tests.
- Mars-ellipsoid screening for imported DEMs and aligned auxiliary layers.
- PDS3/PDS4 label inspection and provenance hashes.
- REMS / RAD CSV import with source-column mapping. These remain rover-location/time observations, not spatially extrapolated fields.

To use a real surface in route calculations:

1. Find a product in ODE/PDS whose footprint actually covers the intended study area.
2. Inspect its full original PDS label and instrument/SIS documentation.
3. Establish that the product is a DEM or a legitimate elevation product; do not treat an image mosaic as elevation.
4. Prepare a georeferenced GeoTIFF in a verified Mars planetary CRS and projected metre units, preserving vertical datum and source metadata.
5. Import it through **DATA → Import a verified Mars DEM** and explicitly confirm vertical units from the original label.
6. Import additional raster layers only after confirming their meaning, band, units, scale and footprint.

The Mars-ellipsoid check is a screening safeguard, not proof that a product is scientifically appropriate. MARSCOPE does not bundle a preprocessed, verified Mount Sharp DEM in this ZIP.

## Project structure

```text
MARSCOPE_0.4.0/
├── RUN_MARSCOPE.bat          # Windows double-click launcher (PowerShell handoff)
├── RUN_MARSCOPE.ps1          # Windows setup/build/start logic
├── run.sh                    # One-command macOS/Linux launcher
├── backend/                  # FastAPI, pathfinding, PDS/ODE, WMTS, geospatial pipeline
├── decision-service/         # TypeScript, TypeSafe SDK + OpenCode System One, decision policy
├── frontend/                 # React, TypeScript, Three.js, NASA evidence UI
├── docs/                     # Architecture, data provenance, Jev policy, validation
└── .gitignore                # Excludes local keys, environments, downloads and audits
```

## Release notes

See [`docs/CHANGELOG.md`](docs/CHANGELOG.md) for the 0.4.0 changes and earlier release summaries. The Jev design is documented in [`docs/JEV_DECISION_ARCHITECTURE.md`](docs/JEV_DECISION_ARCHITECTURE.md), and the data limitations in [`docs/DATA_PROVENANCE.md`](docs/DATA_PROVENANCE.md).

## Windows startup troubleshooting

The Windows batch file is a small wrapper around `RUN_MARSCOPE.ps1` to avoid CMD parsing issues. Startup logs are saved to `.run-logs/marscope-startup.log`. See [`docs/WINDOWS_STARTUP_FIX.md`](docs/WINDOWS_STARTUP_FIX.md).

## API and diagnostics

With the app running:

- App: <http://127.0.0.1:8000>
- FastAPI docs: <http://127.0.0.1:8000/docs>
- Health: <http://127.0.0.1:8000/api/health>
- Local Jev status: <http://127.0.0.1:8000/api/decision/status>

Key endpoints include `/api/data/pds/search`, `/api/data/ode/search`, `/api/data/trek/layers`, `/api/science/evidence`, `/api/decision/evaluate`, `/api/decision/optimize-route` (Node decision service), and `/api/decision/annotate-nasa-image`.

## Tests

Backend:

```bash
cd backend
python -m pip install pytest
python -m pytest -q
```

Decision policy (run by the launcher after build):

```bash
cd decision-service
npm test
```

The TypeScript service also runs a strict TypeScript build. The current environment used to prepare this archive had no npm registry DNS access, so the full npm dependency installation and Vite production build could not be completed here. The launch script performs those steps on the first run in a network-enabled environment and stops with the underlying error if a dependency/build step fails.

## Known limitations

- The default route grid remains synthetic and not georeferenced; no default route is a NASA-derived Gale Crater traverse.
- The JPL panorama is a real observation but not a georeferenced image raster or obstacle map.
- WMTS tiles are discoverable/cacheable but are not yet draped into the 3D terrain mesh.
- Automated rover-image localization, SPICE-based rover frame registration and complete PDS product parsing are not implemented.
- REMS and RAD measurements are rover station time-series. No spatial weather or radiation field is inferred from them.
- Jev thresholds are provisional, not calibrated. Visual Box annotation is experimental and requires expert review.
- No complete spatial Mars weather, wind, dust, radiation-dose or thermal forecast is supplied.
- The EVA panel and resource estimates are research simulations, not validated human performance or certified operational guidance.

**MARSCOPE is a scientific research and hackathon prototype, not an operational astronaut navigation system.** A route returned by the planner is not certified safe.

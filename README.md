# MARSCOPE — From Orbit to Bootprint

**Release:** 0.3.1
**Type:** research / hackathon prototype
**Demonstration region:** Mount Sharp, Gale Crater
**Primary rule:** never present simulated values as NASA observations.

MARSCOPE combines a multi-objective traversal planner with official planetary archive discovery, provenance-aware data import, a cited science assistant, and an offline review package. The code is modular so data providers can be extended without rewriting the planner.

> **Research prototype only.** The default terrain is a deterministic synthetic teaching grid. It is not a geographic crop of Gale Crater. The system is not certified navigation software and must not be used to guide real people or real EVA operations. The mobility, energy, oxygen and time estimates are illustrative assumptions, not validated human-performance predictions.

## What is implemented

### Planning and simulation

- Bounded Pareto-label multi-objective A* with non-negative normalized edge costs.
- Conservative, balanced and science-first route policies.
- User-adjustable objective multipliers, renormalized after unavailable data layers are removed.
- Hard exclusions for obstacles, configured slope and available temperature layers; no diagonal corner-cutting.
- Outbound and return-resource reserve checks for modeled time, energy and oxygen.
- LPA* retained-state replanning for simulated local changes to an already available layer.
- Standard A*, Dijkstra and distance-only baseline comparisons over the same fixture.
- Route explanations, uncertainty, source-availability notes and `N/A` metrics when a layer is not present.

### Official planetary data connections

- **NASA PDS Search API:** live product discovery and product-ID resolution for PDS4 metadata.
- **PDS Geosciences Node ODE REST:** live Mars orbital-product and footprint searches for HiRISE, CTX and CRISM.
- **NASA/JPL Mars Trek WMTS:** official layer catalogue, GetCapabilities parsing and bounded tile caching for offline review.
- **Official product downloader:** downloads user-selected files from an HTTPS allow-list of PDS / NASA mission archive hosts, checks redirects, enforces a 250 MB cap, and stores the original bytes with SHA-256 and a provenance sidecar.
- **PDS3 / PDS4 label inspection:** extracts convenience metadata while preserving original label text and its hash.
- **GeoTIFF inspection and ingestion:** Mars-ellipsoid screening, projected metre-CRS check, DEM-derived slope/roughness, NoData masking and provenance.
- **Aligned science layers:** explicit band, meaning, units and normalization range; only layers covering the active DEM footprint can be imported.
- **Curiosity REMS / RAD CSV import:** explicit column mapping and raw-file retention. These remain rover-station time series, never a spatial field.

### Science and offline capabilities

- BM25-style retrieval over a curated NASA/JPL boxwork evidence set.
- Optional server-side OpenAI Responses API generation grounded only in the retrieved evidence. If no `OPENAI_API_KEY` is configured, MARSCOPE uses the deterministic extractive fallback. The key is never sent to the browser.
- Offline review ZIP containing the current terrain, optional mission plan, data catalogue, evidence set, cached WMTS archives, imported observations, labels and official downloads.
- EVA route-following simulation with cell-by-cell progress, grid-relative heading, next waypoint, remaining-route estimates, upcoming slope/uncertainty warnings, nearby geolocated targets, a reverse trace to the start, and cached-review-map status.
- PWA shell caching for core app resources and selected read-only API responses.

## What this release does not claim to do

The official archives are connected for **discovery and selected file retrieval**, but the app does not ship a preloaded, georeferenced Mount Sharp science stack. The following remain deliberate boundaries:

- No automatic science interpretation of arbitrary PDS binary products. Product-specific labels, SIS documentation, calibration, SPICE/localization and projection checks remain necessary.
- WMTS tiles can be cached for review, but are not currently draped as a georegistered basemap in the planner's terrain mesh. They are not a DEM.
- No complete georeferenced Curiosity observation catalogue or automated rover-image localization is bundled.
- No validated spatial Mars weather, wind, dust, surface-radiation-dose or thermal forecast model is included.
- REMS / RAD point-time observations are imported as station records only. No spatial extrapolation is performed.
- The science assistant has five curated evidence records, not a full PDS-wide scientific literature index. Generative answers are optional and must be checked against the linked originals.
- There is no persistent PostGIS service. Imported files and provenance are stored locally; route sessions are in-memory and are cleared when the backend restarts.
- The offline PWA is an app/reference cache plus a separately exported review ZIP, not a complete offline planetary navigation package. The EVA progress indicator is simulated; cached WMTS tiles are listed but are not yet loaded as the EVA basemap.

## Repository layout

```text
MARSCOPE/
├── backend/
│   ├── app/
│   │   ├── domain/          # label, raster, observations, RAG, offline package
│   │   ├── services/        # PDS / ODE, WMTS, official downloads, optional LLM
│   │   ├── main.py          # FastAPI endpoints and application wiring
│   │   ├── planner.py       # bounded multi-objective A*
│   │   ├── lpa.py           # LPA* incremental repair
│   │   ├── benchmarks.py   # baseline algorithms
│   │   └── terrain.py       # explicit synthetic fixture / terrain container
│   ├── data/evidence/       # versioned curated NASA/JPL evidence records
│   ├── tests/               # planner, API, archive, raster and ingestion tests
│   ├── scripts/             # planetary GeoTIFF preparation helper
│   └── requirements*.txt
├── frontend/
│   ├── src/components/      # Three.js terrain, science assistant, data explorer
│   ├── public/              # PWA manifest and service worker
│   └── vite.config.ts       # local /api proxy
├── docs/                    # science, data, algorithm, architecture, validation
├── scripts/dev.sh
└── .env.example
```

## Run locally

Requirements: Python 3.10+ (tested with Python 3.13) and Node.js 20+.

### 1. Backend

```bash
cd MARSCOPE/backend
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate
pip install -r requirements.txt
# Optional, required only for GeoTIFF ingestion / inspection:
pip install -r requirements-geospatial.txt
uvicorn app.main:app --reload --port 8000
```

API reference: <http://localhost:8000/docs>
Health check: <http://localhost:8000/api/health>

### 2. Frontend (second terminal)

```bash
cd MARSCOPE/frontend
npm install
npm run dev
```

Open <http://localhost:5173>. Vite proxies `/api` to `http://127.0.0.1:8000` by default. For a separately hosted API, create `frontend/.env.local` with:

```dotenv
VITE_API_BASE=https://your-api.example.org
```

Do not put server-side API keys in any `VITE_*` variable.

### 3. Optional generative science answers

The extractive cited assistant works without an API key. To enable optional generation, set these variables in the **backend process environment** (or a backend-only `.env` loaded by your deployment):

```dotenv
OPENAI_API_KEY=your_server_side_key
MARSCOPE_LLM_MODEL=gpt-6-astra
```

The backend calls the OpenAI Responses API with `store: false`, no web tools and only the retrieved NASA/JPL evidence records. Answers always return the corresponding source records separately. If the API is unconfigured or unavailable, MARSCOPE falls back to extractive summaries. Never commit real keys.

### 4. Tests

```bash
cd MARSCOPE/backend
pip install pytest
python -m pytest -q
```

### One-command development helper

From the repository root, `bash scripts/dev.sh` creates the backend virtual environment if needed, installs dependencies, and starts both servers. Logs go to `.run-logs/`.

## Working with official NASA data

1. Open **Data → NASA data access**.
2. Search the NASA PDS registry or ODE footprint catalogue. Results are discovery metadata, not a substitute for product files and labels.
3. Inspect and preserve the original PDS3 `.LBL` or PDS4 `.XML` label. Confirm the target body, instrument, observation time, product level, units, coordinate convention, map projection, vertical datum and pixel scale.
4. Download only a product whose official archive URL and footprint match the study region. The downloader accepts supported file extensions on an allow-list of official archive hosts and caps downloads at 250 MB.
5. Do not assume a PDS image is a DEM. For a DEM import, prepare a georeferenced GeoTIFF using a Mars reference figure, projected metre units and documented vertical metres. Confirm the metre units in the product label in the UI before import.
6. Import an auxiliary raster only after confirming it is the right measurement. The user must explicitly map the band and its units/range; a CRISM radiance band is not automatically a mineral-probability score.
7. Import REMS / RAD tabular data using an explicit source-column mapping. Preserve it as rover-station/time observations.

See `docs/SCIENCE_AND_DATA.md` for the official source inventory, access methods, limitations and coordinate handling. See `docs/ALGORITHM.md` for the objective model and `docs/VALIDATION.md` for the validation boundary.

## Reproducible demo sequence

1. Open the 3D surface view and read the synthetic / not-georeferenced marker.
2. Toggle the available synthetic layers and inspect source status.
3. Select start and destination grid cells.
4. Generate conservative, balanced and science-first alternatives.
5. Compare route length, modeled time/energy, risk, science utility and uncertainty.
6. Run the A* / Dijkstra / distance-only comparison.
7. Inject a simulated obstacle or modify an available local field and inspect the LPA* repair.
8. Open the science assistant and check the NASA/JPL evidence cards.
9. Discover a PDS/ODE product, inspect its label, or cache a small Mars Trek WMTS area.
10. Export an offline review ZIP.

## Known engineering limits

- Bounded Pareto A* retains at most seven labels per node, so it is a bounded approximate frontier search, not an exhaustive Pareto-optimal solver.
- The LPA* repair is for the fixed-start/fixed-goal balanced scalarization. It does not solve the full resource-constrained multiobjective dynamic replanning problem.
- Weight multipliers are adjustable demonstration preferences, not calibrated mission policy.
- The imported DEM's terrain cost products are only as valid as its source product, map geometry, vertical datum, pixel scale and resampling. The ellipsoid check is a screening guard, not proof of product identity.
- Roughness is currently a 3×3 local standard deviation of the DEM. It is not a validated rock-size or human-footing classifier.
- The current generative assistant is optional and bounded to the retrieved source subset. It is not an autonomous science discovery system.

Never describe a route as astronaut-safe because this prototype returns it. Human EVA use would require validated surface data, validated mobility/resource models, human-factors review, mission-authorized limits, uncertainty budgets and formal verification.

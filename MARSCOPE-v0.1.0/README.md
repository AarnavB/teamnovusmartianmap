# MARSCOPE — From Orbit to Bootprint

**Release:** 0.1.0 · **Type:** research/hackathon prototype · **Primary demo area:** Mount Sharp, Gale Crater

MARSCOPE is a local, runnable prototype exploring how scientific evidence, terrain costs, uncertainty, mission resources and human-mobility assumptions could be combined in a planetary route-planning workflow.

> **Important:** the shipped terrain is a deterministic synthetic teaching tile. It is not a georeferenced part of Gale Crater, and none of its heights, slopes, hazards, temperatures, radiation or science-potential values are NASA measurements. The app is not certified navigation software and must not be used for real EVA planning.

## What works in this release

- Interactive Three.js terrain scene with 2D/3D camera, pan/zoom/orbit, route overlays and map-point picking.
- Layer-style switching for elevation, slope, roughness, uncertainty and science-potential surfaces.
- Three route policies: conservative, balanced and science-first.
- Multi-objective A* with non-negative normalized edge costs and bounded Pareto label sets.
- Hard constraints for slope, temperature and resource/return reserve.
- Route analytics for distance, illustrative time/energy, terrain/environment/radiation indices, science value, uncertainty and return feasibility.
- Incremental replanning after a simulated obstacle using retained LPA* `g`/`rhs` state.
- Source registry that separates documented NASA data resources from layers actually connected to the prototype.
- Deterministic synthetic fixtures and automated backend tests.

## Repository layout

```text
MARSCOPE/
├── backend/
│   ├── app/                 # FastAPI, terrain fixture, planners and registry
│   ├── tests/               # deterministic algorithm tests
│   ├── scripts/             # geospatial ingestion helper
│   ├── data/                # fixture metadata; no giant raw archives
│   └── requirements.txt
├── frontend/
│   ├── src/                 # React + TypeScript + Three.js interface
│   ├── package.json
│   └── vite.config.ts
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ALGORITHM.md
│   ├── SCIENCE_AND_DATA.md
│   └── VALIDATION.md
├── scripts/dev.sh
└── .env.example
```

## Run locally

Requirements: Python 3.10+ and Node.js 20+.

### 1. Start the backend

```bash
cd MARSCOPE/backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs: <http://localhost:8000/docs>
Health check: <http://localhost:8000/api/health>

### 2. Start the frontend in a second terminal

```bash
cd MARSCOPE/frontend
npm install
npm run dev
```

Open <http://localhost:5173>.

The frontend expects the API at `http://localhost:8000`. To change it, create `frontend/.env.local`:

```dotenv
VITE_API_BASE=http://localhost:8000
```

### 3. Run tests

```bash
cd MARSCOPE/backend
pip install pytest
python -m pytest -q
```

### Single-command development helper

From the repository root, `bash scripts/dev.sh` starts the backend and frontend in separate background processes. The script writes logs to `.run-logs/`; stop processes with Ctrl+C.

## Default demonstration flow

1. Open the terrain view and note the synthetic-data watermark.
2. Toggle Elevation, Slope, Roughness, Uncertainty and Science Potential.
3. Change start/destination by using **Pick on Map**.
4. Set the slope and EVA-duration constraints, then generate routes.
5. Compare A / B / C route profiles and inspect analytics.
6. Select a route and inject a simulated obstacle. The balanced route is repaired by LPA*.
7. Toggle EVA Mode for the compact field-navigation summary.
8. Open Science and Data panels to inspect evidence notes and source status.

## Data integration status

This release does **not** silently substitute a NASA image or raster for the synthetic height field. The registry records the authoritative sources, data types, coverage and resolution notes. Actual ingestion is a separate next integration step and requires selecting products whose footprints genuinely overlap the intended sub-area.

Begin with `docs/SCIENCE_AND_DATA.md`. For actual image and DEM processing, use the product labels / metadata as the source of truth and run the provided `backend/scripts/prepare_geotiff.py` only on a correctly georeferenced source GeoTIFF. Install the optional `backend/requirements-geospatial.txt` dependencies using a compatible GDAL/PROJ environment. The script reprojects into a local Mars AEQD working CRS while preserving the input file and writing a provenance sidecar.

## Engineering scope and known gaps

- The Pareto label search is bounded per node (seven labels) to cap memory. It is an approximate Pareto A* variant, not an exhaustive global frontier solver.
- The incremental replanner is LPA* for the fixed start/goal balanced scalarization. It repairs changed edge costs for the updated synthetic obstacle. The other route policies are not incrementally repaired in this release.
- EVA time and energy are transparent illustrative models. Suit mass, speed and energy coefficients are assumptions, not empirically validated human Mars locomotion data.
- Radiation and environmental fields are dimensionless synthetic indices, not dose rates or weather forecasts.
- The UI's 3D geometry is generated from the synthetic grid. It is not a 3D reconstruction from HiRISE/MOLA/CTX.
- The evidence panel links to NASA/JPL context. A grounded RAG science assistant, offline cache packaging, and direct product ingestion are not implemented yet.

See `docs/VALIDATION.md` for the tests that exist and the tests required before expanding the prototype.

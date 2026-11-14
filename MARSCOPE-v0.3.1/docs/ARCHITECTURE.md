# MARSCOPE architecture

## Design principles

1. **Source data stays distinct from derived products.** Original PDS files and labels are retained; resampled layers have their own provenance.
2. **Planners consume a stable terrain contract.** A synthetic provider or geospatial provider can populate the same grid interface.
3. **Unknown is not zero.** Missing science, atmosphere and radiation layers are excluded from objective preferences and surfaced as unavailable; uncertainty remains explicit.
4. **Hard constraints cannot be traded against science reward.** Route weights only adjust soft costs.
5. **Local simulation is not live telemetry.** Scenario updates are labelled simulated and only affect layers already present.
6. **Official archive interfaces are metadata/product discovery, not a claim of a complete science database mirror.**

## Runtime topology

```text
React + TypeScript + Three.js (Vite :5173)
   │ same-origin /api requests (Vite proxy in development)
   ▼
FastAPI (:8000)
   ├── application / route handlers
   ├── planner.py               bounded Pareto multi-objective A*
   ├── lpa.py                   LPA* fixed start/goal incremental repair
   ├── benchmarks.py            A* / Dijkstra / distance-only
   ├── terrain.py                terrain contract + deterministic synthetic provider
   ├── services/archive_clients.py  NASA PDS Search + Mars ODE REST
   ├── services/wmts.py             Mars Trek WMTS capabilities and cache
   ├── services/official_downloads.py controlled official-host product downloads
   ├── services/llm_provider.py     optional OpenAI Responses API adapter
   └── domain/
       ├── pds_labels.py            PDS3 / PDS4 label inspection and preservation
       ├── raster_pipeline.py       Mars CRS screening, DEM and aligned layer import
       ├── observation_ingest.py    REMS / RAD CSV field mapping
       ├── observation_store.py     raw table + derived metadata store
       ├── science_assistant.py     retrieval, abstention and cited RAG orchestration
       └── offline_package.py       reproducible ZIP export
```

## Data providers and stores

| Component | Current implementation | Production extension |
|---|---|---|
| Terrain | In-memory `Terrain` contract; deterministic synthetic fixture by default; optional imported GeoTIFF | Windowed COG/raster provider, immutable layer IDs, versioned terrain sessions |
| Product discovery | NASA PDS Search API and Mars ODE REST | Product-node-specific adapters, pagination and richer product schemas |
| Map services | Mars Trek WMTS GetCapabilities and tile cache | Browser/server tile rendering with explicit projection and tile-matrix support |
| Original products | Local download store with SHA-256 sidecars | Object storage with immutable content-addressed keys |
| Labels | Original PDS3/PDS4 text plus extracted fields | Full standards-compliant label parsers and instrument SIS-aware validators |
| Rover observations | Explicitly mapped CSV import, raw file preserved | Per-instrument parsers, SPICE/localization join and time/quality semantics |
| Science evidence | Curated source JSON + BM25-style retrieval | Larger source index with versioned chunks and independently evaluated retrieval |
| RAG model | Optional OpenAI Responses API, server-side key, `store:false`; extractive fallback | Managed provider, evaluation harness, citations and governance |
| Session state | In-memory UUID sessions | Durable database/cache with ownership, expiry and concurrency control |
| Spatial index | No database required for current local grid | PostGIS for footprints, observations, AOIs, layer metadata and queryable vectors |

## Coordinate and geospatial strategy

Every incoming product keeps its source CRS WKT, ellipsoid, pixel transform, native resolution, footprint, NoData and label metadata. For new normalized geographic records, MARSCOPE recommends planetocentric latitude and east-positive longitude while retaining the untouched source convention. Older products may use planetographic latitude and west-positive longitude.

A local metric working CRS must be derived from a verified Mars body reference and site origin. Do not merge coordinate values because they look numerically plausible. Each output raster records the source-to-target coordinate operation, resampling method and output transform. Use nearest-neighbour for classes/flags and an explicitly chosen continuous-data method for continuous fields. Do not upsample coarse data and describe the result as new high-resolution information.

The current import guard checks projected metre units and a Mars-sized ellipsoid. This is a **screening check** only: it cannot prove product identity, geodetic datum, orientation, vertical datum or correctness of map-registration. The original PDS label and applicable SIS remain authoritative.

## Processing flow

```text
PDS Search / ODE REST / Mars Trek WMTS / PDS node archives
                         │
               discovery + footprint query
                         │
                product ID / official URL
                         │
           original file + original label
                 hash + provenance
                         │
            product-specific inspection
                         │
           verify Mars body / CRS / units
                         │
            common local metric raster
                         │
     DEM / slope / roughness / science / environment
                 each as separate layers
                         │
           uncertainty + coverage masks
                         │
      stable Terrain contract → route planner
                         │
                route analytics / 3D UI
```

Do not collapse spectral cubes, categorical geology, DEMs, temperature, radiation or rover observations into one untyped raster.

## HTTP API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Health/version |
| GET | `/api/terrain` | Active terrain and layer availability |
| GET | `/api/registry` | Curated official-source registry and coordinate policy |
| POST | `/api/routes` | Three planner policies and retained LPA* session |
| POST | `/api/replan` | Simulated obstacle update and incremental repair |
| POST | `/api/replan/condition` | Simulated value update on a layer already loaded |
| POST | `/api/benchmark` | Baseline comparison |
| GET | `/api/data/catalog` | Official source/access catalog |
| GET | `/api/data/pds/search` | PDS Search API discovery |
| GET | `/api/data/pds/product/{identifier}` | PDS product resolver |
| POST | `/api/data/pds/inspect-label` | PDS3/PDS4 label inspection and preservation |
| GET | `/api/data/ode/search` | Mars ODE bbox/instrument product search |
| GET | `/api/data/trek/layers` | Mars Trek layer catalogue |
| GET | `/api/data/trek/layers/{id}/capabilities` | WMTS GetCapabilities parser |
| POST | `/api/data/trek/cache` | Bounded WMTS tile cache export |
| POST | `/api/data/download` | Allow-listed official product file download |
| GET | `/api/data/downloads` | Download provenance records |
| POST | `/api/terrain/import-dem` | Verified Mars GeoTIFF DEM → route grid |
| POST | `/api/terrain/import-layer` | Align one explicitly mapped raster layer |
| GET | `/api/data/raster/inspect` | Inspect an imported GeoTIFF |
| POST | `/api/observations/import` | REMS/RAD CSV ingestion |
| GET | `/api/observations` | List station imports |
| GET | `/api/observations/{hash}` | Observation import details |
| GET | `/api/science/evidence` | Curated source evidence |
| POST | `/api/science/ask` | Retrieval / optional grounded generation |
| POST | `/api/offline/package` | Offline review ZIP |
| POST | `/api/reset` | Restore synthetic fixture and clear sessions |

Swagger UI: `/docs`.

## Deployment and reliability notes

- The download service accepts only HTTPS URLs from a fixed allow-list and manually validates redirects. Downloads are limited to 250 MB and preserved byte-for-byte with SHA-256 metadata.
- Raster uploads are capped at 250 MB; CSV imports at 40 MB; PDS labels at 10 MB. GeoTIFF import requires the optional Rasterio/PyProj stack.
- Route planning sessions are local-process memory. A restart clears them; multiple workers will not share them. Use one worker for the demo or replace sessions with a durable store.
- No authentication is configured. Do not expose the local prototype to an untrusted network without access control, rate limiting, request quotas and storage isolation.
- The OpenAI key is backend-only; the RAG adapter sends the question and top retrieved evidence to the Responses API with response storage disabled. Keep data governance and API terms in mind before enabling it for non-public material.

## EVA view and offline status

The frontend advances a simulated astronaut marker along the selected route one grid cell at a time. It derives grid-relative heading, distance to the next cell, outbound remaining distance/time, a reverse trace to the start, and local slope/uncertainty warnings from the active route grid. The API reports cached WMTS package manifests through `GET /api/offline/status`. This is a demonstration of route-following interaction only: it is not localization, does not compute a true-north bearing, and cached tiles are not rendered as a navigation basemap.

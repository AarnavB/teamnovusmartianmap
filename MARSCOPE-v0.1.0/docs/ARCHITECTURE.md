# MARSCOPE architecture

## Runtime topology

```text
React + TypeScript + Three.js (Vite :5173)
   | REST / JSON
   v
FastAPI (:8000)
   ├── terrain.py       deterministic synthetic grid and target annotations
   ├── planner.py       bounded multi-objective A* and route metrics
   ├── lpa.py           retained-state incremental route repair
   ├── benchmarks.py    scalar A*, Dijkstra and distance-only baselines
   └── registry.py      provenance-aware NASA source inventory
```

The API is intentionally stateless for ordinary terrain/registry reads. A route-planning request creates a local in-memory planning session keyed by a UUID so that a later obstacle update can reuse the LPA* search state. Restarting the server clears sessions. A production service would move sessions to a durable job/state store and make them user/session scoped.

## Why this stack

- **React + TypeScript + Vite:** fast interactive cockpit UI, typed API contracts.
- **Three.js:** mesh geometry, route overlays, camera controls and surface interaction without requiring a proprietary planetary globe SDK.
- **FastAPI + Python:** concise numerical/graph algorithm implementation and automatic OpenAPI documentation.
- **No database in v0.1:** the only shipped terrain is a small deterministic fixture. A DB would add operations without improving this demonstration. PostGIS becomes useful once real footprints, map products, observations and route sessions are ingested.

## Coordinate strategy for the real-data phase

Never mix coordinates based only on similar-looking numeric latitude/longitude. Every raster/vector layer must retain the coordinate convention and map projection from its source label or service metadata.

Recommended policy:

1. Ingest source metadata unmodified, including PDS labels, map projection, pixel scale, datum/body model, latitude type and longitude direction.
2. Use a canonical Mars convention for newly normalized geographic records: planetocentric latitude and east-positive longitude, while retaining the original coordinate values/convention as provenance. Older products may use planetographic latitude and west longitude.
3. For a small local analysis window, build a local metric working CRS (for example, a Mars-centred azimuthal-equidistant projection using the IAU Mars reference figure). Record the exact projection parameters and origin alongside every derived raster.
4. Align only products that overlap the same geographic footprint. Resample continuous surfaces (elevation, spectral parameters) with a documented interpolation method; use nearest-neighbour for classes/flags. Do not upscale coarse pixels and treat them as new high-resolution observations.
5. Represent resolution and uncertainty separately. A 200 m/pixel orbital DEM cannot be converted into 20 cm obstacle knowledge by rendering it as a detailed mesh.

The Mars Trek layer listing uses the identifier `EPSG:104905` for listed equirectangular services; inspect the selected layer's GetCapabilities and metadata before assuming its precise geodetic definition. Some individual map products publish a complete projection definition. The demo fixture has no CRS or geographic coordinates by design.

## Data processing boundary

```text
PDS / WMTS / HiRISE / ODE / rover archives
                 |
         immutable source store
      (original files + labels + hashes)
                 |
       product-specific adapters
                 |
   local CRS + validated footprint alignment
                 |
      derived COG / GeoTIFF / tables
                 |
    metadata + uncertainty + provenance
                 |
          API tile / query layer
                 |
       2D / 3D mission interface
```

Do not reduce all observations to one raster. Maintain separate products for DEM, slope, roughness, spectral evidence, geologic mapping, thermal observations, environmental observations, radiation observations, rover localization and source-coverage masks.

## Service/API map

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Backend health |
| GET | `/api/terrain` | Synthetic fixture and its data-status labels |
| GET | `/api/registry` | Dataset registry and coordinate policy |
| POST | `/api/routes` | Three alternative route profiles and LPA* session |
| POST | `/api/replan` | Add one simulated obstacle and repair route with retained LPA* state |
| POST | `/api/benchmark` | Standard A*, Dijkstra and distance-only comparison |
| POST | `/api/reset` | Reset demo terrain and clear local sessions |

OpenAPI / Swagger UI is available at `/docs` when the backend is running.

## Extension boundaries

Real-data ingestion should be a replaceable terrain provider, not a rewrite of the planner. Define a provider interface with arrays plus per-layer metadata, uncertainty and validity masks. The `Terrain` class is currently the small in-memory implementation. A future provider can load a resampled local GeoTIFF/COG window and pass the values and provenance into the same planning interface.

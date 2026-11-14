# Jezero DEM integration with the existing MARSCOPE planner

The existing backend already provides:
- POST /api/terrain/import-dem to ingest a Mars-projected GeoTIFF and replace the active terrain.
- GET /api/terrain to expose the active grid and geospatial metadata.
- POST /api/routes to run the existing multi-objective A* alternatives and LPA* repair on that active grid.

The Jezero integration adds a curated POI catalogue and GET /api/jezero/pois. When a georeferenced DEM is active, the endpoint converts planetocentric, east-positive POIs into planner-grid cells using the active DEM's CRS and bounds. It does not alter or replace the pathfinding algorithm.

## Dataset

USGS Mars 2020 Science Investigation CTX DEM Mosaic:
https://astrogeology.usgs.gov/search/map/mars_2020_science_investigation_ctx_dem_mosaic

Direct GeoTIFF:
https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/M20_JezeroCrater_CTXDEM_20m.tif

Nominal resolution 20 m/pixel; elevation values in metres. Keep the original file outside Git and upload it to the running backend through the existing DEM-import endpoint. The importer accepts up to 250 MB.

## Import sequence

1. Install backend/requirements-geospatial.txt in addition to the backend requirements.
2. Start the FastAPI backend.
3. Upload the USGS GeoTIFF as multipart field file to POST /api/terrain/import-dem. Use width=192, height=192, and vertical_units=m for the first demo import.
4. Confirm GET /api/terrain reports NASA_OR_USER_SUPPLIED_GEOREFERENCED_DEM.
5. Call GET /api/jezero/pois; check each POI's mapping status before offering it as a route endpoint.
6. Use the returned {x,y} grid coordinates as the start and goal in the existing /api/routes request.

The 192 x 192 grid is a demonstration planning grid resampled from the regional DEM. It does not retain 20 m route-cell resolution; report the effective cell_size_m returned by the API. The original 20 m GeoTIFF remains the source for higher-resolution map/elevation inspection.

## Coordinate policy and limitations

- POI latitudes in pois.json are planetocentric; longitudes are positive east.
- The POI converter uses the ellipsoid in the active projected CRS to convert planetocentric to planetographic latitude before projection.
- The converter requires a projected CRS with a geographic base CRS and valid bounds. It does not assume EPSG:3857 or an Earth datum.
- Neretva Vallis and Western Delta Area coordinates are approximate scene markers, not surveyed centroids.
- The Perseverance landing site is a historical landing coordinate, not the rover's current position.
- A mapped grid cell can still be NoData/blocked or exceed the planner's slope threshold. Check terrain obstacles before route planning.
- The DEM supplies elevation-derived slope and roughness only. Radiation, temperature, atmosphere, regolith, mineralogy and science layers remain unavailable unless independently imported and spatially registered.
- This is a research/demo route planner, not certified navigation or a guarantee of surface safety.

# Jezero Crater Digital Elevation Model

**Primary dataset:** USGS Astrogeology Science Center, Mars 2020 Science Investigation CTX DEM Mosaic.

- Product page: https://astrogeology.usgs.gov/search/map/mars_2020_science_investigation_ctx_dem_mosaic
- Direct GeoTIFF: https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/M20_JezeroCrater_CTXDEM_20m.tif
- Nominal resolution: 20 metres/pixel
- Published dimensions: 4,456 columns x 5,067 rows; one 32-bit band
- Vertical units: metres
- Projection: Mars Equirectangular
- Latitude convention: planetocentric
- Longitude convention: positive east
- Published extent: 17.58–19.29 degrees latitude; 76.99–78.58 degrees east
- Published planetary radius: 3,396,160 m. The inspected GeoTIFF's embedded CRS reports a 3,396,190 m radius; preserve the embedded CRS and document the 30 m metadata discrepancy.

The mosaic combines the original Mars 2020 Jezero CTX terrain-relative-navigation DEM with additional stereo-derived DEM coverage. It is a regional planning surface, not a guarantee of local obstacle detection.

## Use with MARSCOPE

The existing backend has a GeoTIFF importer and terrain pipeline. Do not duplicate the A* algorithm or replace the planner. Import the GeoTIFF through POST /api/terrain/import-dem, then use GET /api/jezero/pois to convert curated geographic POIs into active planner-grid cells.

For the first demo, use a 192 x 192 planning grid and report the effective cell_size_m returned by the API. This is a resampled regional grid, not 20 m route-cell resolution. Keep the original GeoTIFF unchanged and outside Git.

## Important limitations

- Inspect the actual GeoTIFF CRS, affine transform, units, NoData and pixel orientation before import.
- The source product uses planetocentric latitude and east-positive longitude. Do not silently interpret planetocentric latitude as planetographic.
- The USGS product page does not provide one universal per-pixel vertical error value.
- Slope and roughness derived from the 20 m DEM do not resolve every small rock or local hazard.
- A DEM alone does not provide measured radiation, temperature, atmosphere, regolith or science targets.
- A route generated from this product is a research/demo output, not certified navigation software.

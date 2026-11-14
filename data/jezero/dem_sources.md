# Jezero Crater Digital Elevation Model (DEM)

## Recommended dataset

**Primary dataset:** USGS Astrogeology Science Center, *Mars 2020 Science Investigation CTX DEM Mosaic*.

- Product page: https://astrogeology.usgs.gov/search/map/mars_2020_science_investigation_ctx_dem_mosaic
- Direct GeoTIFF: https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/M20_JezeroCrater_CTXDEM_20m.tif
- Instrument: Mars Reconnaissance Orbiter Context Camera (CTX)
- Product type: digital terrain model (DTM / DEM) mosaic
- Nominal pixel resolution: 20 metres/pixel
- Raster dimensions listed by USGS: 4,456 columns × 5,067 rows
- Raster data: one 32-bit band
- Vertical units: metres
- Projection: Mars Equirectangular
- Latitude convention: planetocentric
- Longitude convention: positive east
- Longitude domain: -180° to 180°
- Planetary radius in USGS metadata: 3,396,160 metres (equatorial and polar radius)
- Geographic extent listed by USGS:
  - Latitude: 17.58° to 19.29°
  - Longitude: 76.99°E to 78.58°E
- Listed external file size: approximately 87 MB

The mosaic combines the original Mars 2020 Jezero CTX terrain-relative-navigation DEM with additional stereo-derived DEM coverage for the wider crater. USGS describes the added DEMs as generated using the Ames Stereo Pipeline and vertically localized to the Mars Orbiter Laser Altimeter (MOLA) dataset. Some horizontal georeferencing was performed in ArcGIS Pro.

## Why this is the default

Use this 20 m/pixel CTX mosaic as the main elevation source for the Jezero planning area. It covers the crater at a manageable file size and is more suitable as a broad-area planning base than a small, very-high-resolution local patch.

A higher-resolution HiRISE DTM can be considered later for a limited area, but it should not replace the CTX mosaic as the default regional DEM.

## Download and inspect before importing

1. Download the GeoTIFF from the direct link above.
2. Check the actual file size and open its metadata before adding it to the application.
3. Confirm the embedded CRS, horizontal units, vertical units, NoData value, raster transform, and pixel orientation.
4. Confirm that the file is north-up and that the importer can interpret its Mars Equirectangular projection.
5. Keep the original GeoTIFF unchanged. Perform any reprojection, clipping, or resampling on a separate working copy.

Do not infer the raster's full CRS definition from the product title alone. Use the GeoTIFF's embedded geospatial metadata and the USGS product metadata as the source of truth.

## Integration notes for MARSWALK

The planner works on grid coordinates, while the map interface works with geographic/projected map coordinates. The DEM's geotransform must therefore be retained so that grid cells can be converted consistently to map coordinates and back.

For a north-up raster, the usual affine mapping from pixel coordinates (x, y) to projected coordinates (E, N) is:

```text
E = c + x * a
N = f + y * e
```

Here, a is the pixel width, e is normally a negative pixel height, and c/f are the upper-left origin terms from the raster transform. This simplified form applies only when the raster has no rotation or skew; use the full affine transform if it does.

Recommended processing sequence:

1. Read the GeoTIFF and its embedded CRS/transform.
2. Verify that its Mars body definition and units are understood by the import pipeline.
3. Clip to the Jezero area needed by the MVP.
4. Resample to the planner's chosen grid size while preserving the transform and extent.
5. Derive slope and roughness from the elevation grid only after handling NoData cells.
6. Mark NoData cells as unknown/blocked according to the planner's explicit policy; do not silently replace them with zero elevation.
7. Store the CRS, transform, bounds, pixel spacing, and source-product identity with the imported terrain.
8. Test known POI coordinates against the raster-to-grid and grid-to-map conversion before displaying routes.

The current importer specification accepts GeoTIFF files up to 250 MB and expects metre-based elevation values and a Mars-compatible projected CRS. The USGS metadata lists a planetary radius of 3,396,160 m, which is close to the 3,396,190 m Mars radius used in the current project notes. Confirm the importer's actual tolerance and CRS validation against the GeoTIFF metadata before relying on a successful import.

## Important limitations

- This is a stereo-derived terrain product, not a guarantee that every cell is equally accurate.
- The USGS metadata reports horizontal positional accuracy as accurate to the control net; it does not provide a single universal per-pixel vertical error value on the product page.
- Slope and roughness calculated from a 20 m grid describe terrain at that scale. They do not resolve every small rock, wheel-scale hazard, or local obstacle.
- A DEM alone does not provide scientifically measured radiation, temperature, trafficability, or subsurface properties. Keep those layers separate and label any simulated or inferred values clearly.
- A route computed from this dataset is a research/demo output, not a certified safe route for a rover or crewed mission.

## Optional higher-resolution data

The Murray Lab at Caltech lists a 1 m/pixel HiRISE DEM mosaic for the Jezero channel/fan area. It is a much larger local dataset (listed at approximately 582 MB) and uses a Mars Equirectangular projection with central longitude and latitude set to zero. It is an optional close-up source, not the default regional DEM.

- Data page: https://murray-lab.caltech.edu/Mars2020/index.html

Check its coverage and metadata before combining it with the CTX mosaic. Do not mosaic datasets solely because both are described as Mars Equirectangular; their exact projection parameters, vertical reference, registration, and pixel transforms must be compatible.

## Sources

- USGS Astrogeology Science Center, *Mars 2020 Science Investigation CTX DEM Mosaic*: https://astrogeology.usgs.gov/search/map/mars_2020_science_investigation_ctx_dem_mosaic
- USGS Astrogeology Science Center, *Mars 2020 Terrain Relative Navigation CTX DTM Mosaic* (background on the original TRN product): https://astrogeology.usgs.gov/search/map/Mars/Mars2020/JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0
- The Murray Lab, Caltech, Mars 2020 Jezero GIS data: https://murray-lab.caltech.edu/Mars2020/index.html

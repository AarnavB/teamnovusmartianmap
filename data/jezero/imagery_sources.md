# NASA Jezero Imagery Sources

## Default imagery: MRO CTX Jezero Mosaic

- Layer ID: `JEZ_ctx_B_soc_008_orthoMosaic_6m_Eqc_latTs0_lon0`
- Resolution: 6 m/pixel
- CRS: Mars Equirectangular, metres
- Coverage (west, south, east, north): 77.1604655, 18.2110274, 77.6991776, 18.7211945
- Intended use: Main map imagery.

## High-detail imagery: MRO HiRISE Jezero Mosaic

- Layer ID: `JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first_dd`
- Resolution: 0.25 m/pixel
- CRS: Geographic Mars coordinates, degrees
- Coverage (west, south, east, north): 77.2229331, 18.3067994, 77.583964, 18.669315
- Intended use: Close-up imagery only where coverage exists.

## Integration Notes

- Use CTX as the default imagery layer.
- Use HiRISE for close-ups where coverage exists.
- These layers use different CRS definitions. Configure each layer with its correct Mars projection.
- Obtain the WMTS endpoint, tile matrix set, styles, and matrix identifiers from NASA GetCapabilities before wiring the layer into the frontend.
- Do not assume Earth Web Mercator (EPSG:3857).
- Handle missing imagery tiles gracefully.
- Treat the bounding boxes above as coverage bounds, not as a substitute for checking tile availability.

## NASA Documentation

https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars

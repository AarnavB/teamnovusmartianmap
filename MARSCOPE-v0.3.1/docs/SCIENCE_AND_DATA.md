# Scientific location, official archives and data integration

**Research snapshot:** 14 November 2026. Archive holdings, endpoints and layer catalogues evolve; the product label and service documentation retrieved at acquisition time are authoritative.

## 1. Study area: Mount Sharp boxwork terrain, Gale Crater

Curiosity has investigated the boxwork terrain in lower Mount Sharp. NASA/JPL describes a network of resistant ridges with hollows between them. Current science interpretations involve groundwater moving through fractures, minerals cementing portions of the fractures, and later erosion exposing the hardened ridges. Curiosity's MAHLI observations also document local nodules. These are evidence-backed scientific targets, but the imagery and articles are not a gridded topographic or traversability database.

Useful source records (also included in the bundled curated evidence file):

- [NASA: Curiosity Surveys the Boxwork Region](https://science.nasa.gov/photojournal/curiosity-surveys-the-boxwork-region/) — Mastcam panorama acquired 26 September 2025; NASA page published 23 February 2026; 179 images; Sol 4671.
- [NASA: Curiosity Studies Nodules on Boxwork Formations](https://science.nasa.gov/photojournal/curiosity-studies-nodules-on-boxwork-formations/) — MAHLI observations acquired 21 August 2025; 50 images across five locations; Sol 4636.
- [NASA/JPL: NASA's Curiosity Rover Sees Martian Spiderwebs Up Close](https://www.jpl.nasa.gov/news/nasas-curiosity-rover-sees-martian-spiderwebs-up-close/) — NASA/JPL article on boxwork morphology and the mission team's interpretation.
- [NASA: Curiosity Views Boxwork Patterns at a Distance](https://science.nasa.gov/photojournal/curiosity-views-boxwork-patterns-at-a-distance/) — Mastcam panorama acquired 22 May 2025; Sol 4536.
- [NASA PDS Geosciences Node: Mars Science Laboratory archive](https://pds-geosciences.wustl.edu/missions/msl/) — official instrument product archive entry point.

The curated file `backend/data/evidence/curiosity_boxwork.json` preserves evidence ID, observation date, publication date, mission, instrument, sol where available, source URL, source summary and limitations. It is a small demonstration corpus, not a complete literature review.

## 2. Official data systems and their actual role

### NASA Planetary Data System (PDS)

- Home: <https://pds.nasa.gov/>
- PDS Search API guide: <https://nasa-pds.github.io/pds-api/guides/search.html>
- API base used by the adapter: `https://pds.nasa.gov/api/search/1`
- Current integration: free-text product search and product-ID/LID resolution through the documented products endpoint.
- Returns archive discovery metadata. It does not mean every PDS3 product, every node file, or every mission product is represented in one complete indexed response.
- Original product label, detached label, product documentation and instrument SIS must be used to interpret units, processing level, coordinates and array structure.

### PDS Geosciences Node Orbital Data Explorer (ODE)

- Portal: <https://ode.rsl.wustl.edu/mars/>
- REST manual: <https://oderest.rsl.wustl.edu/ODE_REST_V2.1.6.pdf>
- REST base used by the adapter: `https://oderest.rsl.wustl.edu/live2`
- Current integration: Mars product footprint discovery for MRO HiRISE, CTX and CRISM, using instrument identifiers and bounding-box intersection queries; responses preserve product metadata and file/label URLs.
- ODE product-type codes are instrument- and archive-specific. Current defaults (HiRISE RDRV11, CTX EDR, CRISM TRDR) are discovery starting points, not an exhaustive list. Use ODE's product type metadata/IIPT and the product label before choosing a file.
- Product footprints are essential. A product being “from Gale” does not prove that it covers the selected boxwork location.

### NASA/JPL Mars Trek WMTS

- Mars layer catalog / docs: <https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars>
- Current integration: GetCapabilities retrieval, parsing of service-provided layer, style, matrix-set, tile matrix and URL template information, followed by bounded tile caching.
- A listed layer called `curiosity_hirise_mosaic` has catalogue bounds approximately 137.1224669°E–137.7298129°E and 4.9254743°S–4.2489588°S. The catalog lists CRS identifier `urn:ogc:def:crs:EPSG::104905`; inspect capabilities and metadata before assuming the complete projection definition.
- The MOLA/HRSC colour hillshade blend is listed at about 200 m/pixel, and a MOLA hillshade product around 463 m/pixel. These are regional context products, not human-scale obstacle maps.
- WMTS tiles are rendered map imagery, not calibrated elevation or spectral values. Cached tiles currently go into the offline review ZIP; they are **not** yet used as a textured/georeferenced surface in the planner scene.

### HiRISE

- Archive / browse: <https://hirise.lpl.arizona.edu/>
- PDS imaging catalog: <https://www.uahirise.org/catalog/>
- Current integration: discover products through ODE, inspect the original labels, and download supported product files through the allow-listed downloader.
- Example product `TRA_000881_1750` is in Gale Crater (centre approximately 4.866°S, 137.050°E) and has a map-projected image scale near 25 cm/pixel. It must not be assumed to overlap the 2025 boxwork panorama footprint without a geometry intersection check.
- HiRISE image scale is not DEM vertical accuracy. Browse products, map-projected products and stereo-derived DEMs are different data products.

### CTX

- Archive entry point: <https://ode.rsl.wustl.edu/mars/>
- Mars Trek also catalogs a Gale crater CTX mosaic.
- CTX is useful for broader regional image context and coverage screening. Exact pixel scale, projection, processing level and footprint come from the chosen product metadata.
- CTX brightness is not elevation. A single image alone cannot supply slope or roughness.

### MOLA / MGS

- MEGDR information: <https://pds-geosciences.wustl.edu/missions/mgs/megdr.html>
- PDS products include IMG files and labels; available grids have product-specific sampling (including 4, 16, 32, 64 and 128 pixels/degree families).
- Use the label to determine map projection, body figure, vertical datum, pixel spacing and scale. Global MOLA is regional topographic context, not a detector for small rocks or foot placement.

### CRISM / MRO

- PDS ODE: <https://ode.rsl.wustl.edu/mars/>
- CRISM archive help: <https://ode.rsl.wustl.edu/mars/pagehelp/Content/Missions_Instruments/Mars%20Reconnaissance%20Orbiter%20(MRO)/CRISM/CRISM.htm>
- CRISM products include EDR/CDR, TRDR/TER, map-projected MTRDR/MRDR, spectral cubes and derived browse/summary products.
- Instrument spectral range is approximately 0.362–3.92 μm. Spatial sampling depends on observation mode; targeted data and multispectral mapping products can have very different resolutions.
- A calibrated spectral signature is mineralogical evidence with a processing chain and uncertainty. It is not direct proof of a mineral in every individual rock, and it should not be converted to “science potential” without a documented classifier and calibration.

### Curiosity REMS and RAD

- MSL archive: <https://pds-geosciences.wustl.edu/missions/msl/>
- REMS is archived through the PDS Atmospheres Node: <https://pds-atmospheres.nmsu.edu/>
- RAD is archived through the PDS Planetary Plasma Interactions Node: <https://pds-ppi.igpp.ucla.edu/>
- MSL product archives contain instrument-specific raw, calibrated and derived products; formats vary by instrument and processing level.
- REMS and RAD are point/time observations at the rover. They are imported as station records through explicit CSV column mapping. MARSCOPE does not paint them across a terrain grid or claim they predict future astronaut exposure.
- Sol, timestamp, units, calibration, quality flags, and localization must be retained from the original source product/SIS. The CSV importer is a transparent convenience ingestion path, not a replacement PDS parser.

### Mars Odyssey THEMIS

- Mars ODE: <https://ode.rsl.wustl.edu/mars/>
- Product formats, resolution and coverage depend on instrument and observation type. Thermal inertia / spectral context can be relevant only after checking product footprint, calibration and local overlap.
- It is not an hourly local weather forecast.

### Mars 2020 / Perseverance

- PDS archive: <https://pds-geosciences.wustl.edu/missions/mars2020/>
- Useful as a modern mission archive and UI/reference workflow. Perseverance operates in Jezero Crater, not Gale Crater, so its local observations must not be shown as Mount Sharp observations.
- The user-supplied Perseverance raw-image gallery is a separate mission archive, not Curiosity data.

### USGS–NASA planetary geology

- USGS Planetary Geologic Mapping: <https://astrogeology.usgs.gov/>
- Mapping standards and map resources: <https://www.usgs.gov/special-topics/planetary-geologic-mapping>
- Published quadrangle coverage, map scale, projection, units and legend differ by product. A global geological map is not a fine-scale boxwork classification raster.

### NASA Worldview

- <https://worldview.earthdata.nasa.gov/>
- Worldview is Earth-focused. MARSCOPE does not use it as a Mars image, atmosphere, weather or terrain feed. It is a design/interaction reference only.

## 3. CRS, datum and pixel alignment

Mars datasets have used different coordinate conventions, including:

- planetographic latitude with west-positive longitude (common in older maps/products);
- planetocentric latitude with east-positive longitude (used in newer planetary mapping products).

Never merge coordinates because values appear close. Preserve the original CRS WKT and source label text. Keep planetographic/planetocentric latitude and east/west longitude direction explicit.

MARSCOPE recommends planetocentric latitude and east-positive longitude for newly normalized geographic records, but original values/convention remain in provenance. For local path planning, transform only verified overlapping products into one site-centred Mars metric CRS. Record reference-figure axes, projection parameters, origin, operation pipeline and pixel-to-ground spacing. Check that target and source raster footprints intersect before resampling.

The GeoTIFF import guard checks projected metre units and a Mars-sized ellipsoid. That is a screening guard, not a proof of Mars product identity. The user must verify target body, map projection, vertical datum, scale factor, orientation, north/south and east/west convention, and vertical units in the original PDS label/SIS. A CRS may be mislabeled, and a label can contain a projection not represented completely by a simplified EPSG identifier.

## 4. Implemented data workflow

1. **Discover:** PDS Search API or Mars ODE REST metadata query.
2. **Inspect:** open the product record and read the product label, SIS and coverage.
3. **Preserve:** upload the original PDS3/PDS4 label for SHA-256 and raw-text preservation. Parsed fields are convenience extracts only.
4. **Download:** save one file from an allow-listed official HTTPS host; redirects are rechecked, maximum size is 250 MB, and a sidecar stores original/final URL, response headers, size, timestamp and SHA-256.
5. **Prepare:** if the source is PDS IMG/JP2 or another non-GeoTIFF format, convert only with an appropriate planetary-aware GDAL/ISIS workflow, using the original label. The supplied helper prepares an already correctly registered GeoTIFF; it does not calibrate arbitrary PDS binary products.
6. **Import DEM:** map-projected Mars GeoTIFF, projected metres, Mars-sized ellipsoid and explicitly confirmed vertical metres. Derive slope and 3×3 DEM local standard deviation; NoData cells are blocked; unknown auxiliary layers remain unavailable.
7. **Import auxiliary layer:** user explicitly chooses a field, band, source unit and normalization range; the source grid is reprojected to the active DEM grid. Missing coverage increases uncertainty. Normalization is a user mapping, not automatic science calibration.
8. **Import rover tables:** map exact source CSV columns to normalized fields and preserve source CSV bytes/hash. Rover records remain time series.
9. **Export:** create a ZIP containing active terrain, optional plan, catalog/evidence, cached WMTS packages, raw labels, downloaded files and imported observation products.

## 5. Provenance and licensing

Every imported/downloaded product should preserve:

- original product identifier and label bytes/text;
- archive/source URL, access time, checksum and downloaded byte size;
- mission, instrument, observation time/sol, processing level and calibration status;
- target, coordinate convention, CRS WKT, datum/body figure, transform and footprint;
- native resolution, data units, NoData and quality/uncertainty flags;
- processing software/version, resampling, output transform and any user normalization mapping;
- credits and applicable licensing/usage statements.

NASA/PDS and USGS planetary holdings are generally open for use, but follow each product's credit line and archive terms. Partner-generated content and portal imagery may have product-specific attribution requirements. HiRISE pages commonly request NASA/JPL/University of Arizona credit; use the exact product page's requested credit.

## 6. Data that is connected versus not automatically ingested

| Capability | State in 0.3.1 |
|---|---|
| PDS Search API metadata search / resolve | Connected live on demand |
| Mars ODE REST bbox product search | Connected live on demand for HiRISE / CTX / CRISM |
| Mars Trek WMTS layer catalogue / GetCapabilities | Connected live on demand |
| Mars Trek WMTS tile caching | Implemented, bounded, offline ZIP cache |
| Official archive file download | Implemented for allow-listed HTTPS hosts and supported extensions |
| PDS3 / PDS4 label parsing | Lightweight extraction plus exact raw text preservation |
| Mars DEM GeoTIFF import | Implemented with CRS/ellipsoid/unit screening |
| Aligned auxiliary raster import | Implemented with explicit layer/band/unit/range mapping |
| REMS / RAD CSV import | Implemented, explicit mapping, rover station only |
| Curiosity observation localization / SPICE pipeline | Not automated |
| Product-specific PDS IMG / JP2 calibration | Not automated |
| CRISM mineralogical classification | Not implemented; import only as a user-interpreted layer |
| WMTS tiles rendered in the 3D route mesh | Not implemented; cache for review only |
| Live spatial Mars atmosphere / wind / dust / radiation model | Not implemented |
| Full PostGIS archive mirror | Not implemented |

The important next scientific milestone is to select one real DEM product (or stereo-derived DEM) whose verified footprint covers the 2025 boxwork study site, then co-register suitable HiRISE / CTX imagery and rover observations using their real labels and SPICE localization. Until that has been completed and independently checked, the included synthetic fixture remains the only default route substrate.

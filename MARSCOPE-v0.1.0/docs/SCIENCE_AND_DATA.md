# Scientific location and dataset research

**Research checked:** 14 November 2026. Archive contents and service metadata can change; re-check source pages and product labels when acquiring data.

## 1. Demonstration location: Mount Sharp, Gale Crater

Mount Sharp is the central layered mountain inside Gale Crater. Curiosity has been climbing its lower slopes since 2014. NASA/JPL describes the boxwork structures as mineral-hardened ridges associated with groundwater moving through bedrock fractures. NASA published Curiosity views from 2025 that show boxwork terrain, ridges and nearby sandy hollows.

Useful verified context:

- [Curiosity captures a view across boxwork terrain while communicating with an orbiter](https://science.nasa.gov/resource/curiosity-captures-mars-landscape-while-talking-to-an-orbiter/) — image acquisition date July 26, 2025; NASA identifies the region as lower Mount Sharp and describes the ridges as hardened by subsurface-water mineral deposits.
- [Curiosity on the Road to Boxwork Formations](https://www.jpl.nasa.gov/images/pia26552-curiosity-on-the-road-to-boxwork-formations/) — Mastcam panorama from Sol 4476, March 9, 2025; NASA/JPL explains that the view near Gould Mesa showed possible first glimpses of boxwork formations.
- [Curiosity Blog: Deciding Where to Dig Into the Boxworks](https://science.nasa.gov/blog/curiosity-blog-sols-4675-4681-deciding-where-to-dig-into-the-boxworks/) — NASA science-team context dated November 13, 2025; describes a bright arcuate ridge, darker sand-filled hollow and Mishe Mokwa butte.

These publications establish scientific context, but they do **not** by themselves provide a human-scale route DEM or a complete set of georeferenced astronaut traversability labels. The demo does not pin an observation to invented grid coordinates.

## 2. Source inventory and acquisition reality

| Source / instrument | Availability and format | Spatial / temporal notes | Intended use and limit |
|---|---|---|---|
| **Mars Trek** | Documented OGC RESTful WMTS services. The catalog explains the GetCapabilities XML, layer style, tile matrix set, zoom matrix, row/column addressing and missing-tile behavior. Tiles are PNG or JPEG depending on service. | Includes a Gale Crater MRO CTX mosaic with listed bbox 135.1842593°E to 139.2413012°E and 6.5732988°S to 2.8077809°S. The same catalog lists global MOLA/HRSC products. | Best first map-service candidate. The CTX layer's listing does not expose its pixel resolution in the indexed entry; inspect service metadata before claiming one. A WMTS is an image-map service, not a raw DEM API. |
| **Mars Trek MOLA + HRSC blend** | WMTS imagery layer. | Listed hillshade blend is about 200 m/pixel. Global product. | Regional relief / visualization; not boot-scale obstacle detection. |
| **HiRISE** | Official archive provides reduced-resolution browse images, JPEG and full-resolution/map-projected JP2 products, labels and related EDR products. | Example Gale product TRA_000881_1750: acquired 2006-10-04, center 4.866°S, 137.050°E, map-projected scale 25 cm/pixel, equirectangular, about 5 km across. This is a Gale product, but its footprint must be checked against the precise boxwork target before using it as local coverage. | Strongest candidate for local optical surface detail where actual coverage exists. HiRISE pages explicitly state that imagery is public domain and request a NASA/JPL/University of Arizona credit line. |
| **CTX** | MRO Context Camera products in the PDS Imaging Node and Mars Trek mosaics. Product/footprint discovery is through PDS and Mars ODE. | Broader swath and lower spatial resolution than HiRISE; exact values depend on the individual observation/product. | Regional context, route corridors and coverage screening. Do not use CTX as boot-scale hazard detection. |
| **MOLA MEGDR** | PDS3 IMG files with detached labels; maintained PDS4 MOLA topography-derived bundle also available. Original PDS3 archive remains available. Mars ODE provides product search and footprint tools. | Global gridded topography at 4, 16, 32, 64 and 128 pixels/degree. The product is accumulated from MOLA altimetry observations over the MGS mission. | Base regional DEM / topographic context. Product label defines map projection, units and sampling. Coarse compared with small rocks or surface texture. |
| **CRISM** | PDS archive accessible through Mars ODE. Product families include EDR/CDR, TRDR/TER, map-projected MTRDR and MRDR products, spectral cubes, summary products and browse imagery. | Instrument covers 0.362–3.92 μm. Targeted full-resolution mode is about 18 m/pixel at 300 km altitude; multispectral survey products can be around 200 m/pixel. Resolution varies by mode and product. | Mineralogical evidence for hydrated / alteration phases. Preserve spectral channels, calibration, product level, map geometry and footprint. CRISM is not direct proof that a specific astronaut-scale rock contains a mineral. |
| **Curiosity / MSL PDS archive** | PDS instrument archives for APXS, ChemCam, CheMin, DAN, Hazcams/Navcams, MAHLI/MARDI/Mastcam, PLACES, RAD, REMS, SAM and other instruments. Product types vary; do not assume one JSON endpoint. | As of 2026-11-14, PDS lists MSL Release 42, published 2026-08-03, covering new raw/derived data from sols 4710–4843. Release 43 is listed for 2026-12-07 and is still future as of the research date. | Primary ground-truth science and local environmental/radiation observations along the rover traverse. Location and observation time must come from product labels, PLACES and SPICE/localization records. Curiosity's data are not a continuous environmental grid across the crater. |
| **REMS** | Separate PDS Atmospheres Node archive linked from the MSL mission archive. | Rover-point/time observations; instrument and product specific. | Weather context at Curiosity's location/time. Do not interpolate across Gale without a model and uncertainty. |
| **RAD** | PDS Planetary Plasma Interactions (PPI) archive linked from the MSL mission archive. | Radiation instrument records at rover location/time; product-specific units and processing. | Historical radiation context and instrument-grounded comparisons. Does not directly define a future astronaut's dose rate. |
| **Mars Odyssey THEMIS** | PDS / Mars ODE instrument archive and product browser. | Product type and resolution vary between infrared/visible products and mapping modes. | Thermal inertia / spectral context where a footprint overlaps; inspect each product label. Not an hourly weather forecast. |
| **Mars 2020 / Perseverance** | PDS bundles with raw, calibrated and derived instrument data; released in recurring batches. | Perseverance operates in Jezero Crater, not Gale Crater. PDS Release 16 (2026-08-11) added sols 1740–1859. | Useful archive and UI workflow reference, but not a local dataset for Mount Sharp. The user-provided raw-image gallery is for Perseverance, not Curiosity. |
| **USGS–NASA Planetary Geologic Mapping** | Published map products and web-based interactive maps, with GIS resources and mapping standards. | Coverage varies by map sheet / quadrangle; inspect map-specific scale, legend, projection and download formats. | Geological context and consistent map symbology. A global map is not a detailed boxwork classification layer. |
| **NASA Worldview** | Earthdata interactive viewer and Earth imagery layers. | Earth-focused, not a Mars surface imagery feed. | Design inspiration only. Not used as a Mars data source. |

### Practical source links

- [NASA Mars Trek WMTS documentation](https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars)
- [NASA Open APIs status and documentation](https://api.nasa.gov/)
- [Mars Orbital Data Explorer](https://ode.rsl.wustl.edu/mars/)
- [MOLA MEGDR PDS Geosciences Node](https://pds-geosciences.wustl.edu/missions/mgs/megdr.html)
- [HiRISE Gale product TRA_000881_1750](https://hirise.lpl.arizona.edu/TRA_000881_1750)
- [CRISM archive help / product discovery](https://ode.rsl.wustl.edu/mars/pagehelp/Content/Missions_Instruments/Mars%20Reconnaissance%20Orbiter%20(MRO)/CRISM/CRISM.htm)
- [Curiosity / MSL PDS archive](https://pds-geosciences.wustl.edu/missions/msl/)
- [USGS Planetary Geologic Mapping](https://www.usgs.gov/special-topics/planetary-geologic-mapping)
- [NASA Perseverance / Mars 2020 PDS archive](https://pds-geosciences.wustl.edu/missions/mars2020/)

## 3. Coordinate reference systems: a critical integration risk

Mars data can use different conventions. The USGS Gazetteer explains that both of the following have been used and are approved for Mars:

- Planetographic latitude with west-positive longitude (traditional convention; common in older maps).
- Planetocentric latitude with east-positive longitude (adopted by USGS and other organizations for newer Mars mapping).

The USGS notes that maps before 2002 generally used planetographic/west longitude, except for products by the MOLA team. Therefore, coordinate values must never be merged just because they look numerically plausible.

MARSCOPE's proposed canonical convention for newly normalized data is planetocentric latitude + east-positive longitude, while retaining the untouched source coordinates/convention in provenance. Each PDS product label or WMTS GetCapabilities/metadata response remains authoritative. For local path planning, transform only the overlapping, verified data into a site-centred Mars metric CRS (for example, an azimuthal-equidistant projection based on a stated Mars reference figure). Store all projection parameters and the transform pipeline in the layer registry.

The Mars Trek catalog identifies an equirectangular layer using `EPSG:104905`, but the layer's full GetCapabilities/metadata must be inspected before treating that identifier as a complete local CRS definition. A per-product map projection in a PDS label may differ from the catalog default.

## 4. Provenance and licensing

- Preserve the original file, detached/attached PDS labels, product ID, DOI where available, acquisition time/sol, instrument, processing level, source URL, file checksum and source coordinate system.
- Keep processing history: tool and version, reprojection parameters, resampling kernel, output transform, nodata rule, clipping bounds and uncertainty propagation.
- HiRISE product pages explicitly state that the hosted images are public domain and request the credit `NASA/JPL-Caltech/UArizona` (or equivalent page-specific credit).
- NASA/USGS government data are generally openly available, but check the specific archive, partner contribution, image credit and product terms rather than assuming every third-party asset on a portal has identical licensing.
- NASA PDS archives are freely searchable/downloadable through the PDS nodes and Mars ODE. ODE is a product search, metadata and download system; it is not a one-layer map API. NASA's Open APIs portal currently notes that the legacy Mars Rover API has been archived; do not build a new data pipeline around old rover API examples. NASA Images API search/asset endpoints can help discover media, but they are not a substitute for product labels, observation geometry or PDS science records.

## 5. What is and is not connected in v0.1

**Connected:** synthetic grid generator, simulated layers, three route policies, route metrics, obstacle replanning, API registry and source links.

**Documented but not yet ingested:** Mars Trek CTX WMTS, MOLA/HRSC, HiRISE JP2, CRISM cubes/summary products, MOLA MEGDR, Curiosity imagery/PLACES, REMS and RAD.

The demo intentionally does not render the downloaded-looking synthetic grid as Gale imagery. The science panel links to an actual NASA/JPL Curiosity context image, but that image is not registered as a geographic overlay.

## 6. First real-data acquisition sequence

1. Use Mars ODE Map Search / Product Search with a Gale polygon/point query to discover CTX, HiRISE, CRISM and THEMIS footprints.
2. Export and inspect footprint files and product labels. Confirm the observation footprint intersects the intended boxwork target, not merely the Gale crater boundary.
3. Select a source DEM appropriate for the analysis window. MOLA is the regional base; where a suitable higher-resolution DTM exists, retain it as a separate higher-resolution product with its own uncertainty.
4. Download one manageable HiRISE JP2 and its label, and only a CRISM map-projected product whose footprint and product level are justified.
5. Download Curiosity observations and localization products for the relevant rover sols. Join science products to rover pose/time using archived localization and SPICE products; don't guess coordinates from a photograph.
6. Reproject each source into the local working CRS using its declared coordinate convention. Keep original rasters intact.
7. Build coverage and uncertainty masks before deriving slope / roughness. Never interpret missing coverage as zero slope or safe ground.
8. Benchmark a small clipped window first, compare against original product footprints, then expand.

For a first integration, connect **one confirmed HiRISE DTM/orthorectified product and one aligned CTX background**. The source registry should mark a layer active only after footprint, CRS, pixel scale, nodata and visual alignment checks pass.

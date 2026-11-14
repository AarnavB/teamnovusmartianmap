"""Source registry: verified archive/service facts plus implementation status."""
from __future__ import annotations

DATASETS = [
    {
        "id": "mars-trek-gale-ctx", "name": "MRO CTX Gale Crater Mosaic", "mission": "Mars Reconnaissance Orbiter",
        "instrument": "CTX", "access_type": "OGC WMTS map service", "format": "WMTS tiles (PNG/JPEG per capabilities)",
        "coverage": "135.1842593°E to 139.2413012°E; 6.5732988°S to 2.8077809°S (service listing bbox)",
        "crs": "Layer listing identifies EPSG:104905; inspect GetCapabilities and layer metadata before reprojection.",
        "resolution": "Not specified in the cited layer listing; query service metadata.", "observation_date": "Mosaic product; individual source observations vary",
        "units": "Image intensity / display values", "availability": "Documented service; endpoint/capabilities must be resolved from Mars Trek catalog",
        "use": "Regional image context and geospatial backdrop, not human-scale obstacle detection.",
        "url": "https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars",
        "implementation": "DOCUMENTED_NOT_CONNECTED_IN_DEMO",
    },
    {
        "id": "mola-hrsc-global", "name": "MOLA + HRSC Global Hillshade Blend", "mission": "MGS / Mars Express",
        "instrument": "MOLA / HRSC", "access_type": "OGC WMTS map service", "format": "WMTS tiles",
        "coverage": "Global Mars", "crs": "Mars Trek layer listing: EPSG:104905; verify full service metadata.",
        "resolution": "Approximately 200 m/pixel for the listed blend", "observation_date": "Multi-mission mosaic",
        "units": "Rendered hillshade / color relief", "availability": "Documented in Mars Trek WMTS catalog",
        "use": "Regional relief and overview only; far too coarse for boot-scale obstacles.",
        "url": "https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars",
        "implementation": "DOCUMENTED_NOT_CONNECTED_IN_DEMO",
    },
    {
        "id": "hirise-tra-000881-1750", "name": "HiRISE TRA_000881_1750: Gale Crater Interior Deposits", "mission": "Mars Reconnaissance Orbiter",
        "instrument": "HiRISE", "access_type": "Downloadable image products", "format": "JPEG, JPEG2000 (JP2), PDS labels",
        "coverage": "Gale Crater; image centered at 4.866°S, 137.050°E; B&W frame about 5 km across",
        "crs": "Equirectangular map-projected product; original product label is authoritative.",
        "resolution": "25 cm/pixel map-projected scale; original scale range 26.9 cm/pixel (1x1 binning)",
        "observation_date": "2006-10-04", "units": "Image intensity", "availability": "Publicly downloadable from HiRISE site",
        "use": "High-resolution Gale image reference; verify that the actual footprint intersects any target before using it as a local layer.",
        "url": "https://hirise.lpl.arizona.edu/TRA_000881_1750",
        "implementation": "DOCUMENTED_NOT_CONNECTED_IN_DEMO",
    },
    {
        "id": "mola-megdr", "name": "MOLA Mission Experiment Gridded Data Record", "mission": "Mars Global Surveyor",
        "instrument": "MOLA", "access_type": "PDS archive download / ODE discovery", "format": "PDS3 IMG + detached labels; maintained PDS4 bundle also available",
        "coverage": "Global; products are tiled by latitude/longitude and resolution", "crs": "Planetary map projection defined in PDS labels; do not assume Earth EPSG codes.",
        "resolution": "4, 16, 32, 64, and 128 pixels/degree products", "observation_date": "MGS mapping mission accumulation",
        "units": "Topography/radius in label-defined units", "availability": "PDS4 bundle and original PDS3 archive",
        "use": "Regional DEM / elevation context; not sufficient for small rocks or boot-scale hazards.",
        "url": "https://pds-geosciences.wustl.edu/missions/mgs/megdr.html",
        "implementation": "DOCUMENTED_NOT_CONNECTED_IN_DEMO",
    },
    {
        "id": "crism", "name": "CRISM targeted and multispectral products", "mission": "Mars Reconnaissance Orbiter",
        "instrument": "CRISM", "access_type": "PDS archive via Mars ODE", "format": "PDS3/PDS4 products; hyperspectral cubes, map-projected products and browse images",
        "coverage": "Targeted footprints and global/regional multispectral mosaics; inspect observation footprints near Gale",
        "crs": "Product-specific map projection / geometry labels", "resolution": "Targeted full-resolution mode approximately 18 m/pixel at 300 km altitude; multispectral survey products can be around 200 m/pixel; varies by mode",
        "observation_date": "Per observation product", "units": "I/F, Lambert albedo, spectral summary parameters (product-dependent)",
        "availability": "Searchable/downloadable through Mars ODE; not a single raster endpoint",
        "use": "Mineralogical evidence and spectral context; preserve wavelength, calibration and product level.",
        "url": "https://ode.rsl.wustl.edu/mars/pagehelp/Content/Missions_Instruments/Mars%20Reconnaissance%20Orbiter%20(MRO)/CRISM/CRISM.htm",
        "implementation": "DOCUMENTED_NOT_CONNECTED_IN_DEMO",
    },
    {
        "id": "msl-archive", "name": "Mars Science Laboratory / Curiosity archive", "mission": "Mars Science Laboratory",
        "instrument": "Mastcam, Navcam, Hazcam, MAHLI, ChemCam, CheMin, APXS, DAN, SAM, REMS, RAD, PLACES",
        "access_type": "PDS instrument archives / Analyst's Notebook", "format": "Raw and derived image, tabular and instrument-specific products; PDS3/PDS4 varies by bundle",
        "coverage": "Along Curiosity traverse in Gale Crater; spatial context and rover localization are product-dependent",
        "crs": "Rover-local frames and map products; use PLACES/SPICE and labels for localization",
        "resolution": "Instrument-specific; no single archive-wide resolution", "observation_date": "PDS Release 42 (2026-08-03) adds sols 4710–4843; latest release should be rechecked at acquisition time",
        "units": "Instrument-specific", "availability": "PDS data archives; REMS and RAD have separate archive nodes",
        "use": "Actual rover observations, weather and radiation records; keep sol/time, location and product provenance with every record.",
        "url": "https://pds-geosciences.wustl.edu/missions/msl/",
        "implementation": "DOCUMENTED_NOT_CONNECTED_IN_DEMO",
    },
    {
        "id": "worldview", "name": "NASA Worldview", "mission": "NASA Earthdata", "instrument": "Earth-observing satellite products",
        "access_type": "Earth-focused interactive imagery viewer", "format": "Earthdata imagery layers",
        "coverage": "Earth", "crs": "Earth map services", "resolution": "Layer-dependent", "observation_date": "Layer-dependent",
        "units": "Layer-dependent", "availability": "Public web viewer",
        "use": "Design/reference only; not used as a Mars imagery feed.", "url": "https://worldview.earthdata.nasa.gov/",
        "implementation": "NOT_A_MARS_DATA_SOURCE",
    },
]


def get_registry() -> list[dict]:
    return DATASETS

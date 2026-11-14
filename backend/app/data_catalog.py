"""Authoritative data-source and access-method catalog for the MARSCOPE app."""
from __future__ import annotations

SOURCES = [
    {
        "id": "pds-search-api", "name": "NASA Planetary Data System Search API", "organization": "NASA PDS", "kind": "metadata_api",
        "url": "https://pds.nasa.gov/api/search/1/products", "documentation": "https://nasa-pds.github.io/pds-api/guides/search.html",
        "format": "JSON/XML", "coverage": "PDS4 archive registry across PDS nodes", "availability": "public_api",
        "integration": "connected", "description": "Search, resolve and retrieve PDS4 product metadata. Search results are discovery metadata; labels define scientific semantics.",
        "limitations": "PDS API data holdings are federated and the documentation notes that not every archive is fully populated in the search index. Use archive-node products and labels when needed."
    },
    {
        "id": "mars-ode-rest", "name": "Mars Orbital Data Explorer REST", "organization": "NASA PDS Geosciences Node / Washington University", "kind": "metadata_api",
        "url": "https://oderest.rsl.wustl.edu/live2", "documentation": "https://oderest.rsl.wustl.edu/ODE_REST_V2.1.6.pdf",
        "format": "JSON/XML plus product files", "coverage": "Mars orbital products from MRO, MGS, Odyssey, Mars Express and other supported archives", "availability": "public_api",
        "integration": "connected", "description": "Searches product metadata, spatial footprints, observation metadata, browse images and product file URLs.",
        "limitations": "Footprints, instrument/product type codes and actual file links are product dependent. This service is not an astronaut-scale hazard database."
    },
    {
        "id": "mars-trek-wmts", "name": "NASA/JPL Mars Trek WMTS", "organization": "NASA/JPL", "kind": "ogc_wmts",
        "url": "https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars", "documentation": "https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars",
        "format": "WMTS PNG/JPEG tiles", "coverage": "Layer dependent", "availability": "public_service",
        "integration": "capabilities_required", "description": "OGC WMTS layer catalogue. Tile templates, matrix sets, style identifiers, formats and bounds must be read from GetCapabilities.",
        "limitations": "MARSCOPE does not hard-code an unverified tile URL. Rendered map tiles are not equivalent to calibrated science rasters."
    },
    {
        "id": "hirise-pds", "name": "HiRISE archive", "organization": "NASA/JPL / University of Arizona / PDS Imaging Node", "kind": "product_archive",
        "url": "https://hirise.lpl.arizona.edu/", "documentation": "https://www.uahirise.org/catalog/",
        "format": "PDS labels, JP2, GeoTIFF and browse imagery depending on product", "coverage": "Targeted image footprints", "availability": "public_archive",
        "integration": "discoverable_via_ode", "description": "High-resolution orbital observations; use ODE footprint search and inspect exact product label for map projection, pixel scale and radiometry.",
        "limitations": "HiRISE coverage is targeted and discontinuous. A 25 cm/pixel image is not proof of 25 cm terrain elevation or obstacle detectability."
    },
    {
        "id": "ctx-archive", "name": "MRO Context Camera archive", "organization": "NASA/JPL / PDS Geosciences Node", "kind": "product_archive",
        "url": "https://ode.rsl.wustl.edu/mars/", "documentation": "https://oderest.rsl.wustl.edu/ODE_REST_V2.1.6.pdf",
        "format": "PDS products; browse images and label-defined raster products", "coverage": "Near-global coverage with image-specific footprints", "availability": "public_archive",
        "integration": "discoverable_via_ode", "description": "Regional image context and stereo/derived products where available.",
        "limitations": "Image brightness is not elevation. CTX imagery alone cannot supply slope or roughness."
    },
    {
        "id": "crism-archive", "name": "MRO CRISM archive", "organization": "NASA/JPL / PDS Geosciences Node", "kind": "spectral_archive",
        "url": "https://pds-geosciences.wustl.edu/missions/mro/crism/", "documentation": "https://ode.rsl.wustl.edu/mars/",
        "format": "PDS3/PDS4 spectral cubes and derived map-projected products", "coverage": "Targeted footprints and product-dependent mapping", "availability": "public_archive",
        "integration": "discoverable_via_ode", "description": "Mineralogical and spectral context; calibrated products and wavelength metadata must remain attached.",
        "limitations": "Spectral detection is not direct field confirmation and CRISM spatial footprints are much coarser than rover-scale structures."
    },
    {
        "id": "mola-archive", "name": "MOLA MEGDR / PEDR", "organization": "NASA/JPL / PDS Geosciences Node", "kind": "topography_archive",
        "url": "https://pds-geosciences.wustl.edu/missions/mgs/megdr.html", "documentation": "https://ode.rsl.wustl.edu/mars/tools.aspx",
        "format": "PDS IMG / gridded data / altimetry tables", "coverage": "Global or regional products depending on product", "availability": "public_archive",
        "integration": "discoverable_via_ode", "description": "Global and regional topographic context, plus point altimetry products.",
        "limitations": "Grid spacing and vertical datum vary by product. Global MOLA is not a boot-scale hazard sensor."
    },
    {
        "id": "msl-archive", "name": "Mars Science Laboratory instrument archive", "organization": "NASA PDS", "kind": "rover_archive",
        "url": "https://pds-geosciences.wustl.edu/missions/msl/", "documentation": "https://pds-geosciences.wustl.edu/missions/msl/",
        "format": "PDS products including images, tables and instrument-specific binary data", "coverage": "Curiosity traverse in Gale Crater", "availability": "public_archive",
        "integration": "pds_discovery_and_explicit_import", "description": "Curiosity images and science data. Instrument archive records are kept separate from orbital products.",
        "limitations": "Rover frames, telemetry time and localization are product-specific. Do not treat a rover observation as a globally registered surface raster without localization provenance."
    },
    {
        "id": "rems-archive", "name": "Curiosity REMS archive", "organization": "NASA PDS Atmospheres Node", "kind": "environment_observations",
        "url": "https://pds-atmospheres.nmsu.edu/", "documentation": "https://pds-geosciences.wustl.edu/missions/msl/",
        "format": "PDS instrument data products and tables", "coverage": "Time series at Curiosity's rover location", "availability": "public_archive",
        "integration": "explicit_tabular_import", "description": "Weather-station observations; source columns and units must be taken from the exact product label and SIS.",
        "limitations": "A point/time measurement is not a spatial weather grid for a human EVA route."
    },
    {
        "id": "rad-archive", "name": "Curiosity RAD archive", "organization": "NASA PDS Planetary Plasma Interactions Node", "kind": "radiation_observations",
        "url": "https://pds-ppi.igpp.ucla.edu/", "documentation": "https://pds-geosciences.wustl.edu/missions/msl/",
        "format": "PDS instrument data products and tables", "coverage": "Time series at Curiosity's rover location", "availability": "public_archive",
        "integration": "explicit_tabular_import", "description": "Measured radiation at Curiosity's location, with product-specific units, cadence and quality flags.",
        "limitations": "Curiosity RAD measurements do not directly create a spatial radiation map for a human route. Preserve units and calibration context."
    },
    {
        "id": "worldview", "name": "NASA Worldview", "organization": "NASA Earthdata", "kind": "reference_only",
        "url": "https://worldview.earthdata.nasa.gov/", "documentation": "https://worldview.earthdata.nasa.gov/",
        "format": "Earth-focused imagery services", "coverage": "Earth", "availability": "public_service",
        "integration": "not_a_mars_data_source", "description": "Potential UI/interaction design reference only.",
        "limitations": "Never use as a Mars imagery, weather or terrain feed."
    }
]


def get_data_catalog() -> list[dict]:
    return SOURCES

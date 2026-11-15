"""The only supported Mars sites and their source DEM products.

A site becomes available to the planner only after a real raster is imported,
its CRS/units are checked, and the site's reference coordinate is inside the
raster footprint. These metadata records are not themselves terrain data.
"""
from __future__ import annotations

MISSION_SITES = {
    "jezero": {
        "name": "Jezero Crater",
        "mission": "Perseverance / Mars 2020",
        "latitude": 18.44463,
        "longitude_east": 77.45088,
        "coordinate_note": "Published Perseverance landing coordinate",
        "dem": {
            "product": "Mars 2020 Science Investigation CTX DEM Mosaic",
            "source": "USGS Astrogeology Science Center",
            "resolution_m": 20.0,
            "format": "GeoTIFF",
            "vertical_units": "m",
            "filename": "M20_JezeroCrater_CTXDEM_20m.tif",
            "url": "https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/M20_JezeroCrater_CTXDEM_20m.tif",
            "documentation": "https://astrogeology.usgs.gov/search/map/mars_2020_science_investigation_ctx_dem_mosaic",
        },
    },
    "gale": {
        "name": "Gale Crater",
        "mission": "Curiosity / Mars Science Laboratory",
        "latitude": -4.59,
        "longitude_east": 137.44,
        "coordinate_note": "Published Curiosity landing-site reference",
        "dem": {
            "product": "30-m HRSC DTM Mosaic of Gale Crater, Mars",
            "source": "University College London / Zenodo",
            "resolution_m": 30.0,
            "format": "GeoTIFF",
            "vertical_units": "m",
            "expected_md5": "1d714f2142a56e962d50d985b7088b13",
            "filename": "hrsc_km09_h1938_h1927_h1916-dtm-mosaic.tif",
            "url": "https://zenodo.org/records/5808354/files/hrsc_km09_h1938_h1927_h1916-dtm-mosaic.tif?download=1",
            "documentation": "https://zenodo.org/records/5808354",
        },
    },
    "meridiani": {
        "name": "Meridiani Planum",
        "mission": "Opportunity / Mars Exploration Rover",
        "latitude": -2.05,
        "longitude_east": 354.5,
        "coordinate_note": "Centre coordinate of the published Opportunity-area HiRISE DTM footprint; this is not the rover landing coordinate",
        "dem": {
            "product": "Possible Opportunity Rover Landing Site HiRISE DTM",
            "source": "NASA/JPL / University of Arizona HiRISE",
            "resolution_m": 1.01,
            "format": "PDS3 IMG",
            "vertical_units": "m",
            "filename": "DTEEC_001414_1780_001612_1780_U01.IMG",
            "url": "https://hirise.lpl.arizona.edu/PDS/DTM/PSP/ORB_001400_001499/PSP_001414_1780_PSP_001612_1780/DTEEC_001414_1780_001612_1780_U01.IMG",
            "documentation": "https://hirise.lpl.arizona.edu/dtm/dtm.php?ID=PSP_001414_1780",
        },
    },
    "elysium": {
        "name": "Elysium Planitia",
        "mission": "InSight",
        "latitude": 4.502,
        "longitude_east": 135.623,
        "coordinate_note": "Published InSight lander location; source DEM uses planetocentric latitude and positive-east longitude",
        "dem": {
            "product": "CTX Digital Terrain Model of Mars InSight Landing Site Ellipse 9 Center",
            "source": "USGS Astrogeology Science Center",
            "resolution_m": 20.2358,
            "format": "GeoTIFF",
            "vertical_units": "m",
            "filename": "F02_036761_1828_F04_037262_1841_20m_DTM_destripe.tif",
            "url": "https://planetarymaps.usgs.gov/mosaic/insight_landing_site_dtm/F02_036761_1828_F04_037262_1841_20m_DTM_destripe.tif",
            "documentation": "https://astrogeology.usgs.gov/search/map/ctx_digital_terrain_model_of_mars_insight_landing_site_ellipse_9_center",
        },
    },
}

SUPPORTED_SITE_IDS = frozenset(MISSION_SITES)

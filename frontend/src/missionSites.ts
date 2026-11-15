export type MissionSite = {
  id: string;
  region: string;
  mission: string;
  vehicle: string;
  agency: string;
  feature: string;
  focusLabel: string;
  focus: string;
  latitude: number;
  longitudeEast: number;
  coordinateNote: string;
  coordinateSource: string;
  coordinateSourceUrl: string;
  dem: {
    product: string;
    source: string;
    resolutionM: number;
    format: string;
    fileName: string;
    downloadUrl: string;
    documentationUrl: string;
    accept: string;
    coverageNote: string;
  };
};

/**
 * Only these four regions are currently supported. Their coordinates describe
 * the published mission landing point, except Meridiani, which is deliberately
 * the centre of the available Opportunity-area DTM footprint. They are map
 * references, not grid coordinates.
 */
export const MISSION_SITES: readonly MissionSite[] = [
  {
    id: 'jezero',
    region: 'Jezero Crater',
    mission: 'Perseverance',
    vehicle: 'Mars 2020 rover',
    agency: 'NASA / JPL',
    feature: 'Perseverance landing area',
    focusLabel: 'Ancient lake + delta',
    focus: 'Explore an ancient lake-and-delta system, sedimentary deposits and rocks that may preserve evidence of past habitability.',
    latitude: 18.44463,
    longitudeEast: 77.45088,
    coordinateNote: 'Published rover landing coordinate',
    coordinateSource: 'NASA Langley · Mars 2020 landing analysis',
    coordinateSourceUrl: 'https://ntrs.nasa.gov/citations/20210024480',
    dem: {
      product: 'Mars 2020 Science Investigation CTX DEM Mosaic',
      source: 'USGS Astrogeology Science Center',
      resolutionM: 20,
      format: 'GeoTIFF',
      fileName: 'M20_JezeroCrater_CTXDEM_20m.tif',
      downloadUrl: 'https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/M20_JezeroCrater_CTXDEM_20m.tif',
      documentationUrl: 'https://astrogeology.usgs.gov/search/map/mars_2020_science_investigation_ctx_dem_mosaic',
      accept: '.tif,.tiff,image/tiff',
      coverageNote: '20 m/pixel CTX stereo DEM mosaic covering Jezero Crater. The raster footprint must include the published Perseverance landing coordinate.',
    },
  },
  {
    id: 'gale',
    region: 'Gale Crater',
    mission: 'Curiosity',
    vehicle: 'Mars Science Laboratory',
    agency: 'NASA / JPL',
    feature: 'Mount Sharp',
    focusLabel: 'Layered sedimentary rocks',
    focus: 'Investigate layered rocks around Mount Sharp to understand how Mars changed from wetter environments to the conditions observed today.',
    latitude: -4.59,
    longitudeEast: 137.44,
    coordinateNote: 'Published landing-site reference',
    coordinateSource: 'PDS Geosciences Node · ODE landing sites',
    coordinateSourceUrl: 'https://ode.rsl.wustl.edu/mars/pagehelp/Content/Missions_Instruments/Landing_Sites.htm',
    dem: {
      product: '30-m HRSC DTM Mosaic of Gale Crater, Mars',
      source: 'University College London / Zenodo',
      resolutionM: 30,
      format: 'GeoTIFF',
      fileName: 'hrsc_km09_h1938_h1927_h1916-dtm-mosaic.tif',
      downloadUrl: 'https://zenodo.org/records/5808354/files/hrsc_km09_h1938_h1927_h1916-dtm-mosaic.tif?download=1',
      documentationUrl: 'https://zenodo.org/records/5808354',
      accept: '.tif,.tiff,image/tiff',
      coverageNote: '30 m/pixel HRSC stereo DTM mosaic, 311.8 MB. Verify that its source footprint includes the Curiosity landing-site reference before use.',
    },
  },
  {
    id: 'meridiani',
    region: 'Meridiani Planum',
    mission: 'Opportunity',
    vehicle: 'Mars Exploration Rover B',
    agency: 'NASA / JPL',
    feature: 'Opportunity traverse / Victoria Crater area',
    focusLabel: 'Hematite-rich plains',
    focus: 'Study hematite-rich plains and sedimentary rocks across the area explored by Opportunity, including the Victoria Crater region.',
    latitude: -2.05,
    longitudeEast: 354.5,
    coordinateNote: 'Centre of the published Opportunity-area DTM footprint; not the rover landing coordinate',
    coordinateSource: 'HiRISE · Possible Opportunity Rover Landing Site DTM',
    coordinateSourceUrl: 'https://hirise.lpl.arizona.edu/dtm/dtm.php?ID=PSP_001414_1780',
    dem: {
      product: 'Possible Opportunity Rover Landing Site HiRISE DTM',
      source: 'NASA/JPL / University of Arizona HiRISE',
      resolutionM: 1.01,
      format: 'PDS3 IMG',
      fileName: 'DTEEC_001414_1780_001612_1780_U01.IMG',
      downloadUrl: 'https://hirise.lpl.arizona.edu/PDS/DTM/PSP/ORB_001400_001499/PSP_001414_1780_PSP_001612_1780/DTEEC_001414_1780_001612_1780_U01.IMG',
      documentationUrl: 'https://hirise.lpl.arizona.edu/dtm/dtm.php?ID=PSP_001414_1780',
      accept: '.img,.IMG',
      coverageNote: '1.01 m/post HiRISE DTM covering part of the area explored by Opportunity. This is a local stereo footprint, not a regional Meridiani mosaic. GDAL must recognize the embedded PDS label/CRS.',
    },
  },
  {
    id: 'elysium',
    region: 'Elysium Planitia',
    mission: 'InSight',
    vehicle: 'Interior Exploration using Seismic Investigations, Geodesy and Heat Transport',
    agency: 'NASA / JPL',
    feature: 'InSight landing region',
    focusLabel: 'Planetary interior + seismology',
    focus: 'Use the InSight landing ellipse as the topographic context for a stationary geophysical mission investigating Marsquakes and the planet’s interior.',
    latitude: 4.502,
    longitudeEast: 135.623,
    coordinateNote: 'Published InSight lander location; aligned with the USGS DEM footprint',
    coordinateSource: 'NASA Science · InSight landing site',
    coordinateSourceUrl: 'https://science.nasa.gov/resource/insights-landing-site-elysium-planitia/',
    dem: {
      product: 'CTX Digital Terrain Model of Mars InSight Landing Site Ellipse 9 Center',
      source: 'USGS Astrogeology Science Center',
      resolutionM: 20.2358,
      format: 'GeoTIFF',
      fileName: 'F02_036761_1828_F04_037262_1841_20m_DTM_destripe.tif',
      downloadUrl: 'https://planetarymaps.usgs.gov/mosaic/insight_landing_site_dtm/F02_036761_1828_F04_037262_1841_20m_DTM_destripe.tif',
      documentationUrl: 'https://astrogeology.usgs.gov/search/map/ctx_digital_terrain_model_of_mars_insight_landing_site_ellipse_9_center',
      accept: '.tif,.tiff,image/tiff',
      coverageNote: 'Approximately 20.24 m/pixel CTX stereo DTM for the InSight landing-site ellipse 9 area.',
    },
  },
];

export const DEFAULT_MISSION_SITE_ID = 'jezero';

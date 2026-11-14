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
};

/**
 * Historic Mars landing-site profiles. Coordinates are landing-site references
 * in planetocentric latitude and east-positive longitude, not planner grid cells.
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
  },
  {
    id: 'gusev',
    region: 'Gusev Crater',
    mission: 'Spirit',
    vehicle: 'Mars Exploration Rover A',
    agency: 'NASA / JPL',
    feature: 'Columbia Hills region',
    focusLabel: 'Volcanic + aqueous history',
    focus: 'Compare volcanic plains and altered rocks for clues about the history of water in and around an ancient impact crater.',
    latitude: -14.5692,
    longitudeEast: 175.4729,
    coordinateNote: 'Cartographic landing-site solution',
    coordinateSource: 'PDS Geosciences Node · ODE landing sites',
    coordinateSourceUrl: 'https://ode.rsl.wustl.edu/mars/pagehelp/Content/Missions_Instruments/Landing_Sites.htm',
  },
  {
    id: 'meridiani',
    region: 'Meridiani Planum',
    mission: 'Opportunity',
    vehicle: 'Mars Exploration Rover B',
    agency: 'NASA / JPL',
    feature: 'Meridiani landing region',
    focusLabel: 'Hematite-rich plains',
    focus: 'Study hematite-rich plains and sedimentary rocks that record past interactions between water and the Martian surface.',
    latitude: -1.9462,
    longitudeEast: 354.4734,
    coordinateNote: 'Cartographic landing-site solution',
    coordinateSource: 'PDS Geosciences Node · ODE landing sites',
    coordinateSourceUrl: 'https://ode.rsl.wustl.edu/mars/pagehelp/Content/Missions_Instruments/Landing_Sites.htm',
  },
  {
    id: 'elysium',
    region: 'Elysium Planitia',
    mission: 'InSight',
    vehicle: 'Interior Exploration using Seismic Investigations, Geodesy and Heat Transport',
    agency: 'NASA / JPL',
    feature: 'InSight landing region',
    focusLabel: 'Planetary interior + seismology',
    focus: 'Use the comparatively smooth plains as the context for a stationary geophysical mission investigating Marsquakes and the planet’s interior.',
    latitude: 4.5,
    longitudeEast: 135.9,
    coordinateNote: 'Approximate landing-site centre',
    coordinateSource: 'NASA Science · InSight landing site',
    coordinateSourceUrl: 'https://science.nasa.gov/resource/insights-landing-site-elysium-planitia/',
  },
  {
    id: 'ares',
    region: 'Ares Vallis',
    mission: 'Mars Pathfinder',
    vehicle: 'Pathfinder lander + Sojourner rover',
    agency: 'NASA / JPL',
    feature: 'Pathfinder landing region',
    focusLabel: 'Ancient outflow-channel deposits',
    focus: 'Explore an ancient outflow-channel landing area and demonstrate rover-based investigation of rocks and surface materials.',
    latitude: 19.095,
    longitudeEast: 326.747,
    coordinateNote: 'Published landing-site reference',
    coordinateSource: 'PDS Geosciences Node · ODE landing sites',
    coordinateSourceUrl: 'https://ode.rsl.wustl.edu/mars/pagehelp/Content/Missions_Instruments/Landing_Sites.htm',
  },
  {
    id: 'chryse',
    region: 'Chryse Planitia',
    mission: 'Viking 1',
    vehicle: 'Viking 1 lander',
    agency: 'NASA',
    feature: 'Viking 1 landing region',
    focusLabel: 'Historic life-detection site',
    focus: 'Explore the historic first successful NASA Mars landing area and the surface context for Viking’s early life-detection experiments.',
    latitude: 22.269,
    longitudeEast: 312.049,
    coordinateNote: 'Published landing-site reference',
    coordinateSource: 'PDS Geosciences Node · ODE landing sites',
    coordinateSourceUrl: 'https://ode.rsl.wustl.edu/mars/pagehelp/Content/Missions_Instruments/Landing_Sites.htm',
  },
  {
    id: 'utopia',
    region: 'Utopia Planitia',
    mission: 'Viking 2',
    vehicle: 'Viking 2 lander',
    agency: 'NASA',
    feature: 'Viking 2 landing region',
    focusLabel: 'Northern plains',
    focus: 'Compare a high-latitude northern-plains landing environment with equatorial and mid-latitude Mars mission sites.',
    latitude: 47.668,
    longitudeEast: 134.28,
    coordinateNote: 'Published landing-site reference',
    coordinateSource: 'PDS Geosciences Node · ODE landing sites',
    coordinateSourceUrl: 'https://ode.rsl.wustl.edu/mars/pagehelp/Content/Missions_Instruments/Landing_Sites.htm',
  },
  {
    id: 'vastitas',
    region: 'Vastitas Borealis',
    mission: 'Phoenix',
    vehicle: 'Phoenix stationary lander',
    agency: 'NASA / JPL',
    feature: 'Phoenix landing region',
    focusLabel: 'Polar soil + water ice',
    focus: 'Investigate high-latitude soil and shallow water-ice evidence in Mars’s northern plains.',
    latitude: 68.22,
    longitudeEast: 234.25,
    coordinateNote: 'Published landing-site reference',
    coordinateSource: 'PDS Geosciences Node · ODE landing sites',
    coordinateSourceUrl: 'https://ode.rsl.wustl.edu/mars/pagehelp/Content/Missions_Instruments/Landing_Sites.htm',
  },
];

export const DEFAULT_MISSION_SITE_ID = 'jezero';

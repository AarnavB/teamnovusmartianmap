export type Point = { x: number; y: number };

export type Target = {
  id: string;
  name: string;
  x: number;
  y: number;
  description: string;
  evidence_status: string;
  science_category: string;
};

export type TerrainData = {
  id: string;
  name: string;
  status: string;
  warning: string;
  width: number;
  height: number;
  cell_size_m: number;
  seed: number;
  elevation_m: number[][];
  slope_deg: number[][];
  roughness: number[][];
  regolith: number[][];
  temperature_c: number[][];
  environment_index: number[][];
  radiation_index: number[][];
  uncertainty: number[][];
  science_potential: number[][];
  obstacle: boolean[][];
  targets: Target[];
  cell_units: string;
  layer_provenance: string;
};

export type RouteMetrics = {
  distance_m: number;
  duration_min: number;
  energy_wh: number;
  terrain_risk_pct: number;
  environment_risk_pct: number;
  radiation_index_pct: number;
  uncertainty_pct: number;
  scientific_value_pct: number;
  return_feasible: boolean;
  return_time_estimate_min: number;
  return_energy_estimate_wh: number;
  nearby_targets: Target[];
  model_note: string;
};

export type Route = {
  id: string;
  profile: 'conservative' | 'balanced' | 'science_first';
  name: string;
  summary: string;
  path: Point[];
  metrics: RouteMetrics;
  search: {
    expanded_nodes: number;
    generated_labels: number;
    pareto_labels_at_goal: number;
    objective_vector: Record<string, number>;
    approximate_frontier: boolean;
  };
  weights: Record<string, number>;
  is_pareto: boolean;
};

export type PlanResponse = {
  plan_id: string;
  terrain_id: string;
  start: Point;
  goal: Point;
  constraints: Record<string, number>;
  routes: Route[];
  incremental_balanced_path: Point[];
  incremental_algorithm: string;
  scientific_note: string;
};

export type ReplanResponse = {
  plan_id: string;
  path: Point[];
  metrics: RouteMetrics;
  obstacle: Point;
  algorithm: string;
  expanded_during_repair: number;
  total_expanded_lifetime: number;
  obstacles_added: Point[];
  notice: string;
};

export type DatasetRecord = {
  id: string;
  name: string;
  mission: string;
  instrument: string;
  access_type: string;
  format: string;
  coverage: string;
  crs: string;
  resolution: string;
  observation_date: string;
  units: string;
  availability: string;
  use: string;
  url: string;
  implementation: string;
};

export type RegistryResponse = {
  datasets: DatasetRecord[];
  common_coordinate_policy: Record<string, string>;
};


export type BenchmarkResult = {
  algorithm: string;
  runtime_ms: number;
  expanded_nodes: number;
  objective_cost: number;
  distance_m: number;
  duration_min: number;
  energy_wh: number;
  terrain_risk_pct: number;
  scientific_value_pct: number;
  return_feasible: boolean;
  path: Point[];
};

"""Uncertainty-aware, multi-objective A* and route analytics.

All hazard/science fields passed to this planner are explicitly synthetic in
this release. The planner is a research demonstrator, not certified guidance.
"""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from typing import Any

from .terrain import Terrain

OBJECTIVES = ("distance", "time", "energy", "terrain_risk", "environment_risk", "radiation", "uncertainty", "science_opportunity_cost")

PROFILES: dict[str, dict[str, float]] = {
    "conservative": {
        "distance": 0.12, "time": 0.06, "energy": 0.07,
        "terrain_risk": 0.30, "environment_risk": 0.12,
        "radiation": 0.08, "uncertainty": 0.20,
        "science_opportunity_cost": 0.05,
    },
    "balanced": {
        "distance": 0.23, "time": 0.12, "energy": 0.13,
        "terrain_risk": 0.18, "environment_risk": 0.11,
        "radiation": 0.08, "uncertainty": 0.10,
        "science_opportunity_cost": 0.05,
    },
    "science_first": {
        "distance": 0.10, "time": 0.06, "energy": 0.06,
        "terrain_risk": 0.15, "environment_risk": 0.08,
        "radiation": 0.08, "uncertainty": 0.10,
        "science_opportunity_cost": 0.37,
    },
}

@dataclass
class MissionConstraints:
    max_slope_deg: float = 22.0
    max_temperature_c: float = -35.0
    eva_limit_minutes: float = 180.0
    energy_budget_wh: float = 180.0
    return_reserve_fraction: float = 0.25
    suit_mass_kg: float = 42.0
    base_speed_mps: float = 0.65

    @classmethod
    def from_dict(cls, values: dict[str, Any] | None) -> "MissionConstraints":
        if not values:
            return cls()
        allowed = {k: v for k, v in values.items() if k in cls.__dataclass_fields__}
        result = cls(**allowed)
        result.max_slope_deg = max(1.0, min(45.0, float(result.max_slope_deg)))
        result.max_temperature_c = min(5.0, max(-100.0, float(result.max_temperature_c)))
        result.eva_limit_minutes = max(10.0, min(600.0, float(result.eva_limit_minutes)))
        result.energy_budget_wh = max(10.0, min(2000.0, float(result.energy_budget_wh)))
        result.return_reserve_fraction = max(0.10, min(0.50, float(result.return_reserve_fraction)))
        result.suit_mass_kg = max(15.0, min(150.0, float(result.suit_mass_kg)))
        result.base_speed_mps = max(0.10, min(1.5, float(result.base_speed_mps)))
        return result

@dataclass
class Label:
    x: int
    y: int
    costs: tuple[float, ...]
    parent: int | None
    alive: bool = True


class MultiObjectiveAStar:
    """A* with a bounded Pareto label set at each grid cell.

    Each label stores an additive vector of normalized, non-negative costs.
    Componentwise dominance removes inferior labels. A profile-weighted scalar
    priority selects a route policy while preserving multiple nondominated
    labels at intermediate cells. The per-cell cap bounds memory and makes the
    result an explicitly approximate Pareto search rather than an exact full
    frontier enumeration.
    """
    def __init__(self, terrain: Terrain, constraints: MissionConstraints, profile: str, max_labels_per_cell: int = 7):
        if profile not in PROFILES:
            raise ValueError(f"Unknown route profile: {profile}")
        self.terrain = terrain
        self.constraints = constraints
        self.profile = profile
        self.weights = PROFILES[profile]
        self.max_labels_per_cell = max_labels_per_cell
        self.expanded = 0
        self.generated = 0

    def _weight(self, costs: tuple[float, ...]) -> float:
        return sum(self.weights[k] * costs[i] for i, k in enumerate(OBJECTIVES))

    def _heuristic(self, x: int, y: int, goal: tuple[int, int]) -> float:
        remaining_cells = math.hypot(goal[0] - x, goal[1] - y)
        lower_bound_distance = remaining_cells * self.terrain.cell_m / self.terrain.max_path_distance_m
        return self.weights["distance"] * lower_bound_distance

    def _dominates(self, a: tuple[float, ...], b: tuple[float, ...], eps: float = 1e-10) -> bool:
        return all(x <= y + eps for x, y in zip(a, b)) and any(x < y - eps for x, y in zip(a, b))

    def _edge_vector(self, x0: int, y0: int, x1: int, y1: int) -> tuple[float, ...] | None:
        t = self.terrain
        c = self.constraints
        if t.is_blocked(x1, y1, c.max_slope_deg, c.max_temperature_c):
            return None
        # Prevent diagonal corner-cutting between two blocked cardinal cells.
        if x1 != x0 and y1 != y0:
            if t.is_blocked(x1, y0, c.max_slope_deg, c.max_temperature_c) or t.is_blocked(x0, y1, c.max_slope_deg, c.max_temperature_c):
                return None
        diagonal = math.hypot(x1 - x0, y1 - y0)
        distance_m = diagonal * t.cell_m
        target_slope = t.slope_deg[y1][x1]
        avg_slope = (t.slope_deg[y0][x0] + target_slope) / 2.0
        avg_rough = (t.roughness[y0][x0] + t.roughness[y1][x1]) / 2.0
        avg_regolith = (t.regolith[y0][x0] + t.regolith[y1][x1]) / 2.0
        avg_env = (t.environment_index[y0][x0] + t.environment_index[y1][x1]) / 2.0
        avg_rad = (t.radiation_index[y0][x0] + t.radiation_index[y1][x1]) / 2.0
        avg_uncertainty = (t.uncertainty[y0][x0] + t.uncertainty[y1][x1]) / 2.0
        science = max(t.science_potential[y0][x0], t.science_potential[y1][x1])

        # Illustrative mobility model, not a validated human-performance model.
        slope_factor = 1.0 + (avg_slope / max(c.max_slope_deg, 1.0)) * 1.8
        mobility_factor = 1.0 + 0.55 * avg_rough + 0.35 * avg_regolith
        speed_mps = c.base_speed_mps / (slope_factor * mobility_factor)
        duration_s = distance_m / max(speed_mps, 0.05)
        mass_factor = c.suit_mass_kg / 42.0
        energy_wh = distance_m * 0.018 * mass_factor * slope_factor * mobility_factor

        # A non-negative opportunity cost: cells close to science targets cost
        # less than passing through scientifically unremarkable cells. No
        # negative reward edge is introduced, preserving A* assumptions.
        max_range = t.max_path_distance_m
        length_fraction = distance_m / max_range
        terrain_risk = _clamp01(0.50 * target_slope / max(c.max_slope_deg, 1.0) + 0.30 * avg_rough + 0.20 * avg_regolith)
        environment_risk = _clamp01(avg_env)
        return (
            distance_m / max_range,
            duration_s / (c.eva_limit_minutes * 60.0),
            energy_wh / c.energy_budget_wh,
            terrain_risk * length_fraction,
            environment_risk * length_fraction,
            avg_rad * length_fraction,
            avg_uncertainty * length_fraction,
            (1.0 - science) * length_fraction,
        )

    def _within_resource_limits(self, costs: tuple[float, ...]) -> bool:
        # Reserve a configurable fraction for contingencies and return travel.
        allowed_fraction = (1.0 - self.constraints.return_reserve_fraction) / 2.0
        return costs[1] <= allowed_fraction and costs[2] <= allowed_fraction

    def search(self, start: tuple[int, int], goal: tuple[int, int]) -> dict[str, Any]:
        t = self.terrain
        c = self.constraints
        if not t.in_bounds(*start) or not t.in_bounds(*goal):
            raise ValueError("Start and destination must be inside the terrain grid")
        if t.is_blocked(*start, c.max_slope_deg, c.max_temperature_c):
            raise ValueError("Starting cell violates a configured hard constraint")
        if t.is_blocked(*goal, c.max_slope_deg, c.max_temperature_c):
            raise ValueError("Destination violates a configured hard constraint")

        labels: list[Label] = [Label(start[0], start[1], (0.0,) * len(OBJECTIVES), None)]
        at_cell: dict[tuple[int, int], list[int]] = {start: [0]}
        queue: list[tuple[float, int, int]] = []
        serial = 0
        heapq.heappush(queue, (self._heuristic(*start, goal), serial, 0))
        goal_label: int | None = None
        self.expanded = 0
        self.generated = 1

        while queue:
            _, _, label_id = heapq.heappop(queue)
            label = labels[label_id]
            if not label.alive:
                continue
            cell_labels = at_cell.get((label.x, label.y), [])
            if label_id not in cell_labels:
                continue
            if (label.x, label.y) == goal:
                goal_label = label_id
                break
            self.expanded += 1

            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                nx, ny = label.x + dx, label.y + dy
                edge = self._edge_vector(label.x, label.y, nx, ny)
                if edge is None:
                    continue
                new_costs = tuple(a + b for a, b in zip(label.costs, edge))
                if not self._within_resource_limits(new_costs):
                    continue
                key = (nx, ny)
                current_ids = at_cell.setdefault(key, [])
                if any(labels[i].alive and self._dominates(labels[i].costs, new_costs) for i in current_ids):
                    continue
                for i in current_ids:
                    if labels[i].alive and self._dominates(new_costs, labels[i].costs):
                        labels[i].alive = False

                current_ids[:] = [i for i in current_ids if labels[i].alive]
                candidate_score = self._weight(new_costs)
                if len(current_ids) >= self.max_labels_per_cell:
                    worst_id = max(current_ids, key=lambda i: self._weight(labels[i].costs))
                    if candidate_score >= self._weight(labels[worst_id].costs):
                        continue
                    labels[worst_id].alive = False
                    current_ids.remove(worst_id)

                new_id = len(labels)
                labels.append(Label(nx, ny, new_costs, label_id))
                current_ids.append(new_id)
                self.generated += 1
                serial += 1
                priority = candidate_score + self._heuristic(nx, ny, goal)
                heapq.heappush(queue, (priority, serial, new_id))

        if goal_label is None:
            raise ValueError("No route satisfies the hard constraints and resource reserve")

        path: list[tuple[int, int]] = []
        cursor: int | None = goal_label
        while cursor is not None:
            lab = labels[cursor]
            path.append((lab.x, lab.y))
            cursor = lab.parent
        path.reverse()
        return {
            "path": path,
            "expanded_nodes": self.expanded,
            "generated_labels": self.generated,
            "pareto_labels_at_goal": len([i for i in at_cell.get(goal, []) if labels[i].alive]),
            "objective_vector": dict(zip(OBJECTIVES, labels[goal_label].costs)),
            "approximate_frontier": True,
        }


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def route_metrics(terrain: Terrain, path: list[tuple[int, int]], constraints: MissionConstraints) -> dict[str, Any]:
    if len(path) < 2:
        return {
            "distance_m": 0.0, "duration_min": 0.0, "energy_wh": 0.0,
            "terrain_risk_pct": 0.0, "environment_risk_pct": 0.0,
            "radiation_index_pct": 0.0, "uncertainty_pct": 0.0,
            "scientific_value_pct": 0.0, "return_feasible": True,
        }
    total_distance = total_time = total_energy = 0.0
    terrain_vals: list[float] = []
    env_vals: list[float] = []
    rad_vals: list[float] = []
    uncertainty_vals: list[float] = []
    science_vals: list[float] = []
    for (x0, y0), (x1, y1) in zip(path[:-1], path[1:]):
        d = math.hypot(x1 - x0, y1 - y0) * terrain.cell_m
        avg_slope = (terrain.slope_deg[y0][x0] + terrain.slope_deg[y1][x1]) / 2.0
        avg_rough = (terrain.roughness[y0][x0] + terrain.roughness[y1][x1]) / 2.0
        avg_reg = (terrain.regolith[y0][x0] + terrain.regolith[y1][x1]) / 2.0
        slope_factor = 1.0 + (avg_slope / max(constraints.max_slope_deg, 1.0)) * 1.8
        mobility_factor = 1.0 + 0.55 * avg_rough + 0.35 * avg_reg
        speed = constraints.base_speed_mps / (slope_factor * mobility_factor)
        total_distance += d
        total_time += d / max(speed, 0.05)
        total_energy += d * 0.018 * (constraints.suit_mass_kg / 42.0) * slope_factor * mobility_factor
        terrain_vals.append(_clamp01(0.50 * avg_slope / max(constraints.max_slope_deg, 1.0) + 0.30 * avg_rough + 0.20 * avg_reg))
        env_vals.append((terrain.environment_index[y0][x0] + terrain.environment_index[y1][x1]) / 2.0)
        rad_vals.append((terrain.radiation_index[y0][x0] + terrain.radiation_index[y1][x1]) / 2.0)
        uncertainty_vals.append((terrain.uncertainty[y0][x0] + terrain.uncertainty[y1][x1]) / 2.0)
        science_vals.append(max(terrain.science_potential[y0][x0], terrain.science_potential[y1][x1]))
    duration_min = total_time / 60.0
    return_budget_min = constraints.eva_limit_minutes * (1.0 - constraints.return_reserve_fraction)
    return_budget_wh = constraints.energy_budget_wh * (1.0 - constraints.return_reserve_fraction)
    return_feasible = (2.0 * duration_min <= return_budget_min) and (2.0 * total_energy <= return_budget_wh)
    avg = lambda xs: (sum(xs) / len(xs) * 100.0) if xs else 0.0
    science_score = avg(science_vals)
    nearby_targets = []
    for target in terrain.targets:
        best = min(math.hypot(target["x"] - x, target["y"] - y) for x, y in path)
        if best <= 4.5:
            nearby_targets.append({**target, "path_distance_cells": round(best, 1)})
    return {
        "distance_m": round(total_distance, 1),
        "duration_min": round(duration_min, 1),
        "energy_wh": round(total_energy, 2),
        "terrain_risk_pct": round(avg(terrain_vals), 1),
        "environment_risk_pct": round(avg(env_vals), 1),
        "radiation_index_pct": round(avg(rad_vals), 1),
        "uncertainty_pct": round(avg(uncertainty_vals), 1),
        "scientific_value_pct": round(science_score, 1),
        "return_feasible": return_feasible,
        "nearby_targets": nearby_targets,
        "return_time_estimate_min": round(duration_min * 2.0, 1),
        "return_energy_estimate_wh": round(total_energy * 2.0, 2),
        "model_note": "Illustrative relative estimates from synthetic inputs; not validated EVA performance or measured Mars exposure.",
    }


def build_route_set(terrain: Terrain, start: tuple[int, int], goal: tuple[int, int], constraints: MissionConstraints) -> list[dict[str, Any]]:
    labels = {
        "conservative": ("A", "CONSERVATIVE", "Risk-and-uncertainty weighted alternative"),
        "balanced": ("B", "BALANCED", "Compromise across movement, risk and science"),
        "science_first": ("C", "SCIENCE-FIRST", "Seek simulated targets without relaxing hard constraints"),
    }
    routes: list[dict[str, Any]] = []
    for profile, (route_id, title, summary) in labels.items():
        search = MultiObjectiveAStar(terrain, constraints, profile).search(start, goal)
        metrics = route_metrics(terrain, search["path"], constraints)
        routes.append({
            "id": route_id, "profile": profile, "name": title, "summary": summary,
            "path": [{"x": x, "y": y} for x, y in search["path"]],
            "metrics": metrics,
            "search": {k: v for k, v in search.items() if k != "path"},
            "weights": PROFILES[profile],
        })
    for route in routes:
        route["is_pareto"] = not any(
            _route_dominates(other["metrics"], route["metrics"])
            for other in routes if other is not route
        )
    return routes


def _route_dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    lower = ("distance_m", "duration_min", "energy_wh", "terrain_risk_pct", "environment_risk_pct", "radiation_index_pct", "uncertainty_pct")
    better_or_equal = all(float(a[k]) <= float(b[k]) for k in lower) and float(a["scientific_value_pct"]) >= float(b["scientific_value_pct"])
    strictly_better = any(float(a[k]) < float(b[k]) for k in lower) or float(a["scientific_value_pct"]) > float(b["scientific_value_pct"])
    return better_or_equal and strictly_better

"""Comparable scalar A*, Dijkstra and distance-only baselines."""
from __future__ import annotations

import heapq
import math
from time import perf_counter
from typing import Any

from .planner import MissionConstraints, MultiObjectiveAStar, PROFILES, route_metrics
from .terrain import Terrain


def scalar_baseline(
    terrain: Terrain,
    start: tuple[int, int],
    goal: tuple[int, int],
    constraints: MissionConstraints,
    algorithm: str,
    profile: str = "balanced",
) -> dict[str, Any]:
    if algorithm not in {"standard_astar", "dijkstra", "distance_only"}:
        raise ValueError("Unsupported baseline algorithm")
    model = MultiObjectiveAStar(terrain, constraints, profile)
    weights = model.weights
    start_time = perf_counter()
    g_score = {(start[0], start[1]): 0.0}
    parent: dict[tuple[int, int], tuple[int, int]] = {}
    resource_score: dict[tuple[int, int], tuple[float, float, float]] = {start: (0.0, 0.0, 0.0)}
    queue: list[tuple[float, float, int, tuple[int, int]]] = []
    serial = 0

    def heuristic(p: tuple[int, int]) -> float:
        if algorithm == "dijkstra":
            return 0.0
        distance = math.hypot(goal[0] - p[0], goal[1] - p[1]) * terrain.cell_m / terrain.max_path_distance_m
        if algorithm == "distance_only":
            return distance
        return weights["distance"] * distance

    heapq.heappush(queue, (heuristic(start), 0.0, serial, start))
    expanded = 0
    found = False
    allowed_fraction = (1.0 - constraints.return_reserve_fraction) / 2.0
    while queue:
        _, current_cost, _, current = heapq.heappop(queue)
        if current_cost > g_score.get(current, math.inf) + 1e-12:
            continue
        if current == goal:
            found = True
            break
        expanded += 1
        x, y = current
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            nxt = (x + dx, y + dy)
            vector = model._edge_vector(x, y, nxt[0], nxt[1])
            if vector is None:
                continue
            if algorithm == "distance_only":
                edge_cost = vector[0]
            else:
                edge_cost = sum(weights[k] * vector[i] for i, k in enumerate(model_objectives()))
            # Enforce the same cumulative outbound resource reserve in all baselines.
            old_path_cost = g_score[current]
            # The path resource totals are reconstructed separately to keep the
            # baseline objective scalar. For feasibility, cache vector resources.
            resources = resource_score.get(current, (0.0, 0.0, 0.0))
            next_resources = (resources[0] + vector[1], resources[1] + vector[2], resources[2] + vector[8])
            if any(value > allowed_fraction for value in next_resources):
                continue
            tentative = old_path_cost + edge_cost
            if tentative + 1e-12 < g_score.get(nxt, math.inf):
                g_score[nxt] = tentative
                parent[nxt] = current
                resource_score[nxt] = next_resources
                serial += 1
                heapq.heappush(queue, (tentative + heuristic(nxt), tentative, serial, nxt))

    runtime_ms = (perf_counter() - start_time) * 1000.0
    if not found:
        raise ValueError(f"{algorithm} found no feasible route")
    path = [goal]
    while path[-1] != start:
        path.append(parent[path[-1]])
    path.reverse()
    metrics = route_metrics(terrain, path, constraints)
    return {
        "algorithm": algorithm,
        "runtime_ms": round(runtime_ms, 3),
        "expanded_nodes": expanded,
        "objective_cost": round(g_score[goal], 7),
        "distance_m": metrics["distance_m"],
        "duration_min": metrics["duration_min"],
        "energy_wh": metrics["energy_wh"],
        "terrain_risk_pct": metrics["terrain_risk_pct"],
        "scientific_value_pct": metrics["scientific_value_pct"],
        "return_feasible": metrics["return_feasible"],
        "path": [{"x": x, "y": y} for x, y in path],
    }


def model_objectives() -> tuple[str, ...]:
    return ("distance", "time", "energy", "terrain_risk", "environment_risk", "radiation", "uncertainty", "science_opportunity_cost", "oxygen")


def benchmark_label_caps(
    terrain: Terrain,
    start: tuple[int, int],
    goal: tuple[int, int],
    constraints: MissionConstraints,
    caps: tuple[int, ...] = (3, 5),
) -> list[dict[str, Any]]:
    """Compare Multi-Objective A* search performance between bounded label capacities."""
    results: list[dict[str, Any]] = []
    for cap in caps:
        shared_cache: dict[tuple[int, int, int, int], tuple[float, ...] | None] = {}
        model = MultiObjectiveAStar(terrain, constraints, "balanced", max_labels_per_cell=cap, edge_cache=shared_cache)
        started = perf_counter()
        search = model.search(start, goal)
        runtime_ms = round((perf_counter() - started) * 1000.0, 3)
        metrics = route_metrics(terrain, search["path"], constraints)
        results.append({
            "algorithm": f"pareto_astar_cap_{cap}",
            "runtime_ms": runtime_ms,
            "expanded_nodes": search.get("expanded_nodes", model.expanded),
            "generated_labels": search.get("generated_labels", model.generated),
            "pareto_labels_at_goal": search.get("pareto_labels_at_goal", 0),
            "max_labels_per_cell": cap,
            "distance_m": metrics["distance_m"],
            "duration_min": metrics["duration_min"],
            "energy_wh": metrics["energy_wh"],
            "terrain_risk_pct": metrics["terrain_risk_pct"],
            "scientific_value_pct": metrics["scientific_value_pct"],
            "return_feasible": metrics["return_feasible"],
            "path": [{"x": x, "y": y} for x, y in search["path"]],
        })
    return results

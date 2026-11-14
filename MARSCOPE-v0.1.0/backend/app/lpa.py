"""Lifelong Planning A* (LPA*) for incremental grid-cost updates."""
from __future__ import annotations

import heapq
import math
from typing import Any

from .planner import MissionConstraints, MultiObjectiveAStar, PROFILES
from .terrain import Terrain


class LPAStar:
    """Forward LPA*: fixed start, fixed goal, changing local edge costs.

    The planner retains g/rhs values across updates and repairs only the
    affected local consistency region. Costs use the balanced policy's
    non-negative scalarization of the same objective vector as MOO-A*.
    """
    def __init__(self, terrain: Terrain, start: tuple[int, int], goal: tuple[int, int], constraints: MissionConstraints):
        self.terrain = terrain
        self.start = start
        self.goal = goal
        self.constraints = constraints
        self.weights = PROFILES["balanced"]
        self.g = [[math.inf for _ in range(terrain.width)] for _ in range(terrain.height)]
        self.rhs = [[math.inf for _ in range(terrain.width)] for _ in range(terrain.height)]
        self.heap: list[tuple[float, float, int, int, int]] = []
        self.versions: dict[tuple[int, int], int] = {}
        self.edge_model = MultiObjectiveAStar(terrain, constraints, "balanced")
        self.serial = 0
        self.expanded = 0
        self.rhs[start[1]][start[0]] = 0.0
        self._enqueue(start)
        self.compute_shortest_path()

    def _heuristic(self, p: tuple[int, int]) -> float:
        d = math.hypot(self.goal[0] - p[0], self.goal[1] - p[1]) * self.terrain.cell_m
        return self.weights["distance"] * d / self.terrain.max_path_distance_m

    def _key(self, p: tuple[int, int]) -> tuple[float, float]:
        x, y = p
        m = min(self.g[y][x], self.rhs[y][x])
        return (m + self._heuristic(p), m)

    def _enqueue(self, p: tuple[int, int]) -> None:
        x, y = p
        version = self.versions.get(p, 0) + 1
        self.versions[p] = version
        if abs(self.g[y][x] - self.rhs[y][x]) > 1e-12:
            k1, k2 = self._key(p)
            self.serial += 1
            heapq.heappush(self.heap, (k1, k2, version, x, y))

    def _top(self) -> tuple[tuple[float, float], tuple[int, int]] | None:
        while self.heap:
            k1, k2, version, x, y = self.heap[0]
            p = (x, y)
            if self.versions.get(p, 0) != version or abs(self.g[y][x] - self.rhs[y][x]) <= 1e-12:
                heapq.heappop(self.heap)
                continue
            current = self._key(p)
            if (k1, k2) != current:
                heapq.heappop(self.heap)
                self._enqueue(p)
                continue
            return ((k1, k2), p)
        return None

    def _neighbors(self, p: tuple[int, int]) -> list[tuple[int, int]]:
        x, y = p
        result = []
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            q = (x + dx, y + dy)
            if self.terrain.in_bounds(*q):
                result.append(q)
        return result

    def _cost(self, p: tuple[int, int], q: tuple[int, int]) -> float:
        # Reuse the very same edge model and policy weights as MOO-A*.
        vector = self.edge_model._edge_vector(p[0], p[1], q[0], q[1])
        if vector is None:
            return math.inf
        return sum(self.weights[k] * vector[i] for i, k in enumerate(adapter_objectives()))

    def _update_vertex(self, p: tuple[int, int]) -> None:
        x, y = p
        if p != self.start:
            candidates = []
            for pred in self._neighbors(p):
                px, py = pred
                edge = self._cost(pred, p)
                if math.isfinite(self.g[py][px]) and math.isfinite(edge):
                    candidates.append(self.g[py][px] + edge)
            self.rhs[y][x] = min(candidates) if candidates else math.inf
        self._enqueue(p)

    def compute_shortest_path(self) -> None:
        goal_key = self._key(self.goal)
        while True:
            top = self._top()
            if top is None:
                break
            top_key, u = top
            goal_key = self._key(self.goal)
            gx, gy = self.goal
            if not (top_key < goal_key or abs(self.rhs[gy][gx] - self.g[gy][gx]) > 1e-12):
                break
            heapq.heappop(self.heap)
            ux, uy = u
            # Invalidate duplicate queue entries for this node.
            self.versions[u] = self.versions.get(u, 0) + 1
            self.expanded += 1
            if self.g[uy][ux] > self.rhs[uy][ux]:
                self.g[uy][ux] = self.rhs[uy][ux]
                for succ in self._neighbors(u):
                    self._update_vertex(succ)
            else:
                self.g[uy][ux] = math.inf
                self._update_vertex(u)
                for succ in self._neighbors(u):
                    self._update_vertex(succ)

    def update_cells(self, changed: list[tuple[int, int]]) -> None:
        affected: set[tuple[int, int]] = set()
        for p in changed:
            affected.add(p)
            affected.update(self._neighbors(p))
        for p in affected:
            self._update_vertex(p)
        self.compute_shortest_path()

    def extract_path(self) -> list[tuple[int, int]]:
        gx, gy = self.goal
        if not math.isfinite(self.g[gy][gx]):
            raise ValueError("No route remains after the update")
        path_rev = [self.goal]
        current = self.goal
        seen = {current}
        max_steps = self.terrain.width * self.terrain.height
        while current != self.start and len(path_rev) <= max_steps:
            best: tuple[float, tuple[int, int]] | None = None
            for pred in self._neighbors(current):
                px, py = pred
                edge = self._cost(pred, current)
                score = self.g[py][px] + edge
                if math.isfinite(score) and (best is None or score < best[0]):
                    best = (score, pred)
            if best is None or best[1] in seen:
                raise ValueError("Could not reconstruct a consistent route")
            current = best[1]
            seen.add(current)
            path_rev.append(current)
        if current != self.start:
            raise ValueError("Path reconstruction exceeded the grid limit")
        return list(reversed(path_rev))


def adapter_objectives() -> tuple[str, ...]:
    # Kept local to avoid exporting implementation details from planner.py.
    return ("distance", "time", "energy", "terrain_risk", "environment_risk", "radiation", "uncertainty", "science_opportunity_cost")

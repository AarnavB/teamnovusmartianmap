"""Deterministic synthetic terrain used for algorithm/UI validation.

This module intentionally does NOT assign the generated grid real Mars
coordinates or present its values as NASA observations.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Terrain:
    width: int
    height: int
    cell_m: float
    elevation_m: list[list[float]]
    slope_deg: list[list[float]]
    roughness: list[list[float]]
    regolith: list[list[float]]
    temperature_c: list[list[float]]
    environment_index: list[list[float]]
    radiation_index: list[list[float]]
    uncertainty: list[list[float]]
    science_potential: list[list[float]]
    obstacle: list[list[bool]]
    targets: list[dict[str, Any]]
    seed: int = 20261114
    available_layers: set[str] = field(default_factory=lambda: {"elevation", "slope", "roughness", "regolith", "temperature", "atmosphere", "radiation", "uncertainty", "science"})
    terrain_id: str = "gale-demo-synthetic-01"
    status: str = "SIMULATED_NOT_GEOREFERENCED"
    warning: str = "Generated terrain for algorithm demonstration only."
    cell_units: str = "synthetic relative metres"
    layer_provenance: str = "Deterministic synthetic fixture."
    coordinate_info: dict[str, Any] = field(default_factory=dict)

    @property
    def max_path_distance_m(self) -> float:
        return math.hypot(self.width - 1, self.height - 1) * self.cell_m * 1.8

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_blocked(self, x: int, y: int, max_slope_deg: float, max_temperature_c: float) -> bool:
        return (
            not self.in_bounds(x, y)
            or self.obstacle[y][x]
            or self.slope_deg[y][x] > max_slope_deg
            or ("temperature" in self.available_layers and self.temperature_c[y][x] > max_temperature_c)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.terrain_id,
            "name": "Synthetic Mount Sharp teaching tile" if self.status == "SIMULATED_NOT_GEOREFERENCED" else "Imported Mars DEM route grid",
            "status": self.status,
            "warning": self.warning,
            "width": self.width,
            "height": self.height,
            "cell_size_m": self.cell_m,
            "seed": self.seed,
            "elevation_m": self.elevation_m,
            "slope_deg": self.slope_deg,
            "roughness": self.roughness,
            "regolith": self.regolith,
            "temperature_c": self.temperature_c,
            "environment_index": self.environment_index,
            "radiation_index": self.radiation_index,
            "uncertainty": self.uncertainty,
            "science_potential": self.science_potential,
            "obstacle": self.obstacle,
            "targets": self.targets,
            "cell_units": self.cell_units,
            "layer_provenance": self.layer_provenance,
            "available_layers": sorted(self.available_layers),
            "coordinate_info": self.coordinate_info,
        }


def _gaussian(x: float, y: float, cx: float, cy: float, sx: float, sy: float) -> float:
    return math.exp(-(((x - cx) ** 2) / (2 * sx * sx) + ((y - cy) ** 2) / (2 * sy * sy)))


def _clamp(v: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, v))


def generate_terrain(width: int = 64, height: int = 64, cell_m: float = 8.0, seed: int = 20261114) -> Terrain:
    """Build a repeatable synthetic tile with ridges, hollows and rough patches."""
    if width < 16 or height < 16:
        raise ValueError("Terrain dimensions must both be at least 16 cells")
    rng = random.Random(seed)
    elevation = [[0.0 for _ in range(width)] for _ in range(height)]
    rough = [[0.0 for _ in range(width)] for _ in range(height)]
    regolith = [[0.0 for _ in range(width)] for _ in range(height)]
    temp = [[0.0 for _ in range(width)] for _ in range(height)]
    env = [[0.0 for _ in range(width)] for _ in range(height)]
    radiation = [[0.0 for _ in range(width)] for _ in range(height)]
    uncertainty = [[0.0 for _ in range(width)] for _ in range(height)]
    science = [[0.0 for _ in range(width)] for _ in range(height)]
    obstacles = [[False for _ in range(width)] for _ in range(height)]

    # Ridges and depressions are visual motifs only; they are not mapped features.
    ridge_specs = [
        (width * 0.28, height * 0.30, width * 0.23, height * 0.055, 18.0),
        (width * 0.65, height * 0.62, width * 0.27, height * 0.065, 14.0),
        (width * 0.48, height * 0.82, width * 0.17, height * 0.045, 10.0),
    ]
    hollow_specs = [
        (width * 0.48, height * 0.32, width * 0.10, height * 0.10, -8.0),
        (width * 0.75, height * 0.40, width * 0.12, height * 0.10, -6.0),
    ]

    for y in range(height):
        for x in range(width):
            base = 4.5 * math.sin(x / 8.0) + 3.2 * math.cos(y / 9.0) + 1.8 * math.sin((x + y) / 5.4)
            ridge = sum(a * _gaussian(x, y, cx, cy, sx, sy) for cx, cy, sx, sy, a in ridge_specs)
            hollows = sum(a * _gaussian(x, y, cx, cy, sx, sy) for cx, cy, sx, sy, a in hollow_specs)
            texture = rng.uniform(-1.25, 1.25)
            elevation[y][x] = base + ridge + hollows + texture
            ridge_texture = max(_gaussian(x, y, cx, cy, sx, sy) for cx, cy, sx, sy, _ in ridge_specs)
            rough[y][x] = _clamp(0.18 + 0.32 * ridge_texture + rng.random() * 0.35)
            regolith[y][x] = _clamp(0.25 + 0.35 * (1.0 - ridge_texture) + rng.random() * 0.25)
            temp[y][x] = -58.0 + 10.0 * math.sin(y / 10.0) + 5.0 * math.cos(x / 11.0)
            env[y][x] = _clamp(0.12 + 0.50 * abs(math.sin(x / 13.0) * math.cos(y / 11.0)) + rng.random() * 0.12)
            radiation[y][x] = _clamp(0.24 + 0.20 * math.sin(x / 14.0) ** 2 + rng.random() * 0.10)
            uncertainty[y][x] = _clamp(0.34 + 0.38 * (1.0 - ridge_texture) + rng.random() * 0.20)

    slope = [[0.0 for _ in range(width)] for _ in range(height)]
    for y in range(height):
        for x in range(width):
            left = elevation[y][max(0, x - 1)]
            right = elevation[y][min(width - 1, x + 1)]
            up = elevation[max(0, y - 1)][x]
            down = elevation[min(height - 1, y + 1)][x]
            dx = (right - left) / (2.0 * cell_m)
            dy = (down - up) / (2.0 * cell_m)
            slope[y][x] = math.degrees(math.atan(math.hypot(dx, dy)))

    # Three explicitly synthetic points of scientific interest. Their positions
    # are grid indices, not real latitude/longitude coordinates.
    target_specs = [
        (int(width * 0.40), int(height * 0.24), "Ridge-network analogue", "Simulated ridge-like target. Use as a stand-in for a boxwork morphology investigation."),
        (int(width * 0.65), int(height * 0.47), "Hollow analogue", "Simulated low-relief hollow. Use to demonstrate comparing ridge and hollow material."),
        (int(width * 0.54), int(height * 0.76), "Nodule-field analogue", "Simulated target cluster. No rover chemical or mineralogical measurement is attached."),
    ]
    targets: list[dict[str, Any]] = []
    for idx, (tx, ty, name, description) in enumerate(target_specs, start=1):
        targets.append({
            "id": f"SIM-T{idx}", "name": name, "x": tx, "y": ty,
            "description": description,
            "evidence_status": "SIMULATED_TARGET_NOT_A_ROVER_OBSERVATION",
            "science_category": ["ridge morphology", "hollow material", "nodule distribution"][idx - 1],
        })
        for yy in range(max(0, ty - 5), min(height, ty + 6)):
            for xx in range(max(0, tx - 5), min(width, tx + 6)):
                influence = _gaussian(xx, yy, tx, ty, 2.4, 2.4)
                science[yy][xx] = max(science[yy][xx], influence)

    # A few fixed rocks are algorithm obstacles; the user can add more dynamically.
    for ox, oy in [
        (int(width * 0.22), int(height * 0.48)),
        (int(width * 0.51), int(height * 0.57)),
        (int(width * 0.79), int(height * 0.70)),
        (int(width * 0.34), int(height * 0.78)),
    ]:
        obstacles[oy][ox] = True

    return Terrain(
        width=width, height=height, cell_m=cell_m, elevation_m=elevation,
        slope_deg=slope, roughness=rough, regolith=regolith,
        temperature_c=temp, environment_index=env, radiation_index=radiation,
        uncertainty=uncertainty, science_potential=science, obstacle=obstacles,
        targets=targets, seed=seed,
        available_layers={"elevation", "slope", "roughness", "regolith", "temperature", "atmosphere", "radiation", "uncertainty", "science"},
        terrain_id="gale-demo-synthetic-01", status="SIMULATED_NOT_GEOREFERENCED",
        warning="Generated terrain for algorithm demonstration only. This is not a geographic crop of Gale Crater and contains no measured NASA elevation or hazard values.",
        cell_units="synthetic relative metres",
        layer_provenance="Generated deterministically by backend/app/terrain.py; values are not actual Mars measurements.",
        coordinate_info={},
    )

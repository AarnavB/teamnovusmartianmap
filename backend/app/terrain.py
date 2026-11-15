"""Terrain data structures and explicitly isolated synthetic test fixtures.

The production API does not generate terrain: it serves only imported,
georeferenced Mars DEMs. generate_terrain remains available solely for tests.
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
    regolith: list[list[float]] | None
    temperature_c: list[list[float]] | None
    environment_index: list[list[float]] | None
    radiation_index: list[list[float]] | None
    uncertainty: list[list[float]] | None
    science_potential: list[list[float]] | None
    obstacle: list[list[bool]]
    targets: list[dict[str, Any]]
    valid_mask: list[list[bool]] | None = None
    seed: int = 20261114
    available_layers: set[str] = field(default_factory=lambda: {"elevation", "slope", "roughness", "regolith", "temperature", "atmosphere", "radiation", "uncertainty", "science"})
    terrain_id: str = "mars-demo-synthetic-01"
    status: str = "SIMULATED_NOT_GEOREFERENCED"
    warning: str = "Generated terrain for algorithm demonstration only."
    cell_units: str = "synthetic relative metres"
    layer_provenance: str = "Deterministic synthetic fixture."
    coordinate_info: dict[str, Any] = field(default_factory=dict)
    site_id: str = "demo"
    site_name: str = "Mars demo site"

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
            or ("temperature" in self.available_layers and self.temperature_c is not None and self.temperature_c[y][x] > max_temperature_c)
        )

    def to_dict(self) -> dict[str, Any]:
        if self.status == "SIMULATED_NOT_GEOREFERENCED":
            display_name = (
                "Synthetic Martian teaching tile"
                if self.site_id == "demo"
                else f"{self.site_name} — synthetic teaching grid"
            )
        else:
            display_name = f"{self.site_name} — imported Mars DEM route grid"
        return {
            "id": self.terrain_id,
            "site_id": self.site_id,
            "site_name": self.site_name,
            "name": display_name,
            "status": self.status,
            "warning": self.warning,
            "width": self.width,
            "height": self.height,
            "cell_size_m": self.cell_m,
            "elevation_m": self.elevation_m,
            "slope_deg": self.slope_deg,
            "roughness": self.roughness,
            "regolith": self.regolith if "regolith" in self.available_layers else None,
            "temperature_c": self.temperature_c if "temperature" in self.available_layers else None,
            "environment_index": self.environment_index if "atmosphere" in self.available_layers else None,
            "radiation_index": self.radiation_index if "radiation" in self.available_layers else None,
            "uncertainty": self.uncertainty if "uncertainty" in self.available_layers else None,
            "science_potential": self.science_potential if "science" in self.available_layers else None,
            "obstacle": self.obstacle,
            "valid_mask": self.valid_mask,
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


def generate_terrain(
    width: int = 64,
    height: int = 64,
    cell_m: float = 8.0,
    seed: int = 20261114,
    *,
    site_id: str = "demo",
    site_name: str = "Mars demo site",
    reference_latitude: float | None = None,
    reference_longitude_east: float | None = None,
) -> Terrain:
    """Build a deterministic synthetic teaching tile, never a site DEM.

    Distinct seeds create different demonstration surfaces for the UI and
    planner tests. The generated cells are not real Martian topography.
    """
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

    # Seeded feature geometry makes each site's teaching tile visibly distinct.
    phase_x = rng.uniform(-math.pi, math.pi)
    phase_y = rng.uniform(-math.pi, math.pi)
    ridge_specs = [
        (width * rng.uniform(0.18, 0.38), height * rng.uniform(0.20, 0.43), width * rng.uniform(0.16, 0.27), height * rng.uniform(0.04, 0.075), rng.uniform(13.0, 24.0)),
        (width * rng.uniform(0.57, 0.82), height * rng.uniform(0.48, 0.72), width * rng.uniform(0.18, 0.30), height * rng.uniform(0.045, 0.085), rng.uniform(10.0, 20.0)),
        (width * rng.uniform(0.32, 0.60), height * rng.uniform(0.70, 0.88), width * rng.uniform(0.12, 0.22), height * rng.uniform(0.035, 0.06), rng.uniform(7.0, 15.0)),
    ]
    hollow_specs = [
        (width * rng.uniform(0.35, 0.55), height * rng.uniform(0.20, 0.43), width * rng.uniform(0.08, 0.15), height * rng.uniform(0.08, 0.15), rng.uniform(-10.0, -5.0)),
        (width * rng.uniform(0.65, 0.84), height * rng.uniform(0.30, 0.53), width * rng.uniform(0.09, 0.16), height * rng.uniform(0.08, 0.14), rng.uniform(-8.0, -4.0)),
    ]

    for y in range(height):
        for x in range(width):
            base = 4.5 * math.sin(x / 8.0 + phase_x) + 3.2 * math.cos(y / 9.0 + phase_y) + 1.8 * math.sin((x + y) / 5.4 + phase_x * 0.35)
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
        terrain_id=f"mars-demo-{site_id}-{seed}", status="SIMULATED_NOT_GEOREFERENCED",
        warning=f"Deterministic synthetic terrain variant for {site_name}. This is not a geographic crop or measured elevation/hazard dataset for this landing site.",
        cell_units="synthetic relative metres",
        layer_provenance=f"Generated by backend/app/terrain.py with seed {seed}; values are not actual Mars measurements.",
        coordinate_info={
            "georeferenced": False,
            "site_reference_latitude": reference_latitude,
            "site_reference_longitude_east": reference_longitude_east,
            "coordinate_note": "Landing-site coordinates are references only and are not mapped to this synthetic grid.",
        },
        site_id=site_id,
        site_name=site_name,
    )



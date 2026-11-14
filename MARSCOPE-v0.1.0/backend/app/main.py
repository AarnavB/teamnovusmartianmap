from __future__ import annotations

import copy
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .benchmarks import scalar_baseline
from .lpa import LPAStar
from .models import BenchmarkRequest, PlanRequest, ReplanRequest
from .planner import MissionConstraints, build_route_set, route_metrics
from .registry import get_registry
from .terrain import Terrain, generate_terrain

app = FastAPI(
    title="MARSCOPE API",
    version="0.1.0",
    description="Research prototype for Mars human-traversal route-planning concepts. It is not certified navigation software.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TERRAIN: Terrain = generate_terrain()
PLAN_SESSIONS: dict[str, dict[str, Any]] = {}

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "project": "MARSCOPE", "release": "0.1.0"}

@app.get("/api/terrain")
def terrain() -> dict[str, Any]:
    return TERRAIN.to_dict()

@app.get("/api/registry")
def registry() -> dict[str, Any]:
    return {
        "datasets": get_registry(),
        "common_coordinate_policy": {
            "recommended_analysis_coordinates": "Local metric working CRS derived from a verified Mars planetary CRS and a site-centred projection.",
            "mars_longitude_latitude": "Preserve planetocentric latitude and east-positive longitude for modern products unless the product label explicitly specifies another convention.",
            "warning": "The synthetic demo tile has no latitude/longitude and cannot be overlaid on orbital imagery.",
        },
    }

@app.post("/api/routes")
def routes(payload: PlanRequest) -> dict[str, Any]:
    start = (payload.start.x, payload.start.y)
    goal = (payload.goal.x, payload.goal.y)
    constraints = MissionConstraints.from_dict(payload.constraints)
    try:
        route_set = build_route_set(TERRAIN, start, goal, constraints)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Retain an LPA* instance for the balanced policy. Later hazard updates
    # repair this graph incrementally rather than rebuilding its search state.
    try:
        session_terrain = copy.deepcopy(TERRAIN)
        incremental = LPAStar(session_terrain, start, goal, constraints)
        incremental_path = incremental.extract_path()
        if not route_metrics(session_terrain, incremental_path, constraints)["return_feasible"]:
            incremental_path = [(p["x"], p["y"]) for p in route_set[1]["path"]]
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Incremental planner could not establish a route: {exc}") from exc
    plan_id = str(uuid.uuid4())
    PLAN_SESSIONS[plan_id] = {
        "terrain": session_terrain,
        "planner": incremental,
        "start": start,
        "goal": goal,
        "constraints": constraints,
        "obstacles_added": [],
    }

    return {
        "plan_id": plan_id,
        "terrain_id": "gale-demo-synthetic-01",
        "start": {"x": start[0], "y": start[1]},
        "goal": {"x": goal[0], "y": goal[1]},
        "constraints": constraints.__dict__,
        "routes": route_set,
        "incremental_balanced_path": [{"x": x, "y": y} for x, y in incremental_path],
        "incremental_algorithm": "Lifelong Planning A* (LPA*) with retained g/rhs state",
        "scientific_note": "All route results are calculated on the deterministic synthetic tile, not on a NASA terrain raster.",
    }

@app.post("/api/replan")
def replan(payload: ReplanRequest) -> dict[str, Any]:
    session = PLAN_SESSIONS.get(payload.plan_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Plan session not found. Generate a new route set first.")
    terrain: Terrain = session["terrain"]
    x, y = payload.obstacle.x, payload.obstacle.y
    if not terrain.in_bounds(x, y):
        raise HTTPException(status_code=422, detail="Obstacle cell is outside the terrain grid")
    if (x, y) in (session["start"], session["goal"]):
        raise HTTPException(status_code=422, detail="Cannot place a simulated obstacle on the start or destination")
    if terrain.obstacle[y][x]:
        raise HTTPException(status_code=409, detail="That cell is already blocked")

    terrain.obstacle[y][x] = True
    planner: LPAStar = session["planner"]
    try:
        before_expanded = planner.expanded
        planner.update_cells([(x, y)])
        path = planner.extract_path()
        metrics = route_metrics(terrain, path, session["constraints"])
        if not metrics["return_feasible"]:
            raise ValueError("Incremental repair found a geometric path, but its estimated out-and-back resources exceed the configured reserve")
    except ValueError as exc:
        terrain.obstacle[y][x] = False
        # Restore the prior graph's local consistency after rolling back.
        planner.update_cells([(x, y)])
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    session["obstacles_added"].append({"x": x, "y": y})
    return {
        "plan_id": payload.plan_id,
        "path": [{"x": px, "y": py} for px, py in path],
        "metrics": metrics,
        "obstacle": {"x": x, "y": y},
        "algorithm": "LPA* incremental repair",
        "expanded_during_repair": planner.expanded - before_expanded,
        "total_expanded_lifetime": planner.expanded,
        "obstacles_added": session["obstacles_added"],
        "notice": "This is a simulated obstacle injection on synthetic terrain. It is not a real hazard report.",
    }


@app.post("/api/benchmark")
def benchmark(payload: BenchmarkRequest) -> dict[str, Any]:
    start = (payload.start.x, payload.start.y)
    goal = (payload.goal.x, payload.goal.y)
    constraints = MissionConstraints.from_dict(payload.constraints)
    try:
        results = [
            scalar_baseline(TERRAIN, start, goal, constraints, "standard_astar"),
            scalar_baseline(TERRAIN, start, goal, constraints, "dijkstra"),
            scalar_baseline(TERRAIN, start, goal, constraints, "distance_only"),
        ]
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "benchmark_scope": "Same synthetic grid, hard constraints, and resource reserve; scalar A*/Dijkstra use balanced weights.",
        "results": results,
        "warning": "Runtime and route comparisons are local synthetic-fixture measurements, not evidence of performance on NASA rasters or field conditions.",
    }

@app.post("/api/reset")
def reset() -> dict[str, str]:
    global TERRAIN
    TERRAIN = generate_terrain()
    PLAN_SESSIONS.clear()
    return {"status": "reset", "terrain_id": "gale-demo-synthetic-01"}

from pydantic import BaseModel, Field


class Point(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)


class PlanRequest(BaseModel):
    site_id: str = "jezero"
    start: Point
    goal: Point
    constraints: dict = Field(default_factory=dict)


class ReplanRequest(BaseModel):
    plan_id: str
    obstacle: Point



class BenchmarkRequest(BaseModel):
    site_id: str = "jezero"
    start: Point
    goal: Point
    constraints: dict = Field(default_factory=dict)


class ConditionUpdateRequest(BaseModel):
    plan_id: str
    cell: Point
    kind: str
    value: float


class SensitivityRequest(BaseModel):
    site_id: str = "jezero"
    start: Point
    goal: Point
    parameter: str = "max_slope_deg"
    values: list[float] = Field(default_factory=lambda: [14.0, 18.0, 22.0, 26.0, 30.0])
    constraints: dict = Field(default_factory=dict)


class WaypointPlanRequest(BaseModel):
    site_id: str = "jezero"
    start: Point
    waypoints: list[Point] = Field(default_factory=list)
    goal: Point
    constraints: dict = Field(default_factory=dict)

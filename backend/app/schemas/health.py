from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str


class ReadinessResponse(BaseModel):
    status: str
    dependencies: dict[str, str]
    limits: dict[str, int]
    demo_mode: bool
    capabilities: dict[str, bool]

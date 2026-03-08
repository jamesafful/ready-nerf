from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any, List

ModelName = Literal[
    "nerfacto",
    "splatfacto",
    "splatfacto-big",
    "vanilla-nerf",
]

class JobCreateResponse(BaseModel):
    job_id: str
    celery_task_id: str

class JobStatus(BaseModel):
    job_id: str
    state: str
    progress: float = 0.0
    message: str = ""
    model: Optional[str] = None
    outputs: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)

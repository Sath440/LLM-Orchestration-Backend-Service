from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from api.models import TaskStatus


class TaskCreate(BaseModel):
    user_id: str
    description: str
    metadata: dict = Field(default_factory=dict)


class TaskResponse(BaseModel):
    id: int
    user_id: str
    description: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    cost: float
    metadata: dict


class TaskStepResponse(BaseModel):
    id: int
    step_index: int
    instruction: str
    status: TaskStatus
    agent_type: str
    cost: float


class TaskDetailResponse(TaskResponse):
    steps: List[TaskStepResponse]


class MemorySearchRequest(BaseModel):
    query: str
    limit: int = 5


class MemorySearchResult(BaseModel):
    id: int
    content: str
    metadata: dict
    distance: float


class MemorySearchResponse(BaseModel):
    results: List[MemorySearchResult]

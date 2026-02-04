import logging

from fastapi import FastAPI, HTTPException
from sqlalchemy import select

from api.config import settings
from api.database import Base, engine, get_session
from api.models import Task
from api.orchestrator import create_task, list_steps, schedule_task
from api.rate_limit import RateLimiter
from api.schemas import (
    MemorySearchRequest,
    MemorySearchResponse,
    MemorySearchResult,
    TaskCreate,
    TaskDetailResponse,
    TaskResponse,
    TaskStepResponse,
)
from memory.long_term import LongTermMemoryStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(settings.app_name)

app = FastAPI(title="Agent Orchestrator", version="1.0.0")
rate_limiter = RateLimiter()
long_term_store = LongTermMemoryStore()


@app.on_event("startup")
async def on_startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await rate_limiter.close()


async def enforce_rate_limit(task_key: str, limit: int) -> None:
    allowed = await rate_limiter.hit(task_key, limit, window_seconds=60)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/tasks", response_model=TaskResponse)
async def submit_task(payload: TaskCreate) -> TaskResponse:
    await enforce_rate_limit(f"user:{payload.user_id}", settings.rate_limit_per_user)
    task = await create_task(payload.user_id, payload.description, payload.metadata)
    schedule_task(task.id)
    logger.info("task_submitted", extra={"task_id": task.id, "user_id": payload.user_id})
    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        description=task.description,
        status=task.status,
        created_at=task.created_at,
        updated_at=task.updated_at,
        cost=task.cost,
        metadata=task.meta,
    )


@app.get("/tasks/{task_id}", response_model=TaskDetailResponse)
async def get_task(task_id: int) -> TaskDetailResponse:
    async with get_session() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
    steps = await list_steps(task_id)
    return TaskDetailResponse(
        id=task.id,
        user_id=task.user_id,
        description=task.description,
        status=task.status,
        created_at=task.created_at,
        updated_at=task.updated_at,
        cost=task.cost,
        metadata=task.meta,
        steps=[
            TaskStepResponse(
                id=step.id,
                step_index=step.step_index,
                instruction=step.instruction,
                status=step.status,
                agent_type=step.agent_type,
                cost=step.cost,
            )
            for step in steps
        ],
    )


@app.post("/memory/search", response_model=MemorySearchResponse)
async def search_memory(payload: MemorySearchRequest) -> MemorySearchResponse:
    await enforce_rate_limit("memory:search", settings.rate_limit_per_task)
    results = await long_term_store.search(payload.query, k=payload.limit)
    return MemorySearchResponse(
        results=[
            MemorySearchResult(
                id=record.embedding_id,
                content=record.content,
                metadata=record.meta,
                distance=distance,
            )
            for record, distance in results
        ]
    )

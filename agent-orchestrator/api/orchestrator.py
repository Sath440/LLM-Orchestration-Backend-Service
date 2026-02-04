import asyncio
from typing import List

from sqlalchemy import select

from agents.agent import (
    mark_step_status,
    mark_task_status,
    resolve_agent,
    update_cost,
)
from api.database import get_session
from api.models import Task, TaskStatus, TaskStep
from planner.planner import assign_agent, decompose_task


async def create_task(user_id: str, description: str, metadata: dict) -> Task:
    async with get_session() as session:
        task = Task(user_id=user_id, description=description, meta=metadata)
        session.add(task)
        await session.flush()
        steps = decompose_task(description)
        for index, instruction in enumerate(steps):
            session.add(
                TaskStep(
                    task_id=task.id,
                    step_index=index,
                    instruction=instruction,
                    agent_type=assign_agent(instruction),
                )
            )
        await session.commit()
        await session.refresh(task)
        return task


async def list_steps(task_id: int) -> List[TaskStep]:
    async with get_session() as session:
        result = await session.execute(select(TaskStep).where(TaskStep.task_id == task_id).order_by(TaskStep.step_index))
        return result.scalars().all()


async def run_task(task_id: int) -> None:
    await mark_task_status(task_id, TaskStatus.running)
    steps = await list_steps(task_id)
    for step in steps:
        try:
            await mark_step_status(step.id, TaskStatus.running)
            agent = await resolve_agent(step)
            await agent.run(step.instruction)
            await update_cost(step.task_id, step.id, 0.01)
            await mark_step_status(step.id, TaskStatus.completed)
        except Exception:
            await mark_step_status(step.id, TaskStatus.failed)
            await mark_task_status(task_id, TaskStatus.failed)
            return
    await mark_task_status(task_id, TaskStatus.completed)


def schedule_task(task_id: int) -> None:
    asyncio.create_task(run_task(task_id))

from dataclasses import dataclass
from typing import Any, Dict

from sqlalchemy import select

from agents.tools import registry
from api.database import get_session
from api.models import ShortTermMemory, Task, TaskStep, TaskStatus, ToolCall
from memory.long_term import LongTermMemoryStore
from memory.short_term import ShortTermMemoryStore


@dataclass
class AgentContext:
    task_id: int
    step_id: int
    agent_type: str


class AgentBase:
    def __init__(self, context: AgentContext) -> None:
        self.context = context
        self.short_term = ShortTermMemoryStore()
        self.long_term = LongTermMemoryStore()

    async def run(self, instruction: str) -> None:
        await self.record_memory("last_instruction", instruction)
        if "remember" in instruction.lower():
            await self.long_term.add_text(instruction, {"task_id": self.context.task_id})
        if "calculate" in instruction.lower():
            await self.call_tool("calculator", {"expression": "1 + 1"})
        await self.record_memory("last_status", "completed")

    async def record_memory(self, key: str, value: str) -> None:
        await self.short_term.write(self.context.task_id, key, value)

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        registry.validate(tool_name)
        response = registry.call(tool_name, arguments)
        async with get_session() as session:
            session.add(
                ToolCall(
                    task_id=self.context.task_id,
                    agent_type=self.context.agent_type,
                    tool_name=tool_name,
                    arguments=arguments,
                )
            )
            await session.commit()
        return response


class ResearchAgent(AgentBase):
    async def run(self, instruction: str) -> None:
        await self.record_memory("research_note", f"Reviewed: {instruction}")
        await super().run(instruction)


class BuilderAgent(AgentBase):
    async def run(self, instruction: str) -> None:
        await self.record_memory("build_note", f"Executing: {instruction}")
        await super().run(instruction)


class GeneralAgent(AgentBase):
    async def run(self, instruction: str) -> None:
        await self.record_memory("general_note", f"Handling: {instruction}")
        await super().run(instruction)


async def resolve_agent(step: TaskStep) -> AgentBase:
    context = AgentContext(task_id=step.task_id, step_id=step.id, agent_type=step.agent_type)
    if step.agent_type == "research":
        return ResearchAgent(context)
    if step.agent_type == "builder":
        return BuilderAgent(context)
    return GeneralAgent(context)


async def update_cost(task_id: int, step_id: int, delta: float) -> None:
    async with get_session() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one()
        task.cost += delta
        step_result = await session.execute(select(TaskStep).where(TaskStep.id == step_id))
        step = step_result.scalar_one()
        step.cost += delta
        await session.commit()


async def mark_step_status(step_id: int, status: TaskStatus) -> None:
    async with get_session() as session:
        result = await session.execute(select(TaskStep).where(TaskStep.id == step_id))
        step = result.scalar_one()
        step.status = status
        await session.commit()


async def mark_task_status(task_id: int, status: TaskStatus) -> None:
    async with get_session() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one()
        task.status = status
        await session.commit()

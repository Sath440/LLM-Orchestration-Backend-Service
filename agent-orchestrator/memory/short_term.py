from sqlalchemy import select

from api.database import get_session
from api.models import ShortTermMemory


class ShortTermMemoryStore:
    async def write(self, task_id: int, key: str, value: str) -> None:
        async with get_session() as session:
            session.add(ShortTermMemory(task_id=task_id, key=key, value=value))
            await session.commit()

    async def read(self, task_id: int, key: str) -> str | None:
        async with get_session() as session:
            result = await session.execute(
                select(ShortTermMemory).where(
                    ShortTermMemory.task_id == task_id, ShortTermMemory.key == key
                )
            )
            record = result.scalar_one_or_none()
            return record.value if record else None

    async def list(self, task_id: int) -> list[ShortTermMemory]:
        async with get_session() as session:
            result = await session.execute(select(ShortTermMemory).where(ShortTermMemory.task_id == task_id))
            return result.scalars().all()

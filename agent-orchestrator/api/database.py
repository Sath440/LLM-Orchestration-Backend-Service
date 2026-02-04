from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from api.config import settings

Base = declarative_base()

engine = create_async_engine(settings.postgres_dsn, future=True, echo=False)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_session():
    async with SessionLocal() as session:
        yield session

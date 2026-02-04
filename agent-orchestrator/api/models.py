import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from api.database import Base


class TaskStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.pending, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cost = Column(Float, default=0.0)
    meta = Column("metadata", JSON, default=dict)

    steps = relationship("TaskStep", back_populates="task", cascade="all, delete-orphan")
    tool_calls = relationship("ToolCall", back_populates="task", cascade="all, delete-orphan")
    memories = relationship("ShortTermMemory", back_populates="task", cascade="all, delete-orphan")


class TaskStep(Base):
    __tablename__ = "task_steps"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    step_index = Column(Integer, nullable=False)
    instruction = Column(Text, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.pending, nullable=False)
    agent_type = Column(String, nullable=False)
    cost = Column(Float, default=0.0)

    task = relationship("Task", back_populates="steps")


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    agent_type = Column(String, nullable=False)
    tool_name = Column(String, nullable=False)
    arguments = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="tool_calls")


class ShortTermMemory(Base):
    __tablename__ = "short_term_memory"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    key = Column(String, nullable=False)
    value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="memories")


class LongTermMemory(Base):
    __tablename__ = "long_term_memory"

    id = Column(Integer, primary_key=True)
    embedding_id = Column(Integer, unique=True, nullable=False)
    content = Column(Text, nullable=False)
    meta = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

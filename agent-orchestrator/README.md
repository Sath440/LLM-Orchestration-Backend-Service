# LLM Agent Orchestration Backend

A production-grade LLM agent orchestration backend built with **FastAPI**, **PostgreSQL**, **Redis**, and **FAISS**, designed to run locally using Docker Compose.

## Architecture

```
agent-orchestrator/
 ├── api/              # FastAPI app, models, orchestration layer
 ├── agents/           # Agent implementations and tool registry
 ├── memory/           # Short/long-term memory abstractions
 ├── planner/          # Task decomposition logic
 ├── eval/             # Evaluation harness (placeholder for future work)
 ├── infra/            # Infrastructure configs (reserved)
 ├── docker-compose.yml
 └── README.md
```

### Key Components

- **FastAPI service** exposes task submission and status endpoints.
- **Planner** decomposes tasks into steps and assigns agents.
- **Agents** execute steps, call tools, and update memory.
- **Short-term memory** stored per task in PostgreSQL.
- **Long-term memory** stored in FAISS with metadata in PostgreSQL.
- **Redis** enforces rate limits and provides coordination hooks.
- **PostgreSQL** stores tasks, steps, memory, tool calls, and cost tracking.

## Running Locally

### Prerequisites

- Docker and Docker Compose

### Startup

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.

## API Usage

### Submit a Task

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo-user",
    "description": "Analyze the requirements and build a plan. Then implement core APIs.",
    "metadata": {"priority": "high"}
  }'
```

### Get Task Status

```bash
curl http://localhost:8000/tasks/1
```

### Search Long-Term Memory

```bash
curl -X POST http://localhost:8000/memory/search \
  -H "Content-Type: application/json" \
  -d '{"query": "requirements", "limit": 3}'
```

## Operational Behavior

- Tasks start in `pending` and transition to `running`, then `completed` or `failed`.
- Each step is executed by a specialized agent.
- Tool calls are validated against a registry and logged in PostgreSQL.
- Cost tracking is maintained per task and per step.
- Rate limiting is enforced per user and per memory search.

## Development

Install dependencies locally:

```bash
pip install -r requirements.txt
```

Run the API without Docker:

```bash
export POSTGRES_DSN=postgresql+asyncpg://orchestrator:orchestrator@localhost:5432/orchestrator
export REDIS_URL=redis://localhost:6379/0
uvicorn api.main:app --reload
```

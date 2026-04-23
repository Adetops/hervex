# HERVEX

An autonomous AI Agent API. Give it a goal. It figures out the rest.

Built by Heritage Adeleke.

---

## What it does

You submit a goal in plain English. HERVEX plans it into tasks, executes each task using real tools, maintains memory across the session, and returns one complete, coherent result — without hand-holding.

## How it works

```
Client → Goal Intake → Planner → Task Queue → Executor
→ Tools → Memory → Aggregator → Final Result → Client
```

## Stack

- **Python** — core language
- **FastAPI** — API framework
- **Groq (llama-3.3-70b)** — LLM for planning and reasoning
- **Celery + Redis** — async background task execution
- **Tavily** — web search tool
- **MongoDB** — persistent storage
- **Loguru** — structured logging

## Project structure

```
hervex/
├── app/
│   ├── agents/        # LLM planner
│   ├── aggregator/    # Final result synthesis
│   ├── core/          # Config, settings, logging, rate limiter
│   ├── db/            # MongoDB connection, documents, collections
│   ├── enums/         # Shared status enumerations
│   ├── exceptions/    # Custom exceptions and global handlers
│   ├── executor/      # Task execution engine
│   ├── memory/        # Redis session context
│   ├── routers/       # API endpoints
│   ├── schemas/       # Pydantic request/response models
│   ├── services/      # Business logic orchestration
│   ├── tasks/         # Celery configuration and task definitions
│   └── tools/         # Tool registry and tool implementations
└── tests/
```

## Setup

```bash
# Clone and install
git clone https://github.com/Adetops/hervex.git
cd hervex
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Fill in your API keys in .env

# Run Redis locally
redis-server

# Terminal 1 — API server
uvicorn app.main:app --reload

# Terminal 2 — Celery worker
celery -A app.tasks.celery_app worker --loglevel=info (if permitted)
celery -A app.tasks.celery_app worker --loglevel=info -P solo (if not permitted)
```

## Usage

**Submit a goal:**
```bash
POST /goals/
{
  "goal": "Research the top 3 Nigerian fintech startups and write an investment summary",
  "priority": "high"
}
```

**Response:**
```json
{
  "session_id": "abc-123",
  "status": "planning",
  "message": "HERVEX has planned 6 tasks. Poll /runs/abc-123 for progress."
}
```

**Poll for result:**
```bash
GET /runs/abc-123
```

When `status` is `completed`, `final_result` contains HERVEX's complete response.

## Run tests

```bash
pytest tests/ -v
```

## Environment variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key |
| `TAVILY_API_KEY` | Tavily search API key |
| `MONGODB_URI` | MongoDB connection string |
| `MONGODB_DB_NAME` | Database name |
| `REDIS_URL` | Redis connection URL |
| `APP_ENV` | development or production |

#!/bin/bash

# Create all directories
mkdir -p app/routers app/schemas app/services app/agents app/executor app/aggregator app/tools app/memory app/tasks app/db/documents app/db/collections app/enums app/exceptions app/core tests

# App root
touch app/__init__.py app/main.py

# Routers
touch app/routers/__init__.py app/routers/goals.py app/routers/runs.py app/routers/health.py

# Schemas
touch app/schemas/__init__.py app/schemas/goal.py app/schemas/task.py app/schemas/run.py

# Services
touch app/services/__init__.py app/services/goal_service.py app/services/agent_service.py app/services/result_service.py

# Agents
touch app/agents/__init__.py app/agents/planner.py

# Executor
touch app/executor/__init__.py app/executor/runner.py

# Aggregator
touch app/aggregator/__init__.py app/aggregator/result.py

# Tools
touch app/tools/__init__.py app/tools/registry.py app/tools/web_search.py

# Memory
touch app/memory/__init__.py app/memory/context.py

# Tasks
touch app/tasks/__init__.py app/tasks/celery_app.py

# DB
touch app/db/__init__.py app/db/connection.py
touch app/db/documents/__init__.py app/db/documents/goal_document.py app/db/documents/task_document.py app/db/documents/run_document.py
touch app/db/collections/__init__.py app/db/collections/goals.py app/db/collections/tasks.py app/db/collections/runs.py

# Enums
touch app/enums/__init__.py app/enums/status.py

# Exceptions
touch app/exceptions/__init__.py app/exceptions/handlers.py

# Core
touch app/core/__init__.py app/core/config.py app/core/settings.py

# Tests
touch tests/__init__.py tests/test_goals.py tests/test_executor.py

# Root files
touch .env .env.example .gitignore README.md requirements.txt

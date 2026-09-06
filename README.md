# Gather — Event & Social API

Gather is an asynchronous REST API that combines event management with a small social graph. Users can create accounts, follow one another, publish posts, join events, and build a feed from followed profiles.

FastAPI exposes interactive documentation automatically after startup:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Implemented features

- Registration and login with JWT access and refresh tokens.
- User profiles, profile updates, followers, and following lists.
- Event creation, editing, deletion, joining, and leaving.
- Posts, comments, event filtering, and a feed from followed users.
- Paginated collection endpoints.
- Redis caching for event lists, with a graceful fallback when Redis is unavailable.
- Per-IP rate limits for authentication and content-changing requests.
- Async SQLAlchemy repositories and Alembic migration support.
- Isolated async tests backed by in-memory SQLite.

## Technology

| Area | Choice |
| --- | --- |
| API | FastAPI, Pydantic 2, Uvicorn |
| Persistence | PostgreSQL 16, SQLAlchemy 2 async, Alembic |
| Cache | Redis 7 |
| Authentication | JWT via `python-jose`, bcrypt password hashing |
| Tests | pytest, pytest-asyncio, HTTPX, aiosqlite |
| Runtime | Python 3.12 and Docker Compose |

## Architecture

```text
app/
  api/v1/          HTTP routes
  services/        business rules and cache coordination
  repositories/    database access
  models/          SQLAlchemy models
  schemas/         Pydantic request and response models
  middleware/      authentication helpers and rate limiting
  config.py        environment-based configuration
  database.py      async engine and session factory
  redis_client.py  Redis connection and fallback behavior
  main.py          FastAPI application and lifecycle
tests/              authentication and event integration tests
alembic/            database migrations
```

Routes stay thin and delegate business rules to services. Services use repository classes for data access, which keeps HTTP handling, domain logic, and persistence separate.

## Quick start with Docker

1. Copy `.env.example` to `.env`.
2. Replace `JWT_SECRET_KEY` and the example database password before any non-local deployment.
3. Start the API, PostgreSQL, and Redis:

```bash
docker compose up --build
```

The API listens on `http://localhost:8000`. Tables are created during application startup.

To stop the stack:

```bash
docker compose down
```

Add `--volumes` only when you intentionally want to remove the local PostgreSQL and Redis data volumes.

## Manual setup

You need Python 3.12, PostgreSQL, and Redis.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

On Windows PowerShell, activate the environment with `.\.venv\Scripts\Activate.ps1`. For a manual installation, set `DATABASE_URL` and `REDIS_HOST` to services reachable from the host machine rather than the Docker service names.

## Configuration

Configuration is loaded from `.env` through Pydantic Settings.

| Variable | Development default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | Docker PostgreSQL URL | Async SQLAlchemy connection string |
| `REDIS_HOST` | `redis` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_DB` | `0` | Redis database index |
| `JWT_SECRET_KEY` | example value | Token signing secret; replace outside local development |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access-token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh-token lifetime |
| `RATE_LIMIT_AUTH_PER_MINUTE` | `10` | Authentication requests per IP and minute |
| `RATE_LIMIT_CONTENT_PER_MINUTE` | `30` | Content writes per IP and minute |
| `DEBUG` | `true` | Enables SQLAlchemy debug output |

## API overview

All application endpoints use the `/api/v1` prefix.

| Area | Routes | Authentication |
| --- | --- | --- |
| Auth | `POST /auth/register`, `/auth/login`, `/auth/refresh` | Public |
| Current user | `GET /users/me`, `PATCH /users/me` | Required |
| Social graph | User lookup, follow, unfollow, followers, following | Mixed |
| Events | CRUD, join, leave | Reads public; writes require a token |
| Posts | CRUD, event filter, followed-users feed | Reads public; writes/feed require a token |
| Comments | Add and list comments for a post | Write requires a token |

The Swagger UI is the canonical request and response reference because it is generated directly from the route and Pydantic definitions.

## Running tests

```bash
pytest tests/ -v
```

Tests replace PostgreSQL with an in-memory SQLite database and reset the schema between test cases. They do not require the Docker services.

## Production notes

The values in `.env.example` and `docker-compose.yml` are development defaults. Before exposing the service, use unique secrets and passwords, restrict CORS to trusted origins, set `DEBUG=false`, and place the API behind TLS.

## License

This repository does not currently include a license file. Contact the repository owner before reusing or redistributing the code.

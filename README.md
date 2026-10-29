# Gather: Event & Social API

Gather is an asynchronous REST API that combines event management with a small social graph. Users can create accounts, follow one another, publish posts, join events, and build a feed from followed profiles.

FastAPI exposes interactive documentation automatically after startup:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Status

Alpha. The repository contains API behavior tests and an optional PostgreSQL/Redis integration suite. See [TESTING.md](TESTING.md) for coverage boundaries and recorded verification results. There is no CI workflow or verified public demo.

## Implemented features

- Registration and login with JWT access and refresh tokens.
- User profiles, profile updates, followers, and following lists.
- Event creation, editing, deletion, joining, and leaving.
- Posts, comments, event filtering, and a feed from followed users.
- Paginated collection endpoints.
- Redis caching for event lists, with fallback on connection failures, timeouts, and invalid cached JSON.
- Per-IP rate limits for authentication and writes to selected endpoints.
- Async SQLAlchemy repositories and Alembic migration support.
- Isolated SQLite tests plus opt-in PostgreSQL migration and Redis cache integration tests.

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
tests/              HTTP behavior tests and isolated infrastructure integration tests
alembic/            database migrations
```

Routes stay thin and delegate business rules to services. Services use repository classes for data access, which keeps HTTP handling, domain logic, and persistence separate.

## Quick start with Docker

Install Git and Docker with the Compose plugin, then clone the repository:

```bash
git clone https://github.com/t91a60/Gather.git
cd Gather
```

Run the following commands from the repository root.

1. Copy `.env.example` to `.env`.
2. Replace `JWT_SECRET_KEY` and the example database password before any non-local deployment.
3. Start the API, PostgreSQL, and Redis:

```bash
docker compose up --build
```

The API listens on `http://localhost:8000`. Tables are created during application startup. The Compose file sets database credentials and overrides `DATABASE_URL`; changing `.env` alone does not change those values. Keep the database service credentials and application URL in sync when editing the Compose configuration.

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
python -m pip install -r requirements.txt
cp .env.example .env
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

For example, list public events with pagination:

```bash
curl 'http://localhost:8000/api/v1/events?page=1&page_size=20'
```

Use the Swagger UI to register, log in, and send authenticated requests. It is generated directly from the route and Pydantic definitions.

## Running tests

Install `requirements.txt` in the virtual environment, then run:

```bash
python -m pytest -q -rs
```

Ordinary tests use a fresh SQLite database in pytest's temporary directory, enable foreign keys, and override request database sessions for each test. They do not read or overwrite `./test.db`. Redis SDK calls are isolated from external services by default. PostgreSQL integration tests skip when their test URL is absent.

Run the full suite against disposable PostgreSQL and Redis services with the separate test stack:

```bash
docker compose -f compose.test.yml run --build --rm tests
docker compose -f compose.test.yml down
```

This stack publishes no host ports and uses separate test storage. Integration tests create and drop uniquely named PostgreSQL databases; the Redis test requires an empty dedicated database. See [TESTING.md](TESTING.md) for environment variables, prerequisites, and test isolation details.

## Production notes

The values in `.env.example` and `docker-compose.yml` are development defaults. Before exposing the service, use unique secrets and passwords, restrict CORS to trusted origins, set `DEBUG=false`, and place the API behind TLS.

Rate limits are held in each application process (`app/middleware/rate_limit.py`), not shared through Redis. Their content-write coverage is limited to the path prefixes listed there, not every authenticated mutation. The Redis fallback handles connection failures, timeouts, and invalid JSON, but not every cache error. Startup uses `create_all`; the presence of Alembic files does not mean startup applies migrations.

## Troubleshooting

- **Database hostname cannot be resolved:** `db` and `redis` are Compose service names. For a host installation, configure reachable hostnames in `.env`.
- **Ports already in use:** the development stack publishes ports 8000, 5432, and 6379. Stop conflicting local services or adjust the Compose port mappings.
- **Integration tests skipped:** run the dedicated test stack above or configure isolated test services as described in [TESTING.md](TESTING.md).

## Contributing

Keep routes, business rules, and persistence in their existing layers. Add behavior tests for changes and run the relevant suite before opening a pull request. Describe any database schema changes and how they were verified.

## License

This repository does not currently include a license file. Contact the repository owner before reusing or redistributing the code.

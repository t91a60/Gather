# Event/Social API

A REST API combining event management with social media features. Built with FastAPI, PostgreSQL, and Redis.

---

## Stack

| Layer | Technology | Rationale |
|---|---|---|
| Framework | **FastAPI** | Auto OpenAPI/Swagger, Pydantic validation, native async, fast development |
| Database | **PostgreSQL 16** | Proven relational DB with strong support for social-graph relationships |
| ORM | **SQLAlchemy 2.0 (async)** | Mature, async-native, Alembic migrations, repository pattern |
| Cache | **Redis 7** | Event list caching, rate limiting, session store |
| Auth | **JWT (access + refresh)** | Stateless auth, refresh tokens for persistent sessions |
| Tests | **pytest + httpx + aiosqlite** | Async tests on SQLite -- fast, isolated, no external deps |

---

## Architecture

```
app/
  api/v1/          Routes (HTTP layer)
  services/        Business logic, validation, cache orchestration
  repositories/    Data access (SQLAlchemy async sessions)
  models/          Table definitions (SQLAlchemy ORM)
  schemas/         Pydantic models (request/response validation)
  middleware/      JWT authentication, rate limiting
  config.py        Pydantic Settings (loaded from .env)
  database.py      Async engine and session factory
  redis_client.py  Redis client with graceful fallback
  main.py          FastAPI app with lifespan
tests/
  conftest.py      Fixtures, SQLite in-memory DB
  test_auth.py     Registration, login, token refresh
  test_events.py   Event CRUD, join/leave, authorization
```

### Layer rationale

- **Repository** -- abstracts data access behind a clean interface; simplifies testing and future DB changes
- **Service** -- contains all business logic, validation, and cache operations; decoupled from HTTP
- **API** -- thin route definitions that delegate to services; no business logic
- **Middleware** -- cross-cutting concerns (auth, rate limits) handled before request processing

---

## Quick start

### Docker (recommended)

```bash
docker-compose up --build
```

API at `http://localhost:8000`.
Swagger UI at `http://localhost:8000/docs`.
ReDoc at `http://localhost:8000/redoc`.

### Manual

```bash
python -m venv venv
source venv/bin/activate    # Linux/macOS
# .\venv\Scripts\activate   # Windows

pip install -r requirements.txt

# Configure .env with your PostgreSQL and Redis connection strings
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/eventsocial

uvicorn app.main:app --reload
```

---

## Environment variables (`.env`)

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://eventsocial:...@db:5432/eventsocial` | PostgreSQL connection string |
| `REDIS_HOST` | `redis` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_DB` | `0` | Redis database index |
| `JWT_SECRET_KEY` | `change-this...` | JWT signing secret |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `RATE_LIMIT_AUTH_PER_MINUTE` | `10` | Max auth requests per minute |
| `RATE_LIMIT_CONTENT_PER_MINUTE` | `30` | Max content writes per minute |
| `DEBUG` | `true` | SQLAlchemy echo mode |

---

## API endpoints

### Auth (`/api/v1/auth`)

| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `/register` | Register a new user | - |
| POST | `/login` | Log in, receive JWT tokens | - |
| POST | `/refresh` | Refresh access token | - |

### Users (`/api/v1/users`)

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/me` | Get current user profile | + |
| PATCH | `/me` | Update own profile | + |
| GET | `/{user_id}` | Get user by ID | - |
| POST | `/{user_id}/follow` | Follow a user | + |
| DELETE | `/{user_id}/follow` | Unfollow a user | + |
| GET | `/{user_id}/following` | List users being followed | - |
| GET | `/{user_id}/followers` | List followers | - |

### Events (`/api/v1/events`)

| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `/` | Create an event | + |
| GET | `/` | List events (paginated, Redis-cached) | - |
| GET | `/{event_id}` | Get event details with participants | - |
| PUT | `/{event_id}` | Update event (organizer only) | + |
| DELETE | `/{event_id}` | Delete event (organizer only) | + |
| POST | `/{event_id}/join` | Join an event | + |
| DELETE | `/{event_id}/leave` | Leave an event | + |

### Posts & comments (`/api/v1/posts`)

| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `/` | Create a post | + |
| GET | `/` | List posts (optional `?event_id=`) | - |
| GET | `/feed` | Feed from followed users | + |
| GET | `/{post_id}` | Get post details | - |
| PUT | `/{post_id}` | Update own post | + |
| DELETE | `/{post_id}` | Delete own post | + |
| POST | `/{post_id}/comments` | Add a comment | + |
| GET | `/{post_id}/comments` | List comments on a post | - |

---

## Technical decisions

### FastAPI over Express / Spring Boot

- **Auto-generated OpenAPI/Swagger** -- zero-config documentation, interactive client generation
- **Pydantic validation** -- compile-time type safety, clear error messages, no runtime surprises
- **Native async** -- `async/await` throughout the stack without extra libraries
- **Faster development** -- less boilerplate than Java, more structure than raw Express

### SQLAlchemy async over raw SQL

- **Type safety** -- ORM models with Python type hints
- **Migrations** -- Alembic for schema versioning
- **Repository pattern** -- swap databases in tests (SQLite) without changing business logic
- **Async sessions** -- non-blocking database access

### Redis caching

- Event list cached for 5 minutes (configurable TTL)
- Cache invalidated on event create/update/delete
- Graceful fallback when Redis is unavailable (no crash, just cache miss)
- Rate limiting implemented in middleware (in-memory sliding window)

### Pagination

- **Offset-based** -- simple, sufficient for this application scope
- Cursor-based pagination would be better for very large datasets (can be added later)

### Rate limiting

- **Auth endpoints:** 10 requests per minute (registration, login)
- **Content endpoints:** 30 requests per minute (POST/PUT/DELETE on events, posts, comments)
- Sliding window implementation with automatic cleanup

### Testing strategy

- **aiosqlite** in-memory database for tests -- fast, isolated, no PostgreSQL dependency
- Autouse fixture drops and recreates all tables per test function
- Separate user fixtures for auth and event tests to avoid organizer/participant conflicts

---

## Running tests

```bash
# With the virtualenv active:
pytest tests/ -v
```

---

## License

MIT

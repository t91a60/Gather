# Testing Gather

## Agreed testing boundaries

Behavior is tested through HTTP, the Alembic CLI, and isolated PostgreSQL/Redis
integration environments. Tests do not target private service or repository methods.

| Area | Tests |
| --- | --- |
| Registration, login, refresh, invalid token subjects and claims | `tests/test_auth.py` |
| Profiles, username conflicts, following and followers | `tests/test_users.py` |
| Event CRUD, organizer permissions, membership and participant counts | `tests/test_events.py` |
| Post CRUD, author permissions, event filtering and pagination | `tests/test_posts.py` |
| Comment creation, listing and post detail/count consistency | `tests/test_comments.py` |
| Followed-author feed, pagination and unfollowing | `tests/test_feed.py` |
| Authentication requirements and missing resources | `tests/test_api_contract.py` |
| Request validation and pagination limits | `tests/test_validation.py` |
| Rate limits, expiry and client IP isolation | `tests/test_rate_limit.py` |
| CORS preflight and rate-limit responses | `tests/test_cors.py` |
| Redis timeouts and invalid cached JSON through HTTP | `tests/test_cache_fallback.py` |
| PostgreSQL SQL generation and unavailable database diagnostics | `tests/test_migrations.py` |
| Real migrations, database lifecycle and real cache invalidation | `tests/integration/` |

## Local tests without infrastructure

Use Python 3.12 and an isolated virtual environment, install `requirements.txt`, then:

```sh
python -m pytest -q -rs
```

Each ordinary test gets a fresh SQLite database under pytest's temporary directory,
with foreign keys enabled. Tests do not read or overwrite `./test.db`. Request
database dependencies are overridden only for the duration of a test.

Redis is unavailable by default in these tests: the external Redis SDK command
boundary raises a connection error. Specific resilience tests simulate SDK timeouts
or corrupt values. Application services and repositories are not mocked. These
tests do not establish that real PostgreSQL or Redis integration works.

## Full suite with isolated PostgreSQL and Redis

From the repository root, with Docker Compose available:

```sh
docker compose -f compose.test.yml run --build --rm tests
docker compose -f compose.test.yml down
```

This is a separate stack from `docker-compose.yml`. It publishes no host ports,
mounts no repository directory or production data volume, and uses disposable
PostgreSQL storage. Redis persistence is disabled. Credentials are for this test
stack only. The Docker build excludes local `.env` files.

The PostgreSQL integration fixture creates a uniquely named `gather_test_<uuid>`
database for each test and drops only that database afterward. Its schema comes
from `alembic upgrade head`, not `create_all`. Tests exercise downgrade/re-upgrade
and event/post/comment relationships through HTTP.

The Redis integration test uses a dedicated empty Redis database and refuses to
run if it already contains keys. It exercises HTTP reads before and after event
creation, updates, joins, leaves and deletion. Cleanup deletes only the event-list
cache keys in that dedicated test database; it never calls `FLUSHDB`.

Alternatively, explicitly configure dedicated test services before running pytest:

```powershell
$env:TEST_POSTGRES_URL = 'postgresql+asyncpg://gather_test:gather_test@127.0.0.1:15432/postgres'
$env:TEST_REDIS_URL = 'redis://127.0.0.1:16379/0'
python -m pytest -m postgres -q -rs
```

Those example ports require services you start separately. The PostgreSQL user
must have permission to create and drop test databases. Never point these variables
at production services. When URLs are absent, integration tests are reported as
skipped. When configured services fail, the tests fail rather than silently skip.

## TDD workflow and verification status

Add one behavior test, run it, and fix only the failure it exposes. Run the focused
test again before moving to another behavior. Existing correct behavior may pass
immediately; it is retained as a characterization test, not described as a RED/GREEN
cycle. Do not deliberately break working code to manufacture a failing test.

Observed RED/GREEN fixes cover post-detail serialization, malformed token subjects,
CORS on rate-limit responses, Redis timeouts, corrupt cached JSON and Alembic's
driver selection. The rate-limit exception fix was verified in the preceding work.

On 2026-10-24, the local suite passed **113 tests**, with **3 integration tests
skipped** because PostgreSQL, Redis and Docker were unavailable. The test Compose
stack has not been executed in that environment. Real migration application,
database-specific timestamp/constraint behavior and real cache invalidation remain
unverified until the integration suite runs. This is not a claim of 100% code coverage.

The local run reports dependency deprecation warnings from `python-jose` and Redis
client shutdown. Dependencies were not upgraded as part of the behavior fixes.

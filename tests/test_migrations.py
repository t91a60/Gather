import os
from pathlib import Path
import subprocess
import sys


def test_migration_cli_reports_unavailable_database_not_missing_driver(unused_tcp_port):
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["DATABASE_URL"] = (
        f"postgresql+asyncpg://gather_test:gather_test@127.0.0.1:{unused_tcp_port}/gather_test"
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(root / "alembic.ini"),
            "upgrade",
            "head",
        ],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode != 0
    assert "ModuleNotFoundError" not in result.stderr
    assert (
        "ConnectionRefusedError" in result.stderr
        or "Connect call failed" in result.stderr
    )


def test_migrations_generate_postgresql_schema_without_a_database():
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["DATABASE_URL"] = (
        "postgresql+asyncpg://gather_test:gather_test@127.0.0.1/gather_test"
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(root / "alembic.ini"),
            "upgrade",
            "head",
            "--sql",
        ],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    for table in (
        "users",
        "events",
        "event_participants",
        "posts",
        "comments",
        "follows",
    ):
        assert f"CREATE TABLE {table}" in result.stdout
    assert "ON DELETE CASCADE" in result.stdout
    assert "ON DELETE SET NULL" in result.stdout

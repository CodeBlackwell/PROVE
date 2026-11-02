"""Tests for SQLite persistence layer."""

import pytest
from src.core.db import Database


@pytest.fixture
def db(tmp_path):
    return Database(tmp_path / "test.db")


def test_schema_creation(db):
    """Tables exist after init."""
    conn = db._get_conn()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    names = [r["name"] for r in tables]
    assert "conversations" in names
    assert "logs" in names


def test_save_and_get_messages(db):
    db.save_message("s1", "user", "Hello")
    db.save_message("s1", "assistant", "Hi there")
    db.save_message("s1", "user", "Follow up")

    history = db.get_session_history("s1")
    assert len(history) == 3
    assert history[0] == {"role": "user", "content": "Hello"}
    assert history[1] == {"role": "assistant", "content": "Hi there"}
    assert history[2] == {"role": "user", "content": "Follow up"}


def test_get_session_history_limit(db):
    for i in range(10):
        db.save_message("s1", "user", f"Q{i}")
        db.save_message("s1", "assistant", f"A{i}")

    history = db.get_session_history("s1", limit=4)
    assert len(history) == 4
    # Should be the most recent 4 messages in order
    assert history[0] == {"role": "user", "content": "Q8"}
    assert history[3] == {"role": "assistant", "content": "A9"}


def test_session_isolation(db):
    db.save_message("s1", "user", "Session 1")
    db.save_message("s2", "user", "Session 2")

    assert len(db.get_session_history("s1")) == 1
    assert len(db.get_session_history("s2")) == 1
    assert db.get_session_history("s3") == []


def test_session_exists(db):
    assert not db.session_exists("s1")
    db.save_message("s1", "user", "Hello")
    assert db.session_exists("s1")
    assert not db.session_exists("s2")


def test_save_log(db):
    db.save_log(
        "2026-01-01T00:00:00Z", "ERROR", "test.error", session_id="s1", fields={"error": "boom"}
    )

    row = db._get_conn().execute("SELECT level, event, session_id, fields FROM logs").fetchone()
    assert dict(row) == {
        "level": "ERROR",
        "event": "test.error",
        "session_id": "s1",
        "fields": '{"error": "boom"}',
    }


def test_message_metadata(db):
    db.save_message("s1", "user", "Hello", metadata={"model": "haiku", "tokens": 42})

    conn = db._get_conn()
    row = conn.execute("SELECT metadata FROM conversations WHERE session_id = 's1'").fetchone()
    import json

    assert json.loads(row["metadata"]) == {"model": "haiku", "tokens": 42}


# ------------------------------------------------------------------
# Rate limiting
# ------------------------------------------------------------------


def test_rate_limit_allows_within_window(db):
    allowed, remaining = db.check_rate_limit("v1", "chat", max_requests=3, window_seconds=3600)
    assert allowed is True
    assert remaining == 2

    allowed, remaining = db.check_rate_limit("v1", "chat", max_requests=3, window_seconds=3600)
    assert allowed is True
    assert remaining == 1


def test_rate_limit_blocks_when_exceeded(db):
    for _ in range(5):
        db.check_rate_limit("v1", "chat", max_requests=5, window_seconds=3600)

    allowed, remaining = db.check_rate_limit("v1", "chat", max_requests=5, window_seconds=3600)
    assert allowed is False
    assert remaining == 0


def test_rate_limit_isolates_visitors(db):
    for _ in range(3):
        db.check_rate_limit("v1", "chat", max_requests=3, window_seconds=3600)

    # v1 is blocked
    allowed, _ = db.check_rate_limit("v1", "chat", max_requests=3, window_seconds=3600)
    assert allowed is False

    # v2 is not
    allowed, _ = db.check_rate_limit("v2", "chat", max_requests=3, window_seconds=3600)
    assert allowed is True


def test_rate_limit_isolates_endpoints(db):
    for _ in range(3):
        db.check_rate_limit("v1", "chat", max_requests=3, window_seconds=3600)

    # chat is blocked
    allowed, _ = db.check_rate_limit("v1", "chat", max_requests=3, window_seconds=3600)
    assert allowed is False

    # read is not
    allowed, _ = db.check_rate_limit("v1", "read", max_requests=3, window_seconds=3600)
    assert allowed is True


def test_cleanup_rate_limits(db):
    db.check_rate_limit("v1", "chat", max_requests=100, window_seconds=3600)
    conn = db._get_conn()
    count_before = conn.execute("SELECT COUNT(*) AS c FROM rate_limits").fetchone()["c"]
    assert count_before > 0

    # Backdate the record so cleanup will remove it
    conn.execute("UPDATE rate_limits SET created_at = datetime('now', '-2 hours')")
    conn.commit()

    db.cleanup_rate_limits(older_than_seconds=3600)
    count_after = conn.execute("SELECT COUNT(*) AS c FROM rate_limits").fetchone()["c"]
    assert count_after == 0

"""Paid routes count each visitor by address, and a client cannot pick or skip its bucket."""

import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import src.app as appmod
from starlette.testclient import TestClient
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

COMPOSE = Path(__file__).parents[1] / "docker-compose.prod.yml"
GATEWAY = "172.18.0.12"


def production_setting():
    app_block = r"^  app:\n(?:    .*\n)*?    environment:\n(?:      .*\n)*?      FORWARDED_ALLOW_IPS: (\S+)$"
    return re.search(app_block, COMPOSE.read_text(), re.M).group(1)


def visitor(forwarded_for, user_agent="Mozilla/5.0"):
    """A client whose requests pass through uvicorn's proxy handling, as the gateway sends them."""
    proxied = ProxyHeadersMiddleware(appmod.app, production_setting())
    headers = {"x-forwarded-for": forwarded_for, "user-agent": user_agent}
    return TestClient(proxied, client=(GATEWAY, 50000), headers=headers)


@pytest.fixture
def db():
    fake = MagicMock()
    fake.check_rate_limit.return_value = (True, 1)
    fake.session_exists.return_value = False
    fake.get_session_history.return_value = []
    qa = MagicMock()
    qa.answer_stream.side_effect = lambda *args, **kwargs: iter(["answer"])
    jd = MagicMock()
    jd.match.return_value = SimpleNamespace(match_percentage=0, summary="", requirements=[])
    with (
        patch.object(appmod, "db", fake),
        patch.object(appmod, "qa_agent", qa),
        patch.object(appmod, "jd_agent", jd),
    ):
        yield fake


def chat_bucket(db, forwarded_for, **params):
    visitor(forwarded_for).get("/api/chat", params={"q": "hi", **params})
    return db.check_rate_limit.call_args.args[0]


def test_visitors_behind_the_gateway_get_their_own_bucket(db):
    assert chat_bucket(db, "203.0.113.9") != chat_bucket(db, "198.51.100.7")


def test_forged_forwarded_entries_do_not_buy_a_fresh_bucket(db):
    assert chat_bucket(db, "127.0.0.1, 203.0.113.9") == chat_bucket(db, "203.0.113.9")


def test_a_client_chosen_fingerprint_does_not_change_the_bucket(db):
    assert chat_bucket(db, "203.0.113.9", fp="one") == chat_bucket(db, "203.0.113.9", fp="two")


def test_a_crawler_user_agent_is_still_counted_on_chat(db):
    db.check_rate_limit.return_value = (False, 0)
    crawler = visitor("203.0.113.9", user_agent="Googlebot/2.1")
    assert crawler.get("/api/chat", params={"q": "hi"}).status_code == 429


def test_a_crawler_user_agent_is_still_counted_on_jd_match(db):
    db.check_rate_limit.return_value = (False, 0)
    crawler = visitor("203.0.113.9", user_agent="Googlebot/2.1")
    assert crawler.post("/api/jd-match", data={"text": "x"}).status_code == 429


@pytest.mark.parametrize("path", ["/api/sessions", "/api/sessions/abc123", "/api/logs"])
def test_history_and_log_routes_are_gone(db, path):
    response = visitor("203.0.113.9").get(path)
    assert (response.status_code, response.json()) == (404, {"detail": "Not Found"})

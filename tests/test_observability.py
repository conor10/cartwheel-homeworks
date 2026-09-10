"""Offline authentication checks for the Homework 2 endpoint."""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from server import app as server_app


@pytest.fixture
def client(world, tmp_path, monkeypatch):
    monkeypatch.setenv("CARTWHEEL_DB", str(world["db"]))
    monkeypatch.setenv("CARTWHEEL_DEV_SECRET", "hw2-test-secret")
    monkeypatch.setattr(server_app, "SESSIONS_DB", tmp_path / "sessions.db")
    monkeypatch.setattr(server_app, "_SESSIONS", {})
    # Skip the lifespan hook so tests cannot initialize external tracing.
    client = TestClient(server_app.app)
    yield client
    client.close()


def test_session_creation_rejects_claimed_role_mismatch(client):
    response = client.post("/sessions", json={"user_id": 1, "role": "support"})

    assert response.status_code == 403
    assert "token" not in response.json()
    assert server_app._SESSIONS == {}


def test_token_cannot_authorize_another_session(client, monkeypatch):
    first = client.post("/sessions", json={"user_id": 1, "role": "shopper"})
    second = client.post("/sessions", json={"user_id": 2, "role": "shopper"})
    assert first.status_code == second.status_code == 200
    first, second = first.json(), second.json()
    assert first["session_id"] != second["session_id"]
    assert server_app.verify_token(first["token"])["session_id"] == first["session_id"]
    build_agent = Mock(side_effect=AssertionError("unauthorized request reached agent"))
    monkeypatch.setattr(server_app, "build_agent", build_agent)

    response = client.post(
        f"/sessions/{second['session_id']}/messages",
        headers={"Authorization": f"Bearer {first['token']}"},
        json={"message": "Show me my orders."},
    )

    assert response.status_code == 403
    build_agent.assert_not_called()

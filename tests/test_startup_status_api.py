#!/usr/bin/env python3
"""
启动状态 API 测试
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config.settings import Config
from utils.jwt_handler import create_token


@pytest.fixture
def app():
    from app import app

    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_startup_status_requires_admin(client, monkeypatch):
    monkeypatch.setattr(Config, "ADMIN_USERS", {"admin"})
    token = create_token(1, "user")

    response = client.get(
        "/api/startup/status", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


def test_startup_status_returns_payload_for_admin(client, monkeypatch):
    monkeypatch.setattr(Config, "ADMIN_USERS", {"admin"})
    token = create_token(1, "admin")

    response = client.get(
        "/api/startup/status", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body is not None
    assert body.get("code") == 200
    payload = body.get("data", {})
    assert "admin_bootstrap" in payload
    assert "warmup" in payload

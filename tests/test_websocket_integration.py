#!/usr/bin/env python3
"""
WebSocket 服务集成测试

用 ``socketio.test_client(app)`` 驱动真实事件处理器，覆盖 _register_handlers
内的 7 个闭包 handler 与 WebSocketService 的 send_* / get_stats / init_app 方法。

此前 test_websocket.py 只覆盖 dataclass/枚举（28%）。本测试补足行为层：
- init_app 初始化与幂等性
- connect / disconnect 处理器
- authenticate（成功 / 缺 token / 无效 token / id 回退）
- subscribe（成功 / 缺 target / 非法 room_type / 默认类型）
- unsubscribe（成功 / 缺 target / 非法类型）
- ping / get_rooms
- send_to_user / send_to_room / broadcast（含 exclude_sids）
- send_alert / send_notification / send_data_update（user/keyword/broadcast 三路派发）
- 未初始化时 send_* 的 False guard
- emit 抛异常时 send_* 的 False 兜底
- get_stats 连接统计
"""

import pytest

pytestmark = pytest.mark.integration

import logging
import os
import sys
from unittest.mock import patch

import pytest
from flask import Flask

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from services.websocket_service import (
    MessageType,
    RoomType,
    WebSocketMessage,
    WebSocketService,
    create_message,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def app():
    """最小 Flask 应用"""
    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def ws_service(app):
    """已 init_app 的 WebSocketService 实例（每个测试独立）"""
    service = WebSocketService()
    service.init_app(app)
    return service


@pytest.fixture
def socketio(ws_service):
    """底层 SocketIO 实例"""
    return ws_service.socketio


@pytest.fixture
def connected_client(socketio, app):
    """已连接的测试客户端，已消费 connect 的 'connected' 事件"""
    client = socketio.test_client(app)
    client.get_received()  # 消费 "connected"
    return client


@pytest.fixture
def authed_client(connected_client):
    """已连接并认证为 u1 / alice 的客户端（已加入 user:u1 房间）"""
    with patch(
        "services.websocket_service.verify_token",
        return_value={"user_id": "u1", "username": "alice"},
    ):
        connected_client.emit("authenticate", {"token": "valid-token"})
    connected_client.get_received()  # 消费 "auth_success"
    return connected_client


def _sid_of(ws_service) -> str:
    """取当前唯一的连接 sid（单客户端测试场景）"""
    return next(iter(ws_service.connections.keys()))


# ---------------------------------------------------------------------------
# init_app
# ---------------------------------------------------------------------------


class TestInitApp:
    """init_app 初始化与幂等性"""

    def test_init_app_creates_socketio_and_registers_handlers(self, ws_service):
        """init_app 后 socketio 非 None、_initialized=True"""
        assert ws_service.socketio is not None
        assert ws_service._initialized is True

    def test_init_app_twice_logs_warning_and_keeps_socketio(
        self, app, ws_service, caplog
    ):
        """二次 init_app 应记 warning 且不替换 socketio"""
        first = ws_service.socketio
        with caplog.at_level(logging.WARNING, logger="services.websocket_service"):
            ws_service.init_app(app)
        assert ws_service.socketio is first
        assert any("已初始化" in r.message for r in caplog.records)

    def test_register_handlers_noop_without_socketio(self):
        """_register_handlers 在 socketio 为 None 时应早返回（防御分支）"""
        svc = WebSocketService()
        svc._register_handlers()  # 不应抛异常
        assert svc.socketio is None


# ---------------------------------------------------------------------------
# connect / disconnect
# ---------------------------------------------------------------------------


class TestConnectDisconnect:
    """connect / disconnect 处理器"""

    def test_connect_emits_connected_and_registers(self, socketio, app, ws_service):
        """connect 应 emit 'connected' 并登记连接"""
        client = socketio.test_client(app)
        received = client.get_received()
        assert any(r["name"] == "connected" for r in received)
        assert len(ws_service.connections) == 1
        client.disconnect()

    def test_connected_event_contains_sid_and_timestamp(self, socketio, app):
        """'connected' 事件应含 sid 与 timestamp"""
        client = socketio.test_client(app)
        received = client.get_received()
        connected = next(r for r in received if r["name"] == "connected")
        assert "sid" in connected["args"][0]
        assert "timestamp" in connected["args"][0]
        client.disconnect()

    def test_disconnect_removes_connection(self, socketio, app, ws_service):
        """disconnect 应移除 connections 记录"""
        client = socketio.test_client(app)
        client.get_received()
        assert len(ws_service.connections) == 1
        client.disconnect()
        assert len(ws_service.connections) == 0

    def test_disconnect_cleans_user_connections(self, authed_client, ws_service):
        """认证用户断开后 user_connections 也应清空"""
        assert "u1" in ws_service.user_connections
        authed_client.disconnect()
        assert "u1" not in ws_service.user_connections
        assert len(ws_service.connections) == 0


# ---------------------------------------------------------------------------
# authenticate
# ---------------------------------------------------------------------------


class TestAuthenticate:
    """authenticate 处理器"""

    @patch("services.websocket_service.verify_token")
    def test_success_emits_auth_success_and_updates_connection(
        self, mock_verify, connected_client, ws_service
    ):
        mock_verify.return_value = {"user_id": "u1", "username": "alice"}
        connected_client.emit("authenticate", {"token": "valid"})

        received = connected_client.get_received()
        assert any(r["name"] == "auth_success" for r in received)

        conn = ws_service.connections[_sid_of(ws_service)]
        assert conn.user_id == "u1"
        assert conn.username == "alice"
        assert conn.is_authenticated is True
        assert "u1" in ws_service.user_connections

    @patch("services.websocket_service.verify_token")
    def test_success_joins_user_room(self, mock_verify, connected_client, ws_service):
        mock_verify.return_value = {"user_id": "u1", "username": "alice"}
        connected_client.emit("authenticate", {"token": "valid"})
        connected_client.get_received()

        conn = ws_service.connections[_sid_of(ws_service)]
        assert "user:u1" in conn.rooms

    @patch("services.websocket_service.verify_token")
    def test_falls_back_to_id_when_no_user_id(
        self, mock_verify, connected_client, ws_service
    ):
        """user_info 无 user_id 时回退到 str(id)"""
        mock_verify.return_value = {"id": 42, "username": "bob"}
        connected_client.emit("authenticate", {"token": "valid"})
        connected_client.get_received()

        conn = ws_service.connections[_sid_of(ws_service)]
        assert conn.user_id == "42"

    def test_missing_token_emits_auth_error(self, connected_client):
        connected_client.emit("authenticate", {"token": ""})
        received = connected_client.get_received()
        err = next(r for r in received if r["name"] == "auth_error")
        assert "缺少认证令牌" in err["args"][0]["message"]

    def test_empty_data_emits_auth_error(self, connected_client):
        """data 为空 dict（falsy）→ 视为缺 token"""
        connected_client.emit("authenticate", {})
        received = connected_client.get_received()
        assert any(r["name"] == "auth_error" for r in received)

    @patch("services.websocket_service.verify_token")
    def test_invalid_token_emits_auth_error(self, mock_verify, connected_client):
        mock_verify.return_value = None
        connected_client.emit("authenticate", {"token": "bad"})
        received = connected_client.get_received()
        err = next(r for r in received if r["name"] == "auth_error")
        assert "无效或已过期" in err["args"][0]["message"]

    @patch("services.websocket_service.verify_token")
    def test_auth_success_event_contains_user_info(
        self, mock_verify, connected_client
    ):
        mock_verify.return_value = {"user_id": "u1", "username": "alice"}
        connected_client.emit("authenticate", {"token": "valid"})
        received = connected_client.get_received()
        success = next(r for r in received if r["name"] == "auth_success")
        assert success["args"][0]["user_id"] == "u1"
        assert success["args"][0]["username"] == "alice"


# ---------------------------------------------------------------------------
# subscribe / unsubscribe
# ---------------------------------------------------------------------------


class TestSubscribe:
    """subscribe 处理器"""

    def test_success_emits_subscribed_and_joins_room(self, connected_client, ws_service):
        connected_client.emit("subscribe", {"type": "keyword", "target": "AI"})
        received = connected_client.get_received()
        sub = next(r for r in received if r["name"] == "subscribed")
        assert sub["args"][0]["room"] == "keyword:AI"
        conn = ws_service.connections[_sid_of(ws_service)]
        assert "keyword:AI" in conn.rooms

    def test_default_room_type_is_keyword(self, connected_client):
        """未传 type → 默认 'keyword'"""
        connected_client.emit("subscribe", {"target": "AI"})
        received = connected_client.get_received()
        assert any(r["name"] == "subscribed" for r in received)

    def test_missing_target_emits_error(self, connected_client):
        connected_client.emit("subscribe", {"type": "keyword", "target": ""})
        received = connected_client.get_received()
        err = next(r for r in received if r["name"] == "subscribe_error")
        assert "订阅目标不能为空" in err["args"][0]["message"]

    def test_invalid_room_type_emits_error(self, connected_client):
        connected_client.emit("subscribe", {"type": "invalid_type", "target": "AI"})
        received = connected_client.get_received()
        err = next(r for r in received if r["name"] == "subscribe_error")
        assert "无效的房间类型" in err["args"][0]["message"]

    def test_subscribe_user_room_type(self, connected_client, ws_service):
        """RoomType.USER 也应可订阅"""
        connected_client.emit("subscribe", {"type": "user", "target": "bob"})
        received = connected_client.get_received()
        assert any(r["name"] == "subscribed" for r in received)
        conn = ws_service.connections[_sid_of(ws_service)]
        assert "user:bob" in conn.rooms


class TestUnsubscribe:
    """unsubscribe 处理器"""

    def test_success_emits_unsubscribed_and_leaves_room(
        self, connected_client, ws_service
    ):
        connected_client.emit("subscribe", {"type": "keyword", "target": "AI"})
        connected_client.get_received()

        connected_client.emit("unsubscribe", {"type": "keyword", "target": "AI"})
        received = connected_client.get_received()
        assert any(r["name"] == "unsubscribed" for r in received)
        conn = ws_service.connections[_sid_of(ws_service)]
        assert "keyword:AI" not in conn.rooms

    def test_missing_target_returns_false_no_emit(self, connected_client):
        result = connected_client.emit(
            "unsubscribe", {"type": "keyword", "target": ""}, callback=True
        )
        assert result is False
        assert not any(
            r["name"] == "unsubscribed" for r in connected_client.get_received()
        )

    def test_invalid_type_returns_false_no_emit(self, connected_client):
        result = connected_client.emit(
            "unsubscribe", {"type": "invalid", "target": "AI"}, callback=True
        )
        assert result is False
        assert not any(
            r["name"] == "unsubscribed" for r in connected_client.get_received()
        )


# ---------------------------------------------------------------------------
# ping / get_rooms
# ---------------------------------------------------------------------------


class TestPingAndRooms:
    """ping 与 get_rooms 处理器"""

    def test_ping_emits_pong_with_timestamp(self, connected_client):
        connected_client.emit("ping")
        received = connected_client.get_received()
        pong = next(r for r in received if r["name"] == "pong")
        assert "timestamp" in pong["args"][0]

    def test_get_rooms_returns_subscribed_rooms(self, connected_client, ws_service):
        connected_client.emit("subscribe", {"type": "keyword", "target": "AI"})
        connected_client.get_received()

        result = connected_client.emit("get_rooms", callback=True)
        assert "rooms" in result
        assert "keyword:AI" in result["rooms"]

    def test_get_rooms_empty_for_new_connection(self, connected_client):
        result = connected_client.emit("get_rooms", callback=True)
        assert result == {"rooms": []}


# ---------------------------------------------------------------------------
# send_to_user / send_to_room / broadcast
# ---------------------------------------------------------------------------


class TestSendMethods:
    """send_to_user / send_to_room / broadcast"""

    def test_send_to_user_delivers_to_user_room(self, authed_client, ws_service):
        msg = create_message(MessageType.NOTIFICATION, title="hi", content="hello")
        assert ws_service.send_to_user("u1", msg) is True
        received = authed_client.get_received()
        assert any(r["name"] == "message" for r in received)

    def test_send_to_user_unknown_user_returns_true_no_delivery(
        self, connected_client, ws_service
    ):
        """目标房间无客户端时 emit 仍成功（返回 True），但无人收到"""
        msg = create_message(MessageType.NOTIFICATION, title="hi")
        assert ws_service.send_to_user("nobody", msg) is True
        assert not any(
            r["name"] == "message" for r in connected_client.get_received()
        )

    def test_send_to_room_delivers_to_subscribed_client(
        self, connected_client, ws_service
    ):
        connected_client.emit("subscribe", {"type": "keyword", "target": "AI"})
        connected_client.get_received()

        msg = create_message(MessageType.ALERT, title="alert")
        assert ws_service.send_to_room(RoomType.KEYWORD, "AI", msg) is True
        assert any(r["name"] == "message" for r in connected_client.get_received())

    def test_broadcast_reaches_all_clients(
        self, connected_client, socketio, app, ws_service
    ):
        client2 = socketio.test_client(app)
        client2.get_received()

        msg = create_message(MessageType.SYSTEM, content="bc")
        assert ws_service.broadcast(msg) is True
        assert any(r["name"] == "message" for r in connected_client.get_received())
        assert any(r["name"] == "message" for r in client2.get_received())

    def test_broadcast_exclude_sid_skips_excluded(
        self, connected_client, socketio, app, ws_service
    ):
        """exclude_sids 中的客户端不应收到广播"""
        excluded_sid = _sid_of(ws_service)
        client2 = socketio.test_client(app)
        client2.get_received()

        msg = create_message(MessageType.SYSTEM, content="bc")
        assert ws_service.broadcast(msg, exclude_sids=[excluded_sid]) is True
        # 被排除的客户端不应收到
        assert not any(
            r["name"] == "message" for r in connected_client.get_received()
        )
        # 未排除的客户端应收到
        assert any(r["name"] == "message" for r in client2.get_received())

    def test_send_to_user_returns_false_on_emit_error(self, ws_service):
        msg = create_message(MessageType.SYSTEM)
        with patch.object(ws_service.socketio, "emit", side_effect=Exception("boom")):
            assert ws_service.send_to_user("u1", msg) is False

    def test_send_to_room_returns_false_on_emit_error(self, ws_service):
        msg = create_message(MessageType.SYSTEM)
        with patch.object(ws_service.socketio, "emit", side_effect=Exception("boom")):
            assert ws_service.send_to_room(RoomType.USER, "u1", msg) is False

    def test_broadcast_returns_false_on_emit_error(self, ws_service):
        with patch.object(ws_service.socketio, "emit", side_effect=Exception("boom")):
            assert ws_service.broadcast(create_message(MessageType.SYSTEM)) is False


# ---------------------------------------------------------------------------
# send_alert / send_notification / send_data_update 派发
# ---------------------------------------------------------------------------


class TestAlertDispatch:
    """send_alert / send_notification / send_data_update 三路派发"""

    def test_send_alert_to_user(self, authed_client, ws_service):
        assert (
            ws_service.send_alert(
                {"level": "warning", "title": "t", "message": "m"}, user_id="u1"
            )
            is True
        )
        assert any(r["name"] == "message" for r in authed_client.get_received())

    def test_send_alert_to_keyword(self, connected_client, ws_service):
        connected_client.emit("subscribe", {"type": "keyword", "target": "AI"})
        connected_client.get_received()

        assert (
            ws_service.send_alert({"title": "t", "message": "m"}, keyword="AI")
            is True
        )
        assert any(r["name"] == "message" for r in connected_client.get_received())

    def test_send_alert_broadcast_when_no_target(self, connected_client, ws_service):
        assert ws_service.send_alert({"title": "t", "message": "m"}) is True
        assert any(r["name"] == "message" for r in connected_client.get_received())

    def test_send_alert_message_fields(self, authed_client, ws_service):
        """send_alert 构造的 WebSocketMessage 应含 level/title/content/data"""
        ws_service.send_alert(
            {"level": "danger", "title": "预警", "message": "内容", "extra": 1},
            user_id="u1",
        )
        received = authed_client.get_received()
        # socketio.emit 从 handler 外发起时，test_client 把单个 dict 放在 args
        msg = next(r for r in received if r["name"] == "message")["args"]
        assert msg["type"] == "alert"
        assert msg["level"] == "danger"
        assert msg["title"] == "预警"
        assert msg["content"] == "内容"
        assert msg["data"]["extra"] == 1

    def test_send_notification_to_user(self, authed_client, ws_service):
        assert ws_service.send_notification("t", "c", user_id="u1") is True
        received = authed_client.get_received()
        msg = next(r for r in received if r["name"] == "message")["args"]
        assert msg["type"] == "notification"
        assert msg["title"] == "t"
        assert msg["content"] == "c"

    def test_send_notification_broadcast(self, connected_client, ws_service):
        assert ws_service.send_notification("t", "c") is True
        assert any(r["name"] == "message" for r in connected_client.get_received())

    def test_send_data_update_to_user(self, authed_client, ws_service):
        assert ws_service.send_data_update("comments", {"count": 5}, user_id="u1") is True
        received = authed_client.get_received()
        msg = next(r for r in received if r["name"] == "message")["args"]
        assert msg["type"] == "data_update"
        assert msg["data"]["type"] == "comments"
        assert msg["data"]["payload"] == {"count": 5}

    def test_send_data_update_broadcast(self, connected_client, ws_service):
        assert ws_service.send_data_update("comments", {"count": 5}) is True
        assert any(r["name"] == "message" for r in connected_client.get_received())


# ---------------------------------------------------------------------------
# get_stats
# ---------------------------------------------------------------------------


class TestGetStats:
    """get_stats 连接统计"""

    def test_empty_stats_for_new_service(self, ws_service):
        stats = ws_service.get_stats()
        assert stats["total_connections"] == 0
        assert stats["authenticated_users"] == 0
        assert stats["connections"] == []

    def test_stats_reflects_authenticated_connection(self, authed_client, ws_service):
        stats = ws_service.get_stats()
        assert stats["total_connections"] == 1
        assert stats["authenticated_users"] == 1
        conn = stats["connections"][0]
        assert conn["user_id"] == "u1"
        assert conn["username"] == "alice"
        assert "connected_at" in conn
        assert isinstance(conn["rooms"], list)

    def test_stats_reflects_multiple_connections(
        self, connected_client, socketio, app, ws_service
    ):
        client2 = socketio.test_client(app)
        client2.get_received()
        stats = ws_service.get_stats()
        assert stats["total_connections"] == 2
        assert stats["authenticated_users"] == 0


# ---------------------------------------------------------------------------
# 未初始化 guard
# ---------------------------------------------------------------------------


class TestUninitializedGuards:
    """未调 init_app 时 send_* 应返回 False（socketio is None 防御）"""

    def test_send_to_user_returns_false(self):
        svc = WebSocketService()
        assert svc.send_to_user("u1", create_message(MessageType.SYSTEM)) is False

    def test_send_to_room_returns_false(self):
        svc = WebSocketService()
        assert (
            svc.send_to_room(RoomType.USER, "u1", create_message(MessageType.SYSTEM))
            is False
        )

    def test_broadcast_returns_false(self):
        svc = WebSocketService()
        assert svc.broadcast(create_message(MessageType.SYSTEM)) is False

    def test_send_alert_returns_false(self):
        svc = WebSocketService()
        assert svc.send_alert({"level": "warning"}) is False

    def test_send_notification_returns_false(self):
        svc = WebSocketService()
        assert svc.send_notification("t", "c") is False

    def test_send_data_update_returns_false(self):
        svc = WebSocketService()
        assert svc.send_data_update("type", {}) is False

    def test_get_stats_works_without_init(self):
        """get_stats 不依赖 socketio，未初始化也能返回空统计"""
        svc = WebSocketService()
        stats = svc.get_stats()
        assert stats["total_connections"] == 0
        assert stats["connections"] == []

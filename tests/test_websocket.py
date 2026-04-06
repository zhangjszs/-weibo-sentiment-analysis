#!/usr/bin/env python3
"""
WebSocket 服务单元测试
"""

import sys

import pytest

sys.path.insert(0, "src")


class TestWebSocketService:
    """WebSocket 服务测试"""

    @pytest.fixture
    def websocket_service(self):
        """创建 WebSocket 服务实例"""
        from services.websocket_service import WebSocketService

        return WebSocketService()

    def test_init(self, websocket_service):
        """测试初始化"""
        assert websocket_service.socketio is None
        assert len(websocket_service.connections) == 0
        assert len(websocket_service.user_connections) == 0
        assert websocket_service._initialized is False

    def test_get_room_name(self, websocket_service):
        """测试房间名称生成"""
        from services.websocket_service import RoomType

        room_name = websocket_service._get_room_name(RoomType.USER, "user123")
        assert room_name == "user:user123"

        room_name = websocket_service._get_room_name(RoomType.KEYWORD, "测试")
        assert room_name == "keyword:测试"

    def test_create_message(self):
        """测试消息创建"""
        from services.websocket_service import MessageType, create_message

        message = create_message(
            MessageType.ALERT, title="测试预警", content="测试内容"
        )

        assert message.id is not None
        assert message.type == MessageType.ALERT
        assert message.title == "测试预警"
        assert message.content == "测试内容"

    def test_message_to_dict(self):
        """测试消息序列化"""
        from services.websocket_service import MessageType, WebSocketMessage

        message = WebSocketMessage(
            id="test-id",
            type=MessageType.ALERT,
            level="warning",
            title="测试",
            content="测试内容",
            data={"key": "value"},
        )

        msg_dict = message.to_dict()

        assert msg_dict["id"] == "test-id"
        assert msg_dict["type"] == "alert"
        assert msg_dict["level"] == "warning"
        assert msg_dict["title"] == "测试"
        assert msg_dict["content"] == "测试内容"
        assert msg_dict["data"] == {"key": "value"}


class TestWebSocketMessage:
    """WebSocket 消息测试"""

    def test_message_types(self):
        """测试消息类型枚举"""
        from services.websocket_service import MessageType

        assert MessageType.ALERT.value == "alert"
        assert MessageType.NOTIFICATION.value == "notification"
        assert MessageType.DATA_UPDATE.value == "data_update"

    def test_room_types(self):
        """测试房间类型枚举"""
        from services.websocket_service import RoomType

        assert RoomType.USER.value == "user"
        assert RoomType.KEYWORD.value == "keyword"
        assert RoomType.GLOBAL.value == "global"


class TestIntegration:
    """集成测试"""

    def test_websocket_imports(self):
        """测试模块导入"""
        try:
            from services.websocket_service import (
                MessageType,
                RoomType,
                WebSocketMessage,
                WebSocketService,
                create_message,
                websocket_service,
            )

            assert True
        except ImportError as e:
            pytest.fail(f"WebSocket 模块导入失败: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

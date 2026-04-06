#!/usr/bin/env python3
"""
WebSocket 服务模块
功能：实时消息推送、房间订阅、连接管理
特性：JWT认证、房间机制、消息广播、断线重连
"""

import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room

from utils.jwt_handler import verify_token

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型"""

    ALERT = "alert"
    NOTIFICATION = "notification"
    DATA_UPDATE = "data_update"
    SYSTEM = "system"
    PING = "ping"
    PONG = "pong"


class RoomType(Enum):
    """房间类型"""

    USER = "user"
    KEYWORD = "keyword"
    GLOBAL = "global"
    SYSTEM = "system"


@dataclass
class ConnectionInfo:
    """连接信息"""

    sid: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    connected_at: datetime = field(default_factory=datetime.now)
    rooms: Set[str] = field(default_factory=set)
    is_authenticated: bool = False


@dataclass
class WebSocketMessage:
    """WebSocket消息"""

    id: str
    type: MessageType
    level: str = "info"
    title: Optional[str] = None
    content: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "level": self.level,
            "title": self.title,
            "content": self.content,
            "data": self.data,
            "timestamp": self.timestamp,
        }


class WebSocketService:
    """WebSocket服务管理器"""

    def __init__(self):
        self.socketio: Optional[SocketIO] = None
        self.connections: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[str, Set[str]] = {}
        self._lock = threading.Lock()
        self._initialized = False

    def init_app(self, app):
        """初始化SocketIO应用"""
        if self._initialized:
            logger.warning("WebSocket服务已初始化")
            return

        self.socketio = SocketIO(
            app,
            cors_allowed_origins="*",
            async_mode="threading",
            logger=False,
            engineio_logger=False,
            ping_timeout=30,
            ping_interval=15,
        )

        self._register_handlers()
        self._initialized = True
        logger.info("WebSocket服务初始化完成")

    def _register_handlers(self):
        """注册事件处理器"""
        if not self.socketio:
            return

        @self.socketio.on("connect")
        def handle_connect():
            """处理连接事件"""
            sid = request.sid
            logger.info(f"WebSocket连接建立: {sid}")

            with self._lock:
                self.connections[sid] = ConnectionInfo(sid=sid)

            emit("connected", {"sid": sid, "timestamp": datetime.now().isoformat()})

        @self.socketio.on("disconnect")
        def handle_disconnect():
            """处理断开连接事件"""
            sid = request.sid
            logger.info(f"WebSocket连接断开: {sid}")

            with self._lock:
                conn_info = self.connections.pop(sid, None)
                if conn_info and conn_info.user_id:
                    user_sids = self.user_connections.get(conn_info.user_id, set())
                    user_sids.discard(sid)
                    if not user_sids:
                        self.user_connections.pop(conn_info.user_id, None)

        @self.socketio.on("authenticate")
        def handle_authenticate(data):
            """处理认证事件"""
            sid = request.sid
            token = data.get("token", "") if data else ""

            if not token:
                emit("auth_error", {"message": "缺少认证令牌"})
                return False

            user_info = verify_token(token)
            if not user_info:
                emit("auth_error", {"message": "认证令牌无效或已过期"})
                return False

            with self._lock:
                conn_info = self.connections.get(sid)
                if conn_info:
                    conn_info.user_id = user_info.get(
                        "user_id", str(user_info.get("id"))
                    )
                    conn_info.username = user_info.get("username", "")
                    conn_info.is_authenticated = True

                    user_id = conn_info.user_id
                    if user_id not in self.user_connections:
                        self.user_connections[user_id] = set()
                    self.user_connections[user_id].add(sid)

                    user_room = self._get_room_name(RoomType.USER, user_id)
                    join_room(user_room, sid=sid)
                    conn_info.rooms.add(user_room)

            emit(
                "auth_success",
                {
                    "user_id": user_info.get("user_id"),
                    "username": user_info.get("username"),
                },
            )
            logger.info(f"用户认证成功: {user_info.get('username')} (SID: {sid})")
            return True

        @self.socketio.on("subscribe")
        def handle_subscribe(data):
            """处理订阅事件"""
            sid = request.sid
            room_type = data.get("type", "keyword") if data else "keyword"
            target = data.get("target", "") if data else ""

            if not target:
                emit("subscribe_error", {"message": "订阅目标不能为空"})
                return False

            try:
                room_enum = RoomType(room_type)
            except ValueError:
                emit("subscribe_error", {"message": f"无效的房间类型: {room_type}"})
                return False

            room_name = self._get_room_name(room_enum, target)
            join_room(room_name, sid=sid)

            with self._lock:
                conn_info = self.connections.get(sid)
                if conn_info:
                    conn_info.rooms.add(room_name)

            emit("subscribed", {"type": room_type, "target": target, "room": room_name})
            logger.debug(f"用户订阅: {room_type} - {target} (SID: {sid})")
            return True

        @self.socketio.on("unsubscribe")
        def handle_unsubscribe(data):
            """处理取消订阅事件"""
            sid = request.sid
            room_type = data.get("type", "keyword") if data else "keyword"
            target = data.get("target", "") if data else ""

            if not target:
                return False

            try:
                room_enum = RoomType(room_type)
            except ValueError:
                return False

            room_name = self._get_room_name(room_enum, target)
            leave_room(room_name, sid=sid)

            with self._lock:
                conn_info = self.connections.get(sid)
                if conn_info:
                    conn_info.rooms.discard(room_name)

            emit("unsubscribed", {"type": room_type, "target": target})
            logger.debug(f"用户取消订阅: {room_type} - {target} (SID: {sid})")
            return True

        @self.socketio.on("ping")
        def handle_ping():
            """处理心跳"""
            emit("pong", {"timestamp": datetime.now().isoformat()})

        @self.socketio.on("get_rooms")
        def handle_get_rooms():
            """获取当前订阅的房间列表"""
            sid = request.sid
            with self._lock:
                conn_info = self.connections.get(sid)
                if conn_info:
                    return {"rooms": list(conn_info.rooms)}
            return {"rooms": []}

    def _get_room_name(self, room_type: RoomType, target: str) -> str:
        """生成房间名称"""
        return f"{room_type.value}:{target}"

    def send_to_user(self, user_id: str, message: WebSocketMessage) -> bool:
        """发送消息给指定用户"""
        if not self.socketio:
            logger.warning("WebSocket服务未初始化")
            return False

        room_name = self._get_room_name(RoomType.USER, user_id)
        try:
            self.socketio.emit("message", message.to_dict(), room=room_name)
            logger.debug(f"发送消息给用户 {user_id}: {message.type.value}")
            return True
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return False

    def send_to_room(
        self, room_type: RoomType, target: str, message: WebSocketMessage
    ) -> bool:
        """发送消息给指定房间"""
        if not self.socketio:
            logger.warning("WebSocket服务未初始化")
            return False

        room_name = self._get_room_name(room_type, target)
        try:
            self.socketio.emit("message", message.to_dict(), room=room_name)
            logger.debug(f"发送消息给房间 {room_name}: {message.type.value}")
            return True
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return False

    def broadcast(
        self, message: WebSocketMessage, exclude_sids: Optional[List[str]] = None
    ) -> bool:
        """广播消息给所有连接"""
        if not self.socketio:
            logger.warning("WebSocket服务未初始化")
            return False

        try:
            skip_sids = exclude_sids or []
            self.socketio.emit("message", message.to_dict(), skip_sid=skip_sids)
            logger.info(f"广播消息: {message.type.value}")
            return True
        except Exception as e:
            logger.error(f"广播消息失败: {e}")
            return False

    def send_alert(
        self,
        alert_data: Dict[str, Any],
        user_id: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> bool:
        """发送预警消息"""
        message = WebSocketMessage(
            id=str(uuid.uuid4()),
            type=MessageType.ALERT,
            level=alert_data.get("level", "warning"),
            title=alert_data.get("title", "新预警"),
            content=alert_data.get("message", ""),
            data=alert_data,
        )

        if user_id:
            return self.send_to_user(user_id, message)
        elif keyword:
            return self.send_to_room(RoomType.KEYWORD, keyword, message)
        else:
            return self.broadcast(message)

    def send_notification(
        self, title: str, content: str, user_id: Optional[str] = None
    ) -> bool:
        """发送通知消息"""
        message = WebSocketMessage(
            id=str(uuid.uuid4()),
            type=MessageType.NOTIFICATION,
            level="info",
            title=title,
            content=content,
        )

        if user_id:
            return self.send_to_user(user_id, message)
        else:
            return self.broadcast(message)

    def send_data_update(
        self, data_type: str, data: Dict[str, Any], user_id: Optional[str] = None
    ) -> bool:
        """发送数据更新消息"""
        message = WebSocketMessage(
            id=str(uuid.uuid4()),
            type=MessageType.DATA_UPDATE,
            level="info",
            title=f"{data_type} 更新",
            data={"type": data_type, "payload": data},
        )

        if user_id:
            return self.send_to_user(user_id, message)
        else:
            return self.broadcast(message)

    def get_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        with self._lock:
            return {
                "total_connections": len(self.connections),
                "authenticated_users": len(self.user_connections),
                "connections": [
                    {
                        "sid": c.sid,
                        "user_id": c.user_id,
                        "username": c.username,
                        "connected_at": c.connected_at.isoformat(),
                        "rooms": list(c.rooms),
                    }
                    for c in self.connections.values()
                ],
            }


websocket_service = WebSocketService()


def create_message(message_type: MessageType, **kwargs) -> WebSocketMessage:
    """创建WebSocket消息的便捷函数"""
    return WebSocketMessage(id=str(uuid.uuid4()), type=message_type, **kwargs)


__all__ = [
    "WebSocketService",
    "websocket_service",
    "WebSocketMessage",
    "MessageType",
    "RoomType",
    "create_message",
]

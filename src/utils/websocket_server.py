#!/usr/bin/env python3
"""
WebSocket服务模块
功能：实时数据推送、预警消息广播
"""

import logging
import queue
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Set

logger = logging.getLogger(__name__)

try:
    from flask_socketio import SocketIO, emit, join_room, leave_room

    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    logger.warning("Flask-SocketIO未安装，实时推送功能不可用")


@dataclass
class ConnectedClient:
    """连接的客户端"""

    sid: str
    user_id: Optional[str] = None
    rooms: Set[str] = None
    connected_at: datetime = None

    def __post_init__(self):
        if self.rooms is None:
            self.rooms = set()
        if self.connected_at is None:
            self.connected_at = datetime.now()


class WebSocketManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.socketio: Optional[SocketIO] = None
        self.clients: Dict[str, ConnectedClient] = {}
        self._lock = threading.Lock()
        self._message_queue = queue.Queue()
        self._running = False

        self._event_handlers = {}

    def init_app(self, app, cors_allowed_origins: str = "*"):
        """初始化SocketIO应用"""
        if not SOCKETIO_AVAILABLE:
            logger.error("Flask-SocketIO未安装，无法初始化WebSocket")
            return False

        try:
            self.socketio = SocketIO(
                app,
                cors_allowed_origins=cors_allowed_origins,
                async_mode="threading",
                logger=False,
                engineio_logger=False,
            )

            self._register_handlers()
            logger.info("WebSocket服务初始化成功")
            return True

        except Exception as e:
            logger.error(f"WebSocket初始化失败: {e}")
            return False

    def _register_handlers(self):
        """注册SocketIO事件处理器"""

        @self.socketio.on("connect")
        def handle_connect():
            from flask import request

            sid = request.sid

            with self._lock:
                self.clients[sid] = ConnectedClient(sid=sid)

            logger.info(f"客户端连接: {sid}")
            emit("connected", {"message": "连接成功", "sid": sid})

        @self.socketio.on("disconnect")
        def handle_disconnect():
            from flask import request

            sid = request.sid

            with self._lock:
                if sid in self.clients:
                    del self.clients[sid]

            logger.info(f"客户端断开: {sid}")

        @self.socketio.on("authenticate")
        def handle_authenticate(data):
            from flask import request

            sid = request.sid
            user_id = data.get("user_id")

            with self._lock:
                if sid in self.clients:
                    self.clients[sid].user_id = user_id

            join_room(f"user_{user_id}")
            emit("authenticated", {"success": True, "user_id": user_id})
            logger.info(f"客户端认证: {sid} -> {user_id}")

        @self.socketio.on("subscribe")
        def handle_subscribe(data):
            from flask import request

            sid = request.sid
            channel = data.get("channel")

            if channel:
                join_room(channel)
                with self._lock:
                    if sid in self.clients:
                        self.clients[sid].rooms.add(channel)

                emit("subscribed", {"channel": channel})
                logger.info(f"客户端 {sid} 订阅频道: {channel}")

        @self.socketio.on("unsubscribe")
        def handle_unsubscribe(data):
            from flask import request

            sid = request.sid
            channel = data.get("channel")

            if channel:
                leave_room(channel)
                with self._lock:
                    if sid in self.clients:
                        self.clients[sid].rooms.discard(channel)

                emit("unsubscribed", {"channel": channel})

        @self.socketio.on("ping")
        def handle_ping():
            emit("pong", {"timestamp": datetime.now().isoformat()})

    def broadcast(self, event: str, data: Dict[str, Any]):
        """广播消息到所有客户端"""
        if self.socketio:
            self.socketio.emit(event, data)
            logger.debug(f"广播消息: {event}")

    def emit_to_room(self, room: str, event: str, data: Dict[str, Any]):
        """发送消息到指定房间"""
        if self.socketio:
            self.socketio.emit(event, data, room=room)
            logger.debug(f"发送消息到房间 {room}: {event}")

    def emit_to_user(self, user_id: str, event: str, data: Dict[str, Any]):
        """发送消息到指定用户"""
        self.emit_to_room(f"user_{user_id}", event, data)

    def broadcast_alert(self, alert_data: Dict[str, Any]):
        """广播预警消息"""
        self.broadcast("alert", alert_data)

    def broadcast_stats_update(self, stats_data: Dict[str, Any]):
        """广播统计数据更新"""
        self.broadcast("stats_update", stats_data)

    def broadcast_sentiment_update(self, sentiment_data: Dict[str, Any]):
        """广播情感分析更新"""
        self.broadcast("sentiment_update", sentiment_data)

    def get_connected_count(self) -> int:
        """获取连接客户端数量"""
        with self._lock:
            return len(self.clients)

    def get_client_info(self, sid: str) -> Optional[Dict]:
        """获取客户端信息"""
        with self._lock:
            if sid in self.clients:
                client = self.clients[sid]
                return {
                    "sid": client.sid,
                    "user_id": client.user_id,
                    "rooms": list(client.rooms),
                    "connected_at": client.connected_at.isoformat(),
                }
        return None

    def run_background_task(self, task_func, *args, **kwargs):
        """运行后台任务"""
        if self.socketio:
            self.socketio.start_background_task(task_func, *args, **kwargs)


ws_manager = WebSocketManager()


class RealTimeDataPusher:
    """实时数据推送器"""

    def __init__(self, ws_manager: WebSocketManager = None):
        self.ws_manager = ws_manager or ws_manager
        self._running = False
        self._thread = None
        self._interval = 5

    def start(self):
        """启动推送服务"""
        if self._running:
            return

        self._running = True
        logger.info("实时数据推送服务已启动")

    def stop(self):
        """停止推送服务"""
        self._running = False
        logger.info("实时数据推送服务已停止")

    def push_alert(self, alert: Dict):
        """推送预警消息"""
        self.ws_manager.broadcast_alert(alert)

    def push_stats(self, stats: Dict):
        """推送统计数据"""
        self.ws_manager.broadcast_stats_update(stats)

    def push_sentiment(self, sentiment: Dict):
        """推送情感分析"""
        self.ws_manager.broadcast_sentiment_update(sentiment)


realtime_pusher = RealTimeDataPusher()


def init_websocket(app):
    """初始化WebSocket服务"""
    success = ws_manager.init_app(app)
    if success:
        from services.alert_service import alert_engine

        alert_engine.register_callback(
            lambda alert: ws_manager.broadcast_alert(alert.to_dict())
        )
        realtime_pusher.start()
    return success


def get_socketio():
    """获取SocketIO实例"""
    return ws_manager.socketio

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, func

from models.audit_log import AuditLog

from .base_repository import BaseRepository


class AuditRepository(BaseRepository):
    def __init__(self):
        super().__init__(AuditLog)

    def find_with_filter(
        self,
        action: str = "",
        username: str = "",
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        query = self.session.query(AuditLog)

        if action:
            query = query.filter(AuditLog.action == action)

        if username:
            query = query.filter(AuditLog.username.like(f"%{username}%"))

        total = query.count()

        rows = (
            query.order_by(desc(AuditLog.created_at)).limit(limit).offset(offset).all()
        )

        result = []
        for r in rows:
            result.append(
                {
                    "id": r.id,
                    "user_id": r.user_id,
                    "username": r.username,
                    "action": r.action,
                    "detail": r.detail,
                    "ip": r.ip,
                    "created_at": str(r.created_at),
                }
            )

        return result, total

    def log_action(
        self,
        user_id: int,
        username: str,
        action: str,
        detail: str = "",
        ip: str = "",
    ) -> AuditLog:
        """记录审计日志"""
        log = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            detail=detail,
            ip=ip,
        )
        self.save(log)
        return log
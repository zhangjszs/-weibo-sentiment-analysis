#!/usr/bin/env python3
"""
审计日志模型
"""

from sqlalchemy import Column, DateTime, Integer, String, Text

from database import Base
from utils.datetime_utils import utcnow_naive


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, default=0)
    username = Column(String(50), default="")
    action = Column(String(50), default="")
    detail = Column(Text)
    ip = Column(String(50), default="")
    created_at = Column(DateTime, default=utcnow_naive)

    def __repr__(self):
        return f"<AuditLog {self.id} {self.action}>"

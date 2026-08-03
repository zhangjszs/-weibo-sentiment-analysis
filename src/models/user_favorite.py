#!/usr/bin/env python3
"""
用户收藏模型
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint

from database import Base


class UserFavorite(Base):
    __tablename__ = "user_favorites"
    __table_args__ = (UniqueConstraint("user_id", "article_id", name="uq_user_article"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, default=0, nullable=False)
    article_id = Column(String(50), default="", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<UserFavorite user={self.user_id} article={self.article_id}>"
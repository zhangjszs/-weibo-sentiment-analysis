#!/usr/bin/env python3
"""
转发/传播记录模型
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, BigInteger, Index

from database import Base


class Repost(Base):
    __tablename__ = "reposts"
    __table_args__ = (
        Index("idx_article_id", "article_id"),
        Index("idx_user_id", "user_id"),
        Index("idx_created_at", "created_at"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    article_id = Column(String(64), nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    repost_count = Column(BigInteger, default=0)
    comment_count = Column(BigInteger, default=0)
    like_count = Column(BigInteger, default=0)
    depth = Column(Integer, default=0)
    parent_id = Column(BigInteger)

    def __repr__(self):
        return f"<Repost {self.id} article={self.article_id}>"
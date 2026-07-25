from sqlalchemy import BigInteger, Boolean, Column, Integer, String, Text
from sqlalchemy.orm import synonym

from database import Base


class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = {"extend_existing": True}

    # 表无独立主键，用 articleId + created_at 组合
    articleId = Column("articleId", BigInteger, primary_key=True)
    created_at = Column("created_at", String(50), primary_key=True)

    content = Column(Text)
    likeNum = Column("like_counts", BigInteger, default=0)
    user = Column("authorName", Text)
    region = Column(Text)
    authorGender = Column(Text)
    authorAddress = Column(Text)
    authorAvatar = Column(Text)

    # Phase P1.2 双写：补齐 CSV 中已有但 DB 缺失的字段（DB 列名与 CSV header 一致）
    comment_id = Column("comment_id", String(64))
    user_id = Column("user_id", String(64))
    reply_count = Column("reply_count", BigInteger, default=0)
    comment_source = Column("comment_source", String(100))
    is_hot = Column("is_hot", Boolean, default=False)
    parent_id = Column("parent_id", String(64))
    reply_to_user = Column("reply_to_user", String(100))
    verified_type = Column("verified_type", Integer, default=-1)
    followers_count = Column("followers_count", BigInteger, default=0)

    # rootId 是 articleId 的别名，供旧代码兼容
    rootId = synonym("articleId")

    def __repr__(self):
        return f"<Comment articleId={self.articleId!r}>"

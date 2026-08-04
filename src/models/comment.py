from sqlalchemy import BigInteger, Boolean, Column, Index, Integer, String, Text
from sqlalchemy.orm import synonym

from database import Base


class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = (
        Index("idx_articleId", "articleId"),
        Index("idx_comment_created_at", "created_at"),
        {"extend_existing": True},
    )

    # P0 #4：comment_id 为微博评论真实 ID，作主键（此前 ORM 声明 (articleId,
    # created_at) 复合主键，但 DB 实际是 comment_id AUTO_INCREMENT PK —— 身份
    # 错位使 IntegrityError 去重兜底失效）。现与 DB schema / Alembic 迁移
    # a1c4f2e8b9d0 对齐：comment_id VARCHAR(64) 主键，重爬同一评论可正确触发冲突。
    comment_id = Column("comment_id", String(64), primary_key=True)

    articleId = Column("articleId", BigInteger)
    created_at = Column("created_at", String(50))

    content = Column(Text)
    likeNum = Column("like_counts", BigInteger, default=0)
    user = Column("authorName", Text)
    region = Column(Text)
    authorGender = Column(Text)
    authorAddress = Column(Text)
    authorAvatar = Column(Text)

    # Phase P1.2 双写：补齐 CSV 中已有但 DB 缺失的字段（DB 列名与 CSV header 一致）
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
        return f"<Comment comment_id={self.comment_id!r}>"

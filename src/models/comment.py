from sqlalchemy import BigInteger, Column, String, Text
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

    # rootId 是 articleId 的别名，供旧代码兼容
    rootId = synonym("articleId")

    def __repr__(self):
        return f"<Comment articleId={self.articleId!r}>"

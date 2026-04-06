import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from database import Base


class Article(Base):
    __tablename__ = "article"

    id = Column(String(50), primary_key=True)
    likeNum = Column(Integer, default=0)
    commentsLen = Column(Integer, default=0)
    reposts_count = Column(Integer, default=0)
    region = Column(String(50))
    content = Column(Text)
    contentLen = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    type = Column(String(20))
    detailUrl = Column(String(255))
    authorAvatar = Column(String(500))
    authorName = Column(String(100))
    authorDetail = Column(String(255))
    isVip = Column(Integer, default=0)

    def __repr__(self):
        return f"<Article {self.id!r}>"

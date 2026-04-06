import datetime

from sqlalchemy import Column, DateTime, Integer, String

from database import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    create_time = Column("createTime", DateTime, default=datetime.datetime.utcnow)
    nickname = Column(String(50), default=None)
    email = Column(String(100), default=None)
    bio = Column(String(200), default=None)
    avatar_color = Column(String(7), default="#2563EB")

    def __init__(
        self,
        username=None,
        password=None,
        create_time=None,
        nickname=None,
        email=None,
        bio=None,
        avatar_color="#2563EB",
    ):
        self.username = username
        self.password = password
        self.create_time = create_time
        self.nickname = nickname
        self.email = email
        self.bio = bio
        self.avatar_color = avatar_color

    def __repr__(self):
        return f"<User {self.username!r}>"

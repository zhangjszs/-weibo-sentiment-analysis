"""Shared test factories for the Weibo analysis system.

These factories produce ORM instances and analysis payloads without relying on
external services.  Tests should prefer factories over hand-built dicts so
that structural drift is caught in one place.
"""

from __future__ import annotations

import datetime
from typing import Any

from models.article import Article
from models.comment import Comment
from models.user import User
from services.analysis_pipeline import AnalysisSnapshot
from utils.data_provenance import real_meta


def build_article(
    id: str = "article-1",
    topic: str = "测试话题",
    content: str = "这是测试文章内容",
    authorName: str = "测试作者",
    region: str = "北京",
    created_at: datetime.datetime | None = None,
    **kwargs: Any,
) -> Article:
    article = Article(
        id=id,
        likeNum=kwargs.get("likeNum", 0),
        commentsLen=kwargs.get("commentsLen", 0),
        reposts_count=kwargs.get("reposts_count", 0),
        region=region,
        content=content,
        contentLen=len(content),
        created_at=created_at or datetime.datetime(2026, 1, 1, 12, 0, 0),
        type=kwargs.get("type", "article"),
        detailUrl=kwargs.get("detailUrl", f"https://weibo.com/{id}"),
        authorAvatar=kwargs.get("authorAvatar", ""),
        authorName=authorName,
        authorDetail=kwargs.get("authorDetail", ""),
        isVip=kwargs.get("isVip", 0),
    )
    return article


def build_comment(
    comment_id: str = "comment-1",
    articleId: int = 1,
    content: str = "测试评论内容",
    user: str = "评论用户",
    region: str = "上海",
    created_at: str = "2026-01-01 12:00:00",
    **kwargs: Any,
) -> Comment:
    comment = Comment(
        comment_id=comment_id,
        articleId=articleId,
        created_at=created_at,
        content=content,
        likeNum=kwargs.get("likeNum", 0),
        user=user,
        region=region,
        authorGender=kwargs.get("authorGender", ""),
        authorAddress=kwargs.get("authorAddress", ""),
        authorAvatar=kwargs.get("authorAvatar", ""),
        user_id=kwargs.get("user_id", ""),
        reply_count=kwargs.get("reply_count", 0),
        comment_source=kwargs.get("comment_source", "weibo"),
        is_hot=kwargs.get("is_hot", False),
        parent_id=kwargs.get("parent_id", ""),
        reply_to_user=kwargs.get("reply_to_user", ""),
        verified_type=kwargs.get("verified_type", -1),
        followers_count=kwargs.get("followers_count", 0),
    )
    return comment


def build_user(
    id: int = 1,
    username: str = "tester",
    password: str = "test-password",
    nickname: str = "测试用户",
    email: str | None = "tester@example.com",
    bio: str | None = "测试简介",
    **kwargs: Any,
) -> User:
    user = User(
        username=username,
        password=password,
        nickname=kwargs.get("nickname", nickname),
        email=kwargs.get("email", email),
        bio=kwargs.get("bio", bio),
        avatar_color=kwargs.get("avatar_color", "#2563EB"),
    )
    return user


def build_snapshot(
    topic: str = "AI",
    start_at: datetime.datetime | None = None,
    end_at: datetime.datetime | None = None,
    data: dict[str, Any] | None = None,
    errors: list[str] | None = None,
    **kwargs: Any,
) -> AnalysisSnapshot:
    return AnalysisSnapshot(
        topic=topic,
        start_at=start_at or datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        end_at=end_at or datetime.datetime(2026, 1, 7, tzinfo=datetime.timezone.utc),
        data=data or {},
        errors=errors or [],
        generated_at=kwargs.get(
            "generated_at",
            datetime.datetime(2026, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc),
        ),
    )

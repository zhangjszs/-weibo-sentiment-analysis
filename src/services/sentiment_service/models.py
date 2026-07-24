"""情感分析结果数据模型。

拆分自原 ``sentiment_service.py``，逻辑保持不变。
"""

import logging
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class SentimentResult:
    """统一的情感分析结果对象"""

    def __init__(
        self,
        score,
        label,
        reasoning=None,
        emotion=None,
        keywords=None,
        cached=False,
        source="unknown",
    ):
        self.score = score  # 0-1 float
        self.label = label  # positive/negative/neutral
        self.reasoning = reasoning  # 分析理由 (LLM特有)
        self.emotion = emotion  # 细粒度情感 (喜怒哀乐等)
        self.keywords = keywords or []  # 关键词列表
        self.cached = cached  # 是否来自缓存
        self.source = source  # 来源：cache/llm/snownlp/fallback

    def to_dict(self):
        return {
            "score": self.score,
            "label": self.label,
            "reasoning": self.reasoning,
            "emotion": self.emotion,
            "keywords": self.keywords,
            "cached": self.cached,
            "source": self.source,
        }


class SentimentSchema(BaseModel):
    """LLM输出Schema校验"""

    score: float = Field(ge=0.0, le=1.0, default=0.5, description="情感得分，0-1之间")
    label: str = Field(default="neutral", description="情感标签")
    emotion: Optional[str] = Field(default="无感", description="细粒度情绪")
    reasoning: Optional[str] = Field(default="", max_length=100, description="分析理由")
    keywords: Optional[List[str]] = Field(
        default_factory=list, description="关键词列表"
    )

    @field_validator("label")
    def validate_label(cls, v):
        allowed = ["positive", "neutral", "negative"]
        if v not in allowed:
            return "neutral"  # 非法值自动转为neutral
        return v

"""情感分析工具模块。

Phase 3.7 起统一标签 schema：内部逻辑一律使用英文 ``positive`` / ``neutral``
/ ``negative``，仅在展示层（前端、报告、日志中文提示）通过
:func:`label_to_chinese` 转中文，避免不同模块的标签字面量混用导致的 bug。
"""


# 内部统一的英文标签常量
LABEL_POSITIVE = "positive"
LABEL_NEUTRAL = "neutral"
LABEL_NEGATIVE = "negative"

# 阈值（与 SnowNLPStrategy._determine_label 保持一致）
POSITIVE_THRESHOLD = 0.6
NEGATIVE_THRESHOLD = 0.4

# 中英文映射
_LABEL_CN_MAP = {
    LABEL_POSITIVE: "正面",
    LABEL_NEUTRAL: "中性",
    LABEL_NEGATIVE: "负面",
    "积极": "正面",
    "消极": "负面",
}
_LABEL_EN_FROM_CN = {
    "正面": LABEL_POSITIVE,
    "积极": LABEL_POSITIVE,
    "中性": LABEL_NEUTRAL,
    "负面": LABEL_NEGATIVE,
    "消极": LABEL_NEGATIVE,
}


def label_to_chinese(label: str) -> str:
    """英文 label → 中文展示文字。未知 label 返回 '中性'。"""
    if not label:
        return "中性"
    # 已是中文（含别名）→ 规范化为 canonical 中文
    if label in _LABEL_EN_FROM_CN:
        # 别名归一：积极→正面、消极→负面
        en = _LABEL_EN_FROM_CN[label]
        return _LABEL_CN_MAP[en]
    s = str(label).lower()
    if s in _LABEL_CN_MAP:
        return _LABEL_CN_MAP[s]
    return "中性"


def label_to_english(label: str) -> str:
    """任意 label（中/英）→ 英文 label。未知返回 :data:`LABEL_NEUTRAL`。"""
    if not label:
        return LABEL_NEUTRAL
    s = str(label).lower()
    if s in (LABEL_POSITIVE, LABEL_NEUTRAL, LABEL_NEGATIVE, "pos", "neu", "neg"):
        return {
            "pos": LABEL_POSITIVE,
            "neu": LABEL_NEUTRAL,
            "neg": LABEL_NEGATIVE,
        }.get(s, s)
    return _LABEL_EN_FROM_CN.get(label, LABEL_NEUTRAL)


def get_sentiment_label(score: float) -> str:
    """将情感分数转换为英文标签。

    阈值：``>0.6 → positive``、``<0.4 → negative``、其余 ``neutral``。
    展示层需要中文请用 ``label_to_chinese(get_sentiment_label(score))``。
    """
    if score > POSITIVE_THRESHOLD:
        return LABEL_POSITIVE
    if score < NEGATIVE_THRESHOLD:
        return LABEL_NEGATIVE
    return LABEL_NEUTRAL


def get_sentiment_score(label: str) -> float:
    """将情感标签转换为分数（接受中英文）。"""
    en = label_to_english(label)
    return {
        LABEL_POSITIVE: 0.8,
        LABEL_NEUTRAL: 0.5,
        LABEL_NEGATIVE: 0.2,
    }.get(en, 0.5)


def get_sentiment_type(score: float) -> str:
    """获取情感类型（英文），用于前端展示字段。"""
    return get_sentiment_label(score)


def get_sentiment_color(score: float) -> str:
    """获取情感对应的颜色。"""
    label = get_sentiment_label(score)
    return {
        LABEL_POSITIVE: "#67C23A",
        LABEL_NEUTRAL: "#E6A23C",
        LABEL_NEGATIVE: "#F56C6C",
    }.get(label, "#E6A23C")


def analyze_sentiment_distribution(scores: list) -> dict:
    """分析情感分布（key 用英文标签）。"""
    if not scores:
        return {
            LABEL_POSITIVE: 0,
            LABEL_NEUTRAL: 0,
            LABEL_NEGATIVE: 0,
            "total": 0,
            "average": 0,
        }

    positive = sum(1 for s in scores if s > POSITIVE_THRESHOLD)
    negative = sum(1 for s in scores if s < NEGATIVE_THRESHOLD)
    neutral = len(scores) - positive - negative
    total = len(scores)
    average = sum(scores) / total if total > 0 else 0

    return {
        LABEL_POSITIVE: positive,
        LABEL_NEUTRAL: neutral,
        LABEL_NEGATIVE: negative,
        "total": total,
        "average": round(average, 4),
        "positive_ratio": round(positive / total, 4) if total > 0 else 0,
        "neutral_ratio": round(neutral / total, 4) if total > 0 else 0,
        "negative_ratio": round(negative / total, 4) if total > 0 else 0,
    }


__all__ = [
    "LABEL_POSITIVE",
    "LABEL_NEUTRAL",
    "LABEL_NEGATIVE",
    "label_to_chinese",
    "label_to_english",
    "get_sentiment_label",
    "get_sentiment_score",
    "get_sentiment_type",
    "get_sentiment_color",
    "analyze_sentiment_distribution",
]

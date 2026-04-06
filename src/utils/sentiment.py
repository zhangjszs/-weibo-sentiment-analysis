"""
情感分析工具模块
提供统一的情感标签转换功能
"""


def get_sentiment_label(score: float) -> str:
    """
    将情感分数转换为标签

    Args:
        score: 情感分数 (0-1)

    Returns:
        str: 情感标签 ('正面', '中性', '负面')
    """
    if score > 0.5:
        return "正面"
    elif score == 0.5:
        return "中性"
    else:
        return "负面"


def get_sentiment_score(label: str) -> float:
    """
    将情感标签转换为分数

    Args:
        label: 情感标签

    Returns:
        float: 情感分数
    """
    label_map = {"正面": 0.8, "中性": 0.5, "负面": 0.2, "积极": 0.8, "消极": 0.2}
    return label_map.get(label, 0.5)


def get_sentiment_type(score: float) -> str:
    """
    获取情感类型（用于前端展示）

    Args:
        score: 情感分数

    Returns:
        str: 情感类型 ('positive', 'neutral', 'negative')
    """
    if score > 0.5:
        return "positive"
    elif score == 0.5:
        return "neutral"
    else:
        return "negative"


def get_sentiment_color(score: float) -> str:
    """
    获取情感对应的颜色

    Args:
        score: 情感分数

    Returns:
        str: 颜色代码
    """
    if score > 0.5:
        return "#67C23A"
    elif score == 0.5:
        return "#E6A23C"
    else:
        return "#F56C6C"


def analyze_sentiment_distribution(scores: list) -> dict:
    """
    分析情感分布

    Args:
        scores: 情感分数列表

    Returns:
        dict: 情感分布统计
    """
    if not scores:
        return {"positive": 0, "neutral": 0, "negative": 0, "total": 0, "average": 0}

    positive = sum(1 for s in scores if s > 0.5)
    neutral = sum(1 for s in scores if s == 0.5)
    negative = sum(1 for s in scores if s < 0.5)
    total = len(scores)
    average = sum(scores) / total if total > 0 else 0

    return {
        "positive": positive,
        "neutral": neutral,
        "negative": negative,
        "total": total,
        "average": round(average, 4),
        "positive_ratio": round(positive / total, 4) if total > 0 else 0,
        "neutral_ratio": round(neutral / total, 4) if total > 0 else 0,
        "negative_ratio": round(negative / total, 4) if total > 0 else 0,
    }


__all__ = [
    "get_sentiment_label",
    "get_sentiment_score",
    "get_sentiment_type",
    "get_sentiment_color",
    "analyze_sentiment_distribution",
]

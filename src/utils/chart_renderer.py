import io
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.font_manager as fm
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib 未安装，图表嵌入功能不可用")

_CHINESE_FONTS = [
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/msyh.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
]


def _get_chinese_font():
    for p in _CHINESE_FONTS:
        if os.path.exists(p):
            return fm.FontProperties(fname=p)
    return None


class ChartRenderer:
    def __init__(self):
        self._font = _get_chinese_font() if MATPLOTLIB_AVAILABLE else None

    def _to_bytes(self, fig) -> bytes:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    def render_sentiment_pie(self, data: dict) -> Optional[bytes]:
        if not MATPLOTLIB_AVAILABLE:
            return None
        summary = data.get("summary", {})
        pos = summary.get("positive_count", 0)
        neu = summary.get("neutral_count", 0)
        neg = summary.get("negative_count", 0)
        if pos + neu + neg == 0:
            return None
        fig, ax = plt.subplots(figsize=(5, 4))
        labels = ["正面", "中性", "负面"]
        sizes = [pos, neu, neg]
        colors = ["#4CAF50", "#9E9E9E", "#F44336"]
        ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct="%1.1f%%",
            textprops={"fontproperties": self._font} if self._font else {},
        )
        if self._font:
            ax.set_title("情感分布", fontproperties=self._font)
        else:
            ax.set_title("Sentiment Distribution")
        return self._to_bytes(fig)

    def render_topics_bar(self, data: dict) -> Optional[bytes]:
        if not MATPLOTLIB_AVAILABLE:
            return None
        topics = data.get("hot_topics", [])[:10]
        if not topics:
            return None
        names = [t.get("name", "")[:8] for t in topics]
        heats = [t.get("heat", 0) for t in topics]
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.barh(names[::-1], heats[::-1], color="#2196F3")
        if self._font:
            ax.set_xlabel("热度", fontproperties=self._font)
            ax.set_title("热门话题 Top 10", fontproperties=self._font)
            for label in ax.get_yticklabels():
                label.set_fontproperties(self._font)
        else:
            ax.set_xlabel("Heat")
            ax.set_title("Top Topics")
        return self._to_bytes(fig)

    def render_trend_line(self, data: dict) -> Optional[bytes]:
        if not MATPLOTLIB_AVAILABLE:
            return None
        trend = data.get("trend", [])
        if not trend:
            return None
        dates = [t.get("date", "") for t in trend]
        counts = [t.get("count", 0) for t in trend]
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(dates, counts, marker="o", color="#FF9800")
        if self._font:
            ax.set_title("舆情趋势", fontproperties=self._font)
            ax.set_xlabel("日期", fontproperties=self._font)
            ax.set_ylabel("数量", fontproperties=self._font)
        else:
            ax.set_title("Trend")
            ax.set_xlabel("Date")
            ax.set_ylabel("Count")
        ax.tick_params(axis="x", rotation=30)
        return self._to_bytes(fig)

    def render_alert_bar(self, data: dict) -> Optional[bytes]:
        if not MATPLOTLIB_AVAILABLE:
            return None
        alerts = data.get("alerts", [])
        if not alerts:
            return None
        from collections import Counter

        counts = Counter(a.get("level", "info") for a in alerts)
        levels = ["danger", "warning", "info"]
        values = [counts.get(lvl, 0) for lvl in levels]
        labels_cn = ["严重", "警告", "提示"]
        colors = ["#F44336", "#FF9800", "#2196F3"]
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.bar(labels_cn, values, color=colors)
        if self._font:
            ax.set_title("预警级别分布", fontproperties=self._font)
            for label in ax.get_xticklabels():
                label.set_fontproperties(self._font)
        else:
            ax.set_title("Alert Distribution")
        return self._to_bytes(fig)


chart_renderer = ChartRenderer()

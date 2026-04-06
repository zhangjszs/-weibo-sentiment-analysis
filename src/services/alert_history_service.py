#!/usr/bin/env python3
"""
预警历史记录管理服务
功能：历史记录存储、查询、筛选、导出、统计
"""

import csv
import io
import logging
import threading
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from models.alert import Alert, AlertHistory, AlertLevel, AlertType

logger = logging.getLogger(__name__)


@dataclass
class AlertHistoryFilter:
    """历史记录筛选条件"""

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    alert_type: Optional[AlertType] = None
    level: Optional[AlertLevel] = None
    is_read: Optional[bool] = None
    is_handled: Optional[bool] = None
    keyword: Optional[str] = None
    rule_id: Optional[str] = None

    def matches(self, alert: AlertHistory) -> bool:
        """检查是否匹配筛选条件"""
        if self.start_time and alert.created_at < self.start_time:
            return False
        if self.end_time and alert.created_at > self.end_time:
            return False
        if self.alert_type and alert.alert_type != self.alert_type:
            return False
        if self.level and alert.level != self.level:
            return False
        if self.is_read is not None and alert.is_read != self.is_read:
            return False
        if self.is_handled is not None and alert.is_handled != self.is_handled:
            return False
        if self.rule_id and alert.rule_id != self.rule_id:
            return False
        if self.keyword:
            keyword_lower = self.keyword.lower()
            if (
                keyword_lower not in alert.title.lower()
                and keyword_lower not in alert.message.lower()
            ):
                return False
        return True


@dataclass
class PaginationParams:
    """分页参数"""

    page: int = 1
    page_size: int = 20
    sort_by: str = "created_at"
    sort_order: str = "desc"


@dataclass
class PaginatedResult:
    """分页结果"""

    items: List[Dict]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class AlertHistoryManager:
    """预警历史记录管理器"""

    def __init__(self, max_records: int = 10000):
        self.max_records = max_records
        self._history: List[AlertHistory] = []
        self._lock = threading.Lock()
        self._stats_cache: Dict[str, Any] = {}
        self._stats_cache_time: Optional[datetime] = None

    def add_alert(self, alert: Alert) -> AlertHistory:
        """添加预警到历史记录"""
        history = AlertHistory(
            id=alert.id,
            rule_id=alert.rule_id,
            alert_type=alert.alert_type,
            level=alert.level,
            title=alert.title,
            message=alert.message,
            trigger_data=alert.data,
            created_at=alert.created_at,
            is_read=alert.is_read,
            is_handled=alert.is_handled,
            handler=alert.handler,
            handled_at=alert.handled_at,
        )

        with self._lock:
            self._history.append(history)

            if len(self._history) > self.max_records:
                self._history = self._history[-self.max_records :]

            self._invalidate_stats_cache()

        logger.debug(f"添加预警历史记录: {history.id}")
        return history

    def get_by_id(self, alert_id: str) -> Optional[AlertHistory]:
        """根据ID获取历史记录"""
        with self._lock:
            for alert in self._history:
                if alert.id == alert_id:
                    return alert
        return None

    def query(
        self,
        filter_params: AlertHistoryFilter = None,
        pagination: PaginationParams = None,
    ) -> PaginatedResult:
        """查询历史记录"""
        with self._lock:
            filtered = list(self._history)

        if filter_params:
            filtered = [a for a in filtered if filter_params.matches(a)]

        if pagination:
            reverse = pagination.sort_order.lower() == "desc"
            sort_key = pagination.sort_by

            def get_sort_value(alert: AlertHistory):
                if sort_key == "created_at":
                    return alert.created_at
                elif sort_key == "level":
                    level_order = {
                        AlertLevel.INFO: 0,
                        AlertLevel.WARNING: 1,
                        AlertLevel.DANGER: 2,
                        AlertLevel.CRITICAL: 3,
                    }
                    return level_order.get(alert.level, 0)
                elif sort_key == "alert_type":
                    return alert.alert_type.value
                else:
                    return alert.created_at

            filtered.sort(key=get_sort_value, reverse=reverse)

            total = len(filtered)
            total_pages = (
                (total + pagination.page_size - 1) // pagination.page_size
                if pagination.page_size > 0
                else 0
            )

            start_idx = (pagination.page - 1) * pagination.page_size
            end_idx = start_idx + pagination.page_size
            page_items = filtered[start_idx:end_idx]

            return PaginatedResult(
                items=[a.to_dict() for a in page_items],
                total=total,
                page=pagination.page,
                page_size=pagination.page_size,
                total_pages=total_pages,
                has_next=pagination.page < total_pages,
                has_prev=pagination.page > 1,
            )

        return PaginatedResult(
            items=[a.to_dict() for a in filtered],
            total=len(filtered),
            page=1,
            page_size=len(filtered),
            total_pages=1,
            has_next=False,
            has_prev=False,
        )

    def mark_read(self, alert_id: str) -> bool:
        """标记为已读"""
        with self._lock:
            for alert in self._history:
                if alert.id == alert_id:
                    alert.is_read = True
                    self._invalidate_stats_cache()
                    return True
        return False

    def mark_handled(
        self, alert_id: str, handler: str, notes: Optional[str] = None
    ) -> bool:
        """标记为已处理"""
        with self._lock:
            for alert in self._history:
                if alert.id == alert_id:
                    alert.is_handled = True
                    alert.handler = handler
                    alert.handled_at = datetime.now()
                    if notes:
                        alert.notes = notes
                    self._invalidate_stats_cache()
                    return True
        return False

    def batch_mark_read(self, alert_ids: List[str]) -> int:
        """批量标记已读"""
        count = 0
        with self._lock:
            for alert in self._history:
                if alert.id in alert_ids:
                    alert.is_read = True
                    count += 1
            self._invalidate_stats_cache()
        return count

    def batch_mark_handled(self, alert_ids: List[str], handler: str) -> int:
        """批量标记已处理"""
        count = 0
        with self._lock:
            for alert in self._history:
                if alert.id in alert_ids:
                    alert.is_handled = True
                    alert.handler = handler
                    alert.handled_at = datetime.now()
                    count += 1
            self._invalidate_stats_cache()
        return count

    def delete(self, alert_id: str) -> bool:
        """删除历史记录"""
        with self._lock:
            for i, alert in enumerate(self._history):
                if alert.id == alert_id:
                    del self._history[i]
                    self._invalidate_stats_cache()
                    return True
        return False

    def batch_delete(self, alert_ids: List[str]) -> int:
        """批量删除"""
        count = 0
        with self._lock:
            self._history = [a for a in self._history if a.id not in alert_ids]
            count = len(alert_ids)
            self._invalidate_stats_cache()
        return count

    def clear_all(self) -> int:
        """清空所有历史记录"""
        with self._lock:
            count = len(self._history)
            self._history.clear()
            self._invalidate_stats_cache()
        return count

    def _invalidate_stats_cache(self):
        """使统计缓存失效"""
        self._stats_cache = {}
        self._stats_cache_time = None

    def get_statistics(self, time_range: int = 7) -> Dict[str, Any]:
        """获取统计数据"""
        cache_key = f"stats_{time_range}"
        now = datetime.now()

        if (
            self._stats_cache_time
            and self._stats_cache.get(cache_key)
            and (now - self._stats_cache_time).total_seconds() < 300
        ):
            return self._stats_cache[cache_key]

        with self._lock:
            history = list(self._history)

        cutoff = now - timedelta(days=time_range)
        recent = [a for a in history if a.created_at >= cutoff]

        level_counts = defaultdict(int)
        type_counts = defaultdict(int)
        daily_counts = defaultdict(int)
        hourly_counts = defaultdict(int)

        for alert in recent:
            level_counts[alert.level.value] += 1
            type_counts[alert.alert_type.value] += 1

            date_key = alert.created_at.strftime("%Y-%m-%d")
            daily_counts[date_key] += 1

            hour_key = alert.created_at.strftime("%Y-%m-%d %H:00")
            hourly_counts[hour_key] += 1

        total = len(recent)
        unread = sum(1 for a in recent if not a.is_read)
        unhandled = sum(1 for a in recent if not a.is_handled)

        daily_trend = []
        for i in range(time_range):
            date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            daily_trend.append({"date": date, "count": daily_counts.get(date, 0)})
        daily_trend.reverse()

        hourly_trend = []
        for i in range(24):
            hour = (now - timedelta(hours=i)).strftime("%Y-%m-%d %H:00")
            hourly_trend.append({"hour": hour, "count": hourly_counts.get(hour, 0)})
        hourly_trend.reverse()

        stats = {
            "time_range_days": time_range,
            "total_alerts": total,
            "unread_count": unread,
            "unhandled_count": unhandled,
            "level_distribution": dict(level_counts),
            "type_distribution": dict(type_counts),
            "daily_trend": daily_trend,
            "hourly_trend": hourly_trend,
            "generated_at": now.isoformat(),
        }

        self._stats_cache[cache_key] = stats
        self._stats_cache_time = now

        return stats

    def get_level_summary(self) -> Dict[str, int]:
        """获取级别汇总"""
        with self._lock:
            counts = defaultdict(int)
            for alert in self._history:
                counts[alert.level.value] += 1
            return dict(counts)

    def get_type_summary(self) -> Dict[str, int]:
        """获取类型汇总"""
        with self._lock:
            counts = defaultdict(int)
            for alert in self._history:
                counts[alert.alert_type.value] += 1
            return dict(counts)

    def export_to_csv(self, filter_params: AlertHistoryFilter = None) -> str:
        """导出为CSV"""
        with self._lock:
            filtered = list(self._history)

        if filter_params:
            filtered = [a for a in filtered if filter_params.matches(a)]

        filtered.sort(key=lambda x: x.created_at, reverse=True)

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(
            [
                "ID",
                "规则ID",
                "预警类型",
                "预警级别",
                "标题",
                "消息",
                "创建时间",
                "已读",
                "已处理",
                "处理人",
                "处理时间",
                "备注",
            ]
        )

        for alert in filtered:
            writer.writerow(
                [
                    alert.id,
                    alert.rule_id,
                    alert.alert_type.value,
                    alert.level.value,
                    alert.title,
                    alert.message,
                    alert.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "是" if alert.is_read else "否",
                    "是" if alert.is_handled else "否",
                    alert.handler or "",
                    alert.handled_at.strftime("%Y-%m-%d %H:%M:%S")
                    if alert.handled_at
                    else "",
                    alert.notes or "",
                ]
            )

        return output.getvalue()

    def export_to_json(self, filter_params: AlertHistoryFilter = None) -> str:
        """导出为JSON"""
        import json

        with self._lock:
            filtered = list(self._history)

        if filter_params:
            filtered = [a for a in filtered if filter_params.matches(a)]

        filtered.sort(key=lambda x: x.created_at, reverse=True)

        return json.dumps([a.to_dict() for a in filtered], ensure_ascii=False, indent=2)

    def count(self) -> int:
        """获取记录总数"""
        with self._lock:
            return len(self._history)

    def count_unread(self) -> int:
        """获取未读数量"""
        with self._lock:
            return sum(1 for a in self._history if not a.is_read)

    def count_unhandled(self) -> int:
        """获取未处理数量"""
        with self._lock:
            return sum(1 for a in self._history if not a.is_handled)


alert_history_manager = AlertHistoryManager()


__all__ = [
    "AlertHistoryFilter",
    "PaginationParams",
    "PaginatedResult",
    "AlertHistoryManager",
    "alert_history_manager",
]

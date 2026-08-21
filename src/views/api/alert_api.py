#!/usr/bin/env python3
"""
预警管理API路由
功能：预警规则管理、预警历史查询、实时预警推送
"""

import logging
from datetime import datetime

from flask import Blueprint, request

from ._shared import API_PREFIX

from services.alert_service import AlertLevel, AlertRule, AlertType, alert_engine
from utils.api_response import error, ok
from utils.authz import admin_required
from utils.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

alert_bp = Blueprint("alert", __name__, url_prefix=API_PREFIX + "/alert")

bp = alert_bp  # 兼容旧引用：from views.api.alert_api import bp


@alert_bp.route("/rules", methods=["GET"])
def get_rules():
    """获取所有预警规则"""
    try:
        rules = alert_engine.get_rules()
        return ok({"rules": rules, "total": len(rules)}), 200
    except Exception as e:
        logger.error(f"获取预警规则失败: {e}")
        return error("获取预警规则失败", code=500), 500


@alert_bp.route("/rules", methods=["POST"])
@admin_required
@rate_limit(max_requests=10, window_seconds=60)
def create_rule():
    """创建预警规则"""
    try:
        data = request.json

        rule_id = data.get("id")
        name = data.get("name")
        alert_type = data.get("alert_type", "custom")
        level = data.get("level", "warning")
        conditions = data.get("conditions", {})
        cooldown_minutes = data.get("cooldown_minutes", 30)

        if not rule_id or not name:
            return error("规则ID和名称不能为空", code=400), 400

        if alert_engine.get_rule(rule_id):
            return error("规则ID已存在", code=400), 400

        rule = AlertRule(
            id=rule_id,
            name=name,
            alert_type=AlertType(alert_type),
            level=AlertLevel(level),
            conditions=conditions,
            cooldown_minutes=cooldown_minutes,
        )

        alert_engine.add_rule(rule)

        return ok({"rule": rule.to_dict()}, msg="预警规则创建成功"), 201

    except ValueError as e:
        return error(f"参数格式错误: {e}", code=400), 400
    except Exception as e:
        logger.error(f"创建预警规则失败: {e}")
        return error("创建预警规则失败", code=500), 500


@alert_bp.route("/rules/<rule_id>", methods=["PUT"])
@admin_required
@rate_limit(max_requests=20, window_seconds=60)
def update_rule(rule_id: str):
    """更新预警规则"""
    try:
        data = request.json

        allowed_fields = ["name", "enabled", "conditions", "cooldown_minutes", "level"]
        update_data = {k: v for k, v in data.items() if k in allowed_fields}

        if "level" in update_data:
            update_data["level"] = AlertLevel(update_data["level"])

        success = alert_engine.update_rule(rule_id, **update_data)

        if success:
            return ok({"rule_id": rule_id}, msg="预警规则更新成功"), 200
        else:
            return error("预警规则不存在", code=404), 404

    except Exception as e:
        logger.error(f"更新预警规则失败: {e}")
        return error("更新预警规则失败", code=500), 500


@alert_bp.route("/rules/<rule_id>", methods=["DELETE"])
@admin_required
@rate_limit(max_requests=10, window_seconds=60)
def delete_rule(rule_id: str):
    """删除预警规则"""
    try:
        success = alert_engine.remove_rule(rule_id)

        if success:
            return ok({"rule_id": rule_id}, msg="预警规则删除成功"), 200
        else:
            return error("预警规则不存在", code=404), 404

    except Exception as e:
        logger.error(f"删除预警规则失败: {e}")
        return error("删除预警规则失败", code=500), 500


@alert_bp.route("/rules/<rule_id>/toggle", methods=["POST"])
@admin_required
@rate_limit(max_requests=20, window_seconds=60)
def toggle_rule(rule_id: str):
    """切换预警规则启用状态"""
    try:
        rule = alert_engine.get_rule(rule_id)
        if not rule:
            return error("预警规则不存在", code=404), 404

        new_status = not rule.enabled
        alert_engine.update_rule(rule_id, enabled=new_status)

        status_text = "启用" if new_status else "禁用"
        return ok(
            {"rule_id": rule_id, "enabled": new_status}, msg=f"预警规则已{status_text}"
        ), 200

    except Exception as e:
        logger.error(f"切换预警规则状态失败: {e}")
        return error("操作失败", code=500), 500


@alert_bp.route("/history", methods=["GET"])
def get_history():
    """获取预警历史"""
    try:
        limit = request.args.get("limit", 50, type=int)
        level = request.args.get("level")
        unread_only = request.args.get("unread_only", "false").lower() == "true"

        limit = min(limit, 200)

        history = alert_engine.get_alert_history(
            limit=limit, level=level, unread_only=unread_only
        )

        return ok({"alerts": history, "total": len(history)}), 200

    except Exception as e:
        logger.error(f"获取预警历史失败: {e}")
        return error("获取预警历史失败", code=500), 500


@alert_bp.route("/stats", methods=["GET"])
def get_stats():
    """获取预警统计"""
    try:
        stats = alert_engine.get_stats()
        return ok(stats), 200
    except Exception as e:
        logger.error(f"获取预警统计失败: {e}")
        return error("获取预警统计失败", code=500), 500


@alert_bp.route("/unread-count", methods=["GET"])
def get_unread_count():
    """获取未读预警数量"""
    try:
        count = alert_engine.get_unread_count()
        return ok({"unread_count": count}), 200
    except Exception as e:
        logger.error(f"获取未读数量失败: {e}")
        return error("获取未读数量失败", code=500), 500


@alert_bp.route("/<alert_id>/read", methods=["POST"])
def mark_read(alert_id: str):
    """标记预警已读"""
    try:
        success = alert_engine.mark_alert_read(alert_id)

        if success:
            return ok({"alert_id": alert_id}, msg="已标记为已读"), 200
        else:
            return error("预警不存在", code=404), 404

    except Exception as e:
        logger.error(f"标记已读失败: {e}")
        return error("操作失败", code=500), 500


@alert_bp.route("/read-all", methods=["POST"])
@admin_required
def mark_all_read():
    """标记所有预警已读"""
    try:
        count = alert_engine.mark_all_read()
        return ok({"marked_count": count}, msg=f"已标记{count}条预警为已读"), 200
    except Exception as e:
        logger.error(f"标记全部已读失败: {e}")
        return error("操作失败", code=500), 500


@alert_bp.route("/test", methods=["POST"])
@admin_required
@rate_limit(max_requests=5, window_seconds=60)
def test_alert():
    """测试预警功能"""
    try:
        data = request.json
        alert_type = data.get("type", "info")
        message = data.get("message", "这是一条测试预警")

        from utils.websocket_server import ws_manager

        test_alert_data = {
            "id": "test_" + datetime.now().strftime("%Y%m%d%H%M%S"),
            "rule_id": "test",
            "rule_name": "测试预警",
            "alert_type": "custom",
            "level": alert_type,
            "title": "测试预警",
            "message": message,
            "data": {},
            "created_at": datetime.now().isoformat(),
            "is_read": False,
        }

        ws_manager.broadcast_alert(test_alert_data)

        return ok({"alert": test_alert_data}, msg="测试预警已发送"), 200

    except Exception as e:
        logger.error(f"发送测试预警失败: {e}")
        return error("发送测试预警失败", code=500), 500


@alert_bp.route("/evaluate", methods=["POST"])
@admin_required
@rate_limit(max_requests=30, window_seconds=60)
def evaluate_data():
    """评估数据触发预警

    P0 #5 修复：此前调用不存在的 ``evaluate_volume_spike`` 等公开方法（实际只有
    ``_evaluate_*`` 私有方法、签名不同）→ 必抛 AttributeError。改为构造 metrics
    交给 ``check_alerts`` 统一评估，再按 type 过滤返回首条触发的预警（每条规则
    alert_type 唯一，匹配的就是目标规则）。
    """
    try:
        data = request.json
        eval_type = data.get("type")

        # 构造 metrics：字段名与 _evaluate_* 期望的 metrics key 对齐
        if eval_type == "volume_spike":
            metrics = {
                "current_count": data.get("current_count", 0),
                "baseline_count": data.get("baseline_count", 0),
                "time_window_minutes": data.get("time_window", 60),
            }
        elif eval_type == "negative_surge":
            metrics = {
                "negative_count": data.get("negative_count", 0),
                "total_count": data.get("total_count", 0),
                "time_window_minutes": data.get("time_window", 30),
            }
        elif eval_type == "sentiment_shift":
            metrics = {
                "current_sentiment": data.get("current_sentiment", 0.5),
                "previous_sentiment": data.get("previous_sentiment", 0.5),
                "time_window_minutes": data.get("time_window", 30),
            }
        elif eval_type == "hot_topic":
            metrics = {
                "topic_mentions": data.get("topic_mentions", 0),
                "topic_name": data.get("topic_name", ""),
                "time_window_minutes": data.get("time_window", 60),
            }
        else:
            return ok({"triggered": False, "message": f"未知评估类型: {eval_type}"}), 200

        alerts = alert_engine.check_alerts(metrics)
        alert = next(
            (a for a in alerts if a.alert_type and a.alert_type.value == eval_type),
            None,
        )

        if alert:
            return ok({"triggered": True, "alert": alert.to_dict()}), 200
        else:
            return ok({"triggered": False, "message": "未触发预警"}), 200

    except Exception as e:
        logger.error(f"评估预警失败: {e}")
        return error("评估预警失败", code=500), 500

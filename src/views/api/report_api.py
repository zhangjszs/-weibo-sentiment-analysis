#!/usr/bin/env python3
"""
报告生成API路由
功能：PDF/PPT报告生成、下载、模板管理
"""

import logging
import os
import re
import tempfile
import time
import uuid
from datetime import datetime

from flask import Blueprint, request, send_file

from repositories.article_repository import ArticleRepository
from repositories.comment_repository import CommentRepository
from utils.api_response import error, ok
from utils.data_provenance import demo_meta, provenance_response, real_meta
from utils.rate_limiter import rate_limit
from utils.report_generator import ReportConfig, report_generator
from utils.request_validation import get_bounded_str, get_json_body, sanitize_text

from ._shared import API_PREFIX

logger = logging.getLogger(__name__)

report_bp = Blueprint("report", __name__, url_prefix=API_PREFIX + "/report")

bp = report_bp  # 兼容旧引用：from views.api.report_api import bp

_ALLOWED_REPORT_EXTENSIONS = {".pdf", ".pptx"}
# 仅允许本系统生成的文件名前缀，防止指向任意系统文件
_ALLOWED_REPORT_BASENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\-]*$")


def _resolve_report_path(filename: str) -> str | None:
    """校验下载/预览文件名并解析为 tmp 目录内的绝对路径。

    防护：basename 收敛 + 扩展名白名单 + 解析后路径仍在 tmp 内。
    不合法或不存在返回 None（调用方统一返回 404 JSON）。
    """
    if not filename or not isinstance(filename, str):
        return None
    # 拒绝路径分隔符与遍历序列
    if "/" in filename or "\\" in filename:
        return None
    basename = os.path.basename(filename)
    if basename != filename or basename in ("", ".", ".."):
        return None
    if basename.startswith("report_") is False and basename.startswith("reports_") is False:
        # 兼容历史文件：仅放行 report_ 前缀；目录形式一律拒绝
        return None
    if not _ALLOWED_REPORT_BASENAME_RE.match(basename):
        return None
    _, ext = os.path.splitext(basename)
    if ext.lower() not in _ALLOWED_REPORT_EXTENSIONS:
        return None
    temp_dir = os.path.realpath(tempfile.gettempdir())
    candidate = os.path.realpath(os.path.join(temp_dir, basename))
    if os.path.dirname(candidate) != temp_dir:
        return None
    return candidate


def _unique_report_filename(prefix: str, ext: str) -> str:
    """秒级 timestamp + 随机后缀，避免并发覆盖。"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}_{uuid.uuid4().hex[:8]}{ext}"


def cleanup_expired_reports(max_age_hours: float | None = None) -> int:
    """删除 tmp 内超期的本系统报告文件/目录，消费 REPORT_TEMP_CLEANUP_HOURS。

    Returns: 清理的文件/目录数量（best-effort，失败跳过单个条目）。
    """
    from config.settings import Config

    hours = max_age_hours if max_age_hours is not None else Config.REPORT_TEMP_CLEANUP_HOURS
    try:
        cutoff = time.time() - float(hours) * 3600
    except (TypeError, ValueError):
        cutoff = time.time() - 3600
    temp_dir = tempfile.gettempdir()
    removed = 0
    try:
        entries = os.listdir(temp_dir)
    except OSError:
        return 0
    for entry in entries:
        if not (entry.startswith("report_") or entry.startswith("reports_")):
            continue
        path = os.path.join(temp_dir, entry)
        try:
            if os.path.getmtime(path) > cutoff:
                continue
            if os.path.isdir(path):
                import shutil

                shutil.rmtree(path, ignore_errors=True)
            else:
                _, ext = os.path.splitext(entry)
                if ext.lower() not in _ALLOWED_REPORT_EXTENSIONS:
                    continue
                os.remove(path)
            removed += 1
        except OSError:
            continue
    return removed


def _coerce_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_demo_mode(default: bool = False) -> bool:
    return _coerce_bool(request.args.get("demo"), default)


def _article_repo() -> ArticleRepository:
    return ArticleRepository()


def _comment_repo() -> CommentRepository:
    return CommentRepository()


def get_demo_report_data():
    """获取演示报告数据"""
    return {
        "summary": {
            "total_articles": 12580,
            "total_comments": 89632,
            "positive_count": 45230,
            "neutral_count": 28450,
            "negative_count": 15952,
        },
        "sentiment_analysis": {
            "正面情感占比": "50.5%",
            "中性情感占比": "31.7%",
            "负面情感占比": "17.8%",
            "情感倾向指数": "0.68",
            "情感波动趋势": "整体稳定，略有上升",
        },
        "hot_topics": [
            {"name": "科技创新", "heat": 9856},
            {"name": "人工智能", "heat": 8742},
            {"name": "新能源", "heat": 7653},
            {"name": "数字经济", "heat": 6521},
            {"name": "绿色发展", "heat": 5896},
            {"name": "智慧城市", "heat": 5234},
            {"name": "乡村振兴", "heat": 4567},
            {"name": "教育改革", "heat": 4123},
            {"name": "医疗健康", "heat": 3890},
            {"name": "文化传承", "heat": 3456},
        ],
        "alerts": [
            {
                "level": "danger",
                "title": "负面舆情激增",
                "message": "过去30分钟内检测到50条负面评论",
            },
            {
                "level": "warning",
                "title": "讨论量异常增长",
                "message": "讨论量达到基线的3.5倍",
            },
            {
                "level": "info",
                "title": "热点话题出现",
                "message": "话题「科技创新」被提及超过100次",
            },
        ],
        "trend": [
            {"date": "2026-02-15", "count": 850},
            {"date": "2026-02-16", "count": 920},
            {"date": "2026-02-17", "count": 1100},
            {"date": "2026-02-18", "count": 980},
            {"date": "2026-02-19", "count": 1250},
            {"date": "2026-02-20", "count": 1180},
            {"date": "2026-02-21", "count": 1350},
        ],
    }


def _empty_report_data():
    return {
        "summary": {
            "total_articles": 0,
            "total_comments": 0,
            "positive_count": 0,
            "neutral_count": 0,
            "negative_count": 0,
        },
        "sentiment_analysis": {
            "正面情感占比": "0.0%",
            "中性情感占比": "0.0%",
            "负面情感占比": "0.0%",
            "情感倾向指数": "0.00",
            "情感波动趋势": "暂无真实数据",
        },
        "hot_topics": [],
        "alerts": [],
        "trend": [],
    }


def _build_report_data(demo_mode: bool = False):
    """构建报告数据：默认真实数据，仅显式请求时返回演示数据。"""
    if demo_mode:
        return get_demo_report_data(), "demo", True

    try:
        total_articles = _article_repo().count_total()
        total_comments = _comment_repo().count_total()

        positive_count = 0
        neutral_count = 0
        negative_count = 0

        try:
            from services.sentiment_service import SentimentService

            sentiment_counts = SentimentService.analyze_distribution_cached(
                _comment_repo().get_recent_texts(limit=200),
                mode="simple",
                sample_size=200,
            )
            positive_count = int(sentiment_counts.get("正面", 0))
            neutral_count = int(sentiment_counts.get("中性", 0))
            negative_count = int(sentiment_counts.get("负面", 0))
        except Exception as exc:
            logger.warning(f"获取情感分布失败，返回空统计: {exc}")

        sentiment_total = positive_count + neutral_count + negative_count
        if sentiment_total <= 0:
            sentiment_total = 1

        hot_topics = []
        try:
            from utils.getPublicData import getAllCiPingTotal

            for item in getAllCiPingTotal()[:10]:
                if len(item) >= 2:
                    hot_topics.append(
                        {
                            "name": str(item[0]),
                            "heat": int(item[1]),
                        }
                    )
        except Exception as exc:
            logger.warning(f"获取热门话题失败: {exc}")

        alerts = []
        try:
            from services.alert_service import alert_engine

            alert_history = alert_engine.get_alert_history(limit=5)
            for alert in alert_history:
                alerts.append(
                    {
                        "level": alert.get("level", "info"),
                        "title": alert.get("title", "系统预警"),
                        "message": alert.get("message", ""),
                    }
                )
        except Exception as exc:
            logger.warning(f"获取预警历史失败: {exc}")

        trend = []
        try:
            trend_rows = _comment_repo().get_recent_trend(days=7)
            trend = [
                {
                    "date": str(row.get("date")),
                    "count": int(row.get("count") or 0),
                }
                for row in trend_rows
                if row.get("date") is not None
            ]
        except Exception as exc:
            logger.warning(f"获取趋势数据失败，返回空趋势: {exc}")

        positive_ratio = positive_count / sentiment_total
        neutral_ratio = neutral_count / sentiment_total
        negative_ratio = negative_count / sentiment_total
        sentiment_index = (positive_count - negative_count) / sentiment_total

        report_data = {
            "summary": {
                "total_articles": total_articles,
                "total_comments": total_comments,
                "positive_count": positive_count,
                "neutral_count": neutral_count,
                "negative_count": negative_count,
            },
            "sentiment_analysis": {
                "正面情感占比": f"{positive_ratio * 100:.1f}%",
                "中性情感占比": f"{neutral_ratio * 100:.1f}%",
                "负面情感占比": f"{negative_ratio * 100:.1f}%",
                "情感倾向指数": f"{sentiment_index:.2f}",
                "情感波动趋势": "近7日趋势见附图",
            },
            "hot_topics": hot_topics,
            "alerts": alerts,
            "trend": trend,
        }
        return report_data, "real", False
    except Exception as exc:
        logger.warning(f"构建真实报告数据失败，返回空报告数据: {exc}")
        return _empty_report_data(), "real_error", False


@report_bp.route("/generate", methods=["POST"])
@rate_limit(max_requests=5, window_seconds=60)
def generate_report():
    """
    生成报告

    Body:
        format: 报告格式
        title: 报告标题
        data: 报告数据 (可选，不提供则使用演示数据)
    """
    try:
        data = get_json_body()

        format_type = get_bounded_str(data.get("format", "pdf"), max_length=10).lower()
        title = sanitize_text(data.get("title", "舆情分析报告"), max_length=100)
        input_report_data = data.get("data")
        if input_report_data is not None and not isinstance(input_report_data, dict):
            return error("data 必须为对象", code=400), 400
        if isinstance(input_report_data, dict) and len(str(input_report_data)) > 500000:
            return error("data 数据过大", code=400), 400
        request_demo_mode = _coerce_bool(data.get("demo_mode"), False)
        report_data = input_report_data
        if not report_data:
            report_data, _source, _effective_demo_mode = _build_report_data(
                request_demo_mode
            )

        if format_type not in ["pdf", "ppt"]:
            return error("不支持的报告格式，请选择 pdf 或 ppt", code=400), 400

        template = get_bounded_str(data.get("template", "standard"), max_length=20) or "standard"
        if template not in ("brief", "standard", "detailed"):
            return error("不支持的报告模板", code=400), 400
        sections = data.get("sections", None)
        if sections is not None and (
            not isinstance(sections, list)
            or len(sections) > 20
            or not all(isinstance(x, str) for x in sections)
        ):
            return error("sections 必须为字符串数组（最多 20 项）", code=400), 400

        config = ReportConfig(
            title=title,
            subtitle=f"自动生成于 {datetime.now().strftime('%Y年%m月%d日 %H:%M')}",
            author="微博舆情分析系统",
            template=template,
            sections=sections,
        )

        temp_dir = tempfile.gettempdir()
        try:
            cleanup_expired_reports()
        except Exception:
            pass

        if format_type == "pdf":
            output_path = os.path.join(temp_dir, _unique_report_filename("report", ".pdf"))
        else:
            output_path = os.path.join(temp_dir, _unique_report_filename("report", ".pptx"))

        result_path = report_generator.generate_report(
            report_data, format=format_type, output_path=output_path, config=config
        )

        if result_path:
            data_count = 0
            if isinstance(report_data, dict):
                summary = report_data.get("summary", {})
                data_count = (summary.get("total_articles") or 0) + (summary.get("total_comments") or 0)

            meta = demo_meta(topic=title, data_count=data_count) if request_demo_mode else real_meta(topic=title, data_count=data_count)
            return provenance_response(
                {
                    "file_path": result_path,
                    "download_url": f"/api/report/download/{os.path.basename(result_path)}",
                    "format": format_type,
                    "generated_at": datetime.now().isoformat(),
                },
                meta,
                msg="报告生成成功",
            ), 200
        else:
            return error("报告生成失败", code=500), 500

    except Exception as e:
        logger.error(f"报告生成失败: {e}")
        return error("报告生成失败", code=500), 500


@report_bp.route("/generate-all", methods=["POST"])
@rate_limit(max_requests=3, window_seconds=60)
def generate_all_reports():
    """生成所有格式报告"""
    try:
        data = get_json_body()
        title = sanitize_text(data.get("title", "舆情分析报告"), max_length=100)
        input_report_data = data.get("data")
        if input_report_data is not None and not isinstance(input_report_data, dict):
            return error("data 必须为对象", code=400), 400
        request_demo_mode = _coerce_bool(data.get("demo_mode"), False)
        report_data = input_report_data
        if not report_data:
            report_data, _source, _effective_demo_mode = _build_report_data(
                request_demo_mode
            )

        config = ReportConfig(
            title=title,
            subtitle=f"自动生成于 {datetime.now().strftime('%Y年%m月%d日 %H:%M')}",
            author="微博舆情分析系统",
        )

        temp_dir = tempfile.gettempdir()
        try:
            cleanup_expired_reports()
        except Exception:
            pass
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(temp_dir, f"reports_{timestamp}_{uuid.uuid4().hex[:8]}")

        results = report_generator.generate_all(report_data, output_dir, config)

        if results:
            data_count = 0
            if isinstance(report_data, dict):
                summary = report_data.get("summary", {})
                data_count = (summary.get("total_articles") or 0) + (summary.get("total_comments") or 0)

            meta = demo_meta(topic=title, data_count=data_count) if request_demo_mode else real_meta(topic=title, data_count=data_count)
            return provenance_response(
                {
                    "files": {
                        fmt: {
                            "file_path": path,
                            "download_url": f"/api/report/download/{os.path.basename(path)}",
                        }
                        for fmt, path in results.items()
                    },
                    "generated_at": datetime.now().isoformat(),
                },
                meta,
                msg="报告生成成功",
            ), 200
        else:
            return error("报告生成失败", code=500), 500

    except Exception as e:
        logger.error(f"批量报告生成失败: {e}")
        return error("报告生成失败", code=500), 500


@report_bp.route("/download/<filename>", methods=["GET"])
def download_report(filename: str):
    """下载报告文件"""
    try:
        file_path = _resolve_report_path(filename)
        if not file_path or not os.path.isfile(file_path):
            return error("文件不存在", code=404), 404

        return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path))

    except Exception as e:
        logger.error(f"文件下载失败: {e}")
        return error("文件下载失败", code=500), 500


@report_bp.route("/preview/<filename>", methods=["GET"])
def preview_report(filename: str):
    """预览报告文件"""
    try:
        file_path = _resolve_report_path(filename)
        if not file_path or not os.path.isfile(file_path):
            return error("文件不存在", code=404), 404

        return send_file(file_path)

    except Exception as e:
        logger.error(f"文件预览失败: {e}")
        return error("文件预览失败", code=500), 500


@report_bp.route("/templates", methods=["GET"])
def get_templates():
    """获取报告模板列表"""
    templates = [
        {
            "id": "brief",
            "name": "简报",
            "description": "精简版报告，仅包含核心数据",
            "sections": ["summary", "sentiment"],
            "chart_slots": ["sentiment_pie"],
        },
        {
            "id": "standard",
            "name": "标准报告",
            "description": "包含数据概览、情感分析、热门话题、预警记录",
            "sections": ["summary", "sentiment", "topics", "alerts"],
            "chart_slots": ["sentiment_pie", "topics_bar", "alert_bar"],
        },
        {
            "id": "detailed",
            "name": "详细报告",
            "description": "完整版报告，包含所有分析内容",
            "sections": ["summary", "sentiment", "topics", "alerts", "trend"],
            "chart_slots": ["sentiment_pie", "topics_bar", "alert_bar", "trend_line"],
        },
    ]

    return ok({"templates": templates}), 200


@report_bp.route("/demo-data", methods=["GET"])
def get_demo_data():
    """获取演示数据"""
    report_data, data_source, effective_demo_mode = _build_report_data(True)
    report_data["demo_mode"] = effective_demo_mode
    report_data["data_source"] = data_source
    return ok(report_data), 200


@report_bp.route("/data", methods=["GET"])
def get_report_data():
    """获取报告数据（默认真实数据，可通过 demo=true 强制演示数据）"""
    demo_mode = _parse_demo_mode(default=False)
    report_data, data_source, effective_demo_mode = _build_report_data(demo_mode)
    report_data["demo_mode"] = effective_demo_mode
    report_data["data_source"] = data_source
    return ok(report_data), 200

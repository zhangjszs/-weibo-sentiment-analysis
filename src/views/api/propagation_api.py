#!/usr/bin/env python3
"""
传播路径分析API路由
功能：转发链路追踪、传播可视化、KOL影响力分析
"""

import logging
import random
from datetime import datetime, timedelta

from flask import Blueprint, request

from services.propagation_analyzer import PropagationAnalyzer
from utils.api_response import error, ok
from utils.query import querys
from utils.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

bp = Blueprint("propagation", __name__, url_prefix="/api/propagation")
_REPOSTS_TABLE_MISSING = False


def _parse_demo_mode(default: bool = False) -> bool:
    raw = request.args.get("demo")
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _normalize_reposts(rows):
    reposts = []
    for idx, row in enumerate(rows):
        reposts.append(
            {
                "id": row.get("id") or f"repost_{idx + 1}",
                "user_id": row.get("user_id") or f"user_{idx + 1}",
                "user_name": row.get("user_name") or "未知用户",
                "content": row.get("content") or "",
                "post_time": row.get("post_time"),
                "repost_count": int(row.get("repost_count") or 0),
                "comment_count": int(row.get("comment_count") or 0),
                "like_count": int(row.get("like_count") or 0),
                "depth": int(row.get("depth") or 0),
                "parent_id": row.get("parent_id"),
            }
        )
    return reposts


def _load_reposts(article_id: str, count: int, demo_mode: bool):
    """加载传播数据：默认只返回真实数据，演示模式需显式开启。"""
    global _REPOSTS_TABLE_MISSING

    if demo_mode:
        return generate_demo_data(article_id, count), "demo", True

    if _REPOSTS_TABLE_MISSING:
        return [], "reposts_table_missing", False

    try:
        rows = querys(
            """SELECT id, user_id, article_id, content, created_at AS post_time,
                      repost_count, comment_count, like_count, depth, parent_id
               FROM reposts
               WHERE article_id = %s
               ORDER BY created_at ASC
               LIMIT %s""",
            [article_id, max(1, min(count, 500))],
            "select",
        )

        if not rows:
            logger.info("传播数据未查询到真实内容")
            return [], "reposts_empty", False

        user_ids = sorted({row.get("user_id") for row in rows if row.get("user_id")})
        user_name_map = {}
        # 限制用户ID数量，防止 DoS 攻击
        if user_ids and len(user_ids) <= 1000:
            placeholders = ",".join(["%s"] * len(user_ids))
            user_rows = querys(
                f"SELECT id, username FROM user WHERE id IN ({placeholders})",
                user_ids,
                "select",
            )
            user_name_map = {str(u.get("id")): u.get("username") for u in user_rows}
        elif len(user_ids) > 1000:
            logger.warning(f"用户ID数量过多({len(user_ids)})，限制查询前1000个")

        normalized_rows = []
        for row in rows:
            copied = dict(row)
            user_id = str(copied.get("user_id") or "")
            copied["user_name"] = user_name_map.get(user_id) or f"用户{user_id or '未知'}"
            normalized_rows.append(copied)

        return _normalize_reposts(normalized_rows), "reposts_table", False
    except Exception as exc:
        error_text = str(exc)
        if "doesn't exist" in error_text and "reposts" in error_text:
            _REPOSTS_TABLE_MISSING = True
            logger.info("reposts 表不存在")
            return [], "reposts_table_missing", False
        else:
            logger.warning(f"加载真实传播数据失败: {exc}")
        return [], "reposts_table_error", False


def _no_real_data_response(article_id: str, data_source: str):
    return (
        error(
            f"未找到文章 {article_id} 的真实传播数据，可显式传入 demo=true 查看演示链路",
            code=404,
            data={"article_id": article_id, "data_source": data_source},
        ),
        404,
    )


def generate_demo_data(article_id: str, count: int = 100):
    """生成演示数据"""
    nodes = []

    users = [
        ("user_001", "科技观察家", True),
        ("user_002", "互联网分析师", True),
        ("user_003", "微博大V", True),
        ("user_004", "普通用户A", False),
        ("user_005", "普通用户B", False),
        ("user_006", "媒体账号", True),
        ("user_007", "行业专家", True),
        ("user_008", "热心网友", False),
        ("user_009", "资讯博主", True),
        ("user_010", "路人甲", False),
    ]

    base_time = datetime.now() - timedelta(hours=24)

    origin_node = {
        "id": f"{article_id}_origin",
        "user_id": users[0][0],
        "user_name": users[0][1],
        "content": "这是一条原始微博内容，讨论了最新的科技动态...",
        "post_time": base_time,
        "repost_count": random.randint(500, 2000),
        "comment_count": random.randint(100, 500),
        "like_count": random.randint(1000, 5000),
        "depth": 0,
        "parent_id": None,
    }
    nodes.append(origin_node)

    for i in range(1, count):
        user = users[i % len(users)]
        parent_idx = random.randint(0, max(0, i - 1))
        parent = nodes[parent_idx]

        depth = min(parent["depth"] + 1, 5)

        node = {
            "id": f"{article_id}_repost_{i}",
            "user_id": user[0],
            "user_name": user[1],
            "content": f"转发微博，发表了自己的看法... #{i}",
            "post_time": base_time + timedelta(minutes=random.randint(1, 1440)),
            "repost_count": random.randint(0, 500)
            if user[2]
            else random.randint(0, 50),
            "comment_count": random.randint(0, 200)
            if user[2]
            else random.randint(0, 20),
            "like_count": random.randint(0, 1000)
            if user[2]
            else random.randint(0, 100),
            "depth": min(depth, 5),
            "parent_id": parent["id"],
        }
        nodes.append(node)

    return nodes


@bp.route("/analyze/<article_id>", methods=["GET"])
def analyze_propagation(article_id: str):
    """
    分析文章传播路径

    Args:
        article_id: 文章ID
    """
    try:
        analyzer = PropagationAnalyzer()

        demo_mode = _parse_demo_mode(default=False)
        node_count = request.args.get("count", 100, type=int)
        reposts, data_source, effective_demo_mode = _load_reposts(
            article_id, node_count, demo_mode
        )
        if not reposts and not effective_demo_mode:
            return _no_real_data_response(article_id, data_source)

        node_count = analyzer.build_from_reposts(reposts)

        summary = analyzer.get_summary()

        return ok(
            {
                "article_id": article_id,
                "node_count": node_count,
                "summary": summary,
                "demo_mode": effective_demo_mode,
                "data_source": data_source,
            }
        ), 200

    except Exception as e:
        logger.error(f"传播路径分析失败: {e}")
        return error("传播路径分析失败", code=500), 500


@bp.route("/graph/<article_id>", methods=["GET"])
def get_propagation_graph(article_id: str):
    """获取传播图数据（用于可视化）"""
    try:
        analyzer = PropagationAnalyzer()

        demo_mode = _parse_demo_mode(default=False)
        node_count = request.args.get("count", 80, type=int)
        reposts, data_source, effective_demo_mode = _load_reposts(
            article_id, node_count, demo_mode
        )
        if not reposts and not effective_demo_mode:
            return _no_real_data_response(article_id, data_source)

        analyzer.build_from_reposts(reposts)
        graph_data = analyzer.get_graph_data()
        graph_data["demo_mode"] = effective_demo_mode
        graph_data["data_source"] = data_source

        return ok(graph_data), 200

    except Exception as e:
        logger.error(f"获取传播图失败: {e}")
        return error("获取传播图失败", code=500), 500


@bp.route("/kol/<article_id>", methods=["GET"])
def get_kol_analysis(article_id: str):
    """获取KOL影响力分析"""
    try:
        analyzer = PropagationAnalyzer()

        demo_mode = _parse_demo_mode(default=False)
        node_count = request.args.get("count", 100, type=int)
        reposts, data_source, effective_demo_mode = _load_reposts(
            article_id, node_count, demo_mode
        )
        if not reposts and not effective_demo_mode:
            return _no_real_data_response(article_id, data_source)

        analyzer.build_from_reposts(reposts)

        kol_nodes = analyzer.get_kol_nodes()
        user_ranking = analyzer.get_user_influence_ranking(20)

        return ok(
            {
                "article_id": article_id,
                "kol_count": len(kol_nodes),
                "kol_nodes": [n.to_dict() for n in kol_nodes],
                "user_ranking": user_ranking,
                "demo_mode": effective_demo_mode,
                "data_source": data_source,
            }
        ), 200

    except Exception as e:
        logger.error(f"KOL分析失败: {e}")
        return error("KOL分析失败", code=500), 500


@bp.route("/timeline/<article_id>", methods=["GET"])
def get_propagation_timeline(article_id: str):
    """获取传播时间线"""
    try:
        analyzer = PropagationAnalyzer()

        interval = request.args.get("interval", 60, type=int)
        demo_mode = _parse_demo_mode(default=False)
        node_count = request.args.get("count", 100, type=int)
        reposts, data_source, effective_demo_mode = _load_reposts(
            article_id, node_count, demo_mode
        )
        if not reposts and not effective_demo_mode:
            return _no_real_data_response(article_id, data_source)
        analyzer.build_from_reposts(reposts)

        time_dist = analyzer.get_time_distribution(interval)

        return ok(
            {
                "article_id": article_id,
                "interval_minutes": interval,
                "timeline": time_dist,
                "demo_mode": effective_demo_mode,
                "data_source": data_source,
            }
        ), 200

    except Exception as e:
        logger.error(f"获取传播时间线失败: {e}")
        return error("获取传播时间线失败", code=500), 500


@bp.route("/depth/<article_id>", methods=["GET"])
def get_depth_distribution(article_id: str):
    """获取传播深度分布"""
    try:
        analyzer = PropagationAnalyzer()
        demo_mode = _parse_demo_mode(default=False)
        node_count = request.args.get("count", 100, type=int)
        reposts, data_source, effective_demo_mode = _load_reposts(
            article_id, node_count, demo_mode
        )
        if not reposts and not effective_demo_mode:
            return _no_real_data_response(article_id, data_source)
        analyzer.build_from_reposts(reposts)

        depth_dist = analyzer.get_depth_distribution()
        max_depth = 0
        if depth_dist:
            try:
                max_depth = max(int(k) for k in depth_dist.keys())
            except Exception:
                max_depth = max(depth_dist.keys())

        return ok(
            {
                "article_id": article_id,
                "depth_distribution": depth_dist,
                "max_depth": max_depth,
                "demo_mode": effective_demo_mode,
                "data_source": data_source,
            }
        ), 200

    except Exception as e:
        logger.error(f"获取深度分布失败: {e}")
        return error("获取深度分布失败", code=500), 500


@bp.route("/compare", methods=["POST"])
@rate_limit(max_requests=10, window_seconds=60)
def compare_propagation():
    """对比多条传播路径"""
    try:
        data = request.json
        article_ids = data.get("article_ids", [])

        if not article_ids or len(article_ids) < 2:
            return error("请提供至少2个文章ID", code=400), 400

        if len(article_ids) > 5:
            return error("最多对比5条传播路径", code=400), 400

        results = []
        demo_mode = _parse_demo_mode(default=False)

        for aid in article_ids:
            analyzer = PropagationAnalyzer()
            reposts, data_source, effective_demo_mode = _load_reposts(
                aid, 150, demo_mode
            )
            if not reposts and not effective_demo_mode:
                return _no_real_data_response(aid, data_source)
            analyzer.build_from_reposts(reposts)

            path = analyzer.analyze_propagation_path()
            results.append(
                {
                    "article_id": aid,
                    "total_nodes": path.total_nodes,
                    "total_depth": path.total_depth,
                    "total_reposts": path.total_reposts,
                    "propagation_speed": path.propagation_speed,
                    "kol_count": len(analyzer.get_kol_nodes()),
                    "demo_mode": effective_demo_mode,
                    "data_source": data_source,
                }
            )

        return ok({"comparison": results}), 200

    except Exception as e:
        logger.error(f"传播路径对比失败: {e}")
        return error("传播路径对比失败", code=500), 500

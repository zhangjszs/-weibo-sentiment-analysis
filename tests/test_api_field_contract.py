#!/usr/bin/env python3
"""前端消费端点字段契约·第一批（#45）——防 #38 型字段漂移。

字段清单以**前端实际读取**为准（调查见 issue #45 执行报告），每条断言注明
消费方来源文件。覆盖 13 个端点（/api/bigscreen/all 已随 #54 删除——无任何消费方）；
其中 /api/alert/unread-count 当前无活跃消费方（仅孤儿组件），
/api/stats/today 的消费方为遗留页面模板 base_page.html:922（SPA 无）。
形状按后端实现钉住并在注释说明。

发现的前后端不一致（均有结论）：
- /api/bigscreen/trend：前端读 positive/neutral/negative，后端返回 counts
  ——漂移已立 #53，测试以 strict-xfail 标注（修复落地时 XPASS 强制更新）。
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.api

# ---------------------------------------------------------------------------
# 造数（沿用 #47 的种子模式）
# ---------------------------------------------------------------------------


@pytest.fixture
def seeded_ids():
    """tester 用户 / 文章 1 / 一条未读预警 / 一条收藏。返回 alert_id。"""
    from database import db_session
    from models.alert import Alert, AlertLevel, AlertType
    from models.article import Article
    from models.user import User
    from models.user_favorite import UserFavorite

    tester = User(username="tester", password="x" * 60)
    tester.id = 1
    db_session.add(tester)
    db_session.add(
        Article(
            id="1",
            content="舆情分析系统契约测试文章，包含情感词汇：开心 愤怒 悲伤",
            type="post",
            region="广东",
        )
    )
    db_session.add(
        Alert(
            id="contract-alert-1",
            rule_id="contract-rule",
            rule_name="契约测试规则",
            alert_type=AlertType.KEYWORD_MATCH,
            level=AlertLevel.WARNING,
            title="契约测试预警",
            message="契约测试预警内容",
        )
    )
    db_session.add(UserFavorite(user_id=1, article_id="1"))
    db_session.commit()
    yield "contract-alert-1"
    db_session.rollback()


@pytest.fixture
def bearer_headers(monkeypatch):
    """管理员视角 Bearer 头（大屏/预警端点为管理员可见）。"""
    from utils import authz
    from utils.jwt_handler import create_token

    monkeypatch.setattr(authz.Config, "ADMIN_USERS", {"tester"})
    return {"Authorization": f"Bearer {create_token(1, 'tester')}"}


def _get_data(client, path, headers):
    resp = client.get(path, headers=headers)
    assert resp.status_code == 200, f"{path} → {resp.status_code} {resp.data[:160]!r}"
    body = resp.get_json()
    assert body["code"] == 200, f"{path}: code={body['code']} msg={body['msg']}"
    return body["data"]


def _assert_field(data, path, expect_type):
    """按点路径断言字段存在且类型正确；[] 表示列表项字段（取首项）。"""
    node = data
    for part in path.split("."):
        assert isinstance(node, dict) and part in node, f"缺字段 {path}（现值：{node}）"
        node = node[part]
    assert isinstance(node, expect_type), f"字段 {path} 类型 {type(node).__name__} != {expect_type.__name__}"


# ---------------------------------------------------------------------------
# 大屏（消费方 frontend/src/composables/useBigScreen.js + views/dashboard/BigScreen.vue）
# ---------------------------------------------------------------------------


class TestBigScreenFields:
    """大屏五端点 + all 聚合。"""

    def test_stats(self, client, bearer_headers):
        """data 五个统计卡字段（useBigScreen.js:176-180 → BigScreen.vue:41-65）。"""
        data = _get_data(client, "/api/bigscreen/stats", bearer_headers)
        for f in (
            "articleCount",
            "commentCount",
            "positiveCount",
            "negativeCount",
            "neutralCount",
        ):
            _assert_field(data, f, int)

    def test_region(self, client, bearer_headers):
        """data.data[] 或 data[]（useBigScreen.js:215 回退），项含 name/value（:68,:80）。"""
        data = _get_data(client, "/api/bigscreen/region?demo=true", bearer_headers)
        # 后端固定返回 {data: [...], demo_mode, updatedAt}；前端 d.data || d 双兼容
        _assert_field(data, "data", list)
        assert data["data"], "demo 模式应保证非空用于钉住 item 形状"
        _assert_field(data["data"][0], "name", str)
        _assert_field(data["data"][0], "value", int)

    def test_trend_current_backend_shape(self, client, bearer_headers):
        """后端形状 {times, counts}（bigscreen_api.py:121-139）。

        #53 已按 D-007 方案 2 落地：前端改单系列画 counts
        （useBigScreen.js trendData {times, counts} + 趋势单系列「讨论量」），
        后端形状即前端消费形状，无漂移。本测试即转正后的正式断言。
        """
        data = _get_data(client, "/api/bigscreen/trend", bearer_headers)
        _assert_field(data, "times", list)
        _assert_field(data, "counts", list)

    def test_hot_topics(self, client, bearer_headers):
        """data.topics[]（useBigScreen.js:190,223），项 name/percent/heat（BigScreen.vue:155-162）。"""
        data = _get_data(client, "/api/bigscreen/hot-topics?demo=true", bearer_headers)
        _assert_field(data, "topics", list)
        assert data["topics"], "demo 模式应保证非空用于钉住 item 形状"
        topic = data["topics"][0]
        for f in ("name", "percent", "heat"):
            _assert_field(topic, f, (str, int))

    def test_alerts_item_shape(self, client, bearer_headers, seeded_ids):
        """data.alerts[]（useBigScreen.js:198,227），项 id/level/time/title（BigScreen.vue:92-97）。

        注意大屏项读 `time`（大屏专用短格式），与预警中心的 `created_at` 不同。
        """
        data = _get_data(client, "/api/bigscreen/alerts", bearer_headers)
        _assert_field(data, "alerts", list)
        assert data["alerts"], "已 seed 预警，真实路径应非空"
        item = data["alerts"][0]
        for f in ("id", "level", "time", "title"):
            _assert_field(item, f, (str, int))


# ---------------------------------------------------------------------------
# 预警中心（消费方 composables/useAlert.js + views/alert/center.vue + components/alert/*）
# ---------------------------------------------------------------------------


class TestAlertFields:
    def test_rules(self, client, bearer_headers, seeded_ids):
        """data.rules[]（useAlert.js:129），项 id/name/alert_type/enabled
        （center.vue:47-60、useAlert.js:156-159）。"""
        from database import db_session
        from models.alert import AlertLevel, AlertRule, AlertType

        db_session.add(
            AlertRule(
                id="contract-rule",
                name="契约测试规则",
                alert_type=AlertType.KEYWORD_MATCH,
                level=AlertLevel.WARNING,
                conditions={},
                cooldown_minutes=30,
            )
        )
        db_session.commit()

        data = _get_data(client, "/api/alert/rules", bearer_headers)
        _assert_field(data, "rules", list)
        assert data["rules"], "已 seed 规则应非空"
        item = data["rules"][0]
        for f in ("id", "name", "alert_type", "enabled"):
            _assert_field(item, f, (str, bool))

    def test_history(self, client, bearer_headers, seeded_ids):
        """data.alerts + data.total（useAlert.js:104-105）；项 level/title/message/
        alert_type/created_at/is_read/data（AlertList.vue:59-119、center.vue:127-151）。"""
        data = _get_data(client, "/api/alert/history?limit=10", bearer_headers)
        _assert_field(data, "alerts", list)
        _assert_field(data, "total", int)
        assert data["alerts"], "已 seed 预警应非空"
        item = data["alerts"][0]
        for f in ("level", "title", "message", "alert_type", "created_at", "is_read", "data"):
            assert f in item, f"history item 缺字段 {f}（现值：{item}）"

    def test_stats(self, client, bearer_headers, seeded_ids):
        """data.total_alerts/unread_count/level_distribution/active_rules
        （AlertChart.vue:19,40,61,82、AlertList.vue:39）。

        level_distribution 仅含出现过的级别；前端对四级分别 `|| 0` 兜底
        （AlertChart.vue:137-140），故只断言 seed 级别存在、不要求零缺省补全。
        """
        data = _get_data(client, "/api/alert/stats", bearer_headers)
        _assert_field(data, "total_alerts", int)
        _assert_field(data, "unread_count", int)
        _assert_field(data, "active_rules", int)
        _assert_field(data, "level_distribution", dict)
        assert "warning" in data["level_distribution"], (
            f"已 seed warning 预警，level_distribution 应含（现值：{data['level_distribution']}）"
        )

    def test_unread_count(self, client, bearer_headers, seeded_ids):
        """data.unread_count——SPA 唯一消费方曾是未挂载的孤儿预警铃铛组件
        （已随 #54 删除，此处不再留组件名以防死链）；端点暂留，当前无活跃消费方。"""
        data = _get_data(client, "/api/alert/unread-count", bearer_headers)
        _assert_field(data, "unread_count", int)


# ---------------------------------------------------------------------------
# 收藏 / 用户资料 / 今日统计 / 分析快照
# ---------------------------------------------------------------------------


class TestFavoritesFields:
    def test_favorites_list(self, client, bearer_headers, seeded_ids):
        """data.items + data.total（Favorites.vue:120-121）；项 id/content/source/
        created_at/like_num/comment_num/forward_num/article_id（:42-136）。"""
        data = _get_data(client, "/api/favorites", bearer_headers)
        _assert_field(data, "items", list)
        _assert_field(data, "total", int)
        assert data["items"], "已 seed 收藏应非空"
        item = data["items"][0]
        for f in (
            "id",
            "content",
            "source",
            "created_at",
            "like_num",
            "comment_num",
            "forward_num",
            "article_id",
        ):
            assert f in item, f"favorites item 缺字段 {f}（现值：{item}）"


class TestUserProfileFields:
    def test_profile(self, client, bearer_headers, seeded_ids):
        """data.nickname/email/bio/avatar_color（Profile.vue:298-302）、
        username（:18,:252,:256）、is_admin（:28）、create_time（:40）。"""
        data = _get_data(client, "/api/user/profile", bearer_headers)
        for f in (
            "username",
            "nickname",
            "email",
            "bio",
            "avatar_color",
            "is_admin",
            "create_time",
        ):
            assert f in data, f"profile 缺字段 {f}（现值：{data}）"


class TestStatsTodayFields:
    def test_today(self, client, bearer_headers):
        """data.today_articles/today_comments/latest_update。

        消费方：遗留页面模板 base_page.html:922（fetch('/api/stats/today')），
        SPA 前端无消费但端点保留（#54 调查结论）；
        形状取自 article_service.get_today_stats 实现，防静默漂移。"""
        data = _get_data(client, "/api/stats/today", bearer_headers)
        for f in ("today_articles", "today_comments"):
            _assert_field(data, f, int)
        assert "latest_update" in data, f"缺 latest_update（现值：{data}）"


class TestV1AnalysisFields:
    def test_demo_analysis(self, client, bearer_headers, seeded_ids):
        """demo=true 路径的分析快照字段。

        消费方：views/home/index.vue:117-130（绕过 api/analysis.js 直连）、
        components/Analysis/AnalysisSummary.vue:48-100、
        components/Common/ProvenanceBadge.vue:46-64。
        断言：meta.source_type/time_range.start|end/data_count/source_name/
        limitations/model_name；trend；sentiment.distribution.positive；
        propagation.total_nodes；summary.total_articles|total_comments|total_count。
        """
        data = _get_data(client, "/api/v1/analysis?topic=测试&demo=true", bearer_headers)
        _assert_field(data, "meta", dict)
        _assert_field(data, "meta.source_type", str)
        # 未传 start_at/end_at 时为 null：前端 AnalysisSummary.vue:48-49 用
        # v-if="meta.time_range?.start" 兜底展示「未指定」，null 属合法契约
        assert "start" in (data["meta"].get("time_range") or {}), (
            f"time_range 缺 start（现值：{data['meta'].get('time_range')}）"
        )
        assert "end" in (data["meta"].get("time_range") or {}), (
            f"time_range 缺 end（现值：{data['meta'].get('time_range')}）"
        )
        _assert_field(data, "meta.data_count", int)
        assert "source_name" in data["meta"], f"meta 缺 source_name（现值：{data['meta']}）"
        assert isinstance(data["meta"].get("limitations"), list), "meta.limitations 应为列表"
        assert "model_name" in data["meta"], f"meta 缺 model_name（现值：{data['meta']}）"

        _assert_field(data, "trend", list)
        _assert_field(data, "sentiment.distribution.positive", (int, float))
        _assert_field(data, "propagation.total_nodes", (int, float))
        _assert_field(data, "summary.total_articles", (int, float))
        _assert_field(data, "summary.total_comments", (int, float))
        _assert_field(data, "summary.total_count", (int, float))

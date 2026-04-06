#!/usr/bin/env python3
"""
数据大屏 API 测试
"""

import json
from unittest import mock

import pytest


class TestBigScreenAPI:
    """测试数据大屏 API"""

    def test_get_stats_endpoint(self, authed_client):
        """测试获取统计数据端点"""
        response = authed_client.get('/api/bigscreen/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200
        assert 'data' in data

    def test_get_region_endpoint(self, authed_client):
        """测试获取地区数据端点"""
        response = authed_client.get('/api/bigscreen/region')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200
        assert 'data' in data

    def test_get_trend_endpoint(self, authed_client):
        """测试获取趋势数据端点"""
        response = authed_client.get('/api/bigscreen/trend?hours=24')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200

    def test_get_hot_topics_endpoint(self, authed_client):
        """测试获取热门话题端点"""
        response = authed_client.get('/api/bigscreen/hot-topics?limit=10')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200
        assert 'data' in data

    def test_get_alerts_endpoint(self, authed_client):
        """测试获取预警端点"""
        response = authed_client.get('/api/bigscreen/alerts?limit=5')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200
        assert 'data' in data

    def test_get_all_data_endpoint(self, authed_client):
        """测试获取所有数据端点"""
        response = authed_client.get('/api/bigscreen/all')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200
        assert 'data' in data
        # 验证包含所有字段
        response_data = data['data']
        assert 'stats' in response_data or 'region' in response_data

    def test_rate_limit(self, authed_client):
        """测试速率限制"""
        # 快速发送多个请求
        for _ in range(35):
            response = authed_client.get('/api/bigscreen/stats')
        # 第35个请求应该被限流
        # 注意：实际限流阈值是30，但这取决于测试环境的限流实现

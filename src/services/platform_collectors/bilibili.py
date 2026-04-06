#!/usr/bin/env python3
"""
B站数据采集器
支持搜索视频内容
"""

import os
from typing import Any, Dict, List

import requests

from .base import BasePlatformCollector, Platform, PlatformContent


class BilibiliCollector(BasePlatformCollector):
    """B站采集器"""

    API_BASE = "https://api.bilibili.com"
    SEARCH_API = "https://api.bilibili.com/x/web-interface/search/type"
    
    @property
    def platform(self) -> Platform:
        return Platform.BILIBILI

    def parse(self, raw: Dict[str, Any]) -> PlatformContent:
        return PlatformContent.from_bilibili(raw)

    def _fetch_data(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """
        从B站搜索获取数据
        
        B站搜索API相对开放，但仍需要处理分页和频率限制
        """
        if os.getenv("BILIBILI_COLLECTOR_ENABLED", "false").lower() != "true":
            raise NotImplementedError("B站采集未启用，使用模拟数据")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://search.bilibili.com/",
        }
        
        params = {
            "keyword": keyword,
            "search_type": "video",
            "page": 1,
            "pagesize": min(limit, 50),
        }
        
        try:
            response = requests.get(
                self.SEARCH_API,
                params=params,
                headers=headers,
                timeout=30,
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("data", {}).get("result", []):
                    return data["data"]["result"]
                else:
                    self.logger.warning("B站搜索返回空结果")
                    raise NotImplementedError("B站搜索无结果")
            else:
                self.logger.warning(f"B站搜索返回状态码: {response.status_code}")
                raise NotImplementedError("B站采集失败")
                
        except Exception as e:
            self.logger.error(f"B站采集请求失败: {e}")
            raise NotImplementedError(f"B站采集失败: {e}")

    def _generate_demo_data(self, keyword: str, limit: int) -> List[PlatformContent]:
        """生成B站模拟数据"""
        from datetime import datetime, timedelta
        import random

        results = []
        up_masters = [
            ("科技美学", "tech_beauty"),
            ("老师好我叫何同学", "he_tongxue"),
            ("极客湾", "geekwan"),
            ("TESTV", "testv"),
        ]
        
        base_time = datetime.now() - timedelta(days=2)
        
        for i in range(min(limit, 10)):
            up = random.choice(up_masters)
            results.append(PlatformContent(
                platform=self.platform,
                content_id=f"BV1xx411x7{i:02d}",
                content_type=Platform.ContentType.VIDEO,
                author_id=up[1],
                author_name=up[0],
                content=f"【{up[0]}】{keyword}深度体验测评！",
                like_count=random.randint(1000, 50000),
                comment_count=random.randint(100, 5000),
                repost_count=random.randint(100, 3000),
                view_count=random.randint(10000, 500000),
                created_at=base_time + timedelta(hours=i),
                url=f"https://www.bilibili.com/video/BV1xx411x7{i:02d}",
                keywords=[keyword, "B站", "视频"],
            ))
        
        return results

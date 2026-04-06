#!/usr/bin/env python3
"""
知乎数据采集器
支持搜索问题和回答
"""

import os
from typing import Any, Dict, List

import requests

from .base import BasePlatformCollector, ContentType, Platform, PlatformContent


class ZhihuCollector(BasePlatformCollector):
    """知乎采集器"""

    API_BASE = "https://www.zhihu.com/api/v4"
    
    @property
    def platform(self) -> Platform:
        return Platform.ZHIHU

    def parse(self, raw: Dict[str, Any]) -> PlatformContent:
        return PlatformContent.from_zhihu(raw)

    def _fetch_data(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """
        从知乎搜索获取数据
        
        Note: 需要处理知乎的反爬机制
        """
        if os.getenv("ZHIHU_COLLECTOR_ENABLED", "false").lower() != "true":
            raise NotImplementedError("知乎采集未启用，使用模拟数据")
        
        # 知乎搜索 API
        search_api = f"{self.API_BASE}/search_v3"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "fetch",
        }
        
        params = {
            "t": "general",
            "q": keyword,
            "offset": 0,
            "limit": limit,
        }
        
        try:
            response = requests.get(
                search_api,
                params=params,
                headers=headers,
                timeout=30,
            )
            
            if response.status_code == 200:
                data = response.json()
                # 解析搜索结果
                results = []
                for item in data.get("data", []):
                    if item.get("type") == "search_result":
                        object_data = item.get("object", {})
                        if object_data.get("type") == "answer":
                            results.append(object_data)
                        elif object_data.get("type") == "article":
                            results.append(object_data)
                return results
            else:
                self.logger.warning(f"知乎搜索返回状态码: {response.status_code}")
                raise NotImplementedError("知乎采集失败")
                
        except Exception as e:
            self.logger.error(f"知乎采集请求失败: {e}")
            raise NotImplementedError(f"知乎采集失败: {e}")

    def _generate_demo_data(self, keyword: str, limit: int) -> List[PlatformContent]:
        """生成知乎模拟数据"""
        from datetime import datetime, timedelta
        import random

        results = []
        authors = [
            ("科技爱好者", "tech_lover"),
            ("产品经理", "pm_zhang"),
            ("算法工程师", "algo_engineer"),
            ("互联网观察家", "internet_observer"),
        ]
        
        base_time = datetime.now() - timedelta(days=5)
        
        for i in range(min(limit, 12)):
            author = random.choice(authors)
            results.append(PlatformContent(
                platform=self.platform,
                content_id=f"zhihu_{i}_{int(base_time.timestamp())}",
                content_type=ContentType.ANSWER,
                author_id=author[1],
                author_name=author[0],
                content=f"关于{keyword}的问题，我认为需要从以下几个方面分析：首先...",
                like_count=random.randint(10, 5000),
                comment_count=random.randint(5, 500),
                view_count=random.randint(1000, 100000),
                created_at=base_time + timedelta(hours=i * 4),
                url=f"https://www.zhihu.com/question/demo_{i}",
                keywords=[keyword, "知乎", "问答"],
            ))
        
        return results

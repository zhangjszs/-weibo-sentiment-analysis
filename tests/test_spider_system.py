#!/usr/bin/env python3
"""
微博爬虫系统测试脚本
用于验证各模块功能和配置是否正常
"""

import pytest

pytest.skip(
    "integration script (requires external spider modules/network)",
    allow_module_level=True,
)

import csv
import os
import sys

import requests

# 添加spider目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "spider"))

from config import get_config_manager


def test_config():
    """测试配置系统"""
    print("=== 测试配置系统 ===")
    config = get_config_manager()

    # 获取统计信息
    stats = config.get_config_stats()
    print(f"User-Agent数量: {stats['user_agents_count']}")
    print(f"可用代理数量: {stats['working_proxies_count']}")
    print(f"代理状态: {'启用' if stats['proxy_enabled'] else '禁用'}")
    print(f"默认超时: {stats['default_timeout']}秒")
    print(f"延迟范围: {stats['delay_range']}秒")

    # 测试随机请求头
    headers = config.get_random_headers()
    print(f"随机User-Agent: {headers['User-Agent'][:50]}...")

    print("✅ 配置系统测试通过\n")


def test_network_connection():
    """测试网络连接"""
    print("=== 测试网络连接 ===")
    config = get_config_manager()

    # 测试基础连接
    test_urls = ["http://httpbin.org/ip", "https://www.baidu.com", "https://weibo.com"]

    for url in test_urls:
        try:
            headers = config.get_random_headers()
            response = requests.get(url, headers=headers, timeout=10)
            print(f"✅ {url} - 状态码: {response.status_code}")
        except Exception as e:
            print(f"❌ {url} - 错误: {e}")

    print("网络连接测试完成\n")


def test_weibo_api():
    """测试微博API可用性"""
    print("=== 测试微博API可用性 ===")
    config = get_config_manager()

    # 测试微博热搜API
    api_url = "https://weibo.com/ajax/feed/hottimeline"
    params = {
        "since_id": "0",
        "refresh": "0",
        "group_id": "102803",
        "containerid": "102803",
        "extparam": "discover|new_feed",
        "max_id": "0",
        "count": "10",
    }

    try:
        headers = config.get_random_headers()
        response = requests.get(api_url, headers=headers, params=params, timeout=15)
        print(f"微博API状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if "statuses" in data:
                print(f"✅ 获取到 {len(data['statuses'])} 条热搜数据")
                print("✅ 微博API可正常访问")
            else:
                print(f"❌ API响应格式异常: {data}")
        elif response.status_code == 403:
            print("❌ 403禁止访问 - 需要更新Cookie或添加代理")
            print("📋 请更新config.py中的Cookie配置")
        else:
            print(f"❌ API访问失败: {response.status_code}")
            print(f"响应内容: {response.text[:200]}")

    except Exception as e:
        print(f"❌ API测试异常: {e}")

    print()


def test_csv_files():
    """测试CSV文件读写"""
    print("=== 测试CSV文件功能 ===")

    # 检查现有数据文件
    data_files = ["articleData.csv", "commentsData.csv", "userInfo.csv", "navData.csv"]

    base_dir = os.path.dirname(os.path.dirname(__file__))

    for file_name in data_files:
        # 首先检查data文件夹
        data_file_path = os.path.join(base_dir, "data", file_name)
        # 然后检查spider文件夹
        spider_file_path = os.path.join(base_dir, "spider", file_name)

        file_path = None
        if os.path.exists(data_file_path):
            file_path = data_file_path
        elif os.path.exists(spider_file_path):
            file_path = spider_file_path

        if file_path:
            try:
                with open(file_path, encoding="utf8") as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                    print(
                        f"✅ {file_name} - {len(rows) - 1} 条数据记录 (位置: {os.path.relpath(file_path, base_dir)})"
                    )
            except Exception as e:
                print(f"❌ {file_name} - 读取错误: {e}")
        else:
            print(f"⚠️  {file_name} - 文件不存在")

    print()


def test_spider_modules():
    """测试爬虫模块导入"""
    print("=== 测试爬虫模块导入 ===")

    modules_to_test = [
        ("spiderContent", "文章爬取模块"),
        ("spiderComments", "评论爬取模块"),
        ("spiderUserInfo", "用户信息爬取模块"),
        ("spiderMaster", "主控制模块"),
    ]

    sys.path.append("spider")

    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {description} ({module_name}) - 导入成功")
        except Exception as e:
            print(f"❌ {description} ({module_name}) - 导入失败: {e}")

    print()


def generate_test_report():
    """生成测试报告"""
    print("=== 系统状态报告 ===")
    config = get_config_manager()
    stats = config.get_config_stats()

    print(f"Python版本: {sys.version.split()[0]}")
    print(f"工作目录: {os.getcwd()}")
    print("配置状态: 正常")
    print(f"代理状态: {'启用' if stats['proxy_enabled'] else '禁用'}")
    print(f"可用代理: {stats['working_proxies_count']} 个")
    print(f"User-Agent池: {stats['user_agents_count']} 个")
    print()

    # 检查关键文件
    critical_files = [
        "spider/config.py",
        "spider/spiderContent.py",
        "spider/spiderComments.py",
        "spider/spiderUserInfo.py",
        "spider/spiderMaster.py",
    ]

    print("关键文件检查:")
    for file_path in critical_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path} ({size} bytes)")
        else:
            print(f"❌ {file_path} - 缺失")

    print("\n📋 使用建议:")
    if stats["working_proxies_count"] == 0:
        print("- 建议运行 spider/proxy_fetcher.py 获取代理IP")

    print("- 如遇403错误，请更新config.py中的Cookie")
    print("- 建议先运行小规模测试验证功能")
    print("- 使用 python spider/spiderMaster.py 启动完整爬虫")


def main():
    """主测试函数"""
    print("🚀 微博舆情分析爬虫系统 - 功能测试")
    print("=" * 50)

    # 依次执行各项测试
    test_config()
    test_network_connection()
    test_weibo_api()
    test_csv_files()
    test_spider_modules()
    generate_test_report()

    print("🏁 测试完成！")
    print("\n💡 如果所有测试通过，您可以:")
    print("1. 使用 python spider/spiderMaster.py 启动完整爬虫")
    print("2. 根据需要选择不同的爬取模式")
    print("3. 查看生成的CSV文件获取爬取结果")


if __name__ == "__main__":
    main()

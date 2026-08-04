#!/usr/bin/env python3
"""
微博Cookie测试脚本
快速验证Cookie是否有效
"""

import pytest

pytestmark = pytest.mark.unit

import pytest

pytest.skip(
    "integration script (requires real weibo cookie/network)", allow_module_level=True
)

import time

import requests


def test_cookie(cookie_string):
    """测试Cookie是否有效"""

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://weibo.com/",
        "Cookie": cookie_string,
    }

    print("🔍 测试Cookie有效性...")
    print("⏰ 等待15秒避免频率限制...")
    time.sleep(15)

    # 测试微博API
    test_url = "https://weibo.com/ajax/feed/hottimeline"
    params = {
        "since_id": "0",
        "refresh": "0",
        "group_id": "102803",
        "containerid": "102803",
        "extparam": "discover|new_feed",
        "max_id": "0",
        "count": "3",  # 只请求3条数据
    }

    try:
        response = requests.get(test_url, headers=headers, params=params, timeout=30)
        print(f"📊 状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if "statuses" in data and len(data["statuses"]) > 0:
                print("✅ Cookie有效！成功获取微博数据")
                print(f"📝 获取到 {len(data['statuses'])} 条微博")
                return True
            else:
                print("⚠️ Cookie可能有效，但数据格式异常")
                print(f"响应数据: {data}")
                return False

        elif response.status_code == 403:
            print("❌ Cookie无效或已过期 (403 Forbidden)")
            print("💡 请按照指南更新Cookie")
            return False

        elif response.status_code == 429:
            print("⚠️ 请求过于频繁 (429 Too Many Requests)")
            print("💡 请等待更长时间再试")
            return False

        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False


def main():
    """主程序"""
    print("🍪 微博Cookie测试工具")
    print("=" * 40)

    # 请在这里粘贴您的新Cookie
    cookie = """请将您从浏览器获取的Cookie粘贴到这里"""

    if cookie == "请将您从浏览器获取的Cookie粘贴到这里":
        print("⚠️ 请先更新Cookie！")
        print("\n📋 获取Cookie步骤：")
        print("1. 打开Chrome，访问 https://weibo.com 并登录")
        print("2. 按F12 → Network标签 → 刷新页面")
        print("3. 点击任意weibo.com请求 → Headers → Request Headers")
        print("4. 复制Cookie值，替换上面的cookie变量")
        print("5. 重新运行此脚本")
        return

    # 测试Cookie
    if test_cookie(cookie):
        print("\n🎉 测试成功！现在可以运行完整爬虫：")
        print("cd spider")
        print("python spiderMaster.py")
    else:
        print("\n❌ 测试失败，建议：")
        print("1. 重新获取Cookie")
        print("2. 确保已登录微博")
        print("3. 等待一段时间再试")


if __name__ == "__main__":
    main()

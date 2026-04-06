"""
代理获取和测试工具
从免费代理网站获取可用代理
"""

import random
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


def fetch_free_proxies():
    """从免费代理网站获取代理列表"""
    proxies = []

    # 方法1: 从 free-proxy-list.net 获取
    try:
        url = "https://www.proxy-list.download/api/v1/get?type=http"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            proxy_list = response.text.strip().split("\n")
            proxies.extend([proxy.strip() for proxy in proxy_list if proxy.strip()])
    except Exception as e:
        print(f"获取代理方法1失败: {e}")

    # 方法2: 从其他免费代理源获取
    try:
        url = "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            proxy_list = response.text.strip().split("\n")
            proxies.extend(
                [
                    proxy.strip()
                    for proxy in proxy_list
                    if proxy.strip() and ":" in proxy
                ]
            )
    except Exception as e:
        print(f"获取代理方法2失败: {e}")

    # 去重
    proxies = list(set(proxies))
    print(f"获取到 {len(proxies)} 个代理")
    return proxies


def test_proxy_speed(proxy):
    """测试单个代理的速度和可用性"""
    proxy_dict = {"http": f"http://{proxy}", "https": f"http://{proxy}"}

    try:
        start_time = time.time()
        response = requests.get("http://httpbin.org/ip", proxies=proxy_dict, timeout=8)
        end_time = time.time()

        if response.status_code == 200:
            speed = end_time - start_time
            ip = response.json().get("origin", "Unknown")
            return {"proxy": proxy, "speed": speed, "ip": ip, "status": "success"}
    except Exception as e:
        return {"proxy": proxy, "error": str(e), "status": "failed"}

    return None


def get_working_proxies(max_workers=20, max_test=50):
    """获取可用的代理列表"""
    print("正在获取免费代理...")
    all_proxies = fetch_free_proxies()

    if not all_proxies:
        print("未获取到任何代理")
        return []

    # 随机选择一部分进行测试
    test_proxies = random.sample(all_proxies, min(max_test, len(all_proxies)))
    print(f"开始测试 {len(test_proxies)} 个代理...")

    working_proxies = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_proxy = {
            executor.submit(test_proxy_speed, proxy): proxy for proxy in test_proxies
        }

        for future in as_completed(future_to_proxy):
            result = future.result()
            if result and result["status"] == "success":
                working_proxies.append(result)
                print(
                    f"✓ {result['proxy']} - {result['speed']:.2f}s - IP: {result['ip']}"
                )

    # 按速度排序
    working_proxies.sort(key=lambda x: x["speed"])
    print(f"\n找到 {len(working_proxies)} 个可用代理")

    return [p["proxy"] for p in working_proxies]


def update_config_with_proxies():
    """更新config.py中的代理列表"""
    working_proxies = get_working_proxies()

    if not working_proxies:
        print("未找到可用代理，保持原配置")
        return

    # 读取当前config.py
    config_path = "config.py"
    try:
        with open(config_path, encoding="utf-8") as f:
            content = f.read()

        # 更新FREE_PROXIES列表
        proxy_list_str = ",\n    ".join(
            [f'"{proxy}"' for proxy in working_proxies[:10]]
        )  # 只取前10个

        # 替换FREE_PROXIES内容
        pattern = r"FREE_PROXIES = \[(.*?)\]"
        replacement = f"FREE_PROXIES = [\n    {proxy_list_str}\n]"

        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        # 写回文件
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"已更新config.py，添加了 {len(working_proxies[:10])} 个代理")

    except Exception as e:
        print(f"更新config.py失败: {e}")


if __name__ == "__main__":
    print("开始获取并测试免费代理...")
    update_config_with_proxies()
    print("完成！")

#!/usr/bin/env python3
"""非大屏页面 console 告警冒烟（#55，重建 #43 的验证手段）。

前置：
- Flask 已以空 SQLite 库运行在 127.0.0.1:5000（admin 由
  AUTO_CREATE_DEMO_ADMIN 引导创建，密码 e2e-demo-password，无需手动
  INSERT——引导自 #56 修复后在 SQLite 直接可用）
- Vite dev server 已运行在 http://localhost:3000

输出：pageerror / console warning / console error / favicon 响应状态的
JSON 清单（供 issue 验收留证）。
判定：全程 0 pageerror / 0 warning / 0 error，且 favicon 请求存在且 200。
"""

import json
import sys

from playwright.sync_api import sync_playwright

BASE = "http://localhost:3000"

# #55 验收指定的浏览路径（不含 /big-screen，其 pageerror 属 #52）
PAGES = ["/home", "/article-analysis", "/sentiment-analysis", "/ip-analysis"]


def main() -> int:
    pageerrors = []
    console_warnings = []
    console_errors = []
    icon_responses = []

    def on_console(msg):
        line = f"{msg.type}: {msg.text}"
        if msg.type == "warning":
            console_warnings.append(line)
        elif msg.type == "error":
            console_errors.append(line)

    def on_response(resp):
        if "/favicon" in resp.url or resp.url.endswith("/vite.svg"):
            icon_responses.append((resp.url, resp.status))

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("pageerror", lambda e: pageerrors.append(str(e)))
        page.on("console", on_console)
        page.on("response", on_response)

        page.goto(f"{BASE}/login", wait_until="domcontentloaded")
        page.get_by_placeholder("请输入用户名").fill("admin")
        page.get_by_placeholder("请输入密码").fill("e2e-demo-password")
        page.get_by_role("button", name="登 录").click()
        page.wait_for_url("**/home", timeout=15000)

        for path in PAGES:
            page.goto(f"{BASE}{path}", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)  # 等图表初始化 + 页签/图标渲染

        # headless Chromium 不主动请求 favicon，改用显式请求核验：
        # 1) index.html 的 icon link 指向存在的资源；2) 该资源可 200 获取
        index_html = page.request.get(f"{BASE}/").text()
        icon_href = "missing"
        for token in index_html.split("<link"):
            if 'rel="icon"' in token.split(">")[0]:
                icon_href = token.split('href="')[1].split('"')[0]
                break
        if icon_href == "missing":
            icon_responses.append(("index.html link=missing", 0))
        else:
            icon_resp = page.request.get(f"{BASE}{icon_href}")
            icon_responses.append((f"index.html link={icon_href}", icon_resp.status))

        browser.close()

    report = {
        "pageerrors": pageerrors,
        "console_warnings": console_warnings,
        "console_errors": console_errors,
        "icon_responses": icon_responses,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    favicon_ok = icon_responses and all(s == 200 for _, s in icon_responses)
    clean = not (pageerrors or console_warnings or console_errors)
    return 0 if clean and favicon_ok else 1


if __name__ == "__main__":
    sys.exit(main())

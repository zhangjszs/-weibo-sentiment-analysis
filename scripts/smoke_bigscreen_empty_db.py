#!/usr/bin/env python3
"""大屏空数据冒烟（#52，重建 #43 的验证手段）。

前置：
- Flask 已以空 SQLite 库运行在 127.0.0.1:5000（demo admin 已开）
- Vite dev server 已运行在 http://localhost:3000

输出：pageerror / console error 的 JSON 清单（供 issue 验收留证）。
"""

import json
import sys

from playwright.sync_api import sync_playwright

BASE = "http://localhost:3000"


def main() -> int:
    pageerrors = []
    console_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("pageerror", lambda e: pageerrors.append(str(e)))
        page.on(
            "console",
            lambda m: console_errors.append(m.text) if m.type == "error" else None,
        )

        page.goto(f"{BASE}/login", wait_until="domcontentloaded")
        page.get_by_placeholder("请输入用户名").fill("admin")
        page.get_by_placeholder("请输入密码").fill("e2e-demo-password")
        page.get_by_role("button", name="登 录").click()
        page.wait_for_url("**/home", timeout=15000)

        page.goto(f"{BASE}/big-screen", wait_until="domcontentloaded")
        page.wait_for_timeout(5000)  # 等图表初始化 + 一轮数据刷新

        browser.close()

    report = {"pageerrors": pageerrors, "console_errors": console_errors}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if pageerrors else 0


if __name__ == "__main__":
    sys.exit(main())

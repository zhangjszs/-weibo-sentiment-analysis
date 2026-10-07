# 环境探测缓存

> 人工可直接编辑本文件覆盖；人工版本优先于重新探测。
> 机器相关信息（绝对路径等）**不得**写入本文件。

- 主分支：main（未设保护，可直接推送）
- 后端安装：`.venv/bin/python`（Python 3.12.14），依赖已就绪
- 后端 Lint：`.venv/bin/python -m ruff check src tests`
- 后端测试（fast gate）：`.venv/bin/python -m pytest -m "unit or api" -p no:launch_testing -p no:launch_ros -q --maxfail=1`
  - **必带 `-p no:launch_testing -p no:launch_ros`**：本机 shell 源过 `/opt/ros/*/setup.bash`，
    ROS 2 launch_testing 以 pytest11 entry point 注册插件，其依赖 `osrf_pycommon` 缺失，
    会在 collection 阶段直接崩溃（`ModuleNotFoundError: No module named 'osrf_pycommon'`）。
    屏蔽这两个插件不影响项目本身，CI 无此问题。
  - 实测：HEAD 全绿 = `1261 passed, 197 deselected`（本机；`-o addopts=""` 时可看全部失败）
  - 注意：`pytest.ini` 的 `addopts` 已含 `-q --maxfail=1`，覆盖时需 `-o addopts=""`
- 前端依赖：`frontend/node_modules` 已安装
- 前端 Node：mise 管理，需先 `export PATH="$HOME/.local/share/mise/installs/node/22.23.2/bin:$PATH"`（系统 PATH 中无 node/npm）
- 前端测试：`cd frontend && npm run test:run`（实测 4 files / 45 tests 全过）
- 前端 Lint：`cd frontend && npm run lint`
- 前端构建：`cd frontend && npm run build`
- CI：`.github/workflows/ci.yml`（backend-fast / frontend-fast / integration），`.github/workflows/security-scan.yml`
- gh：可用（账号 zhangjszs，scope: repo, workflow）
- 本机 shell 带 `http_proxy` 系变量：curl localhost 偶发 502 假象，加 `--noproxy '*'`
- 浏览器冒烟（#43 实测可行）：playwright 已装 `.venv`；chromium 用
  `~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome` 缓存，launch 时
  `executable_path=` 指定。后端 SQLite 文件库自举：`import models` 后
  `database.init_db()`（顺序不可反）；admin 用户手动插（demo admin 引导的
  `NOW()` 在 SQLite 不存在）；环境变量 shell 导出可覆盖 .env 同名项
- 冒烟脚本两枚（scripts/，复用同一套前置）：`smoke_bigscreen_empty_db.py`
  （#52 大屏空库）、`smoke_console_noise.py`（#55 console 清洁度）。
  前置：`TEST_DATABASE_URL=sqlite:///<库文件>` 下 `python -c` 自举
  （**先 `sys.path.insert(0, 'src')`**——只有 run.py 注入路径）→
  `hash_password` + `querys` 手动 INSERT admin → 起 run.py（同库）→
  vite dev 3000 → 跑脚本。headless Chromium 不主动请求 favicon（#55
  脚本已改用显式请求核验 icon link）；跑完记得杀掉两个 dev server

## 探测于 2026-09-29T23:28:24Z，agent DeepSeek-V4.1-Flash-20260930T000000Z
## 更新 2026-10-01T12:12:00Z，agent DeepSeek-V4.1-Flash-20261001T120450Z（补 ROS 插件屏蔽）
## 更新 2026-10-05T08:55:00Z，agent executor-glm-20261005T0714Z（补浏览器冒烟与代理注意事项）
## 更新 2026-10-07T02:30:00Z，agent executor-glm-20261007-relay（补两枚冒烟脚本前置 + python -c 需 sys.path 注入）

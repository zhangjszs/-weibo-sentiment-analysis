# 环境探测缓存

> 人工可直接编辑本文件覆盖；人工版本优先于重新探测。
> 机器相关信息（绝对路径等）**不得**写入本文件。

- 主分支：main（未设保护，可直接推送）
- 后端安装：`.venv/bin/python`（Python 3.12.14），依赖已就绪
- 后端 Lint：`.venv/bin/python -m ruff check src tests scripts`（#110 起 `scripts/` 纳入门禁；AGENTS.md 与 ci.yml 已同步）
- 后端测试（fast gate）：`.venv/bin/python -m pytest -m "unit or api" -p no:launch_testing -p no:launch_ros -q --maxfail=1`
  - **必带 `-p no:launch_testing -p no:launch_ros`**：本机 shell 源过 `/opt/ros/*/setup.bash`，
    ROS 2 launch_testing 以 pytest11 entry point 注册插件，其依赖 `osrf_pycommon` 缺失，
    会在 collection 阶段直接崩溃（`ModuleNotFoundError: No module named 'osrf_pycommon'`）。
    屏蔽这两个插件不影响项目本身，CI 无此问题。
  - 实测（2026-10-17，HEAD=2f6790c）：native（`WEIBO_CORE_RUST=1`）1494 passed / 69 skipped / 196 deselected；fallback（`WEIBO_CORE_RUST=0`）1492/71/196；均 exit 0（`-o addopts=""` 时可看全部失败）
  - 注意：`pytest.ini` 的 `addopts` 已含 `-q --maxfail=1`；**不要再手动加 `-q`**（verbosity 降到 −2，汇总行不打印）；覆盖 addopts 时需 `-o addopts=""`
  - no-cov 口径 ~35s；`--cov=src` 口径 ~80–86s（插桩 ~45–50s），两种口径分开记录不可混用
  - 覆盖率对文件缓存状态敏感：同 HEAD 复跑 native 68.5259%–68.66% 波动；最低可复现 68.5259%（11106/16207）
- 前端依赖：`frontend/node_modules` 已安装
- 前端 Node：mise 管理，需先 `export PATH="$HOME/.local/share/mise/installs/node/22.23.2/bin:$PATH"`（系统 PATH 中无 node/npm）
- 前端测试：`cd frontend && npm run test:run`（2026-10-17 基线 41 files / 190 tests 全过）
- 前端 Lint：`cd frontend && npm run lint`
- 前端构建：`cd frontend && npm run build`
- CI：`.github/workflows/ci.yml`（backend-fast / frontend-fast / integration），`.github/workflows/security-scan.yml`
- gh：可用（账号 zhangjszs，scope: repo, workflow）
- 本机 shell 带 `http_proxy` 系变量：curl localhost 偶发 502 假象，加 `--noproxy '*'`
- 浏览器冒烟（#43 实测可行）：playwright 已装 `.venv`；chromium 用
  `~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome` 缓存，launch 时
  `executable_path=` 指定。后端 SQLite 文件库自举：`import models` 后
  `database.init_db()`（顺序不可反）；admin 引导自 #56 修复后在 SQLite
  直接可用（`AUTO_CREATE_DEMO_ADMIN=True` + `FLASK_ENV=development` +
  `DEMO_ADMIN_PASSWORD=<强密码>` 导出后再起 run.py，无需手动插行）；
  环境变量 shell 导出可覆盖 .env 同名项
- 冒烟脚本两枚（scripts/，复用同一套前置）：`smoke_bigscreen_empty_db.py`
  （#52 大屏空库）、`smoke_console_noise.py`（#55 console 清洁度）。
  前置（2026-10-07 实测简化，**无需手动 INSERT admin**）：
  1) `TEST_DATABASE_URL=sqlite:///<库文件>` 下 `python -c` 建表
     （**先 `sys.path.insert(0, 'src')`**——只有 run.py 注入路径；
     `import models` 后 `database.init_db()`，顺序不可反；只建表不插数）
  2) 同库环境变量起 run.py：`AUTO_CREATE_DEMO_ADMIN=True` +
     `FLASK_ENV=development` + `DEMO_ADMIN_PASSWORD=e2e-demo-password`
     （与脚本登录凭据一致）；启动日志出现「已创建演示管理员账号」即
     引导成功（#56 修复后 SQLite 直接可用，浏览器登录实证通过）
  3) vite dev 3000 → 跑脚本。headless Chromium 不主动请求 favicon（#55
     脚本已改用显式请求核验 icon link）；跑完记得杀掉两个 dev server

## 探测于 2026-09-29T23:28:24Z，agent DeepSeek-V4.1-Flash-20260930T000000Z
## 更新 2026-10-01T12:12:00Z，agent DeepSeek-V4.1-Flash-20261001T120450Z（补 ROS 插件屏蔽）
## 更新 2026-10-05T08:55:00Z，agent executor-glm-20261005T0714Z（补浏览器冒烟与代理注意事项）
## 更新 2026-10-07T02:30:00Z，agent executor-glm-20261007-relay（补两枚冒烟脚本前置 + python -c 需 sys.path 注入）
## 更新 2026-10-07T05:45:00Z，agent executor-glm-20261007-r2（#56 修复后 SQLite 冒烟自举无需再手动种 admin）

## 补记（2026-10-17，executor 轮：#106/#107 实测补充）

- **Rust 工具链**：`rustc` 不在 PATH（mise shim 未配置）；用 `~/.cargo/bin/cargo +1.99.0` 显式调。
  `maturin develop` 默认 **dev 构建慢约 20x**，基准/交付必须 `--release`（#105 实测）。
- **前后对比测量法（不污染工作区）**：`git worktree add --detach /tmp/opencode/wt-<label> <commit>`，
  各 worktree 用同一 `.venv/bin/python` 同机串行跑，配对两次取稳（#106 复测 #95 用法）。
- **socket 审计方法（#106，仅审计、不入库）**：临时探针拦截 `socket.socket`（AF_INET/AF_INET6，
  不设 localhost 白名单）记录连接尝试；本机 `localhost:6379` 超时 3.005s——即 /ready 3s×2 的复现根源。
- **CI 证据读取**：Actions job 的 step summary 无法经 REST/check-runs 读到（`output.summary` 恒 null，
  网页需会话态）；需要 agent 可验收时把 summary 内容 echo 进 job log（折叠 `::group::`），
  再用 `gh api repos/<slug>/actions/jobs/<id>/logs --allow-escape-sequences` 读取。
- **git**：`git pull --rebase` 在 `.agent` 有未提交改动时会被拒——先提交 .agent 再拉。

## 补记（2026-10-17，executor 轮：#108/#110 实测补充）

- **Rust 工具链 pin（#108 后）**：`export PATH="$HOME/.cargo/bin:$PATH"` 后，在 `rust/` 或 `rust/weibo_core/` 下直接用 `cargo`/`rustc` 即按 `rust/rust-toolchain.toml` 选 1.99.0（`rustup show` 报 `overridden by .../rust/rust-toolchain.toml`）；本机全局默认恰好也是 1.99.0，单看版本无法证明 pin，需 rustup 来源或 A/B 对照。构建 wheel 必须 `--release`。
- **`docs/API.md` sha256 基线**：`71f7dcb8149bf5e9aa099b8a60de0a2bd11466ecf66ac76dbad1bb98c7d9ea1f`——`scripts/append_api.py` 是一次性追加生成器，**永远不要运行**（运行会向 API.md 追加重复章节）；修它只能静态验证（`ast.parse` + ruff）。

## 更新 2026-10-17T11:30:00Z，agent executor（#106/#107：Rust 工具链、worktree 复测法、socket 探针、CI summary 读法、pytest 口径）
## 更新 2026-10-17T12:05:00Z，agent executor（#108/#110：ruff 门禁含 scripts、rust-toolchain.toml pin 生效、API.md sha256 基线）

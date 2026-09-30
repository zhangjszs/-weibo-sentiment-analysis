# 环境探测缓存

> 人工可直接编辑本文件覆盖；人工版本优先于重新探测。
> 机器相关信息（绝对路径等）**不得**写入本文件。

- 主分支：main（未设保护，可直接推送）
- 后端安装：`.venv/bin/python`（Python 3.12.14），依赖已就绪
- 后端 Lint：`.venv/bin/python -m ruff check src tests`
- 后端测试（fast gate）：`.venv/bin/python -m pytest -m "unit or api" -q --maxfail=1`
  - 实测：HEAD 全绿 = `1249 passed, 3 skipped, 197 deselected`
  - 注意：`pytest.ini` 的 `addopts` 已含 `-q --maxfail=1`，覆盖时需 `-o addopts=""`
- 前端依赖：`frontend/node_modules` 已安装
- 前端 Node：mise 管理，需先 `export PATH="$HOME/.local/share/mise/installs/node/22.23.2/bin:$PATH"`（系统 PATH 中无 node/npm）
- 前端测试：`cd frontend && npm run test:run`（实测 4 files / 45 tests 全过）
- 前端 Lint：`cd frontend && npm run lint`
- 前端构建：`cd frontend && npm run build`
- CI：`.github/workflows/ci.yml`（backend-fast / frontend-fast / integration），`.github/workflows/security-scan.yml`
- gh：可用（账号 zhangjszs，scope: repo, workflow）

## 探测于 2026-09-29T23:28:24Z，agent DeepSeek-V4.1-Flash-20260930T000000Z

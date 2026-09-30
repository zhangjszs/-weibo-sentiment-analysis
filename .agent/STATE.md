# STATE

> 事实账本（可机器解析）。「已完成」仅保留最近 20 条，更早的见 git 历史。

## 当前活跃
- 任务：#30 [P1] integration 层 27 个测试失效（本轮新立项，未动代码）
- 状态：待办
- 建议下一步：按 #30 的「实现建议」先修 sys.modules 污染（影响面最大且会掩盖其他失败）

## 阻塞项
- CI `integration` job 仍红：27 failed / 162 passed / 5 skipped，全部为**既有问题**
  （在基线 76629c3 上同样复现），详见 #30。`backend-fast` 与 `frontend-fast` 已全绿。

## 关键事实（已实测验证）
- `main` 未设分支保护，可直接推送
- **backend-fast 与 frontend-fast 自本轮起持续全绿**（此前自 2026-08-30 起一直红）
- 前端 node 需 mise 的 node 22 在 PATH 中，系统 PATH 无 node/npm
- `pytest.ini` 的 `addopts` 自带 `--maxfail=1`，看全部失败要 `-o addopts="-q"`
- 本机无 MySQL/Docker，integration 的 MySQL 行为只能靠 CI 复验
- 本地 `pytest -m integration` 走 SQLite（除非显式给 TEST_DATABASE_URL）
- 本地有真实 `.env`（含密钥，勿提交），会影响起子进程的用例
- integration 失败分布：nlp_service_passthrough 16 / echarts_data_queries 8 /
  bigscreen_api 2 / table_data_queries 1
- `test_nlp_service_passthrough.py` 单独跑 30 passed，与 test_bigscreen_api 一起跑
  则 18 failed —— 模块顶层改 sys.modules 造成的顺序敏感

## 已完成
- #29 后端 Ruff 全仓清零（1609 → 0），fast gate 与 CI 首次真正可执行
- #29 staging 密钥校验测试改为自证环境，不再依赖「本机无这些变量」的偶然前提
- #25 CI 门禁：前端单测入 CI、集成随 PR 跑、env 补 ALLOWED_ORIGINS/ADMIN_USERS
- #25 测试依赖 cwd 入 sys.path：CI 的 pytest 入口脚本下必崩，改为 conftest 兜底
- #25 conftest 无条件覆盖 TEST_DATABASE_URL 导致集成测试跑在 SQLite 上，改为仅缺省时回退
- #27 MySQL TEXT 列建索引缺前缀长度（1170），迁移链 `upgrade head` 整链失败
- #27 前缀须用 sa.text()：字符串形式被 alembic 当成列名（渲染成 `authorName(100)`）
- #27 列类型改查 information_schema.DATA_TYPE：按 str(col["type"]) 在 MySQL 上漏判 TEXT
- #27 同类缺陷扩散到 align_legacy_sql，提取 alembic/index_helpers.py 供两处共用
- 新建 #30：integration 层 27 个失效测试的三类根因与修法

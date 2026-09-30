# STATE

> 事实账本（可机器解析）。「已完成」仅保留最近 20 条，更早的见 git 历史。

## 当前活跃
- 任务：#20 [High] WebSocket 死链 + SW 缓存鉴权接口 + 裸 fetch 绕过统一鉴权
- 状态：待办（下一棒从这里接）

## 阻塞项
- 无已知阻塞。CI 三 job 全绿（最近 run 36743871749）。

## 关键事实（已实测验证）
- `main` 未设分支保护，可直接推送
- backend-fast / frontend-fast / integration 全绿（2026-09-30 起）
- Security Scan 自 7b9d4b4 起连续两次转绿——"每次都红"的旧记录已过时
- **commit message 里 `fix: #N` 会自动关闭 issue**（GitHub 关键字），已在本轮
  #19 上发生；不想自动关就用 `test:`/`chore:` 等非关键字类型开头
- 前端测试在 `frontend/tests/*.test.js`（vitest，jsdom）；`vitest.config.js`
  exclude 了 auth-session.test.js（不在套件内跑，改 authSession 时注意别只看它）
- 自定义 axios adapter 测试必须把合并后的 config 回填到 response/error，
  否则拦截器读不到 `_loadingShown`（request-loading.test.js 有现成范例）
- 前端 node 需 mise 的 node 22 在 PATH 中
- `pytest.ini` 的 `addopts` 自带 `--maxfail=1`，看全部失败要 `-o addopts="-q"`
- 本地 `pytest -m integration` 走 SQLite；conftest `app` fixture 自举 schema
  且**不再调 database.reset()**（勿回退，见 #30 第 3 类根因）
- nlp_service 测试以私有模块名 `_nlp_tasks_under_test` 加载，勿改回 `app.tasks`

## 已完成
- #19 关闭：loading 触发/计数对称（request.js）、useTable loadError+竞态、
  路由守卫 me 缓存 TTL+public 放行 404+adminOnly 跳 /403、home 防连点、
  report 空数据导出拦截、analysis store allSettled+缓存保护（4 commits，
  前端测试 45→64，CI 全绿；commit fix: #19 关键字自动关闭了 issue）
- #30 关闭：bigscreen 500 根因（app fixture reset 丢弃 engine + 会话无
  schema）；echarts/table 9 用例改 patch Repository；nlp passthrough 私有
  模块名加载根治 sys.modules 污染；integration 27 failed 归零、CI 首次全绿
- #29 后端 Ruff 全仓清零（1609 → 0），fast gate 与 CI 首次真正可执行
- #29 staging 密钥校验测试改为自证环境，不再依赖「本机无这些变量」的偶然前提
- #25 CI 门禁：前端单测入 CI、集成随 PR 跑、env 补 ALLOWED_ORIGINS/ADMIN_USERS
- #25 测试依赖 cwd 入 sys.path：CI 的 pytest 入口脚本下必崩，改为 conftest 兜底
- #25 conftest 无条件覆盖 TEST_DATABASE_URL 导致集成测试跑在 SQLite 上，改为仅缺省时回退
- #27 MySQL TEXT 列建索引缺前缀长度（1170），迁移链 `upgrade head` 整链失败
- #27 前缀须用 sa.text()：字符串形式被 alembic 当成列名（渲染成 `authorName(100)`）
- #27 列类型改查 information_schema.DATA_TYPE：按 str(col["type"]) 在 MySQL 上漏判 TEXT
- #27 同类缺陷扩散到 align_legacy_sql，提取 alembic/index_helpers.py 供两处共用

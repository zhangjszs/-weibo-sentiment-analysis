# STATE

> 事实账本（可机器解析）。「已完成」仅保留最近 20 条，更早的见 git 历史。

## 当前活跃
- 任务：#19 [High] 前端 Loading 永不触发 + 大面积静默失败 + 空状态缺失
- 状态：待办（下一棒从这里接）

## 阻塞项
- 无已知阻塞。CI 三 job 全绿（run 36741984139，含 integration/MySQL）。

## 关键事实（已实测验证）
- `main` 未设分支保护，可直接推送
- backend-fast / frontend-fast / integration 全绿（2026-09-30 起）
- Security Scan 在 7b9d4b4 上首次转绿（此前每次都红）——是否稳定待观察
- 前端 node 需 mise 的 node 22 在 PATH 中，系统 PATH 无 node/npm
- `pytest.ini` 的 `addopts` 自带 `--maxfail=1`，看全部失败要 `-o addopts="-q"`
- 本机无 MySQL/Docker，integration 的 MySQL 行为靠 CI 复验（本次已绿）
- 本地 `pytest -m integration` 走 SQLite；conftest `app` fixture 现自举 schema
  且**不再调 database.reset()**（reset 会丢弃 repositories 捕获的旧 engine
  绑定，第二个测试起打到空库——#30 第 3 类根因，勿回退此改动）
- 本地有真实 `.env`（含密钥，勿提交），会影响起子进程的用例
- nlp_service 测试以私有模块名 `_nlp_tasks_under_test` 加载，勿改回 `app.tasks`

## 已完成
- #30 bigscreen 500 根因：app fixture 调 reset() 丢弃 engine + 测试会话无
  schema；改全进程复用 engine、sqlite 每测试 drop+create、MySQL 仅补缺表
- #30 echarts/table 9 用例改 patch ArticleRepository/CommentRepository，
  直方图在 database.engine 边界注入假连接，守卫与断言保留
- #30 nlp passthrough 改 importlib 私有模块名加载，根治 sys.modules 污染
- #30 关闭：本地 integration 189 passed（原 27 failed），CI integration/MySQL 绿
- #29 后端 Ruff 全仓清零（1609 → 0），fast gate 与 CI 首次真正可执行
- #29 staging 密钥校验测试改为自证环境，不再依赖「本机无这些变量」的偶然前提
- #25 CI 门禁：前端单测入 CI、集成随 PR 跑、env 补 ALLOWED_ORIGINS/ADMIN_USERS
- #25 测试依赖 cwd 入 sys.path：CI 的 pytest 入口脚本下必崩，改为 conftest 兜底
- #25 conftest 无条件覆盖 TEST_DATABASE_URL 导致集成测试跑在 SQLite 上，改为仅缺省时回退
- #27 MySQL TEXT 列建索引缺前缀长度（1170），迁移链 `upgrade head` 整链失败
- #27 前缀须用 sa.text()：字符串形式被 alembic 当成列名（渲染成 `authorName(100)`）
- #27 列类型改查 information_schema.DATA_TYPE：按 str(col["type"]) 在 MySQL 上漏判 TEXT
- #27 同类缺陷扩散到 align_legacy_sql，提取 alembic/index_helpers.py 供两处共用

# STATE

> 事实账本（可机器解析）。「已完成」仅保留最近 20 条，更早的见 git 历史。

## 当前活跃
- 任务：#15 [Medium] 会话/JWT：无 aud/iss、jti 不校验、logout 不作废、
  extend 无旋转；鉴权三套重复
- 状态：待办（下一棒从这里接）

## 阻塞项
- 无已知阻塞。CI 三 job 连续三次全绿。

## 关键事实（已实测验证）
- `main` 未设分支保护，可直接推送
- **commit message 里 `fix: #N` 会自动关闭 issue**（GitHub closing keyword）；
  #19、#20 都因此自动关（评论事后补发即close 后补发也正常显示）
- backend-fast / frontend-fast / integration 全绿（2026-09-30 起）
- Security Scan 连续三次转绿——"每次都红"的旧记录已过时
- 前端测试在 `frontend/tests/*.test.js`（vitest，jsdom），67 个；
  `vitest.config.js` exclude 了 auth-session.test.js
- mock axios 时 `create` 返回值必须带 `interceptors` 桩——同模块图里
  request.js 也会 create 并注册拦截器（router-guard.test.js 有范例）
- 自定义 axios adapter 必须回填合并后的 config（request-loading.test.js）
- 前端 node 需 mise 的 node 22 在 PATH 中
- `pytest.ini` 的 `addopts` 自带 `--maxfail=1`，看全部失败要 `-o addopts="-q"`
- 本地 `pytest -m integration` 走 SQLite；conftest `app` fixture 自举 schema
  且**不再调 database.reset()**（勿回退，见 #30 第 3 类根因）
- nlp_service 测试以私有模块名 `_nlp_tasks_under_test` 加载，勿改回 `app.tasks`
- nginx.conf 由 frontend/Dockerfile 进生产镜像；#20 给它加了 /socket.io
  Upgrade 代理，**本机无 Docker 只做了结构验证，人工上线时确认握手 101**

## 已完成
- #20 关闭：WS 接入 socket.io-client + vite/nginx /socket.io 通道 + 抖动
  退避；SW 不缓存 /api/*、离线回退 index.html；裸 fetch 统一 axios；登出
  清 tab 持久化；Inter 字体本地化（4 commits，67 前端测试，CI 绿）
- #19 关闭：loading 触发/计数对称（request.js）、useTable loadError+竞态、
  路由守卫 me 缓存 TTL+public 放行 404+adminOnly 跳 /403、home 防连点、
  report 空数据导出拦截、analysis store allSettled+缓存保护
- #30 关闭：integration 27 failed 归零（sys.modules 污染 / patch 目标 /
  测试会话无 schema + reset 丢弃 engine），CI integration/MySQL 首次绿
- #29 后端 Ruff 全仓清零（1609 → 0），fast gate 与 CI 首次真正可执行
- #29 staging 密钥校验测试改为自证环境，不再依赖「本机无这些变量」的偶然前提
- #25 CI 门禁：前端单测入 CI、集成随 PR 跑、env 补 ALLOWED_ORIGINS/ADMIN_USERS
- #25 测试依赖 cwd 入 sys.path：CI 的 pytest 入口脚本下必崩，改为 conftest 兜底
- #25 conftest 无条件覆盖 TEST_DATABASE_URL 导致集成测试跑在 SQLite 上，改为仅缺省时回退
- #27 MySQL TEXT 列建索引缺前缀长度（1170），迁移链 `upgrade head` 整链失败
- #27 前缀须用 sa.text()：字符串形式被 alembic 当成列名（渲染成 `authorName(100)`）
- #27 列类型改查 information_schema.DATA_TYPE：按 str(col["type"]) 在 MySQL 上漏判 TEXT
- #27 同类缺陷扩散到 align_legacy_sql，提取 alembic/index_helpers.py 供两处共用

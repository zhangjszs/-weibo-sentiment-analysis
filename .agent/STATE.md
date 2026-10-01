# STATE

> 事实账本（可机器解析）。「已完成」仅保留最近 20 条，更早的见 git 历史。

## 当前活跃
- 任务：无——全部 open issue 已关闭（#31/#32/#33/#34/#35/#36/#37 于 2026-10-01T15:4x 关闭）
- 状态：下一棒若无事可做，按接力协议第七节进入主动发现模式（每轮最多 1 个新 issue，先查重）

## 阻塞项
- 无已知阻塞。CI 三 job 绿；Security Scan 绿（#31 修复）；
  **#32 后带 Bandit HIGH/CRITICAL 门禁**；**#34/#35 后 CI 带覆盖率门禁（fail_under=60，实测 65%）**；
  **#37 后前端 lint 带 --max-warnings 0 门禁（告警 103→0）**。

## 关键事实（已实测验证）
- `main` 未设分支保护，可直接推送
- **commit message 里 `fix: #N` 会自动关闭 issue**（GitHub closing keyword）；
  #19/#20/#15 都因此自动关；部分完成的 issue 在评论后 `gh issue reopen` 即可
- app fixture 会删 config* 模块重导入：测试里 monkeypatch Config 必须**在
  fixture 之后** `import config.settings` 取新类，顶层 import 到的是旧类
- Werkzeug 测试客户端在 HTTP 边界就拒绝带换行的头值（测日志注入用超长值）
- 模块级别名导出会被 ruff F401 --fix 删除，需配 `__all__`（authz.py 的
  require_jwt 即此写法）
- backend-fast / frontend-fast / integration 全绿（2026-09-30 起）
- 本会话累计已关闭：#30/#19/#20/#15/#21/#16/#28/#31/#32/#33/#34（全部推送 main）
- 前端测试现 10 文件 73 个（auth-session 已纳入）
- **前端 lint 告警已清零并加零告警门禁（#37）**：lint 脚本带 `--max-warnings 0`；
  清理内容 = 未使用 import/解构项/catch 绑定（94）+ v-for 模板遮蔽（2）+ prop 缺省（7）。
  **教训：改 v-for 循环变量必须全量改名**——Sidebar 第二循环曾漏改
  `{{ route.meta.title }}`，指向外层 `useRoute()` 的 route（当前路由）而非循环项，
  lint/build/测试都不会报，diff 逐行复核才发现。
- **Security Scan 此前从未绿过**：main 上连续 20+ 次全红（截止 2026-10-01T01:46Z）。
  曾误记为"连续六次转绿"，实为混淆 CI 与 Security Scan 两个 workflow。根因：
  9536e2b（traeagent）删掉了 d36906b 加的 `|| true`，任一扫描有发现即 step 中止。
  #31 已修复并确认首次转绿（恢复 `|| true` + bandit 发现清零）。
- **Security Scan 现在是有牙齿的门禁（#32）**：`bandit -c .bandit -r src/ -lll`
  作为阻断步骤，只有 HIGH/CRITICAL 才红（LOW 噪音不阻断）。safety 无
  `SAFETY_API_KEY` 时显式 `::notice::` 跳过（不再静默空报告）；pip-audit 仍报告模式。
- `requirements/requirements.audit.txt` 已于 #33 删除（全仓无引用 + 内容漂移）；
  README.md / docs/LOCAL_DEPLOYMENT.md 目录树同步移除该条目。现 `requirements/`
  只剩 `requirements.txt` + `requirements-dev.txt`。
- **CI 覆盖率门禁已激活（#34）**：ci.yml 的 backend-fast 加了
  `--cov=src --cov-report=term-missing`，pyproject 的 `fail_under=50` 才真正生效
  （此前 CI 从不传 `--cov`，是死配置）。实测全量 unit+api 覆盖率 **65.11%**。
  pytest-cov 会读取 pyproject 的 fail_under（已验证）。**#35 已把阈值由 50→60**
  （实际 65%，留 ~5% 缓冲）；阈值唯一真相在 pyproject，CI 不同步。
- **`docs/项目评估与规划.md` 是时点快照，多处已过时**：其低优先项 25（`list/`
  误建 venv）、26（双日志目录 `logs/`：现仅 `src/logs/` 且 gitignore）、
  28（PyMySQL：src 无直接 import）、7（pickle.load）均**已不成立**；
  动手前务必现场核实，勿照单直取（本会话曾被其误导）。#36 已给该文档顶部加
  **"历史快照 · 勿照单直取"横幅**，后续读者应在动手前先看横幅。
- 本机 shell 源过 `/opt/ros/*/setup.bash`，ROS launch_testing 作为 pytest 插件
  自动加载且 `osrf_pycommon` 缺失 → collection 崩溃。本地跑 pytest 必带
  `-p no:launch_testing -p no:launch_ros`（CI 无此问题，勿写进 pytest.ini）
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
- #37 关闭：前端 lint 告警 103→0 并加 `--max-warnings 0` 门禁（38 文件，+89/-117）；
  lint 0/0、73 测试、build 全过（1 commit）
- #36 关闭：给 `docs/项目评估与规划.md`（2026-07-30 快照）加"历史快照·勿照单直取"
  横幅，列已核实过时条目作示例（1 commit，纯文档）
- #35 关闭：覆盖率阈值 fail_under 50→60（实际 65%，留缓冲），仍单源于 pyproject；
  本地同命令实测 `Required test coverage of 60.0% reached … 65.11%` 通过（1 commit）
- #34 关闭：CI backend-fast 加 `--cov=src --cov-report=term-missing`，激活
  pyproject 的 fail_under=50（此前死配置）；实测覆盖率 65.11% > 50 通过（1 commit）
- #33 关闭：删除冗余 `requirements/requirements.audit.txt`（全仓零引用、内容与
  requirements.txt 漂移），README/LOCAL_DEPLOYMENT 目录树同步移除（1 commit）
- #32 关闭：Security Scan 加 Bandit HIGH/CRITICAL 门禁步骤（`-lll`，实测
  HIGH→1 / LOW→0）、safety 无 secret 显式 `::notice::` 跳过并写占位报告；
  YAML 校验通过、CI+Security Scan 双绿（run 36874452700，1 commit）
- #31 关闭：Security Scan 恢复 `|| true`（回归修复）、6 处 hashlib.md5 加
  usedforsecurity=False、B608/B615/B105 加 #nosec、新增 .bandit 跳过 B311/B110，
  bandit 报告 111→0；bandit 本地 0 发现，fast gate 1261 passed（1 commit）
- #28 关闭：run_migration.py 改走 alembic（原裸 pymysql 绕迁移链）、
  alembic/env.py 尊重 TEST_DATABASE_URL（迁移链 SQLite 实测跑到 head）、
  check_db/check_env 对齐 Config、deploy 注释、alembic.ini 占位清空、
  docs 计数去硬编码（1 commit；fast gate 1261 / CI 绿）
- #16 关闭：删 platform_collector.py 单数版+测试、_create_task_queues、
  utils.metrics 死路径、rate_limiter __main__、_api_cache；print→logger；
  AGENTS/README/CONTEXT 漂移校正（307 别名、密钥隔离要求、情感链路
  mode 路由、接口表 /api/*、CONTEXT 补 Architecture 段）——2 commits，
  fast gate 1261 / CI 绿；String(100) 拓宽与验证码均留白待立项
- #21 关闭：删死依赖 5 个（socket.io-client/@fontsource 因 #20 已在用，
  保留）、死代码（locales/、sentiment.js、3 个 composable、v-lazy、
  propagation/stats 无消费方函数）、lint 去 --fix 纳入 tests、no-console
  收紧 allow[warn,error]（警告 146→103）、auth-session 测试从 node:test
  改写 vitest 纳入套件（2 commits；前端 73 测试 / lint 0 error / build /
  CI 绿）
- #15 关闭（第三轮）：登录失败锁定（username+IP 5 次锁 15 分钟，成功清零，
  两条登录轨覆盖）+ logout 审计补齐（feat a548221 + 5 测试；fast gate 1283 /
  integration 189 / CI 绿；验证码留白：需产品决策建议另行立项）
- #15 第二轮（统一校验）：jwt_required 升级单轨标准实现（Bearer+Cookie、
  统一 error envelope）、require_jwt 变真别名、中间件 401 文案区分缺失/
  无效、ADMIN_USERS 空 dev 启动告警（refactor: 6135bb2 + 4 测试；
  fast gate 1278 / CI 绿）
- #15 部分（reopen）：jti 黑名单（Redis 优先/内存兜底）+ aud/iss 验签、
  两处 logout 作废 token、extend 旋转、预热不再伪造 user_id=0 管理员
  token、admin_required 401/403 区分、g.user_id 使限流 user 键生效、
  登录 redirect 白名单（//evil.com）、X-Request-Id 消毒（4 commits +
  11 新测试；fast gate 1274、integration 189、CI 绿；commit fix: #15
  自动关闭后已 reopen）
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

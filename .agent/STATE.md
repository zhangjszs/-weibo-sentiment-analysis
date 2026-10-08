# STATE

> 事实账本（可机器解析）。「已完成」仅保留最近 20 条，更早的见 git 历史。

## 当前活跃
- 任务：无 in-progress——**ready 队列空**（#53 已完成转 in-review，
  open 仅剩 #53 in-review 待验收）。本轮（executor-20261008-r1，
  2026-10-08）：从 main 5f68c9b 起步并已 fetch 确认与 origin 同步；
  无现场可恢复（STATE/HANDOFF 均无 in-progress），按 PLAN 执行队列领取 #53。
- #53 [P2] 大屏趋势改单系列画 counts：完成转 in-review
  （1909d9b → main c402b4d，已推送，临时分支已删）。
  useBigScreen.js trendData 改 {times, counts} + fetch 映射取 counts +
  trendChartOptions 单系列「讨论量」（删三组假数据回退）；
  strict-xfail 测试删除转正式断言；新增 bigscreen-trend.test.js 3 用例
  （RED→GREEN 实证：旧映射 3 failed → 新映射 3 passed）。
- 状态：in-review 累计 **1 项**（#53）待 Planner 验收。
- 剩余队列：无（open 仅 #53 in-review）。ready 空。

## 阻塞项
- 无阻塞。CI 双绿（c402b4d → CI run 37769996969 success +
  Security Scan 37769997040 success，精确按 commit 查询）。

## 关键事实（已实测验证）
- **基线推进**：后端 fast gate **1460 passed**（xfail 测试删除后无 xfail，
  门禁仍绿）；前端 85 → **88**（#53 新增 bigscreen-trend 3 用例）；
  五门禁 + 体积门禁绿（入口 JS 余量 53648B / 首屏 CSS 余量 15772B）。
- **#53 方案 2 落地形态**：trendData {times, counts}；trendChartOptions
  单 series（name 讨论量，line+smooth+#3B82F6，data 直引 counts）；
  空数据 series 为空数组（诚实无数据，#52 兜底保证不崩）；
  xAxis times 回退保留；timelineData 回放滑块未动（独立演示数据）。
- **路由 meta.icon 必须是字符串名**（#55 契约测试守护，反例变红实证）：
  组件对象进 Pinia reactive store 触发告警、JSON 持久化退化触发
  missing-template；字符串走 ICON_COMPONENTS 全局注册（#39）。
  **markRaw 方案被否**——它修不了持久化破坏。
- **/api/stats/today 有真实消费方**：src/views/page/templates/base_page.html
  的 loadTodayStats()（fetch + today_articles/latest_update），且
  base_page.html 被 index.html 等 8 个在用模板 extends。任何「死端点清理」
  调查须把**服务端模板**计入消费方（#45/#54 两轮都只扫了 SPA 五层）。
- **sw.js precache 用 cache.addAll**：任一 404 → 整个 install 失败；
  precache 清单必须与 public/ 实际文件一致（现指向 /vite.svg，缓存
  static-v2→static-v3）。
- **冒烟脚本两枚**（scripts/）：smoke_bigscreen_empty_db.py（#52 大屏空库）+
  smoke_console_noise.py（#55 非大屏页面 console 清洁度，RED→GREEN 两轮
  实证）。注意 headless Chromium 不主动请求 favicon——#55 脚本用显式请求
  核验 index.html 的 icon link。
- **SQLite 自举**：`TEST_DATABASE_URL=... python -c` 需先
  `sys.path.insert(0, 'src')`（只有 run.py 做路径注入）；`import models` 后
  `database.init_db()` 顺序不可反；demo admin 引导自 #56 修复后在 SQLite
  可用（`AUTO_CREATE_DEMO_ADMIN=True` + `FLASK_ENV=development` +
  `DEMO_ADMIN_PASSWORD` 环境变量，create_app 即落 admin 行），冒烟不再需要
  手动 INSERT。
- **大屏 trend 漂移已修（#53，本轮）**：前端单系列画 counts，后端
  {times, counts} 即前端消费形状，无漂移；strict-xfail 已移除转正式断言。
- user 模型自定义 `__init__` 不收 id：造数用
  `u = User(username=...); u.id = 1` 再 add。
- 探测脚本「token 中毒」坑：`/api/auth/logout` 与 `/api/session/extend`
  会拉黑/轮换共享 Bearer 的 jti，批量探测须用新 token 且把这两条排最后。
- 测试环境 celery 是 eager/memory 模式：测 broker 降级必须 patch 任务
  对象抛 OperationalError（`TestBrokerDegradationContract` 有范例）。
- Flask `Rule.build()` 部分规则返回空路径——契约枚举用正则替换
  `<arg>`（契约测试文件里的 `_ARG_RE` 可复用）。
- 本机 shell 有 http_proxy 系变量：curl localhost 加 `--noproxy '*'`。
- 登录锁定/限流/WS 广播/通知队列/爬虫运行态从来不用 Redis（#46）：
  均为进程内存，详见 docs/DEPLOYMENT.md「Redis 依赖与降级行为」。
- main 未设分支保护，可直接推送；commit 一律 `Refs #N`（不自动关闭，
  提交标题勿含「fix: #N」以免 GitHub 自动关闭——#52 已踩坑），
  `.agent/` 变更单独 `chore(agent):` 提交。
- 命令行 `-q` 与 pytest.ini addopts 叠成 `-qq` 会吞汇总行：看计数用
  `-o addopts="" -q`；管道后判退出码用 `PIPESTATUS[0]`（tail 会吃掉）。
- 跑后端测试会在 `src/data/` 留 commentsData.csv 未跟踪产物——勿提交。
- 前端 node 必须走 mise 的 PATH（ENV.md 有完整命令）。
- 前端 composable 全链路单测模式（#53 实证）：`vi.mock('@/api/stats')` +
  `vi.mock('@/utils/chinaMap')` + harness 组件 mount 驱动 onMounted，
  `flushPromises` 后断 vm 数据，`unmount` 清定时器；旧代码 RED→新代码
  GREEN 可作护栏有效性实证。

## 已完成
- **#53 完成转 in-review**：trend 单系列 counts（1909d9b → main c402b4d）；
  bigscreen-trend.test.js 3 用例 RED→GREEN + 后端 fast gate 1460 passed +
  前端五门禁全绿 + CI/安全双绿
- **#57 完成转 in-review**（上一棒，Planner 已验收关闭）：manifest.json
  删两条 /logo.png 悬空条目 + sw.js 通知 icon → /vite.svg
- **#56 完成转 in-review**（上一棒，Planner 已验收关闭）：ensure_demo_admin
  INSERT 改 ORM + create_time 显式 naive UTC；RED→GREEN 文件库自举实证
- **冒烟前置简化完成（2026-10-07，370dd95）**：双冒烟全绿；全新 SQLite
  库零手动 INSERT 走通引导+登录
- **#55 完成并验收关闭**：meta.icon 字符串化 19 处 + favicon 三处指向
  vite.svg + el-empty 冒号修复；tabbar-icons 契约测试 3 用例
- **#54 完成并验收关闭**：删 /api/bigscreen/all + AlertNotification.vue
  （净 -409 行）；stats/today 按护栏保留
- **#52 完成关闭**（2026-10-06）：大屏空数据 addColorStop 崩溃
  （d968188，真实浏览器冒烟 RED→GREEN，CI 绿）
- **#51/#50/#49/#48 完成并验收关闭**：format:check 门禁 / 文档路径校验 /
  vitest resolver 单源 / 体积预算门禁
- **M3 五项（2026-10-05）**：#43 浏览器冒烟 / #44 GET envelope 契约 /
  #47 写接口契约 / #45 字段契约（立 #53）/ #46 Redis 降级文档
- #42 调研交付（验证码三候选对比 + 国内可用性核实，维持不上）

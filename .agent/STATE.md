# STATE

> 事实账本（可机器解析）。「已完成」仅保留最近 20 条，更早的见 git 历史。

## 当前活跃
- 任务：无 in-progress——**ready 队列已清空**，本轮收尾（2026-10-07）。
- #54 [P4] 死代码清理：完成转 in-review（053bff2）。/api/bigscreen/all +
  AlertNotification.vue 已删；**/api/stats/today 保留**（base_page.html
  loadTodayStats 实际消费且该模板被 8 个在用模板 extends，按 Issue 护栏）。
- #55 [P4] console 告警清理：完成转 in-review（a0d44ed）。路由 meta.icon
  全部字符串化（19 处）、favicon 三处指向 /vite.svg、sw.js static-v3。
- 状态：in-review 累计 **11 项**（#43~#47、#48~#51、#54、#55）待 Planner 验收。
- 剩余队列：#53（needs-info，等 D-007）。ready 空。

## 阻塞项
- 无阻塞。CI 全绿（两次推送后实证：run 37547491509 / 37549117841）。

## 关键事实（已实测验证）
- **基线推进**：fast gate 1463 → **1460 passed + 1 strict xfail**（−3 = #54
  删 2 用例 + GET 契约按 url_map 枚举少 1 参数化用例，与删除一致非回退）；
  前端 82 → **85**（#55 新增 tabbar-icons 3 用例）；五门禁 + 体积门禁绿。
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
  static-v2→static-v3）。manifest.json 仍引用 /logo.png（文件不存在，
  仅 PWA 安装元数据、无 console 噪音，未清）。
- **冒烟脚本两枚**（scripts/）：smoke_bigscreen_empty_db.py（#52 大屏空库）+
  smoke_console_noise.py（#55 非大屏页面 console 清洁度，RED→GREEN 两轮
  实证）。注意 headless Chromium 不主动请求 favicon——#55 脚本用显式请求
  核验 index.html 的 icon link。
- **SQLite 自举**：`TEST_DATABASE_URL=... python -c` 需先
  `sys.path.insert(0, 'src')`（只有 run.py 做路径注入）；`import models` 后
  `database.init_db()` 顺序不可反；admin 用 hash_password + querys 手动
  INSERT（demo admin 引导 SQL 的 NOW() 在 SQLite 报错，方言问题未立项）。
- **大屏 trend 形状漂移（#53，未修）**：前端读 positive/neutral/negative
  （useBigScreen.js:219），后端两条路径都只返 {times, counts}；修法需产品
  决策（D-007），strict-xfail 钉住，修复落地时 XPASS 强制转正。
- strict-xfail 是钉已知漂移的手段：修复落地时 XPASS 使门禁变红，
  强制把断言转正。
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
- main 未设分支保护，可直接推送；commit 一律 `Refs #N`（不自动关闭），
  `.agent/` 变更单独 `chore(agent):` 提交。
- 命令行 `-q` 与 pytest.ini addopts 叠成 `-qq` 会吞汇总行：看计数用
  `-o addopts="" -q`；管道后判退出码用 `PIPESTATUS[0]`（tail 会吃掉）。
- 跑后端测试会在 `src/data/` 留 commentsData.csv 未跟踪产物——勿提交。
- 前端 node 必须走 mise 的 PATH（ENV.md 有完整命令）。

## 已完成
- **#55 完成转 in-review**：meta.icon 字符串化 19 处 + favicon 三处指向
  vite.svg + el-empty 冒号修复；tabbar-icons 契约测试 3 用例（反例变红）
  + smoke_console_noise.py（RED 11 告警+404 → GREEN 0/0/0+200）
  （1 commit a0d44ed）
- **#54 完成转 in-review**：删 /api/bigscreen/all + AlertNotification.vue
  （净 -409 行）；stats/today 按护栏保留（消费方调查结论）；契约收缩至
  13 端点；接管上一棒崩溃现场并还原第一遍误删的服务单测（1 commit 053bff2）
- **#52 完成关闭**（上一棒 2026-10-06）：大屏空数据 addColorStop 崩溃
  （d968188，真实浏览器冒烟 RED→GREEN，CI 绿）；顺带入库 #39 后续
  BaseChart import 修复 + 图标守护测试（7c6a3f8）
- **#51 完成转 in-review**：Prettier 全量格式化 74 文件 + format:check
  入 CI（1 commit 66c1d7b）
- **#50 完成转 in-review**：文档路径校验误报修复 + CI 接线（1 commit 47b6606）
- **#49 完成转 in-review**：vitest 接入共享 Components resolver +
  模板解析契约 2 用例（1 commit bca6a53）
- **#48 完成转 in-review**：构建体积预算门禁（1 commit 1f93c25）
- **M3 五项（2026-10-05）**：#43 浏览器冒烟 / #44 GET envelope 契约 /
  #47 写接口契约 / #45 字段契约（立 #53）/ #46 Redis 降级文档，
  全部完成转 in-review
- #42 调研交付（验证码三候选对比 + 国内可用性核实，维持不上）

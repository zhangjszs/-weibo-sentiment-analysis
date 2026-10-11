# STATE

> 事实账本（可机器解析）。「已完成」仅保留最近 20 条，更早的见 git 历史。

## 当前活跃
- 任务：本轮收尾（5 个 Issue 全部转 in-review，无 in-progress）。本席 executor-20261011T0526Z。
- 状态：in-review 5 项（#64、#83、#65、#66、#82，待 Planner 验收）；auto-discovered 2 项
  （#84、#85 待定级；本轮累计 2/3）。
- 剩余队列：ready-for-agent 约 14 个（#67–#80；#59 needs-info；#81 open 待 #72）。
- 本轮起点 main `34d84c9` → 现 main `edf707e`（与 origin 同步，5 merge 全部推送）。

## 阻塞项
- 无阻塞。

## 关键事实（已实测验证）
- **前端规模（#61 删除后）**：.js 32（api 14 · utils 5 · stores 4 · composables 6 ·
  router 1 · plugins 1 · main.js）· .vue 45（views 6305 行 · components 3322 行）·
  JS+Vue 合计 13,731 行。
- **前端测试基线（#82 后）**：20 files / **109 tests** 全绿（#66 后 112 − websocket 3）。
  漂移说明：STATE 旧记 93 为 #62 时点；#63 +1 → 94，#64 +8 → 102，#83 +1 → 103，
  #65 +5 → 108，#66 +4 → 112，#82 −3 → 109。
- **大屏数据链路（#62 实测）**：`useBigScreen` 5 处失败路径原仅 `console.error`；
  `analysisStore.fetchAll` 内部 `allSettled`，**失败不抛出**，失败信息落在
  `store.error`（只记第一项）——所以只靠 try/catch 判失败会漏掉全部部分失败。
  判定「是否已有可用数据」用 `store.lastFetched[key] === 0`（只有成功返回才更新）。
- **拦截器兜底（勿重复弹窗）**：`api/request.js:82-166` 对每个失败请求已弹
  ElMessage（业务码/HTTP 码/网络错误三类），故大屏错误态用常驻状态而非 toast。
- **#19 失败态语义去向后继**：`useTable.js` 已删；语义已落地在 #62
  （失败保留旧数据 + 显式错误态），#65/#66/#67 待落地。
- **UX 三件套缺口（#60 调研，逐项对应 Issue）**：BigScreen 已由 #62 补齐；
  其余缺 loading：platform(#65) / spider(#66) / tasks(#68) / Profile(#71)；
  缺视图级错误态：platform(#65) / spider(#66) / report(#73) / alert-center(#67)；
  缺空态：alert 规则面板(#67) / BigScreen 热门话题(#78) / comment 热门评论(#80)。
- **响应式**：`Layout/index.vue:53-55` 与 `MobileNav.vue:40-42` 各一份硬编码
  <768（原第三份 `useResponsive.js` 已由 #61 删除）。R-1（#72）以 Layout
  传 prop 实现单源。真实缺陷：`home/index.vue:26/:34` 固定 `:span="12"`、
  `hotWords.vue:32/:50` 固定 `:span="8"/"16"`。
- **测试盲区**：24 视图零 mount（#62 起 BigScreen 已被真实 mount 覆盖）；
  3 个静态 grep 测试（icon-registration 整文件、element-plus-icons 第 2 it、
  tabbar-icons 第 1 describe）+ 1 个零 src 依赖（analysis-contract）。
- **剩余死代码**：`utils/websocket.js` 198 行（有测试无消费者，归 T-4 #82）。
- **#62 附带发现（拟开 auto-discovered）**：`useBigScreen.onRefreshIntervalChange`
  在用户改刷新间隔时 `clearInterval(dataTimer)` 后改挂 `simulateDataUpdate`
  （随机数），真实数据自动刷新被静默替换为假数据。
- **编译器警告**：`home/index.vue:61` `const filters = reactive(...)` 配
  `v-model`（模板 `:4`），vitest 持续输出 `v-model cannot update a const
  reactive binding filters`（归 U-11 #80）。

## 已完成
- **#82 完成转 in-review（2026-10-11）**：删 `frontend/src/utils/websocket.js`（198 行）+
  `frontend/tests/websocket-client.test.js`（3 用例）；动手前复核零消费者（含服务端模板），
  docs 历史引用保留；提交 d0b3025 → merge edf707e @ main（已推送）；前端五门禁全绿
  （109/109 = 112-3）+ 后端 fast gate 1460 passed + ruff + CI/安全双绿。D-011 默认转正落地，
  #58 第二批范围已干净。
- **#66 完成转 in-review（2026-10-11）**：spider 页首屏加载/错误态（useSpider 新增
  overviewLoading/overviewError/logsError + spider.vue 两区指示/错误块 + 重试 + 空态收紧；
  scss 样式）；新增 4 用例；提交 381c81a → merge 272b5c6 @ main（已推送）；
  前端五门禁全绿（112/112）+ 后端 fast gate 1460 passed + ruff + CI/安全双绿。
- **#65 完成转 in-review（2026-10-11）**：platform 页三路 fetch 补加载/错误态（单文件 +
  重试；失败不清旧数据）；新增 5 用例；提交 fdaf4e9 → merge e14d48c @ main（已推送）；
  前端五门禁全绿（108/108）+ 后端 fast gate 1460 passed + ruff + CI/安全双绿。
  附带 auto-discovered #85（对比/情感图写死假数据不消费接口）。
- **#64 完成转 in-review（2026-10-11）**：登录/注册旅程 8 真实 mount 用例（单文件
  `tests/login-journey.test.js`，零源码改动；真实 router + 真实 doLogin；ElMessage
  spyOn；导航断言 vi.waitFor）；提交 91c592a → merge a1c6d1d @ main（已推送）；
  前端五门禁全绿（102/102）+ 后端 fast gate 1460 passed + ruff + CI/安全双绿。
  基线说明：全仓基线 #63 后为 94（STATE 旧记 93 为 #62 时点），#64 后 102。
- **#62 完成转 in-review（2026-10-10，Planner 已验收关闭）**：大屏 loading 绑定 + 区域级错误态 +
  重试入口（全量/面板两级），5 处失败路径全部产生可见状态；新增 9 用例；
  提交 492356c → merge @ main；前端五门禁全绿（93/93）+ 后端 fast gate
  1460 passed + ruff + CI/安全双绿。
- **#61 完成转 in-review（2026-10-10）**：删除 6 个零消费者死模块（1,027 行）
  + 孤儿测试（113 行），同步 `docs/FRONTEND_TS_MIGRATION.md` 第四/六批工作量；
  提交 30f4d2a → merge 5910646 @ main（已推送）；前端五门禁全绿（test 84/84）
  + 后端 fast gate 1460 passed + 文档路径门禁 + ruff + CI/安全双绿。
- **#60 完成转 in-review（2026-10-09，Planner 已验收关闭）**：产出 UX 与技术
  债务调研文档（abf466f → merge 9a039c3 @ main）；22 项候选已立项 #61–#82。
- **#58 完成转 in-review（2026-10-09，Planner 已验收关闭）**：前端 TS
  迁移策略文档 `docs/FRONTEND_TS_MIGRATION.md`（f586877）。
- **#53 验收关闭（2026-10-08，Planner c835b31）**：trend 单系列 counts
  （1909d9b → main c402b4d）；bigscreen-trend.test.js 3 用例 RED→GREEN +
  后端 fast gate + 前端五门禁全绿 + CI/安全双绿；M4 彻底收尾
- **#57/#56/#55/#54/#52 验收关闭**：manifest 悬空条目 / ensure_demo_admin
  ORM + create_time naive UTC / meta.icon 字符串化 19 处 / 死代码清理
  （-409 行）/ 大屏空数据 addColorStop 崩溃（真实浏览器冒烟 RED→GREEN）
- **M3 五项（2026-10-05）**：#43 浏览器冒烟 / #44 GET envelope 契约 /
  #47 写接口契约 / #45 字段契约（立 #53）/ #46 Redis 降级文档
- #42 调研交付（验证码三候选对比 + 国内可用性核实，维持不上）

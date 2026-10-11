# STATE

> 事实账本（可机器解析）。「已完成」仅保留最近 20 条，更早的见 git 历史。

## 当前活跃
- 任务：本轮收尾（2 个 Issue 全部转 in-review，无 in-progress）。本席 executor-20261011T1534Z。
- 状态：in-review 2 项（#67、#68，待 Planner 验收）。
- 剩余队列：ready-for-agent 约 14 个（#69–#80, #84, #85；#59 needs-info；#81 open 待 #72）。
- 本轮起点 main `64dbf57` → 现 main `5305683`（与 origin 同步，2 merge 全部推送）。

## 阻塞项
- 无阻塞。

## 关键事实（已实测验证）
- **前端规模（#68 后）**：.js 32（api 14 · utils 5 · stores 4 · composables 6 · router 1 · plugins 1 · main.js）· .vue 45（views 6305 行 · components 3322 行）· JS+Vue 合计 13,731 行。
- **前端测试基线（#68 后）**：22 files / **117 tests** 全绿（#82 后 109 → #67 +5 → 114 → #68 +3 → 117）。
  漂移说明：#82 后 109，#67 新增 `alert-center-states.test.js` (+5) → 114，#68 新增 `task-list-loading.test.js` (+3) → 117。
- **大屏数据链路（#62 实测）**：`useBigScreen` 5 处失败路径原仅 `console.error`；`analysisStore.fetchAll` 内部 `allSettled`，**失败不抛出**，失败信息落在 `store.error`（只记第一项）。
- **拦截器兜底（勿重复弹窗）**：`api/request.js:82-166` 对每个失败请求已弹 ElMessage（业务码/HTTP 码/网络错误三类）。
- **#19 失败态语义落地状态**：`useTable.js` 已删；语义已落地在 #62、#65、#66、#67（失败保留旧数据 + 显式错误态/重试）。
- **UX 三件套缺口（#60 调研，逐项对应 Issue）**：BigScreen(#62)、platform(#65)、spider(#66)、alert-center(#67)、tasks(#68) 已全部补齐；
  其余缺 loading：Profile(#70/#71)；
  缺视图级错误态：report(#69)；
  缺空态：BigScreen 热门话题(#78) / comment 热门评论(#80)。
- **响应式**：`Layout/index.vue:53-55` 与 `MobileNav.vue:40-42` 各一份硬编码 <768。R-1（#72）以 Layout 传 prop 实现单源。
- **测试盲区**：持续消化中，新增 `login-journey.test.js` (8)、`alert-center-states.test.js` (5)、`task-list-loading.test.js` (3)。
- **编译器警告**：`home/index.vue:61` `const filters = reactive(...)` 配 `v-model`（模板 `:4`），vitest 持续输出 `v-model cannot update a const reactive binding filters`（归 U-11 #80）。

## 已完成
- **#68 完成转 in-review（2026-10-11）**：tasks.vue 两张表格补加载态（TaskList.vue 为 spiderHistory 绑定 spiderLoading，为 startupWarmupResults 绑定 startupLoading；tasks.vue 传入 prop；新增 `task-list-loading.test.js` 3 用例）；提交 1e6339d → merge 5305683 @ main（已推送）；前端五门禁全绿（117/117）+ 后端 ruff clean。
- **#67 完成转 in-review（2026-10-11）**：alert 中心补齐错误态与规则空态（useAlert 增加 retryFetch/fetchError 并保留历史告警；center.vue 增加错误态重试条与规则空态；center.scss 补齐样式；新增 `alert-center-states.test.js` 5 用例）；提交 c424341 → merge f64318c @ main（已推送）；前端五门禁全绿（114/114）+ 后端 ruff clean。
- **#82 验收关闭（2026-10-11）**：删 `frontend/src/utils/websocket.js`（198 行）+ `frontend/tests/websocket-client.test.js`（3 用例）；提交 d0b3025 → merge edf707e @ main。
- **#66 验收关闭（2026-10-11）**：spider 页首屏加载/错误态（useSpider 新增 overviewLoading/overviewError/logsError + spider.vue 两区指示/错误块 + 重试 + 空态收紧）；新增 4 用例；提交 381c81a → merge 272b5c6 @ main。
- **#65 验收关闭（2026-10-11）**：platform 页三路 fetch 补加载/错误态（单文件 + 重试；失败不清旧数据）；新增 5 用例；提交 fdaf4e9 → merge e14d48c @ main。
- **#83 验收关闭（2026-10-11）**：大屏刷新间隔真实数据刷新被假数据替换修复；提交 0512896 → merge b9554b0 @ main。
- **#64 验收关闭（2026-10-11）**：登录/注册旅程 8 真实 mount 用例；提交 91c592a → merge a1c6d1d @ main。
- **#62 验收关闭（2026-10-10）**：大屏 loading 绑定 + 区域级错误态 + 重试入口；新增 9 用例；提交 492356c → merge @ main。
- **#61 验收关闭（2026-10-10）**：删除 6 个零消费者死模块（1,027 行）+ 孤儿测试（113 行）；提交 30f4d2a → merge 5910646 @ main。
- **#60 验收关闭（2026-10-09）**：UX 与技术债务调研文档（abf466f → merge 9a039c3 @ main）。
- **#58 验收关闭（2026-10-09）**：前端 TS 迁移策略文档（f586877）。
- **#53 验收关闭（2026-10-08）**：trend 单系列 counts（1909d9b → main c402b4d）。
- **#57/#56/#55/#54/#52 验收关闭**：manifest 悬空条目 / ensure_demo_admin / meta.icon 字符串化 / 死代码清理 / 大屏空数据 addColorStop 崩溃。
- **M3 五项（2026-10-05）**：#43 浏览器冒烟 / #44 GET envelope 契约 / #47 写接口契约 / #45 字段契约 / #46 Redis 降级文档。

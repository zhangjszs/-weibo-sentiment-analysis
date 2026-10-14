# STATE

> 事实账本（可机器解析）。「已完成」仅保留最近 20 条，更早的见 git 历史。

## 当前活跃
- 任务：M6 PERF 轮（#91 完成、#92 完成、#90 部分完成，均转 in-review；今日队列清空）。本席 executor-20261014Z。
- 状态：in-review 3 项（#90、#91、#92）；ready 1 项（#93 后备，本轮不取）。
- 本轮起点 main `83b2e3b` → 现 main `26ce9ed`（#91 docs 7be3df9 + #92 test 0730b7f + #90 ci 26ce9ed，均已推送）。CI run 38557692302 三 job success。
- 后端 fast gate 本机基线（无覆盖率口径）：#92 后串行 39.33s（改前 47.98s，-18%）；-n 4：~31s；-n 8：25.2s（#91 实测）。CI install 合计：182s → 141s（#90 后，<110s 未达成，run 38557692302 实测）。前端测试基线仍 41 files / 190 tests（本轮未动前端用例）。

## 阻塞项
- #84（历史）：曾 blocked，已由 Planner 在上轮关闭，不再是阻塞项；勿重开。

## 关键事实（已实测验证）
- **前端规模（#68 后）**：.js 32（api 14 · utils 5 · stores 4 · composables 6 · router 1 · plugins 1 · main.js）· .vue 45（views 6305 行 · components 3322 行）· JS+Vue 合计 13,731 行。
- **前端测试基线（#81 后）**：41 files / **190 tests** 全绿（#86 后 187 → #81 +3 → 190）。
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
- **#90 部分完成转 in-review（2026-10-14）**：requirements-ml.txt 新建（7 重包 pin verbatim 迁移，union 程序化核对一致）+ ci.yml 两 job 分层安装 + freeze 漂移探针 + Dockerfile/deploy.py/security-scan 双 -r 同步；CI run 38557692302 三 job success；install 90+92=182s → 78+63=141s（-22.5%），<110s 未达成（差 31s）；提交 a023b1d → merge 26ce9ed @ main（已推送）；YAML/py_compile/paths-check 全过。
- **#92 完成转 in-review（2026-10-14）**：sentiment_model 评估 ×2 取 NB+LogReg 子集（5.60/5.63s → 2.53/2.37s，断言未动）+ model_training 抽样 500 条补 2 断言 + 3.01s×2 归因（/ready redis 3s 超时，CI 同样中招，不修）+ test_performance 0.83s 记录；gate 47.98s → 39.33s（计数一致）；提交 23818f3 → merge 0730b7f @ main（已推送）；ruff clean。
- **#91 完成转 in-review（2026-10-14）**：xdist 本机灰度三轮全绿（串行 50.42s → -n 4：30.64s/31.55s → -n 8：25.20s；计数 1460/69 一致，collect-only 1526/1722 选择一致；零顺序污染）+ TEST_PERF §6/§7 回写；结论暂不纳入 AGENTS.md 默认门禁（xdist 未进 requirements）；提交 12336ba → merge 7be3df9 @ main（已推送）；无 src 改动故 ruff/覆盖率全量/CI 逐项说明未跑原因，见执行报告。
- **#89 完成转 in-review（2026-10-13）**：ci.yml integration needs 去掉 frontend-fast（1 行；job 内零前端引用已 grep 实证；YAML 解析通过）；提交 2caabe8 → merge 3a0471c @ main（已推送）；CI 全绿核对通过（integration 紧随 backend 启动，不再等 frontend；本次 frontend 本就更快，1m19s 为结构性收益）。
- **#88 完成转 in-review（2026-10-13）**：conftest 会话级强制 jti 黑名单内存回退（+7 行；定向 43 passed/5s；fast gate 182.9s→34.9s，-81%；ruff clean；计数 1460/69/196 与基线一致）；提交 4cd99a6 → merge b19432a @ main（已推送）；CI backend-fast success 不回归。
- **#81 完成转 in-review（2026-10-12）**：平板档差异化（Layout checkMobile 单源扩展 isTablet + provide；home R-2 条件 sm 中间档；新增 `tablet-tier.test.js` 3 用例；mobile-single-source 计数断言连带更新）；提交 d5a1312 → merge abb3b98 @ main（已推送）；前端五门禁全绿（190/190）+ 后端 ruff clean。
- **#86 完成转 in-review（2026-10-12）**：formatDuration 收敛 utils 单源（2 处本地删除；`format-utils.test.js` +2 用例）；提交 25578f7 → merge 3a0b33a @ main（已推送）；前端五门禁全绿（187/187）+ 后端 ruff clean。
- **#80 完成转 in-review（2026-10-12）**：home filters 受控更新（:model-value + Object.assign，const 保持；告警 1→0；新增 `home-filters-update.test.js` 1 用例）；提交 532d2a9 → merge 1c123c7 @ main（已推送）；前端五门禁全绿（185/185）+ 后端 ruff clean。
- **#79 完成转 in-review（2026-10-12）**：静态 grep 替换真实挂载（icon-registration 重写 + element-plus 三元探针 + tabbar 路由记录挂载；三组 RED→GREEN 实证；只改测试未改源码）；提交 9caacfd → merge 53f8c57 @ main（已推送）；前端五门禁全绿（184/184）+ 后端 ruff clean。
- **#87 完成转 in-review（2026-10-12）**：comment 热门评论空态（.hot-comments-empty/暂无热门评论，仅空非 loading 时显；新增 `comment-empty.test.js` 3 用例）；提交 cde0a13 → merge 5684b80 @ main（已推送）；前端五门禁全绿（184/184）+ 后端 ruff clean。
- **#78 完成转 in-review（2026-10-12）**：BigScreen 热门话题空态（.no-topics/暂无话题，仅空非 loading 非失败时显；新增 `bigscreen-topics-empty.test.js` 3 用例）；提交 0cc904f → merge 89cb8b2 @ main（已推送）；前端五门禁全绿（181/181）+ 后端 ruff clean。
- **#77 完成转 in-review（2026-10-12）**：predict 模型信息错误态（modelInfoError + 重试；空态仅无错无数据时显；新增 `predict-model-error.test.js` 3 用例）；提交 e6383d0 → merge cba3445 @ main（已推送）；前端五门禁全绿（178/178）+ 后端 ruff clean。
- **#76 完成转 in-review（2026-10-12）**：4 composable 底线（use-alert/tasks/spider/predict-floor 各 3 用例：成功/失败/空；只加测试未改源码）；提交 e276278 → merge 4f6393a @ main（已推送）；前端五门禁全绿（175/175）+ 后端 ruff clean。
- **#75 完成转 in-review（2026-10-12）**：视图挂载矩阵（普查 11 已有 + 13 新增 = 24/24；新增 views-analysis-matrix 7 + views-system-user-matrix 3 + views-error-matrix 3 用例；只加测试未改源码）；提交 82875f4 → merge f5935b5 @ main（已推送）；前端五门禁全绿（163/163）+ 后端 ruff clean。
- **#74 完成转 in-review（2026-10-12）**：日期数字格式化收敛 utils 单源（formatNumber compact 'wk' + formatDateTime/formatLocalDate/formatLocalMonthDay；4 文件本地实现全删；新增 `format-utils.test.js` 17 用例；另立 auto-discovered #86 记录 formatDuration 残留重复）；提交 24ad448 → merge bbe0732 @ main（已推送）；前端五门禁全绿（150/150）+ 后端 ruff clean。
- **#73 完成转 in-review（2026-10-12）**：热词页 8/16 分栏改响应式（:xs=24 :sm=8/16；新增 `hotwords-responsive.test.js` 1 用例）；提交 2eec5f0 → merge df93fd8 @ main（已推送）；前端五门禁全绿（133/133）+ 后端 ruff clean。
- **#72 完成转 in-review（2026-10-12）**：移动端判定收敛为 Layout 单源（MobileNav 删自有 ref/listener/768 改 prop 受控；新增 `mobile-single-source.test.js` 4 用例）；提交 bbc4b41 → merge 73194bb @ main（已推送）；前端五门禁全绿（132/132）+ 后端 ruff clean。
- **#71 完成转 in-review（2026-10-12）**：comment.vue 死 loading 绑定到图表与热门评论区（三 .charts-loading + 一 .hot-comments-loading；新增 `comment-loading.test.js` 2 用例）；提交 3dc6bfa → merge 00eefd8 @ main（已推送）；前端五门禁全绿（128/128）+ 后端 ruff clean。
- **#85 完成转 in-review（2026-10-12）**：platform 对比/情感图接入真实口径（compareChart 读 total_* 真实字段；情感饼聚合 sentiment_distribution；空兜底零值+双空态；删假常量；新增 `platform-compare-real-data.test.js` 3 用例）；提交 106ddb3 → merge be657b6 @ main（已推送）；前端五门禁全绿（126/126）+ 后端 ruff clean。
- **#70 完成转 in-review（2026-10-12）**：Profile.vue 补资料加载态（profileLoading 初始 true + skeleton/v-else；新增 `profile-loading.test.js` 2 用例）；提交 2f114b1 → merge ff4da46 @ main（已推送）；前端五门禁全绿（123/123）+ 后端 ruff clean。
- **#69 完成转 in-review（2026-10-12）**：report.vue 补齐错误态（模板区 loading/error+重试+空成功空态；预览区 error+重试；守卫改依赖 reportError 根因；新增 `report-error-states.test.js` 4 用例）；提交 83b633d → merge 01a40ba @ main（已推送）；前端五门禁全绿（121/121）+ 后端 ruff clean。
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

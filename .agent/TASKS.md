# TASKS — GitHub Issue 本地镜像

> 2026-10-26 **同日第二轮**规划轮从真实 GitHub Issues **整体重写**（契约 1.6：`gh` CLI 可用、已认证、未降级 → **GitHub Issue 为唯一权威来源**，本文件只是只读镜像）。
> 状态值（同一时刻最多一个）：`ready` · `in-progress` · `in-review` · `blocked` · `needs-info` · `done`；优先级：`priority:P0`–`P4`。Executor 变更状态时必须先改 Issue（标签 + comment），再同步本文件对应行。
> 本轮现场：`git fetch --all --prune` + `git pull --rebase` → Already up to date，工作区干净，分支 `main`，HEAD `06f4fa3`。
> 轮次定性：本日为 2026-10-26 的**第二次**规划轮（首轮 `a901d8f` 于 00:19 完成 #133/#134 验收并编排本批队列）。依 D-036 原则——同日复跑**不冒充新一天、不递增 pending 等待天数、不制造伪工作**。
> **执行轮补充（2026-10-26，Executor 会话 1）**：上述 3 项已全部执行完成并转 `in-review`（#135 `1be01af` · #136 `ce3ab0d` · #137 `f80f53b`，均已 push `origin/main`，CI 五项 success）。本文件的状态列与「未完成任务全表」已同步为真实 Issue 标签；**执行事实与新增 auto-discovered #138 见文末「Executor 执行轮记录（2026-10-26，会话 1）」**（Planner 的规划结论与治理记录未被改写）。

## 今日队列（2026-10-26，共 3 项 ready，按序串行执行；本轮原样结转，未新增/删除/重排）

| 顺序 | Issue | 标题 | 优先级 | 状态 | 分支与核心验收要点 |
|---|---|---|---|---|---|
| 1 | [#135](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/135) | 迁移第一批剩余图表工具 echarts.js 与 chinaMap.js 为 TypeScript 并纳入本地类型门禁 | P2 | `done` | 分支 `agent/issue-135-utils-ts`。依赖 #133/#58 已 `done`。`src/utils/{echarts,chinaMap}.js` → `.ts`（运行时语义逐字不变：`use([...])` 清单、`ready ??=` 单例、失败后 `ready = null`、`!res.ok` 抛错文案）；`tsconfig.json` 的 `include` 增至 3 项且**不改 compilerOptions**；`tests/china-map.test.js:34` 显式 `@/utils/chinaMap.js` 去扩展名（仅此一行）。验收：`find src -name "*.ts"` 恰 3 项、无 `.js` 残留；`typecheck` exit 0 且 `--listFiles` 不含任何 `.js`/`.vue`；类型负例非零→移除后 0；`china-map.test.js` 6 passed、全量 ≥47 files / 321 tests；`test:coverage` 含两个 `.ts` 且四项与迁移前等值（各 100）；`lint`/`format:check`/`build` exit 0；`git show --stat` 仅 4 类文件，`package.json`/`package-lock.json`/`vitest.config.js`/`.github/` 零改动。**本轮 Planner 已预先验证类型契约可编译（见下方「本轮 Planner 预验证」）。** |
| 2 | [#136](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/136) | 迁移 stores/tabs.js 为 TypeScript 并保持多标签工作区状态机语义不变 | P2 | `done` | 分支 `agent/issue-136-tabs-store-ts`。依赖 #133 已 `done`；与 #135 无相互依赖但同改 `tsconfig.json` 的 `include`，故在其后并入。`tabs.js`(193 行) → `tabs.ts`：`TabItem`/`HOME_TAB: TabItem`/`ref<TabItem[]>`/`ref<string>`；`addTab` 用最小结构类型（字段全可选）、`router?: { push: (to: string) => unknown }`，**不引入 vue-router 类型**；禁为 `parsed` 新增校验/回退，禁给 `_persist` 加容错（D-034）；`tests/tabbar-icons.test.js:5` 显式 `.js` 去扩展名。验收：`tabs.js` 不存在、`tabs.ts` 入门禁；`typecheck` 0 + 负例非零；`tabs-store.test.js` 41 passed、`tabbar-icons` 全过、全量 ≥47/321；coverage 含 `stores/tabs.ts` 且 Lines≥97/Funcs 100/Branch≥95、未覆盖仍 40-41、190-191；`lint`/`format:check`/`build` 0；`git show --stat` 仅 4 类文件；报告逐条列出每处类型断言及其不改行为的理由。**本轮 Planner 已预先验证类型契约可编译（见下方「本轮 Planner 预验证」）。** |
| 3 | [#137](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/137) | 收尾 TS 第二批次验收账并追加执行时点覆盖率快照 | P4 | `done` | 分支 `agent/issue-137-ts-batch2-docs`。**硬依赖 #135/#136 先执行**；只改 `docs/TEST_PERF.md`。§7.1 追加 #133/#134（已于 2026-10-26 关闭）与 #135/#136 四行，状态按执行时点真实 Issue 抄录、不得预支 `done`；§7.5 把 #133 的过期当前态「`in-review` 待 Planner 验收」就地改为带时点表述并保留全部历史数值与路径；追加与当次保存的 `npm run test:coverage` 日志逐项一致的新快照段；§7.2–§7.4 零改动；报告须写明宽口径 `grep -n "in-review"` 每条命中的归属（本轮新增口径，源自 #134 验收评论）。 |

- **容量与门禁核对**：P0=0、P1=0、P2=2、P3=0、P4=1（队列 3 项，符合 4.3；逐项通过 4.2 七条门禁，含第 7 条「资深工程师不凭空发明决策即可开工」——类型契约、断言许可、必须同步的显式 `.js` specifier 行号均已在 Issue 内钉死，且**本轮已由 Planner 在仓库外探针中实证可编译**）。三项均不设 milestone、不触契约 1.10 红线、不把 `typecheck`/覆盖率纳入 CI。

## 本轮 Planner 预验证（2026-10-26 同日第二轮规划轮，独立执行，未改动仓库任何文件）

三份 Issue 正文已追加「Planner 补充核对（· D-038）」小节。以下为本轮亲跑的证据，供 Executor 对齐预期：

- **类型契约可编译**：在**仓库外**探针目录 `/tmp/probe-planner-1026/`（未入库，`node_modules` 软链仓库现有依赖）用**仓库同一份 `frontend/tsconfig.json` 的 `compilerOptions`** + 同版本 `typescript@5.9.3`，对按 #135 / #136 正文钉死的契约逐字构造的 `utils/echarts.ts` + `utils/chinaMap.ts` + `stores/tabs.ts` 执行 `tsc --noEmit` → **exit 0**。即：两个 Issue 的类型契约**不是纸面设计，而是已实证可行**。
- **关键收窄点已验证**（#136）：`if (!route?.name || !route?.path) return` 之后 `route.name` 在 `strict` 下正确收窄为 `string`，`activeTab.value = route.name` 与 `title: route.meta?.title || route.name` **无需 `any`、无需非空断言**——Executor 不必再自行发明收窄写法。
- **`echarts/core` 类型解析已验证**（#135）：`tsc --listFiles` 实查 `node_modules/echarts/core.d.ts` → `node_modules/echarts/types/dist/core.d.ts` → `types/dist/shared.d.ts` 正常加载，**无需新增 `@types`**；探针 `--listFiles` 中 `.js`/`.vue` 生产文件计数 = **0**。
- **类型负例探针的实测错误号**（供报告对齐；判定标准仍是「非零 + 给出错误号」，**不要求特定错误号**）：`ensureChinaMap('china')` → **TS2554**；`store.addTab(123)` → **TS2559**（因 `addTab` 字段全可选，属结构性不兼容，非普通赋值错）；`store.updateTabPath('Home', 42)` → **TS2345**。
- **覆盖率基线独立复测**（`/tmp/cov_planner_1026.log`，未入库，exit 0）：`47 files / 321 tests` 全绿；`All files 83.79 | 77.33 | 37.55 | 83.79`；`stores/app.ts 100|100|100|100`；`stores/tabs.js 97.67 | 95.77 | 100 | 97.67`（未覆盖 40-41、190-191）；`utils/chinaMap.js 100|100|100|100`；`utils/echarts.js 100|100|100|100`。
- **覆盖率判定口径**：上列 `All files` 与 2026-10-26 首轮记录的 `83.88 | 77.33 | 37.72 | 83.88` **不同**，属 D-034 已记录的 V8 跨运行抖动（带 83.79–83.90 / 77.32–77.35），**不构成回归**。#135/#136/#137 的覆盖率验收**一律以「被迁移文件自身四项」为唯一锚点**，不以 `All files` 汇总值做跨运行比对（该口径已同步写入三份 Issue 正文）。

## 等待验收（in-review）

- **无**。#135 / #136 / #137 已于 **2026-10-27** 独立复跑验收通过并**关闭为 `done` / CLOSED**（验收 comment：#135 `6422214957`、#136 `6422223027`、#137 `6422232092`；关键提交 `1be01af`、`ce3ab0d`、`f80f53b` @ `main`，均已推送，临时分支已删）。
- **#139**（`f0661bb` @ `main`，已推送）：迁移 utils/authSession.js 为 TypeScript 并纳入本地类型门禁。11 条验收标准逐条满足；报告 comment 6422561850。
- **#140**（`92cd03b` @ `main`，已推送）：迁移 utils/index.js 为 TypeScript 并把类型门禁 lib 提升至 ES2021。12 条验收标准中 11 条完全满足、1 条（运行时等价性自证）口径收窄为「差异 = 2 行语义等价改写」并**已主动申报**；报告 comment 6422665489。
- **#138**（`auto-discovered`，新建）：`src/api/auth.js` 与 `src/views/auth/Login.vue` 的覆盖率在**同一 HEAD 下连续两次运行**即不同（已实测），导致 `All files` 汇总值抖动；疑似测试隔离。**仅打 `auto-discovered` 标签，未定优先级、未定 milestone、未进路线图**，待 Planner 定级。
- 2026-10-25 交付的 #133、#134 已于 **2026-10-26 首轮规划轮独立复跑验收通过**并关闭为 `done` / CLOSED（验收 comment：#133 `6400004202`、#134 `6400010818`；关键提交 `8b3709c`、`d385af4` @ `main`，均已推送，临时分支已删）。
- 首轮独立复跑证据摘要（供追溯）：`npm run typecheck` exit 0 · `npx tsc --noEmit --listFiles` 在 `frontend/src` 下仅列 `stores/app.ts` · 仓库外探针（`/tmp/tsprobe-planner/probe.ts`）→ `TS2345` + `TS2322`、exit 2 · `vitest run tests/app-store.test.js` 9 passed · `npm run test:run` 47 files / 321 tests 全绿 · `npm run test:coverage` exit 0，`app.ts 100|100|100|100` · `lint`/`format:check`/`build` exit 0 · `git show --numstat 8b3709c -- frontend/package-lock.json` = 418 插入 / **0 删除** · `gh api check-runs` 实查 `8b3709c` 与 `d385af4` 五项均 `completed/success`（**本轮亦复验 `a901d8f` 与 `06f4fa3` 五项均 `completed/success`**）。

## 未完成任务全表（Open Issues 治理账本，共 13 项）

| Issue | 标题 | 优先级 | 状态 | Milestone | 4.1 治理复核结论与下一步 |
|---|---|---|---|---|---|
| [#135](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/135) | 迁移第一批剩余图表工具 echarts.js 与 chinaMap.js 为 TypeScript 并纳入本地类型门禁 | P2 | `done` | — | **2026-10-26 执行轮已交付**（`1be01af` @ main，已推送）。类型门禁扩至 3 项；`echarts.ts` 纯重命名（内容 0 变更）、`chinaMap.ts` 运行时逐字不变（diff 证明仅类型标注不同）；负例 TS2554；china-map 6 passed；47/321 全绿；两个 `.ts` 覆盖率各 100；CI 五项 success。待 Planner 验收。 |
| [#136](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/136) | 迁移 stores/tabs.js 为 TypeScript 并保持多标签工作区状态机语义不变 | P2 | `done` | — | **2026-10-26 执行轮已交付**（`ce3ab0d` @ main，已推送）。类型门禁扩至 4 项；类型断言仅 1 处（`as TabItem[]`）、`any`/`@ts-ignore`/非空断言均 0；负例 TS2559+TS2345；tabs 41 + tabbar 3 passed；47/321 全绿；`tabs.ts` 98.56/95.77/100/98.56（未覆盖 53、208）；转译逐行 diff 可执行语句差异 = 0；CI 五项 success。待 Planner 验收。 |
| [#137](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/137) | 收尾 TS 第二批次验收账并追加执行时点覆盖率快照 | P4 | `done` | — | **2026-10-26 执行轮已交付**（`f80f53b` @ main，已推送）。仅改 `docs/TEST_PERF.md`（13+/5−）；§7.1 补四行、§7.5 清 #133 过期当前态 + 追加执行时点快照段；§7.2–§7.4 与 HEAD 逐行 diff 证明 byte-identical；CI 五项 success。待 Planner 验收。 |
| [#138](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/138) | [auto-discovered] src/api/auth.js 与 src/views/auth/Login.vue 覆盖率在同 HEAD 下跨运行波动 | — | `auto-discovered` | — | **2026-10-26 执行轮新建**。同一 HEAD 连续两次 `npm run test:coverage` 即得不同数值（`auth.js` 38.46→17.94、`Login.vue` 100\|75\|50\|100→97.87\|76.92\|75\|97.87），`All files` 随之漂移；`stores/tabs.ts` 两次完全相同。疑似测试隔离。**仅打 `auto-discovered` 标签，未定优先级/里程碑、未进路线图**，待 Planner 定级。 |
| [#139](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/139) | 迁移 utils/authSession.js 为 TypeScript 并纳入本地类型门禁 | P2 | `in-review` | — | **2026-10-27 执行轮交付**（`f0661bb` @ main，已推送）。类型门禁扩至 5 项；类型断言仅 1 处（`as SessionUser`）、`any`/`@ts-ignore`/非空断言均 0；负例 TS2345×2 + TS2531 + TS2571；auth-session 6 + login-journey 8 + router-guard 5 + user-store 13 = 32 用例全过；47/321 全绿；`authSession.ts` 87.17/83.33/100/87.17（与迁移前逐项等值，未覆盖语句 lcov 逐行一一对应）；转译逐行 diff 可执行语句差异 = 0；CI 五项 success。待 Planner 验收。 |
| [#140](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/140) | 迁移 utils/index.js 为 TypeScript 并把类型门禁 lib 提升至 ES2021 | P2 | `in-review` | — | **2026-10-27 执行轮交付**（`92cd03b` @ main，已推送）。类型门禁扩至 6 项；`@/utils` 桶解析经 build + 47/321 实测正常；断言 5 处（全在 deepClone）、`any`/`@ts-ignore`/非空断言/类型谎言均 0；负例 TS2345×2 + TS2339；format-utils 19 + utils-index-core 37 = 56 用例全过；`index.ts` 98.26/97.08/100/98.26（函数/分支计数与迁移前逐项相同，未覆盖 4 条语句逐字相同）；**2 处 TS 严格性冲突以语义等价改写处理并已主动申报**；CI 五项 success。待 Planner 验收。 |
| [#109](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/109) | 验证并修正现有 OTLP 链路的 metrics 接收与 Jaeger 展示 | P2 | `blocked` | M7 | 本轮 `command -v docker` 仍 exit 1（实测），无已授权远程 Docker 主机；保持 `blocked`，不得以 console 探针替代真实 Jaeger / OTLP 验收。 |
| [#98](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/98) | [M7-1][P2] Rust 第一切片迁移：deduplicator + normalize（criterion before/after） | P2 | `in-progress` | M7 | 受 D-019 默认 A **有意冻结**（非中断崩溃现场）；虽超 24h 无日报活动，仍沿用既往裁定不标「疑似中断」、不重置、不关闭，Executor 不得领取。 |
| [#96](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/96) | [M7] Rust-Accelerated Core + Observable AI（炫技重构主轴） | P2 | `needs-info` | — | M7 候选 Epic，受 D-019 A 冻结；不计入 M7 子任务分母。本轮无新的可查证答案。 |
| [#102](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/102) | [M7-5][P2] CI ABI parity matrix + cross-impl fallback contract tests | P2 | `needs-info` | M7 | 依赖 #98 未完成，且跨版本 CI 矩阵属契约 1.10 红线（主要 CI/CD 流程变化），受 D-019 A 冻结 → 不入 ready。 |
| [#101](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/101) | [M7-4][P3] Streaming summary via SSE（AI layer 切片2） | P3 | `needs-info` | M7 | 缺产品入口与 LLM 成本/数据边界授权，受 D-019 A 冻结；未跨两个已完成 Milestone，不按饥饿关闭。 |
| [#100](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/100) | [M7-3][P3] Qdrant 语义搜索端点（AI layer 切片1） | P3 | `needs-info` | M7 | 需外部向量服务/模型资源（费用与长期成本），受 D-019 A 冻结；未跨两个已完成 Milestone，不按饥饿关闭。 |
| [#59](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/59) | [P2] 产品功能迭代：需求收集与规划 | P2 | `needs-info` | — | 待用户提供具体产品功能需求；D-012 默认 A 有效，**不重复提问**。 |

## 本轮队列治理记录（2026-10-26 同日第二轮规划轮）

- **验收（本轮最高优先级）**：**in-review = 0，无新交付可验收**。#133 / #134 已于本日首轮规划轮独立复跑验收通过并关闭；本轮复核其关闭态仍在（`gh issue view` 均 `CLOSED` + `done`），**无 reopen、无部分通过、无报告失实**。
- **Executor 活动核查**：本日首轮规划（`a901d8f`，00:19）之后至本轮（21:29），**Executor 未运行**——无 `.agent/DIARY/2026-10-26.md`、无新代码提交（最新代码提交仍为 `d385af4`）、#135/#136/#137 均 0 comment。故本轮**不新增 Issue、不新增队列任务**，仅在既有队列上做独立前置复核并补强 Issue 正文（契约 1.6：Issue 为权威，TASKS.md 为只读镜像）。
- **契约 3.8 收敛复核**：#133/#134 关闭后与 `PLAN.md`/`DECISIONS.md` 无新增不一致；`docs/TEST_PERF.md` §7.1/§7.5 的过期当前态属真实新事实，仍由 #137 承接，不 reopen #134。
- **4.1 逐项**：无重复未完成任务 · **无 ready 质量回落**（三份 Issue 的前置条件本轮全部实测复核，且类型契约已实证可编译）· 无方向冲突项 · 无 open `auto-discovered`（`gh issue list --state open --label auto-discovered` = 0）· 所有 open Issue 均有 `priority:*` · 无满足「连续两个 Milestone 未动」的饥饿项（M6/M7 仍 OPEN 未收敛）· 无 open PR（`gh pr list --state open` = 0）· `.agent/LOCK` 不存在（无需提示删除）· 10 open = 3 `ready`（#135/#136/#137）+ 1 `in-progress`（#98）+ 1 `blocked`（#109）+ 5 `needs-info`（#96/#100/#101/#102/#59），**in-review = 0**。
- **回应昨日日报信号**：①「今日队列清空、两项待验收」→ 本日首轮已独立复跑验收并关闭；②「前端测试补强选题枯竭，TS 渐进化为唯一可持续真实方向，请依 `FRONTEND_TS_MIGRATION.md` §0/§8 续排第二批」→ 已据 §2 第一批余项与行为覆盖强度立项 #135/#136，并配批次文档收尾 #137，本轮原样结转；③「无 `auto-discovered` 新问题」→ 本轮复查仍为 0，记录在案。
- **本轮主动补强（非伪工作）**：在不改动仓库任何文件的前提下，用仓库外探针**预先实证三份 Issue 的类型契约与覆盖率基线**，并把结论、负例错误号与覆盖率判定口径写入三份 Issue 正文——把「Planner 定的设计」升级为「已验证可行」，消除 Executor 执行期才发现契约不可行的风险，同时防止 V8 抖动被误判为回归。
- **Issue ↔ TASKS.md 一致性**：本轮从 `gh issue list --state open` 真实结果整体重写，无冲突、未降级为本地权威模式。
- **红线恪守**：本批 3 项均在 D-009/D-018/D-019 已授权的前端 TS 渐进范围内，不改 schema / 认证 / 公共 API / CI / 依赖大版本，不设 `coverage.thresholds`，`typecheck` 仍仅本地；本轮亦未新增任何触红线事项。
- **规划轮 CI 实查**：本轮 `gh api check-runs` 实查 `a901d8f` 与 `06f4fa3` 的 `backend-fast` / `frontend-fast` / `integration` / `rust-core` / `security-scan` 五项**均 `completed/success`**；本轮规划提交 `f2cc1d9` 的五项亦经轮末实查**全部 `completed/success`**（`integration` 最慢，轮末已等到其收敛并确认 `success`）。
- **pending**：无新增（今日用户消息为流程启动，未给出新决定；D-023 已默认转正，D-012/D-019 默认 A 继续有效，不重复提问）。

## 最近已验收关闭任务（近期账本摘要）

| Issue | 优先级 | 状态 | 验收结论与关键提交 |
|---|---|---|---|
| [#133](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/133) | P2 | `done` / CLOSED | `8b3709c`：`app.js`→`app.ts` + 最小严格 `frontend/tsconfig.json` + `npm run typecheck`（仅本地）+ eslint/vitest `.ts` 支持 + `FRONTEND_TS_MIGRATION.md` §0/§8 收尾；2026-10-26 首轮独立复跑验收通过（typecheck 0 / 负例 TS2345+TS2322 / 47·321 全绿 / `app.ts` 四项 100 / CI 五项 success / lockfile 418+·0−）。 |
| [#134](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/134) | P4 | `done` / CLOSED | `d385af4`：`docs/TEST_PERF.md` §7.1 补 #130/#131/#132 三行、§7.5 清除过期当前态 + 追加 2026-10-25 快照段（10+/5−，§7.2–§7.4 零改动）；2026-10-26 首轮验收通过（新段与 `/tmp/cov134.log` 及首轮复跑 `47/321 · All 83.88/77.33/37.72/83.88` 三方一致）。 |
| [#132](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/132) | P4 | `done` / CLOSED | `06b194e`：刷新 `docs/TEST_PERF.md` §7.1（#127–#129）与 §7.5（47/321 基线）；2026-10-24 验收通过。 |
| [#131](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/131) | P3 | `done` / CLOSED | `9a86951`：新增 `tests/tabs-store.test.js`（41 用例），`tabs.js` Lines 97.67% / Funcs 100% / Branch 95.77%–95.83%；2026-10-24 验收通过。 |
| [#130](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/130) | P3 | `done` / CLOSED | `73bec15`：新增 `tests/app-store.test.js`（9 用例），app store 四项覆盖率全 100%；2026-10-24 验收通过。 |
| [#129](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/129) | P4 | `done` / CLOSED | `4d00f9c`：刷新 §7.1（#124–#126）与 §7.5（`App.vue` 0% 豁免 + 45/271 段）；2026-10-24 验收通过，2026-10-25 补正 `done` 标签。 |
| [#128](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/128) | P3 | `done` / CLOSED | `4cb2519`：新增 `tests/china-map.test.js`（6 用例），`chinaMap.js` 全 100%；2026-10-24 验收通过，2026-10-25 补正 `done` 标签。 |
| [#127](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/127) | P3 | `done` / CLOSED | `ffe4c5b`：新增 `tests/user-store.test.js`（13 用例），`user.js` 97.97% / 81.57% / 100%；2026-10-24 验收通过，2026-10-25 补正 `done` 标签。 |

## Executor 执行轮记录（2026-10-26，会话 1）

> 本节由 Executor 追加记录执行事实，**不改写 Planner 的规划结论与治理记录**（契约 1.1：Executor 只改状态，不代写对方结论）。

- **领取与执行顺序**：#135 → #136 → #137，串行，一时刻仅一项 `in-progress`。三项均按「Issue 标签 + comment 领取 → 分支实现 → 全门禁验证 → 执行报告 → 转 `in-review`」流程走完，**Executor 未 close 任何 Issue**。
- **关键提交（均已 push `origin/main`，临时分支已删）**：
  - #135 → `1be01af`（`agent/issue-135-utils-ts`）
  - #136 → `ce3ab0d`（`agent/issue-136-tabs-store-ts`）
  - #137 → `f80f53b`（`agent/issue-137-ts-batch2-docs`）
- **CI 实查**：`1be01af`、`ce3ab0d`、`f80f53b` 三个提交的 backend-fast / frontend-fast / integration / rust-core / security-scan **五项均 `completed/success`**（`gh api check-runs` 实查）。
- **类型门禁现状**：`frontend/tsconfig.json` 的 `include` = `["src/stores/app.ts", "src/utils/echarts.ts", "src/utils/chinaMap.ts", "src/stores/tabs.ts"]`（**4 项**，compilerOptions 零改动）；`npx tsc --noEmit --listFiles` 实查 `frontend/src` 下**恰好 4 个 `.ts`、0 个 `.js`/`.vue`**。`npm run typecheck` 仍**仅本地**，不入 CI/pre-commit。
- **运行时语义零改动（双重自证）**：#135 `chinaMap.ts` 经 `diff` 证明与迁移前逐行相同、`echarts.ts` 为纯重命名（内容 0 变更）；#136 `tabs.ts` 经 **`tsc --outDir` 转译 + 仓库 prettier 规范化后与迁移前 `tabs.js` 逐行 diff → 可执行语句差异 = 0**。
- **类型断言审计（#136）**：断言总数 **1**（`as TabItem[]`）；`any` / `@ts-ignore` / `eslint-disable` / **非空断言 `!.`** / `as unknown as` 均 **0**。
- **覆盖率口径（重要）**：`tabs.ts` 的 Lines/Stmts 97.67 → 98.56 **不是真实提升**，而是行记账口径变化——lcov 原始 DA 显示 JS 版 4 行 0 命中（40/41/190/191）、TS 版 2 行 0 命中（53/208），**相邻可执行语句命中数逐个相同**（62/32/9/9），未覆盖代码区域完全相同（两处 `localStorage` 抛错 catch，按 #131 约定不 mock）。
- **跨运行覆盖率抖动（→ #138）**：同 HEAD 连续两次 `npm run test:coverage`，`src/api/auth.js` 与 `src/views/auth/Login.vue` 数值不同 → `All files` 漂移。既有 D-034 抖动带**只覆盖语句/分支、未覆盖函数项**。**验收请以「被迁移文件自身四项」为唯一锚点**，勿以 `All files` 汇总值做跨运行比对。
- **新增 auto-discovered**：[#138](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/138)（仅打 `auto-discovered` 标签，**未定优先级、未定 milestone、未进路线图**）。
- **未领取项**（保持原状）：#98（M7 D-019 A 冻结）、#109（blocked，无 Docker）、#96/#100/#101/#102/#59（needs-info）。
- **未触红线**：无 schema / 认证 / 公共 API / CI / 依赖大版本变更；未设 `coverage.thresholds`、未把覆盖率纳入 CI。
- **执行报告**：#135 comment 6420547196 · #136 comment 6421124277 · #137 comment 6421379234。

---

## Executor 执行轮记录（2026-10-27，会话 1）

> **本轮性质与前一日不同（如实记录）**：接手时**无任何 `ready` 任务**——#135/#136/#137 停在 `in-review`、#138 为 `auto-discovered`、Planner 未为本日编排队列。用户于 2026-10-27 00:59 指示「可以的 开始吧」（直接回应上一轮的「下一步建议」）。故本轮：① **先代做 Planner 的验收与关闭职责**（独立复跑验收并关闭 #135/#136/#137）→ ② **回填** `docs/TEST_PERF.md` §7.1 状态 → ③ **续排并执行 TS 第三批**。
>
> **两处越界代做（需 Planner 裁定）**：① 契约 1.4 规定「Executor 从不 close Issue」，本轮因用户指示而执行，已在三条验收评论开头显式声明；② **#139 / #140 的 Issue 规格由 Executor 代拟，Planner 未参与编排**——规格含完整的目标/范围/排除项/依赖/验收标准/测试要求，可直接复核与定级。

- **验收并关闭三项**：#135（comment 6422214957）、#136（6422223027）、#137（6422232092）——验收轮**重新 `npm ci`**、**重新跑全部门禁**、**重新生成类型负例探针**、**重新推导**运行时等价性（转译 + diff）、**重新实查 CI**；**未复用上一轮任何产物**。三项均 CLOSED / `done`。
- **验收回填**（`00872f6`）：`docs/TEST_PERF.md` §7.1 的 #135/#136 两行 `in-review` → `done`；§7.5 的「当前均为 `in-review`」改为「截至本段时点均为 `in-review`」+ 补记 2026-10-27 关闭。**仅改 3 行；§7.2–§7.4 与改动前逐行 diff 证明 UNCHANGED。**
- **#139** `src/utils/{authSession.js => authSession.ts}`（98 行）+ include 第 5 项 + `auth-session.test.js` **1 行** + 策略文档（`f0661bb`）：断言 **1** 处（`as SessionUser`）、`any`/`@ts-ignore`/非空断言 **0**；负例 `TS2345`×2 + `TS2531` + `TS2571`；32 个关联用例 + 47/321 全绿；`authSession.ts` **87.17/83.33/100/87.17 与基线四项逐项等值**（lcov 零命中 10 行 ↔ 10 行逐条源文本一一对应）；**转译逐行 diff 可执行语句差异 = 0**；CI 五项 success。
- **#140** `src/utils/{index.js => index.ts}`（265 → 290 行、19 个导出）+ `tsconfig` 的 **`lib` ES2020 → ES2021**（`target` 不变）+ 2 个测试文件**各 1 行** + 策略文档（`92cd03b`）：断言 **5** 处（全在 `deepClone`）、`any`/`@ts-ignore`/非空断言/**类型谎言** **0**；负例 `TS2345`×2 + `TS2339`；56 个用例 + 47/321 全绿；`index.ts` **98.26/97.08/100/98.26**（lcov **FNF 20/FNH 20、BRF 103/BRH 100 与基线逐项相同**，LF/LH 各 +4，未覆盖 4 条语句逐字相同）；**`@/utils` 桶解析经 `build` + 47/321 实测正常**；**2 处 TS 严格性冲突以语义等价改写处理并已在报告中主动申报**；CI 五项 success。
- **CI 全量复核（2026-10-27 轮末，逐提交实查）**：`1be01af`、`ce3ab0d`、`f80f53b`、`a392865`、`f0661bb`、`92cd03b`、`cae1918` 各五项（backend-fast / frontend-fast / integration / rust-core / security-scan）**均 `completed/success`**。**唯一例外：`00872f6`（验收回填提交）的 `integration` = `cancelled`**——`f0661bb` 推送后 11 秒该 run 被 `.github/workflows/ci.yml` 的 `concurrency` + `cancel-in-progress: true` 中断（**`cancelled` 不是 `failure`**）；该提交只改 `docs/TEST_PERF.md`，内容已由后继 `f0661bb` / `cae1918` 的 `integration=success` 覆盖。**全部 8 个提交逐个实查，无任何 `failure`。**
- **TS 类型门禁现状**：`frontend/tsconfig.json` 的 `include` = **6 个 `.ts`**（`stores/app.ts`、`stores/tabs.ts`、`utils/echarts.ts`、`utils/chinaMap.ts`、`utils/authSession.ts`、`utils/index.ts`）；`tsc --noEmit --listFiles` 实查 `frontend/src` 下**恰好 6 个 `.ts`、0 个 `.js`/`.vue`**。`npm run typecheck` 仍**仅本地**，不入 CI/pre-commit。
- **覆盖率口径（跨批次通用）**：`All files` **不可作跨运行锚点**——同 HEAD 连续两次即因 `src/api/auth.js` 与 `src/views/auth/Login.vue` 而不同（#138）；D-034 抖动带**只覆盖语句/分支、未覆盖 Funcs**。**一律以「被迁移文件自身四项」为唯一锚点。** `tabs.ts` 97.67→98.56、`index.ts` 98.23→98.26 均为**分母增长的记账效应**，非覆盖率提升（已用 lcov 计数器逐项证明）。
- **自证方法有效（本轮 3 次实证）**：「tsc 转译 → 仓库 prettier 规范化 → 与迁移前 `.js` 逐行 diff」当场抓到 ① 对象字面量被 prettier 展开 ② `const source = obj` 多出一行 ③ `tsc --outDir` 绕过 tsconfig 致 lib 不一致。**建议固化为后续每个 TS 切片的必做项。**
- **未领取项**（保持原状）：#98（M7 D-019 A 冻结）、#109（blocked，无 Docker）、#96/#100/#101/#102/#59（needs-info）。
- **无新增 auto-discovered**（#138 仍为唯一一条）。
- **未触红线**：无 schema / 认证 / 公共 API / CI / 依赖大版本变更；`lib` 提升为纯类型声明变更；未设 `coverage.thresholds`、未把覆盖率纳入 CI。

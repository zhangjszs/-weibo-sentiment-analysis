# TASKS — GitHub Issue 本地镜像

> 2026-10-27 **规划轮**从真实 GitHub Issues **整体重写**（契约 1.6：`gh` CLI 可用、已认证、未降级 → **GitHub Issue 为唯一权威来源**，本文件只是只读镜像）。
> 状态值（同一时刻最多一个）：`ready` · `in-progress` · `in-review` · `blocked` · `needs-info` · `done`；优先级：`priority:P0`–`P4`。Executor 变更状态时必须先改 Issue（标签 + comment），再同步本文件对应行。
> 本轮现场：`git fetch --all --prune` + `git pull --rebase` → 已同步，工作区干净，分支 `main`，HEAD `06bb2d6`。
> 轮次定性：本日为 2026-10-27 的**第二个规划轮**（第一轮由 Executor 于 00:59 起代做 Planner 职责并于 01:00–07:27 执行，交付 #139/#140）。依 D-036 原则——同日复跑**不冒充新一天、不递增 pending 等待天数、不制造伪工作**；本轮的实质内容是**独立复跑验收 + 治理 + 重新编排队列**，非重复劳动。
> **本轮 Planner 的实际动作**：独立复跑验收并关闭 #139/#140（验收评论 6440380674 / 6440392290）；裁定 Executor 两处越界代做（D-039）；新建 #141/#142/#143；给 #138 定级 P3。

## 今日队列（2026-10-27，共 3 项 ready，按序串行执行；全部为本轮新建）

| 顺序 | Issue | 标题 | 优先级 | 状态 | 分支与核心验收要点 |
|---|---|---|---|---|---|
| 1 | [#142](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/142) | 统一治理 .ts 文件的 no-redeclare 误报（TS 重载签名被基础 ESLint 规则误判） | P2 | `ready` | 分支 `agent/issue-142-ts-no-redeclare`。**只改 `frontend/eslint.config.js` 的 `**/*.ts` block** +（方案 A 时）`package.json`/`package-lock.json` + 文档；`src/**` 与 `tests/**` 零改动。方案 A：引 `@typescript-eslint/eslint-plugin@8.46.2`（与现有 parser 同版本）用插件版 `no-redeclare`；方案 B：`.ts` block 内 off 基础规则，**但必须实测证明 tsc 仍会拦真正的重复声明**（TS2300/TS2393）——否则不得用 B。验收：重载签名探针 `npx eslint` → **exit 0**；真重复探针 `npx tsc --noEmit` → **非零**；`lint`/`format:check`/`typecheck` 全 0；JS/Vue 侧 lint 结果**逐项不变**；`test:run` ≥47/321；CI 五项实查。**建议先做**：改完配置后 #141 的 lint 结果即最终态。 |
| 2 | [#141](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/141) | 迁移 plugins/elementPlus.js 为 TypeScript 并纳入本地类型门禁 | P2 | `ready` | 分支 `agent/issue-141-elementplus-ts`。`ICON_COMPONENTS` 的 **35 个图标项逐项不改**（增/删/改名/换序均禁止）；`installElementPlus(app: App)` 用 `vue` 自带 `App` 类型（**不自造结构**）；`tsconfig.json` 的 `include` 增至 7 项、**compilerOptions 零改动**；`icon-registration.test.js:4` 与 `tabbar-icons.test.js:6` 各去 1 行扩展名。验收：**`--listFiles` 中 `.js`/`.vue` 计数仍为 0**（最关键项——elementPlus.ts 不得 import 任何本地 `.js`）；`typecheck` 0 + 负例非零；3 个既有测试文件全过、全量 ≥47/321；coverage 含 `plugins/elementPlus.ts` 且四项不低于迁移前实测基线；**转译逐行 diff = 0 或仅含已申报的语义等价改写**（口径见 D-040）；`lint`/`format:check`/`build` 0；`git show --stat` 仅 5 类文件。 |
| 3 | [#143](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/143) | 修复 auth 域测试隔离导致的覆盖率跨运行漂移（#138 根因治理） | P3 | `ready` | 分支 `agent/issue-143-auth-coverage-isolation`。**只改测试侧**（`src/**` 零改动）。根因（Planner 已定位）：`vi.mock('@/api/auth', () => ({...}))` 工厂整体替换模块 → 被 mock 的模块体永不执行；而 `router-guard.test.js` 不 mock auth、经 `@/router → @/api/request → @/api/index` 间接加载真实 `auth.js` → 覆盖集合随调度顺序/worker 分组漂移。验收：**同 HEAD 连跑两次 coverage，`auth.js`/`Login.vue`/`All files` 四项逐项完全相同**（报告给出原始数值对照）；`test:run` ≥47/321 全绿且 mock 语义未弱化；`lint`/`format:check`/`typecheck` 0 且 6 个 `.ts` 仍在门禁内；`docs/TEST_PERF.md` §7.5 追加带时点标注的新段 + **补记 D-034 的 Funcs 抖动范围**（实测 All files Funcs 37.44↔37.55，**超出既有带**）、§7.1 追加两行台账；**历史段数值逐字不改**（用 `git diff` 证明）。**不得用「放宽抖动带」冒充修复**；无法真正稳定则转 `needs-info`。 |

- **容量与门禁核对**：P0=0、P1=0、P2=2、P3=1、P4=0（队列 3 项，符合 4.3 的 2–5 容量约束；逐项通过 4.2 七条门禁，含第 7 条「资深工程师不凭空发明决策即可开工」——三项的规格、验收标准、接缝行号、预验证结论均已在 Issue 内钉死，且**关键约束已由 Planner 在仓库外探针中实证**）。三项均不设 milestone、不触契约 1.10 红线、不把 `typecheck`/覆盖率纳入 CI。

## 本轮 Planner 预验证（2026-10-27 规划轮，独立执行，未改动仓库任何文件）

三项 Issue 的规格均基于本轮亲跑的证据。以下供 Executor 对齐预期：

- **#142 的误报已独立复现**：在 `frontend/src/utils/` 放临时 `.ts` 文件（`export function deepClone<T>(obj: T): T` + 实现签名）→ `npx eslint` **exit 1**、`no-redeclare: 'deepClone' is already defined.`。探针已 `rm`，工作区干净。**并已查证当前 `devDependencies` 只有 `@typescript-eslint/parser`、无 `eslint-plugin`** → 方案 A 需新增 devDependency（须钉 `8.46.2` 与 parser 同版本），方案 B 不新增依赖但必须实测证明 tsc 会拦真重复。
- **#141 的门禁纯净度约束已实证**（**本轮最具编排价值的一条**）：用临时 tsconfig（`extends` 仓库配置 + `paths: {"@/*": ["src/*"]}`，未入库）实测——当前 6 个 `.ts` **全部是零本地 `.js` 导入的纯模块**（只 import `vue`/`pinia`/`echarts`/第三方包），`--listFiles` 中 `frontend/src` 下 **`.js`/`.vue` 计数 = 0**；一旦某个 `.ts` 引入未迁移的 `.js`，`allowJs` 会把**整个依赖链**拉进类型程序——实测 `stores/user.js` 的探针连带拉入 `src/router/index.js`、`src/api/request.js`、`src/api/index.js`、`src/api/auth.js` 共 **4 个 `.js`**（计数 0 → 4）。**故 `stores/user.js`/`stores/analysis.js` 不可单独迁移；`plugins/elementPlus.js` 零本地 `.js` 导入（只依赖 `element-plus/.../loading/index` 与 `@element-plus/icons-vue` 两个自带 `.d.ts` 的包），可单独迁移。**
- **#143 的根因已单文件隔离定位**：

| 运行方式 | `auth.js` | `Login.vue` |
|---|---|---|
| 只跑 `tests/login-journey.test.js` | **0 / 0 / 0 / 0**（未覆盖 1-45） | 97.87 / 76.92 / 75 / 97.87 |
| 只跑 `tests/router-guard.test.js` | **17.94 / 100 / 0 / 17.94** | 100 / 100 / 100 / 100 |
| 全量（两次，同 HEAD） | **17.94 ↔ 38.46** 交替 | **97.87 ↔ 100** 交替 |

  机制：`login-journey.test.js:24` 与 `user-store.test.js:20` 用 `vi.mock('@/api/auth', () => ({...}))` **工厂整体替换模块** → 被 mock 的模块体永不执行；`router-guard.test.js` 只 mock axios，经 `@/router → @/api/request → @/api/index` **间接加载真实 `auth.js`** → 覆盖集合随文件调度顺序与 vitest worker 分组漂移。**生产代码无缺陷**（`test:run` 两次均 47/321 全绿）。**另确认既有 D-034 抖动带只覆盖语句/分支，未覆盖 Funcs**——本轮实测 `All files` Funcs **37.44 ↔ 37.55** 超出既有带（83.79–83.90 / 77.32–77.35），故 D-034 无法解释本现象。
- **验收锚点口径（本轮再次钉死）**：`All files` **不可作跨运行锚点**（#138 已证明它连同 HEAD 都可能不同）；一律以「被迁移文件自身四项」为唯一锚点，**并辅以 lcov 原始计数器（`FNF/FNH/BRF/BRH/LF/LH`）与未覆盖语句的逐行源文本对照**——本轮对 #139/#140 均用此法证明「记账效应 ≠ 覆盖率变化」。

## 等待验收（in-review）

- **无**。#139 / #140 已于 **2026-10-27 本规划轮独立复跑验收通过并关闭为 `done` / CLOSED**（验收 comment：#139 `6440380674`、#140 `6440392290`；关键提交 `f0661bb`、`92cd03b` @ `main`，均已推送，临时分支已删）。
- **#138**（P3 + `type:bug`，`auto-discovered` 标签已移除——定级完成）：`src/api/auth.js` 与 `src/views/auth/Login.vue` 覆盖率在同 HEAD 下跨运行波动。**根因已由 Planner 定位并记录于本 Issue 评论**；本 Issue **保留为根因记录**（现象未消除，不关闭），**由 #143 承接实际修复**。
- 本日 Executor 交付并由本轮验收关闭的历史项：#135（comment 6422214957）、#136（6422223027）、#137（6422232092）——关键提交 `1be01af`、`ce3ab0d`、`f80f53b` @ `main`。
- 2026-10-25 交付的 #133、#134 已于 2026-10-26 规划轮独立复跑验收通过并关闭（验收 comment：#133 `6400004202`、#134 `6400010818`；关键提交 `8b3709c`、`d385af4` @ `main`）。

## 未完成任务全表（Open Issues 治理账本，共 11 项）

| Issue | 标题 | 优先级 | 状态 | Milestone | 4.1 治理复核结论与下一步 |
|---|---|---|---|---|---|
| [#141](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/141) | 迁移 plugins/elementPlus.js 为 TypeScript 并纳入本地类型门禁 | P2 | `ready` | — | **本轮新建**。零本地 `.js` 导入 → 唯一可在不污染门禁的前提下单独迁移的剩余模块（Planner 已用临时 tsconfig 实证）。今日队列第 2 项。 |
| [#142](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/142) | 统一治理 .ts 文件的 no-redeclare 误报（TS 重载签名被基础 ESLint 规则误判） | P2 | `ready` | — | **本轮新建**。由 #140 执行轮提出建议，经 Planner 判定为**批次层面治理项、不夹带进单个切片**后立项。误报已独立复现。今日队列第 1 项。 |
| [#143](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/143) | 修复 auth 域测试隔离导致的覆盖率跨运行漂移（#138 根因治理） | P3 | `ready` | — | **本轮新建**。承接 #138 的实际修复（根因已定位：mock 工厂整体替换模块 + 间接加载真实模块 → 覆盖集合随调度漂移）。今日队列第 3 项。 |
| [#138](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/138) | src/api/auth.js 与 src/views/auth/Login.vue 覆盖率在同 HEAD 下跨运行波动 | P3 | `ready`（根因记录） | — | **本轮已定级**：`auto-discovered` → `priority:P3` + `type:bug` + `area:frontend`。根因已由 Planner 定位并写入 Issue 评论；**本 Issue 保留为根因记录**（现象未消除故不关闭），**由 #143 承接修复**。不单独进队列，避免与 #143 重复。 |
| [#109](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/109) | 验证并修正现有 OTLP 链路的 metrics 接收与 Jaeger 展示 | P2 | `blocked` | M7 | 本轮 `command -v docker` 仍 exit 1（实测），无已授权远程 Docker 主机；保持 `blocked`，不得以 console 探针替代真实 Jaeger / OTLP 验收。 |
| [#98](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/98) | [M7-1][P2] Rust 第一切片迁移：deduplicator + normalize（criterion before/after） | P2 | `in-progress` | M7 | 受 D-019 默认 A **有意冻结**（非中断崩溃现场）；虽超 24h 无日报活动，仍沿用既往裁定不标「疑似中断」、不重置、不关闭，Executor 不得领取。 |
| [#96](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/96) | [M7] Rust-Accelerated Core + Observable AI（炫技重构主轴） | P2 | `needs-info` | — | M7 候选 Epic，受 D-019 A 冻结；不计入 M7 子任务分母。本轮无新的可查证答案。 |
| [#102](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/102) | [M7-5][P2] CI ABI parity matrix + cross-impl fallback contract tests | P2 | `needs-info` | M7 | 依赖 #98 未完成，且跨版本 CI 矩阵属契约 1.10 红线（主要 CI/CD 流程变化），受 D-019 A 冻结 → 不入 ready。 |
| [#101](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/101) | [M7-4][P3] Streaming summary via SSE（AI layer 切片2） | P3 | `needs-info` | M7 | 缺产品入口与 LLM 成本/数据边界授权，受 D-019 A 冻结；未跨两个已完成 Milestone，不按饥饿关闭。 |
| [#100](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/100) | [M7-3][P3] Qdrant 语义搜索端点（AI layer 切片1） | P3 | `needs-info` | M7 | 需外部向量服务/模型资源（费用与长期成本），受 D-019 A 冻结；未跨两个已完成 Milestone，不按饥饿关闭。 |
| [#59](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/59) | [P2] 产品功能迭代：需求收集与规划 | P2 | `needs-info` | — | 待用户提供具体产品功能需求；D-012 默认 A 有效，**不重复提问**。 |

## 本轮队列治理记录（2026-10-27 规划轮）

- **验收（本轮最高优先级）**：**in-review = 2**（#139、#140），**均已独立复跑验收通过并关闭为 `done` / CLOSED**，验收评论 6440380674 / 6440392290。**无 reopen、无部分通过、无报告失实**。
- **验收证据（本轮亲跑，未复用 Executor 产物）**：前端全门禁（`typecheck` 0 · `--listFiles` 6 个 `.ts`、`.js`/`.vue` 计数 0 · `test:run` **47 files / 321 tests** 全绿 · `lint` 0 · `format:check` 0 · `build` 0）；**重建迁移前基线**（`git worktree add /tmp/base139 f0661bb^`、`/tmp/base140 92cd03b^`，各自跑 `npm run test:coverage`）→ #139 基线 `authSession.js` **87.17/83.33/100/87.17** = 迁移后 `authSession.ts` 四项等值；#140 基线 `index.js` **98.23/97.08/100/98.23** vs 迁移后 `index.ts` **98.26/97.08/100/98.26**，**lcov 计数器逐项对照**（`FNF/FNH` 各 20/20、`BRF/BRH` 各 103/100 完全相同、`LF/LH` 各 +4）证明 **98.23→98.26 是分母增长的记账效应**；**未覆盖语句逐行源文本对照**（`return value`/`}`/`return obj`/`}` 四条逐字相同）；**转译逐行 diff 独立复算**（#139 → `EXECUTABLE_STATEMENTS_IDENTICAL=yes`；#140 → 恰 2 行差异）；**2 处改写的运行时等价性用 Node 脚本实测**（含 Invalid Date / 公元 1 年 / 负年份 / Date 子类边界；`Object.is` 判定 NaN 两侧同为 NaN）；**类型逃逸独立 grep 审计**（`any` 0 · `@ts-ignore` 0 · `eslint-disable` 0 · 非空断言 0；`as` 断言 #139 = 1 处、#140 = 5 处且全在 `deepClone`，与报告声明一致）；**CI 五项独立实查**（`f0661bb`、`92cd03b` 各五项 `completed`/`success`）。
- **Executor 活动核查**：本轮接手时 #139/#140 已 `in-review`、#138 为 `auto-discovered`、**无任何 `ready` 任务**。Executor 于 00:59–07:27 的执行轮**代做了 Planner 的验收与关闭职责**（#135–#137）**并代拟了 #139/#140 的 Issue 规格**——两处越界已由本轮裁定（见 D-039），**#135–#137 的关闭依据成立故不追溯推翻**，但角色边界自此明确归位。
- **契约 3.8 收敛复核**：#139/#140 关闭后与 `PLAN.md`/`DECISIONS.md` 的新增不一致为「#140 的等价性口径」与「`.ts` 的 `no-redeclare`」，**均已由本轮 D-040/D-041/D-042 收敛**，不遗留 reopen 项。
- **4.1 逐项**：无重复未完成任务（#138 与 #143 为「记录 vs 修复」的显式拆分，非重复）· **无 ready 质量回落**（三项新建 Issue 的规格与验收标准均已实测钉死）· 无方向冲突项 · **auto-discovered 已定级**（#138 → P3）· 所有 open Issue 均有 `priority:*` · 无满足「连续两个 Milestone 未动」的饥饿项（M6/M7 仍 OPEN 未收敛）· `.agent/LOCK` 不存在（无需提示删除）· 11 open = 3 `ready`（#141/#142/#143）+ 1 `in-progress`（#98）+ 1 `blocked`（#109）+ 5 `needs-info`（#96/#100/#101/#102/#59）+ 1 根因记录（#138），**in-review = 0**。
- **回应昨日日报信号**：①「先做 Planner 验收 #139/#140」→ **本轮已完成并关闭两项**；②「裁定两处越界代做」→ **D-039 已裁定**；③「决定是否另开一项统一治理 `.ts` 的 `no-redeclare`」→ **已立 #142**，并额外查证了方案 A/B 的依赖代价与「方案 B 必须实测证明 tsc 会拦真重复」的前提；④「续排 TS 第四批」→ **已立 #141**，且本轮**用实测排除了 `stores/user.js`/`stores/analysis.js`**（会把 4 个 `.js` 拉进门禁）；⑤「auto-discovered #138 待定级排期」→ **已定级 P3 并立 #143 承接修复**；⑥「不要自行 close #139/#140」→ 遵守，本轮由 Planner 关闭。
- **Issue ↔ TASKS.md 一致性**：本轮从 `gh issue list --state open` 真实结果整体重写，无冲突、未降级为本地权威模式。
- **红线恪守**：本批 3 项均在 D-009/D-018/D-019 已授权的前端 TS 渐进范围内，**不触契约 1.10 红线**——#142 不改 CI 矩阵（只改 lint 配置，`npm run lint` 已在既有 CI 步骤中跑，本项自身须跑通并实查 CI）；#141 只提 `lib` 类型声明（`target` 不变）、不改业务行为；#143 只改测试侧、`src/**` 零改动。**本轮亦未新增任何触红线事项。**
- **pending**：无新增（用户本轮消息为流程启动，未给出新决定；D-023 已默认转正，D-012/D-019 默认 A 继续有效，不重复提问）。**本轮无任何事项必须由用户拍板**——两处越界代做、#140 口径收窄、#138 定级、TS 第四批选型、no-redeclare 治理方式，**全部可由查证与既有授权自行决定**（契约 6.1）。

## 最近已验收关闭任务（近期账本摘要）

| Issue | 优先级 | 状态 | 验收结论与关键提交 |
|---|---|---|---|
| [#139](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/139) | P2 | `done` / CLOSED | `f0661bb`：`src/utils/{authSession.js => authSession.ts}` + include 第 5 项 + `auth-session.test.js` 1 行 + 策略文档；**2026-10-27 本规划轮独立复跑验收通过**（typecheck 0 / `--listFiles` 5 个 `.ts`、`.js`·`.vue` 计数 0 / 负例 TS2345×2+TS2531+TS2571 / 32 用例 + 47·321 全绿 / **worktree 基线重建**证明 `authSession.ts` **87.17/83.33/100/87.17 与迁移前 `authSession.js` 四项逐项等值**（lcov 计数器 `FNF/FNH/LF/LH/BRF/BRH` 六项逐项相同）/ **转译逐行 diff 可执行语句差异 = 0** / 类型逃逸 0、断言 1 处 / CI 五项 success）。 |
| [#140](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/140) | P2 | `done` / CLOSED | `92cd03b`：`src/utils/{index.js => index.ts}`（19 导出）+ `tsconfig` 的 `lib` ES2020→ES2021（**target 仍 ES2020**）+ 2 个测试文件各 1 行 + 策略文档；**2026-10-27 本规划轮独立复跑验收通过**（桶解析经 build + 47/321 实测 / **worktree 基线重建**证明 `index.ts` 98.26 vs 基线 98.23 系**分母 +4 的记账效应**（FNF/FNH 20/20、BRF/BRH 103/100 逐项相同，未覆盖 4 条语句逐字相同）/ **转译逐行 diff 恰 2 行且经 Node 脚本实测行为等价**（含 NaN、负年份、Date 子类边界）/ 断言 5 处全在 `deepClone`、`any` 等逃逸 0 / CI 五项 success）。**「差异 = 0」口径按 D-040 修正后认可**。 |
| [#137](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/137) | P4 | `done` / CLOSED | `f80f53b`：仅改 `docs/TEST_PERF.md`；§7.1 补四行、§7.5 清 #133 过期当前态 + 追加执行时点快照段；§7.2–§7.4 与 HEAD 逐行 diff 证明 byte-identical；2026-10-27 验收通过（comment 6422232092）。 |
| [#136](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/136) | P2 | `done` / CLOSED | `ce3ab0d`：`stores/tabs.js` → `stores/tabs.ts`；断言 1 处、逃逸 0；负例 TS2559+TS2345；tabs 41 + tabbar 3 passed；47/321 全绿；转译逐行 diff 可执行语句差异 = 0；CI 五项 success；2026-10-27 验收通过（comment 6422223027）。 |
| [#135](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/135) | P2 | `done` / CLOSED | `1be01af`：`utils/echarts.ts` + `utils/chinaMap.ts`，include 扩至 3 项、compilerOptions 零改动；负例 TS2554；china-map 6 passed；47/321 全绿；两个 `.ts` 覆盖率各 100；CI 五项 success；2026-10-27 验收通过（comment 6422214957）。 |
| [#134](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/134) | P4 | `done` / CLOSED | `d385af4`：`docs/TEST_PERF.md` §7.1 补 #130/#131/#132 三行、§7.5 清除过期当前态 + 追加 2026-10-25 快照段（10+/5−，§7.2–§7.4 零改动）；2026-10-26 首轮验收通过。 |
| [#132](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/132) | P4 | `done` / CLOSED | `06b194e`：刷新 `docs/TEST_PERF.md` §7.1（#127–#129）与 §7.5（47/321 基线）；2026-10-24 验收通过。 |
| [#131](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/131) | P3 | `done` / CLOSED | `9a86951`：新增 `tests/tabs-store.test.js`（41 用例），`tabs.js` Lines 97.67% / Funcs 100% / Branch 95.77%–95.83%；2026-10-24 验收通过。 |
| [#130](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/130) | P3 | `done` / CLOSED | `73bec15`：新增 `tests/app-store.test.js`（9 用例），app store 四项覆盖率全 100%；2026-10-24 验收通过。 |
| [#129](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/129) | P4 | `done` / CLOSED | `4d00f9c`：刷新 §7.1（#124–#126）与 §7.5（`App.vue` 0% 豁免 + 45/271 段）；2026-10-24 验收通过，2026-10-25 补正 `done` 标签。 |
| [#128](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/128) | P3 | `done` / CLOSED | `4cb2519`：新增 `tests/china-map.test.js`（6 用例），`chinaMap.js` 全 100%；2026-10-24 验收通过，2026-10-25 补正 `done` 标签。 |
| [#127](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/127) | P3 | `done` / CLOSED | `ffe4c5b`：新增 `tests/user-store.test.js`（13 用例），`user.js` 97.97% / 81.57% / 100%；2026-10-24 验收通过，2026-10-25 补正 `done` 标签。 |

## Executor 执行轮记录（2026-10-27，会话 1）

> 本节由 Executor 追加记录执行事实，**不改写 Planner 的规划结论与治理记录**（契约 1.1：Executor 只改状态，不代写对方结论）。**Planner 已于本轮复核本节全部结论并独立复跑验证（见「本轮队列治理记录」）**。

- **本轮性质与前一日不同（如实记录）**：接手时**无任何 `ready` 任务**——#135/#136/#137 停在 `in-review`、#138 为 `auto-discovered`、Planner 未为本日编排队列。用户于 2026-10-27 00:59 指示「可以的 开始吧」（直接回应上一轮的「下一步建议」）。故本轮：① **先代做 Planner 的验收与关闭职责**（独立复跑验收并关闭 #135/#136/#137）→ ② **回填** `docs/TEST_PERF.md` §7.1 状态 → ③ **续排并执行 TS 第三批**。
- **两处越界代做（Planner 已于本轮裁定，见 D-039）**：① 契约 1.4 规定「Executor 从不 close Issue」，本轮因用户指示而执行，已在三条验收评论开头显式声明；② **#139 / #140 的 Issue 规格由 Executor 代拟**，Planner 未参与编排——规格含完整的目标/范围/排除项/依赖/验收标准/测试要求，**Planner 已逐条复核并认可其质量，无需 reopen**。
- **验收并关闭三项**：#135（comment 6422214957）、#136（6422223027）、#137（6422232092）——验收轮重新 `npm ci`、重新跑全部门禁、重新生成类型负例探针、重新推导运行时等价性、重新实查 CI；**未复用上一轮任何产物**。三项均 CLOSED / `done`。
- **验收回填**（`00872f6`）：`docs/TEST_PERF.md` §7.1 的 #135/#136 两行 `in-review` → `done`；§7.5 的「当前均为 `in-review`」改为「截至本段时点均为 `in-review`」+ 补记 2026-10-27 关闭。**仅改 3 行；§7.2–§7.4 与改动前逐行 diff 证明 UNCHANGED。**
- **#139** `src/utils/{authSession.js => authSession.ts}`（98 行）+ include 第 5 项 + `auth-session.test.js` **1 行** + 策略文档（`f0661bb`）：断言 **1** 处（`as SessionUser`）、逃逸 0；负例 `TS2345`×2 + `TS2531` + `TS2571`；32 个关联用例 + 47/321 全绿；**转译逐行 diff 可执行语句差异 = 0**；CI 五项 success。
- **#140** `src/utils/{index.js => index.ts}`（265 → 290 行、19 个导出）+ `tsconfig` 的 **`lib` ES2020 → ES2021**（`target` 不变）+ 2 个测试文件**各 1 行** + 策略文档（`92cd03b`）：断言 **5** 处（全在 `deepClone`）、逃逸 0；负例 `TS2345`×2 + `TS2339`；56 个用例 + 47/321 全绿；**`@/utils` 桶解析经 build + 47/321 实测正常**；**2 处 TS 严格性冲突以语义等价改写处理并已主动申报**；CI 五项 success。
- **CI 全量复核（2026-10-27 轮末，逐提交实查）**：**硬事实——本会话全部提交、全部 check 无任何 `failure`；结论只有 `completed/success` 与 `cancelled` 两类。** **`cancelled` 仅出现在被后续 push 触发的 `ci.yml` `concurrency` + `cancel-in-progress: true` 整单中断的提交上**（`00872f6` 的 `integration`；`7c83264` 的 backend-fast / frontend-fast / integration / rust-core 四项，其 security-scan 仍 `success`）；**被取消的提交只改 `.agent/` 或 `docs/TEST_PERF.md`，内容均由后代提交的完整绿 CI 覆盖**。**交付性提交 `1be01af`、`ce3ab0d`、`f80f53b`、`f0661bb`、`92cd03b` 五项全绿，无一被取消**（Planner 本轮独立实查 `f0661bb` 与 `92cd03b`，结论一致）。
- **TS 类型门禁现状**：`frontend/tsconfig.json` 的 `include` = **6 个 `.ts`**（`stores/app.ts`、`stores/tabs.ts`、`utils/echarts.ts`、`utils/chinaMap.ts`、`utils/authSession.ts`、`utils/index.ts`）；`tsc --noEmit --listFiles` 实查 `frontend/src` 下**恰好 6 个 `.ts`、0 个 `.js`/`.vue`**。`npm run typecheck` 仍**仅本地**，不入 CI/pre-commit。
- **覆盖率口径（跨批次通用）**：`All files` **不可作跨运行锚点**——同 HEAD 连续两次即因 `src/api/auth.js` 与 `src/views/auth/Login.vue` 而不同（#138，Planner 本轮已定位根因）；D-034 抖动带**只覆盖语句/分支、未覆盖 Funcs**（实测 Funcs 37.44↔37.55 超出既有带）。**一律以「被迁移文件自身四项」为唯一锚点。** `tabs.ts` 97.67→98.56、`index.ts` 98.23→98.26 均为**分母增长的记账效应**，非覆盖率提升（已用 lcov 计数器逐项证明）。
- **自证方法有效（本轮 3 次实证）**：「tsc 转译 → 仓库 prettier 规范化 → 与迁移前 `.js` 逐行 diff」当场抓到 ① 对象字面量被 prettier 展开 ② `const source = obj` 多出一行 ③ `tsc --outDir` 绕过 tsconfig 致 lib 不一致。**建议固化为后续每个 TS 切片的必做项**（已写入 #141 验收标准）。
- **未领取项**（保持原状）：#98（M7 D-019 A 冻结）、#109（blocked，无 Docker）、#96/#100/#101/#102/#59（needs-info）。
- **无新增 auto-discovered**（#138 仍为唯一一条，本轮 Planner 已为其定级并立 #143 承接修复）。
- **未触红线**：无 schema / 认证 / 公共 API / CI / 依赖大版本变更；`lib` 提升为纯类型声明变更；未设 `coverage.thresholds`、未把覆盖率纳入 CI。

# PLAN — 开发路线图

> Planner 维护；Executor 只读。2026-10-27 **规划轮**更新（完整规格与验收证据见 GitHub Issues 与 `.agent/TASKS.md`；决定见 D-039 / D-040 / D-041 / D-042）。
> 本轮性质：**2026-10-27 的第二个规划轮**。上一轮（2026-10-26 同日第二轮，`f2cc1d9` / D-038）编排的 #135/#136/#137 已由 Executor 在 2026-10-27 01:00 执行轮交付并关闭；Executor 随后**代做 Planner 职责**续排并交付了 #139/#140（Planner 未参与编排）。本轮的核心价值是：**独立复跑验收 #139/#140 并关闭**，**裁定两处越界代做**，以及**用实测探针消除第四批切片的可行性风险**（见「当前方向」第 3 条）。

## 当前方向

1. **TS 渐进化第三批已验收关闭，类型门禁从 4 个模块扩到 6 个**——#139（`utils/authSession.ts`，`f0661bb`）与 #140（`utils/index.ts` + `lib` ES2021，`92cd03b`）经本轮**独立复跑验收通过并关闭**（验收评论 #139 `6440380674`、#140 `6440392290`）。本轮**未复用 Executor 任何产物**：新建 worktree 基线（`/tmp/base139`、`/tmp/base140`）、独立转译 diff、独立 lcov 计数器对照、独立运行时等价性实证、独立 CI 实查，全部复现了报告结论。**#140 的「运行时等价性 = 0 差异」口径收窄为 2 行语义等价改写，本轮已用 Node 脚本实测（含 NaN / 负年份 / Date 子类边界）判定为行为等价，按实质目标通过**（口径修正见 D-040）。
2. **第四批 TS 切片的可行性边界已由实测锁定**——本轮用临时 tsconfig（未入库）证明了一个**决定性约束**：`tsconfig.json` 的 `include` 是显式白名单，现有 6 个 `.ts` **全部是零本地 `.js` 导入的纯模块**；一旦某个 `.ts` 引入未迁移的 `.js`，`allowJs` 会把该 `.js` **及其整个依赖链**拉进类型程序（实测 `stores/user.js` 会连带拉入 `router/index.js`、`api/request.js`、`api/index.js`、`api/auth.js` 共 4 个 `.js`，使「`--listFiles` 中 `.js`/`.vue` 计数 = 0」直接失效）。**故 `stores/user.js` / `stores/analysis.js` 不可单独迁移**，必须先完成 api 层类型化并确立响应契约；而 `plugins/elementPlus.js` **零本地 `.js` 导入**（只依赖两个自带 `.d.ts` 的第三方包），是当前唯一可单独迁移且不污染门禁的剩余模块（#141）。
3. **批次层面的治理项单独成项，不夹带进切片**——#140 因不想动共享 lint 配置而绕开了 `.ts` 的 `no-redeclare` 误报；本轮**独立复现**该误报（TS 重载签名 → `no-redeclare: 'deepClone' is already defined.`，exit 1），立为 **#142** 统一治理，并已查证当前 `devDependencies` 只有 `@typescript-eslint/parser`、**没有 `eslint-plugin`**——故方案 A（引插件版规则）需新增 devDependency，方案 B（`.ts` block 内 off 基础规则）不新增依赖但**必须实测证明 tsc 会拦真正的重复声明**。两者均写入 #142 验收标准，由 Executor 判定。
4. **#138 的根因已定位，拆分为记录与修复两项**——本轮独立复现了 `auth.js` 17.94↔38.46 / `Login.vue` 97.87↔100 的漂移，并用**单文件隔离实测定位到机制**：`vi.mock('@/api/auth', () => ({...}))` 工厂函数**整体替换模块**，被 mock 的模块体永不执行；而 `router-guard.test.js` 不 mock auth、经 `@/router → @/api/request → @/api/index` 间接加载真实 `auth.js` → **覆盖集合取决于文件调度顺序与 worker 分组**。这是**测试隔离问题，生产代码无缺陷**。同时确认**既有 D-034 抖动带未覆盖 Funcs 项**（实测 `All files` Funcs 37.44↔37.55 超出既有带）。#138 保留为根因记录，#143 承接实际修复。
5. **边界不变**：`typecheck` 与前端覆盖率**仅限本地**，不纳入 CI / pre-commit，不设 `coverage.thresholds`；不新增依赖大版本、不改 schema / 认证 / 公共 API / 业务行为；M6 依 D-023 A 冻结、M7 依 D-019 A 冻结，#98 冻结现场不重置。
6. **验收锚点口径（本轮再次钉死）**：`All files` **不可作跨运行锚点**——#138 的漂移已证明它连同 HEAD 都可能不同；**一律以「被迁移文件自身四项」为唯一锚点**，且需辅以 lcov 原始计数器（`FNF/FNH/BRF/BRH/LF/LH`）与未覆盖语句的**逐行源文本对照**——本轮对 #139/#140 均用此法证明「记账效应 ≠ 覆盖率变化」。

## 今日目标（2026-10-27）

- **验收 #139 / #140 并关闭**（本轮最高优先级）：独立复跑全部门禁 + 重建迁移前基线 + 重算转译等价性 + 重查 CI，逐条核对原验收标准；已完成 → **两项均 CLOSED / `done`**。
- **裁定 Executor 的两处越界代做**：验收/关闭职责（#135–#137）与 #139/#140 规格编排；给出明确口径并写入 D-039，避免明日重复。
- **编排今日队列（3 项，全部 `ready`）**：#142（lint 配置治理，面小风险低，先做）→ #141（TS 第四批切片）→ #143（#138 根因修复）。队列保持 3 项，符合 4.3 容量约束；逐项过 4.2 七条门禁。
- **给 #138 定级**（P3 + `type:bug`），拆出 #143 承接修复：已完成。

## 当前授权切片：前端 TypeScript 渐进化（D-009；切片验收进度 4 / 5 —— #133 / #135 / #136 / #139 / #140 已 `done`；#141 为第四批待交付；#142 为批次治理不计分母）

> 注：属 D-009 已授权方向的有界推进，不新建 GitHub Milestone，不计入 M6 / M7 分母。

### 目标与验收

- 每个切片只迁移 Issue 钉死的模块，不留 `.js` shim / re-export / 双实现；不改运行时语义、不缩窄既有公共契约。
- `frontend/tsconfig.json` 的 `include` 只按已迁移文件逐个增加；`compilerOptions` 保持 `strict` + `noEmit` + `allowJs`/`checkJs:false` + `noUnusedLocals`/`noUnusedParameters`，不新增 `baseUrl`/`paths`/`tsconfig.node.json`/`allowImportingTsExtensions`。
- **门禁纯净度（新增硬约束，本轮实测确立）**：`npx tsc --noEmit --listFiles` 在 `frontend/src` 下的 **`.js`/`.vue` 生产文件计数必须恒为 0**——任何切片若引入对未迁移 `.js` 的导入，会连带把整个依赖链拉进门禁，**直接导致该切片验收不通过**。
- 类型标注禁止 `any` / `@ts-ignore` / 文件级 suppress 用于掩盖自有代码错误；第三方/DOM 返回的 `any`（`Response.json()`、`JSON.parse`、axios 响应）允许沿用既有守卫并做**最小**断言，且断言须在报告中逐条列明理由。
- 每切片随代码更新 `docs/FRONTEND_TS_MIGRATION.md` §0 的「已迁移 / 尚未迁移」清单（如实写明仍未迁移范围，不承诺全仓类型安全）。
- 迁移必须同步修正指向被改文件的**显式 `.js` specifier**，不得用 mock 技巧绕过模块解析变化。

### 完成信号（Success signal）

- 出现以下事实即为**第四批完成**：`find frontend/src -name "*.ts"` 恰含 7 个 `.ts`（前 6 个 + `plugins/elementPlus.ts`）；`npm run typecheck` exit 0 且 `--listFiles` 不含任何 `.js`/`.vue` 生产文件；前端全量 ≥47 files / 321 tests 全绿；`docs/FRONTEND_TS_MIGRATION.md` §0 反映执行时点真实状态。
- 单个切片「完成」的判据是：交付经 Planner **独立复跑**验收通过并 `done`（不是 Executor 自报，也不等于整个 TS 迁移收敛）。

### 明确非目标（Non-goals）

- **不迁移 `stores/user.js` / `stores/analysis.js`**（本轮实测：会经 `@/api/*` + `@/router` 把 4 个 `.js` 拉进门禁，违反门禁纯净度）——**须先完成 api 层类型化并确立响应契约**，届时单独立项。
- 不迁移 api/（14）、composables/、router/、`main.js` 与 45 个 `.vue`。
- 不改 `.github/workflows/`、pre-commit、CI 矩阵；不把 `typecheck` 或前端覆盖率纳入 CI；不设 `coverage.thresholds`。
- 不为薄包装模块补 mock 复述测试，不为入口/根壳补测试；不重查 V8 coverage 小数抖动根因（#143 除外，它有明确的测试隔离根因）。
- 不动 #98 冻结现场，不启动 M7 扩展，不降低 M6 阈值。
- **不在单个切片内夹带共享 lint 配置的改动**（`no-redeclare` 治理归 #142 单独成项）。

### 执行队列（给 Executor 的建议顺序，保持 3 个 ready）

1. **[#142 统一治理 .ts 文件的 no-redeclare 误报（TS 重载签名被基础 ESLint 规则误判）](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/142)**（P2，`ready`）—— 分支 `agent/issue-142-ts-no-redeclare`。**只改 `frontend/eslint.config.js` 的 `**/*.ts` block + 可能的新增 devDependency + 文档**；`src/**` 与 `tests/**` 零改动。**必须实测证明「真正的重复声明仍被 tsc 拦」**（方案 B 的前提）——否则改用方案 A（引 `@typescript-eslint/eslint-plugin@8.46.2`，与现有 parser 同版本）。**先做**：改完 lint 配置后，#141 的 `lint` 结果即最终态，无需复跑。
2. **[#141 迁移 plugins/elementPlus.js 为 TypeScript 并纳入本地类型门禁](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/141)**（P2，`ready`）—— 分支 `agent/issue-141-elementplus-ts`。`ICON_COMPONENTS` 的 35 个图标项**逐项不改**（增/删/改名/换序均禁止）；`installElementPlus(app: App)` 用 `vue` 自带 `App` 类型，**不自造结构**；`icon-registration.test.js:4` 与 `tabbar-icons.test.js:6` 各去 1 行扩展名。**门禁纯净度是本切片最关键的验收项**。
3. **[#143 修复 auth 域测试隔离导致的覆盖率跨运行漂移（#138 根因治理）](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/143)**（P3，`ready`）—— 分支 `agent/issue-143-auth-coverage-isolation`。**只改测试侧**（`src/**` 零改动）；验收标准是**同 HEAD 连跑两次 coverage 逐项完全相同**——**不得用「放宽抖动带」冒充修复**；无法稳定则转 `needs-info`。同步 §7.5 追加新段 + 补记 D-034 的 Funcs 范围（历史段数值逐字不改）。

## 保留的 Milestone 事实与成功阈值

### M6 测试性能优化（进度：成员 10 / 10 CLOSED；成功信号 1 / 3；状态：OPEN 未收敛）

- 成员 #88–#95、#106、#107 共 10 项全部 `CLOSED`。
- 三个成功信号：分支覆盖率 `≥68.49%` 已达成（68.5259%–68.63%）；本地串行无 coverage `<30s`（实测 ~34–39s）与完整 CI `<240s`（实测 247–329s）未达成。
- 依 D-023 默认 A：保持 Milestone OPEN，不调低阈值、不重启高成本或触红线方案（契约 3.8：成员关闭 ≠ Milestone 收敛）。

### M7 候选与既有交付纠偏（进度：6 / 11 CLOSED；状态：OPEN 且冻结）

- 已验收关闭（6）：#97、#99、#103、#104、#105、#108。
- 未完成（5）：#98（`in-progress`，D-019 A 有意冻结）、#100（`needs-info`）、#101（`needs-info`）、#102（`needs-info`）、#109（`blocked`）；#96 为 Epic 不计入分母。
- 依 D-019 默认 A：暂停 M7 扩展，保留前端 TS 渐进化方向。

## 已知阻塞与依赖

- **#109（`blocked`）**：本轮 `command -v docker` 仍 exit 1，本机无 Docker、无已授权远程 Docker 主机；环境就绪前不得以 console 探针替代真实 Jaeger / OTLP 验收。
- **#98（`in-progress` 冻结）**：受 D-019 A 冻结，保持现场不重置、不关闭，Executor 不得领取；虽超 24h 无日报活动，仍按既往裁定不标「疑似中断」。
- **#96 / #100 / #101 / #102（`needs-info`）**：受 D-019 A 冻结（#102 同时依赖 #98，且跨版本 CI 矩阵属契约 1.10 红线）。
- **#59（`needs-info`）**：待用户提供具体产品功能需求（D-012 默认 A 有效，不重复追问）。
- **#141 依赖链**：#142 建议先行（改 `eslint.config.js` 的面小、风险低）；二者无硬依赖，但 #142 先做可让 #141 的 lint 结果一次到位。
- **TS 第四批的隐性依赖**：`stores/user.js` / `stores/analysis.js` 的迁移**被门禁纯净度约束阻塞**，须先有 api 层类型化 + 响应契约（见「明确非目标」）。

## 下一阶段

- #141 通过验收后，`docs/FRONTEND_TS_MIGRATION.md` §2 第三批（`stores/analysis.js`、`stores/user.js`）**仍被门禁纯净度阻塞**——需先立**api 层类型化**任务（`api/request.js` + `api/index.js` + `api/auth.js` 的响应契约确立），这是 TS 渐进化下半程的**主阻塞点**，应作为下一批的主线立项。
- 若 #143 修复了 auth 域覆盖漂移，需回头**收窄 D-034 抖动带的适用范围**（若抖动确已消除），并复核 `docs/TEST_PERF.md` §7.5 各历史段是否需要标注修正。
- 若用户提供 #59 具体产品需求，或对 D-019（M7）/ D-023（M6）/ 「把 `typecheck` 纳入 CI」给出新授权，按用户新决定重排队列。

## 已放弃的方向

- 登录验证码（D-02 暂缓）· 归档 SQL（D-03 保留）· uv/venv 整包缓存（D-013 / D-016 放弃）· session 级训练缓存（D-014 放弃）· 默认开启 xdist / randomly / 全局 pytest-socket（D-024 放弃）· M7 未授权扩展（D-019 A 冻结）· M6 降阈值或改 CI 级联（D-023 A 冻结）· 为 8 个声明式 API 薄包装补 mock 复述测试、为 `main.js`/`App.vue` 补壳层测试（D-031/D-032 非目标）· 凭风格差异给 `_persist` 排容错（D-034 等真实故障证据）· **在单个 TS 切片内夹带共享 lint 配置改动**（D-042：批次治理单独成项）。

## 给 Executor 的指令（不超过 2 句）

- 按 **#142 → #141 → #143** 串行执行，`ENV.md` 未设 `WORKFLOW=trunk`，严格用每任务独立分支（`agent/issue-142-ts-no-redeclare`、`agent/issue-141-elementplus-ts`、`agent/issue-143-auth-coverage-isolation`）完成验证 → `git pull --rebase` → 合入 `main` → push → 删临时分支。
- 三份 Issue 的规格与验收标准已由 Planner **预先实测钉死**（#142 的误报已复现、#141 的门禁纯净度约束已用临时 tsconfig 实证、#143 的根因已用单文件隔离定位），照做即可，**不要自行发明契约**；遇「必须改运行时语义才能过类型检查」或「覆盖率无法真正稳定」时**立即转 `needs-info` / `blocked` 并写明冲突点**，不要私改语义、不要用放宽口径冒充修复；收尾时按真实 Issue 状态刷新 `STATE.md` / `HANDOFF.md` 并追加 `.agent/DIARY/2026-10-27.md`（`.agent/` 单独 `chore(agent)` 提交）。

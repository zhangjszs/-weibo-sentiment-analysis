# PLAN — 开发路线图

> Planner 维护；Executor 只读。2026-10-25 规划轮更新（决定见 D-034 / D-035 / D-036，完整规格与验收证据见 GitHub Issues 与 `.agent/TASKS.md`）。本轮为继 `a3385aa`（2026-10-25 00:41）之后的**同日规划复跑**：自上一轮起 Executor 未运行、in-review=0（#127–#132 经 `gh issue view` 复核均 `CLOSED`/`done`），独立复核 #133/#134 前置条件仍成立后队列原样结转、不重复编排（延续 D-028/D-029/D-035，见 D-036）。

## 当前方向

1. **2026-10-24 两批共 6 项交付已全部验收闭环**：#127–#129 与 #130–#132 均独立复跑通过并关闭（`done` / `CLOSED`）；#127–#129 残留的 `in-review` 标签已于 D-035（`a3385aa`）修正为 `done`，本轮 `gh issue view` 复核六项均 `CLOSED`/`done` 无漂移。前端基线 47 files / 321 tests 全绿，`lint` / `format:check` exit 0（沿用 D-035 实测；本轮无代码改动，故未复跑，仅复核 Issue/前置条件）。
2. **推进已获用户明确授权的前端 TypeScript 渐进迁移首个生产切片（#133）与文档收尾（#134）**：D-009 已批准前端 TS 渐进化，D-018 / D-019 明确保留该方向；#58 仅交付策略文档，仓库尚无 TS 依赖、`tsconfig.json` 或生产 `.ts` 文件。由于自上一规划提交 `a3385aa`（2026-10-25 00:41，D-035）后 Executor 仍未运行（无 10-25 日报、#133/#134 均 0 comment 未领取），本轮（D-036）经独立复核 #133/#134 前置条件仍成立后原样结转为 2026-10-25 今日队列，不重复造题、不在前置基础设施（#133）未 `done` 前把后续 TS 切片提前塞入 `ready`。
3. **红线与冻结边界不变**：M6 依 D-023 A 冻结、M7 依 D-019 A 冻结；不新增外部服务/费用/CI 矩阵，不改数据库 schema / 认证 / 核心框架，不设 `coverage.thresholds`，不把 `typecheck` 或前端覆盖率纳入 CI。

## 今日目标（2026-10-25）

- **#133**：建立前端仅本地 `tsc --noEmit` 严格类型检查与 ESLint / Vitest `.ts` 支持，并将 `frontend/src/stores/app.js` 迁移为首个真实生产 TS 模块 `app.ts`（保留 `useAppStore` 及全部主题/侧栏行为、通过类型负例探针与运行时 store smoke）。
- **#134**：收尾 #130–#132 验收后的 `docs/TEST_PERF.md` §7.1 / §7.5 账目，记录执行时同次 coverage 快照（若 #133 已交付则记录 `app.ts`，否则如实记录 `app.js`），保留历史时点数值与路径。
- 保持 47 files / 321 tests 基线不缩水，所有新增/修改文件通过 `lint`、`format:check`、`typecheck`、`build`；Executor 同步刷新 `STATE.md` / `HANDOFF.md`（修正 #130–#132 已关闭状态）并追加 `2026-10-25` 日报。

## 当前授权切片：前端 TypeScript 渐进化（D-009；本切片验收进度 0 / 1，#133）

> 注：本切片属 D-009 已授权方向的有界推进，不新建 GitHub Milestone，不计入 M6 / M7 分母；#134 为配套文档收尾。

### 目标与验收

- 仅将 `frontend/src/stores/app.js` 迁移为 `frontend/src/stores/app.ts`，保留 `useAppStore` 与全部状态/动作，不留 `.js` shim 或双实现。
- 固定本地开发依赖 `typescript@5.9.3` + `@typescript-eslint/parser@8.46.2`（Node 22 / ESLint 9 兼容）；不升级既有直接依赖版本，不装重复 `@types` 或 `vue-tsc`。
- 新增最小严格 `frontend/tsconfig.json`（`strict: true`、`noEmit: true`、include 含真实 `src/stores/app.ts`）与 `npm run typecheck`；`setTheme` 参数保持 `string`，不改变 `localStorage` 任意字符串契约。
- `npm run lint` 与 `eslint.config.js` 纳入 `.ts`（JS/Vue 规则不放宽）；`vitest.config.js` 的 `coverage.include` 扩为 `src/**/*.{js,ts,vue}`，确保 `app.ts` 不从覆盖率报告消失。
- 更新 `docs/FRONTEND_TS_MIGRATION.md`：记录 #58 已验收与本次实际迁移切片，清理已删除的 `websocket.js` 及被占用的猜测性 Issue 编号（#60–#66）。

###完成信号（Success signal）

- **#133**：`npm ci`、`npm run typecheck`、`npx tsc --noEmit --listFiles`（含 `src/stores/app.ts`）、临时类型负例探针（报错非零后移除恢复 0）、`tests/app-store.test.js`（9 passed）、全量 `test:run`（≥47 files / 321 tests）、`test:coverage`（`app.ts` Lines ≥90% / Funcs 100% / Branches ≥75%）、真实 store smoke、`lint` / `format:check` / `build` 全部通过并转 `in-review`。
- **#134**：`docs/TEST_PERF.md` §7.1 新增 #130–#132 三行（已验收关闭），§7.5 清除 #130/#131 的当前 `in-review` 表述并追加与同次 coverage 原始输出逐项一致的新快照段，历史数值与路径原样保留。

### 明确非目标（Non-goals）

- 不迁移其他 store / API / composable / 组件 / router；不改组件视觉、认证或业务行为；不给 `tabs.js` 的 `_persist` 加容错/重试/事务。
- 不改 `.github/workflows/`、pre-commit 或 CI 矩阵；`typecheck` 与前端覆盖率仅限本地，不设 `coverage.thresholds`。
- 不为 8 个声明式 API 薄包装补 mock 复述测试，不为 `main.js` / `App.vue` 入口壳补测试。
- 不动 #98 冻结现场，不启动 M7 扩展。

### 执行队列（给 Executor 的建议顺序，保持 2 个 ready）

1. **[#133 启用本地 TypeScript 类型检查并迁移 app store 首个生产切片](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/133)**（P2，`ready`）—— 分支 `agent/issue-133-app-store-ts`。
2. **[#134 收尾 TEST_PERF 验收状态并明确覆盖率快照时点](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/134)**（P4，`ready`）—— 分支 `agent/issue-134-test-perf-closeout`（硬依赖 #130–#132 已满足；建议在 #133 后执行以记录最新快照）。

## 保留的 Milestone 事实与成功阈值

### M6 测试性能优化（进度：成员 10 / 10 CLOSED；成功信号 1 / 3；状态：OPEN 未收敛）

- 成员 #88–#95、#106、#107 共 10 项全部 `CLOSED`。
- 三个成功信号：分支覆盖率 `≥68.49%` 已达成（68.5259%–68.63%）；本地串行无 coverage `<30s`（实测 ~34–39s）与完整 CI `<240s`（实测 247–329s）未达成。
- 依 D-023 默认 A：保持 Milestone OPEN，不调低阈值、不重启高成本或触红线方案（契约 3.8：成员关闭 ≠ Milestone 收敛）。

### M7 候选与既有交付纠偏（进度：6 / 11 CLOSED；状态：OPEN 且冻结）

- 已验收关闭（6）：#97、#99、#103、#104、#105、#108。
- 未完成（5）：#98（`in-progress`，D-019 A 冻结）、#100（`needs-info`）、#101（`needs-info`）、#102（`needs-info`）、#109（`blocked`）；#96 为 Epic 不计入分母。
- 依 D-019 默认 A：暂停 M7 扩展，保留前端 TS 渐进化方向。

## 已知阻塞与依赖

- **#109（`blocked`）**：本机 `command -v docker` 仍不可用（exit 1），无已授权远程 Docker 主机；环境就绪前不得以 console 探针替代真实 Jaeger / OTLP 验收。
- **#98（`in-progress` 冻结）**：受 D-019 A 冻结，保持现场不重置、不关闭，Executor 不得领取。
- **#96 / #100 / #101 / #102（`needs-info`）**：受 D-019 A 冻结（#102 同时依赖 #98）。
- **#59（`needs-info`）**：待用户提供具体产品功能需求（D-012 默认 A 有效，不重复追问）。

## 下一阶段

- 待 #133 / #134 交付并经下一轮 Planner 独立复跑验收通过后，基于已落地的 `tsconfig.json` 与工具链，按 `docs/FRONTEND_TS_MIGRATION.md` 第一批清单继续编排下一批小步、可验证的纯函数/工具/store TS 迁移切片。
- 若用户随时提供 #59 具体产品需求或对 D-019 / D-023 给出新决定，按用户新授权调整队列。

## 已放弃的方向

- 登录验证码（D-02 暂缓）· 归档 SQL（D-03 保留）· uv/venv 整包缓存（D-013 / D-016 放弃）· session 级训练缓存（D-014 放弃）· 默认开启 xdist / randomly / 全局 pytest-socket（D-024 放弃）· M7 未授权扩展（D-019 A 冻结）· M6 降阈值或改 CI 级联（D-023 A 冻结）。

## 给 Executor 的指令（不超过 2 句）

- 按 **#133 → #134** 串行执行，因 `ENV.md` 未设置 `WORKFLOW=trunk`，请严格按契约 1.9 使用每任务独立分支（`agent/issue-133-app-store-ts`、`agent/issue-134-test-perf-closeout`）完成验证、合入 `main` 并清理临时分支。
- 先按真实 GitHub Issue 状态刷新 `STATE.md` 与 `HANDOFF.md`（#130–#132 已 `done`/`CLOSED`），每项完成后留下契约 1.7 固定字段执行报告并转 `in-review`（严禁自行 close），在 `.agent/DIARY/2026-10-25.md` 追加日报并单独以 `chore(agent): ...` 提交。

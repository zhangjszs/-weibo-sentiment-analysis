# TASKS — GitHub Issue 本地镜像

> 2026-10-25 规划轮从真实 GitHub Issues **整体重写**（契约 1.6：GitHub Issue 可用且为唯一权威来源，`gh` CLI 正常、未降级）。
> 状态值（同一时刻最多一个）：`ready` · `in-progress` · `in-review` · `blocked` · `needs-info` · `done`；优先级：`priority:P0`–`P4`。Executor 变更任务状态时必须先改 GitHub Issue（标签 + comment），再同步本文件对应行。

## 今日队列（2026-10-25，共 2 项 ready，建议按序串行执行）

| 顺序 | Issue | 标题 | 优先级 | 状态 | 分支与核心验收要点 |
|---|---|---|---|---|---|
| 1 | [#133](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/133) | 启用本地 TypeScript 类型检查并迁移 app store 首个生产切片 | P2 | `ready` | 分支 `agent/issue-133-app-store-ts`。依赖 #58/#130 已 `done`；D-009/D-018/D-019 授权有效。固定 devDep `typescript@5.9.3` + `@typescript-eslint/parser@8.46.2`；新增最小严格 `frontend/tsconfig.json` 与 `npm run typecheck`；`src/stores/app.js` → `app.ts`（不留 `.js` shim，`setTheme` 参数保持 `string`）；`lint` 与 `vitest.config.js` `coverage.include` 纳入 `.ts`；更新 `docs/FRONTEND_TS_MIGRATION.md`。验收：`npm ci` / `typecheck` / `lint` / `format:check` / `build` 退出码 0；`tsc --noEmit --listFiles` 含 `src/stores/app.ts`；临时类型负例非零且恢复后为 0；`app-store.test.js` 9 passed、全量 ≥47 files / 321 tests；`app.ts` Lines ≥90% / Funcs 100% / Branches ≥75%；真实 store smoke 记录证据。 |
| 2 | [#134](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/134) | 收尾 TEST_PERF 验收状态并明确覆盖率快照时点 | P4 | `ready` | 分支 `agent/issue-134-test-perf-closeout`。硬依赖 #130–#132 已 `done`；建议在 #133 后执行。仅修改 `docs/TEST_PERF.md`：§7.1 追加 #130（`73bec15`）/#131（`9a86951`）/#132（`06b194e`）三行（已验收关闭）；§7.5 清除 #130/#131 作为当前 `in-review` 的表述，保留全部历史时点数值与路径，并追加当次 `npm run test:coverage` 实测快照段（按实际提交记录 `app.ts` 或 `app.js`，不预支未验收状态）。 |

- **容量与门禁核对**：P0=0、P1=0、P2=1、P3=0、P4=1（队列共 2 项，符合 4.3 容量约束，全部通过 4.2 七条 ready 门禁）。两项均不设 milestone，不在 #133 完成前把后续依赖它的 TS 切片提前放入 `ready`。

## 等待验收（in-review）

- 当前无 `in-review` 任务。
  - 昨日（2026-10-24）交付的 #127–#129 与 #130–#132 共 6 项均已于 2026-10-24 验收通过并关闭（`CLOSED` + `done` 标签）。
  - 自上一规划提交 `9d85159`（2026-10-24 23:33 +0800）以来 Executor 尚未运行，故本轮无新 `in-review` 产出；`STATE.md` / `HANDOFF.md` 中残留的「#130/#131/#132 仍 in-review」系上一执行会话快照，由今日 Executor 启动时按实际 Issue 状态刷新（Planner 严守契约 1.1 不代写）。

## 未完成任务全表（Open Issues 治理账本，共 9 项）

| Issue | 标题 | 优先级 | 状态 | Milestone | 4.1 治理复核结论与下一步 |
|---|---|---|---|---|---|
| [#133](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/133) | 启用本地 TypeScript 类型检查并迁移 app store 首个生产切片 | P2 | `ready` | — | 今日队列第 1 项；2026-10-24 创建后 Executor 尚未运行，按 D-035 原样结转。 |
| [#134](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/134) | 收尾 TEST_PERF 验收状态并明确覆盖率快照时点 | P4 | `ready` | — | 今日队列第 2 项；硬依赖 #130–#132 已满足，按 D-035 原样结转。 |
| [#109](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/109) | 验证并修正现有 OTLP 链路的 metrics 接收与 Jaeger 展示 | P2 | `blocked` | M7 | 本轮复核本机 `command -v docker` 仍不可用（exit 1），无已授权远程 Docker 主机；保持 `blocked`。 |
| [#98](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/98) | [M7-1][P2] Rust 第一切片迁移：deduplicator + normalize（criterion before/after） | P2 | `in-progress` | M7 | 受 D-019 默认 A 有意冻结（非中断崩溃现场）；按契约 9 保持 `in-progress` 不重置、不关闭，Executor 不得领取。 |
| [#96](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/96) | [M7] Rust-Accelerated Core + Observable AI（炫技重构主轴） | P2 | `needs-info` | — | M7 候选 Epic，受 D-019 默认 A 冻结；不计入 M7 子任务分母。 |
| [#102](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/102) | [M7-5][P2] CI ABI parity matrix + cross-impl fallback contract tests | P2 | `needs-info` | M7 | 依赖 #98 未完成，且跨版本 CI 矩阵属契约 1.10 红线，受 D-019 A 冻结。 |
| [#101](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/101) | [M7-4][P3] Streaming summary via SSE（AI layer 切片2） | P3 | `needs-info` | M7 | 缺产品入口/LLM 成本与数据边界授权，受 D-019 A 冻结；未跨两个已完成 Milestone，不按饥饿关闭。 |
| [#100](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/100) | [M7-3][P3] Qdrant 语义搜索端点（AI layer 切片1） | P3 | `needs-info` | M7 | 缺外部向量服务/模型资源授权，受 D-019 A 冻结；未跨两个已完成 Milestone，不按饥饿关闭。 |
| [#59](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/59) | [P2] 产品功能迭代：需求收集与规划 | P2 | `needs-info` | — | 待用户提供具体产品功能需求；D-012 默认 A 有效，不重复提问。 |

## 本轮队列治理与标签修正记录（2026-10-25）

- **修正 #127 / #128 / #129 遗留状态标签漂移**：三项虽已于 2026-10-24 首轮规划验收关闭（`CLOSED`），但 GitHub 标签仍残留 `in-review`。本轮已执行 `gh issue edit 127/128/129 --remove-label in-review --add-label done`，使 #88–#132 全部已验收关闭任务的 GitHub 状态标签统一为 `done`。
- **4.1 逐项检查**：无重复未完成任务 · 无 ready 质量回落 · 无方向冲突未决项 · 无 open `auto-discovered` · 无缺失优先级任务 · 无满足「连续两个 Milestone 未动」的 P3/P4 饥饿项 · 无 open PR。
- **回应昨日日报信号**：
  1. 执行会话 2/3 日报请求验收 #130–#132 并补充新队列：已于 `9d85159` 完成独立复跑验收关闭并排入 #133 / #134，本轮核实 `9d85159` 五项 CI 全绿并结转至今日执行轮。
  2. 执行会话 2 观察 `stores/tabs.js` 的 `_persist()` 无 `try/catch`：已于 #131 验收结论与 D-034 定级为未复现源码观察（缺失败恢复契约），不单独立项修改生产行为。

## 最近已验收关闭任务（近期账本摘要）

| Issue | 优先级 | 状态 | 验收结论与关键提交 |
|---|---|---|---|
| [#132](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/132) | P4 | `done` / CLOSED | `06b194e`：刷新 `docs/TEST_PERF.md` §7.1（#127–#129）与 §7.5（47/321 基线）；2026-10-24 验收通过。 |
| [#131](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/131) | P3 | `done` / CLOSED | `9a86951`：新增 `tests/tabs-store.test.js`（41 用例），`tabs.js` Lines 97.67% / Funcs 100% / Branch 95.77%–95.83%；2026-10-24 验收通过。 |
| [#130](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/130) | P3 | `done` / CLOSED | `73bec15`：新增 `tests/app-store.test.js`（9 用例），`app.js` 四项覆盖率全 100%；2026-10-24 验收通过。 |
| [#129](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/129) | P4 | `done` / CLOSED | `4d00f9c`：刷新 `docs/TEST_PERF.md` §7.1（#124–#126）与 §7.5（`App.vue` 0% 豁免 + 45/271 段）；2026-10-24 验收通过，2026-10-25 补正 `done` 标签。 |
| [#128](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/128) | P3 | `done` / CLOSED | `4cb2519`：新增 `tests/china-map.test.js`（6 用例），`chinaMap.js` 全 100%；2026-10-24 验收通过，2026-10-25 补正 `done` 标签。 |
| [#127](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/127) | P3 | `done` / CLOSED | `ffe4c5b`：新增 `tests/user-store.test.js`（13 用例），`user.js` 97.97% / 81.57% / 100%；2026-10-24 验收通过，2026-10-25 补正 `done` 标签。 |

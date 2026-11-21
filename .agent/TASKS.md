# TASKS — GitHub Issue 本地镜像

> 2026-11-22 从 GitHub Issues 整体刷新；未降级。先在 Issue 修改状态，再同步本文件。无生命周期标签的记录项不可领取。
> 初始 `main` = `origin/main` = `9349e44`（fetch 成功、0/0）；pull/rebase 因已有未暂存改动拒绝，未移动用户改动。

## 今日队列（3 项 `ready`）

| 顺序 | Issue | 标题 | 优先级 | 状态 | 分支与主验收 |
|---|---|---|---|---|---|
| 1 | [#144](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/144) | 修复 Axios 与 Vue 已知依赖告警（同主版本） | P1 | `ready` | `agent/issue-144-axios-vue-audit`；仅锁文件两条目标链，Axios 1.20.0、Vue 3.5.42；目标告警消失、已有门禁和 bundle 预算绿。 |
| 2 | [#143](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/143) | 稳定 auth 域覆盖率并验证漂移机制（#138） | P3 | `ready` | `agent/issue-143-auth-coverage-isolation`；测试侧及 TEST_PERF 台账；同一锁基线，默认调度两次 auth.js / Login.vue / All files 四项相同；保留 mock/历史数值，7 TS / 0 JS/Vue。 |
| 3 | [#145](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/145) | 盘点前端请求与会话 API 的既有契约并明确 TS 切片边界 | P3 | `ready` | `agent/issue-145-api-contract-inventory`；仅迁移说明 §9：六个现有调用、请求拦截器与依赖环、D-043 下的最小候选。 |

三项均有明确范围、非目标和可判定验收，无硬依赖、无未决产品取舍、不触 1.10。顺序不是硬依赖；无 P0，P1 一项。

## 验收与恢复（不在今日 `ready` 队列）

- [#142](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/142#issuecomment-7067168599) **部分通过 → `in-progress`**。`ccac121` 已推送；原[报告](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/142#issuecomment-6441021624)的规则行为经 ESLint 探针复核（合法重载 0、真重复 1），原推送五项 CI 成功。锁 diff 97+/0−，均锁 8.46.2，但只新增插件及 4 个传递锁项，另 3 项复用；相同 semver 范围不保证重新解析时同版。补报告、迁移说明 §0 与缺失的日报续段，不回滚。
- [#141](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/141#issuecomment-7067169596) **部分通过，保留 `in-progress`（疑似中断）**。`9349e44` 已推送，五项 CI 成功；本轮核对 5 文件、图标 29→29 同序（旧规格 35 为 Planner 笔误，已更正）、7 TS / 0 JS/Vue、目标 lint 0。缺固定字段报告及定向测试、类型负例、覆盖、转译证据；本地分支仍在，由 Executor 收尾后转 `in-review`。
- 本轮无仍为 `in-review` 的项，没有新关闭。前轮 #139（`f0661bb`，评论 6440380674）、#140（`92cd03b`，评论 6440392290）已验收关闭；#135–#137 的关闭仍有效（D-039）。

## 未完成任务全表（13 个 Open Issues）

| Issue | 标题 | 优先级 | 状态 | Milestone | 治理结论 |
|---|---|---|---|---|---|
| [#144](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/144) | 修复 Axios 与 Vue 已知依赖告警（同主版本） | P1 | `ready` | — | 新增，限定可在当前版本范围内处理的两条依赖链。 |
| [#143](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/143) | 稳定 auth 域覆盖率并验证漂移机制（#138） | P3 | `ready` | — | 已刷新范围与类型门禁；载入差异已证实，默认调度归因待验证。 |
| [#145](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/145) | 盘点前端请求与会话 API 的既有契约并明确 TS 切片边界 | P3 | `ready` | — | 新增，只盘点，不启动迁移或新契约。 |
| [#142](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/142) | 统一治理 .ts 文件的 no-redeclare 误报（TS 重载签名被基础 ESLint 规则误判） | P2 | `in-progress` | — | 验收退回，补证与更正说明。 |
| [#141](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/141) | 迁移 plugins/elementPlus.js 为 TypeScript 并纳入本地类型门禁 | P2 | `in-progress` | — | 疑似中断，不重置，补报告与交接。 |
| [#138](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/138) | [auto-discovered] src/api/auth.js 与 src/views/auth/Login.vue 覆盖率在同 HEAD 下跨运行波动 | P3 | 无生命周期标签 | — | 已定级；标题前缀不是现有标签。现象记录，不与 #143 重复领取。 |
| [#109](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/109) | 验证并修正现有 OTLP 链路的 metrics 接收与 Jaeger 展示 | P2 | `blocked` | M7 | 本机无容器命令/默认 socket，无已授权远端；不以 console 替代。 |
| [#98](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/98) | [M7-1][P2] Rust 第一切片迁移：deduplicator + normalize（criterion before/after） | P2 | `in-progress` | M7 | D-019 A 有意冻结，不判中断、不重置。 |
| [#102](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/102) | [M7-5][P2] CI ABI parity matrix + cross-impl fallback contract tests | P2 | `needs-info` | M7 | #98 未通过，跨版本矩阵未获授权。 |
| [#101](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/101) | [M7-4][P3] Streaming summary via SSE（AI layer 切片2） | P3 | `needs-info` | M7 | D-019 A 冻结，产品入口及数据/成本边界未授权。 |
| [#100](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/100) | [M7-3][P3] Qdrant 语义搜索端点（AI layer 切片1） | P3 | `needs-info` | M7 | D-019 A 冻结，新增服务与成本未授权。 |
| [#96](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/96) | [M7] Rust-Accelerated Core + Observable AI（炫技重构主轴） | P2 | `needs-info` | — | 冻结 Epic，不计 M7 分母。 |
| [#59](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/59) | [P2] 产品功能迭代：需求收集与规划 | P2 | `needs-info` | — | 缺具体需求，按 D-012 A，不重复询问。 |

## 本轮治理与日报

- 昨日日报缺失；最新 10-27 日报只覆盖较早会话。以 `ccac121` / `9349e44`、Issues、Actions、旧 `STATE`/`HANDOFF` 还原，未把历史交付算成昨日。旧信号已分别落实于 D-039–D-044，#138 由 #143 承接，后续漏记由 Executor 按 D-022 在当前执行日补记。
- 入轮时镜像把 #141/#138 误列 `ready`，Issue 为 `in-progress` / 无状态；#142 已 `in-review` 却仍列在旧日队列。按 Issue 覆盖，已请 Executor 在其 `HANDOFF` 记录；Planner 不代写。
- 13 open：3 `ready`、3 `in-progress`、1 `blocked`、5 `needs-info`、1 记录项。全有优先级，无未定级发现、重复执行项、方向冲突或跨两个已结束 Milestone 的低优先级饥饿项。M6 10/10 CLOSED、成功信号 1/3；M7 6/11 CLOSED 且冻结。无 pending 或需用户决策事项。


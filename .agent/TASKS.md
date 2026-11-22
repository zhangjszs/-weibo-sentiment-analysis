# TASKS — GitHub Issue 本地镜像

> 2026-11-22 从 GitHub Issues 整体刷新；未降级。先在 Issue 修改状态，再同步本文件。无生命周期标签的记录项不可领取。
> 初始 `main` = `origin/main` = `9349e44`（fetch 成功、0/0）；pull/rebase 因已有未暂存改动拒绝，未移动用户改动。

## 今日队列（含执行状态）

| 顺序 | Issue | 标题 | 优先级 | 状态 | 分支与主验收 |
|---|---|---|---|---|---|
| 1 | [#144](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/144) | 修复 Axios 与 Vue 已知依赖告警（同主版本） | P1 | `in-review` | `b6661ad` 已推送；[报告](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/144#issuecomment-7073836608)，三项目标告警消失，门禁和 bundle 预算通过。 |
| 2 | [#143](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/143) | 稳定 auth 域覆盖率并验证漂移机制（#138） | P3 | `blocked` | `d423f3b` 已推送；[报告](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/143#issuecomment-7073909332)。合并顺序可改变聚合分支读数；历史 auth 双文件漂移未复现，未改测试。 |
| 3 | [#145](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/145) | 盘点前端请求与会话 API 的既有契约并明确 TS 切片边界 | P3 | `in-review` | `b0737dd` 已推送；[报告](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/145#issuecomment-7074006035)，仅迁移说明 §9，7 TS / 0 JS/Vue。 |

三项均有明确范围、非目标和可判定验收，无硬依赖、无未决产品取舍、不触 1.10。顺序不是硬依赖；无 P0，P1 一项。

## 验收与恢复（不在今日 `ready` 队列）

- [#142](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/142) **`in-review`**。`ccac121` 及更正 `85e2845` 已推送；[报告补记](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/142#issuecomment-7067407062)核对 `+97/-0`、新增插件及四个传递锁项、三个复用项；[更正提交五项 CI 通过](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/142#issuecomment-7067468614)。
- [#141](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/141) **`in-review`**。`9349e44` 已推送；[恢复报告](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/141#issuecomment-7067430942)补齐快照重建的类型负例、定向测试、覆盖和转译证据，29 项图标同序。
- 本轮未关闭 Issue。前轮 #139（`f0661bb`，评论 6440380674）、#140（`92cd03b`，评论 6440392290）已验收关闭；#135–#137 的关闭仍有效（D-039）。

## 未完成任务全表（13 个 Open Issues）

| Issue | 标题 | 优先级 | 状态 | Milestone | 治理结论 |
|---|---|---|---|---|---|
| [#144](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/144) | 修复 Axios 与 Vue 已知依赖告警（同主版本） | P1 | `in-review` | — | 已补前后审计、验证及五项 CI 报告，待 Planner 复核。 |
| [#143](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/143) | 稳定 auth 域覆盖率并验证漂移机制（#138） | P3 | `blocked` | — | 已补调查台账，需历史 auth 双漂移样本或 Planner 单列工具链修复范围。 |
| [#145](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/145) | 盘点前端请求与会话 API 的既有契约并明确 TS 切片边界 | P3 | `in-review` | — | 六请求与最小候选已盘点，五项 CI 通过；未实施迁移。 |
| [#142](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/142) | 统一治理 .ts 文件的 no-redeclare 误报（TS 重载签名被基础 ESLint 规则误判） | P2 | `in-review` | — | 补证及迁移说明更正已提交，待 Planner 复核。 |
| [#141](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/141) | 迁移 plugins/elementPlus.js 为 TypeScript 并纳入本地类型门禁 | P2 | `in-review` | — | 已在干净快照重建证据并补报告，待 Planner 复核。 |
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
- Planner 刷新时有 13 个 open Issue；本表状态按 Executor 的实际流转更新。M6 10/10 CLOSED、成功信号 1/3；M7 6/11 CLOSED 且冻结。


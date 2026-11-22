# TASKS — GitHub Issue 本地镜像

> 2026-11-22 同日续接，按 GitHub open Issues 整体重建；未降级。变更状态先操作 Issue，再同步本文件。没有生命周期标签的记录不可领取。

## 今日队列（按建议顺序）

| 顺序 | Issue | 优先级 | 状态 | 交付范围与验收入口 |
|---|---|---|---|---|
| 1 | [#146](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/146) | P1 | `ready` | 五个传递依赖的同范围锁更新；独立分支 `agent/issue-146-transitive-lock-audit`。仅依赖已 `done` 的 #144；逐项复核版本树、审计及现有前端门禁。 |
| 2 | [#147](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/147) | P3 | `ready` | V8 合并确定性与正确性验证；独立分支 `agent/issue-147-v8-coverage-merge-study`。无未完成前置；同一批原始输入排列回放，核对 `addTab` 与 Vue 映射，仅追加 TEST_PERF §7.5。 |

两项均有范围、非目标、可判定标准和可达输入；无产品选择、无红线、无相互前置。P0=0，P1=1。

## 本轮验收（不在领取队列）

| Issue | 结论 | 关键证据 |
|---|---|---|
| [#141](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/141#issuecomment-7074613252) | 通过，`done` / CLOSED | `9349e44`，29 项图标同序、转译 diff 0、覆盖 100→100；负例和日报已按恢复口径补证。 |
| [#142](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/142#issuecomment-7074613243) | 通过，`done` / CLOSED | `ccac121` + `85e2845`；ESLint 重载 0 / 重复 1；锁 +97/−0，新锁项 5、复用 3，文档已纠正同区间不保证同版。 |
| [#144](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/144#issuecomment-7074613225) | 通过，`done` / CLOSED | `b6661ad` 仅两条锁链；三项目标告警消失，前端 47/321 与体积预算通过；其余五项归 #146。 |
| [#145](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/145#issuecomment-7074613322) | 通过，`done` / CLOSED | `b0737dd` 仅新增契约清单 §9；六接口、闭环与候选边界核对，7 TS / 0 JS 或 Vue；未授权实现。 |
| [#143](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/143#issuecomment-7074612895) | 部分通过，保留 `blocked` | `d423f3b` 的取证与台账通过，未修复历史 auth 漂移；取得可重复的原始双漂移样本才恢复。#147 不替代本项验收。 |

## 未完成任务全表（11 个 Open Issues）

| Issue | 标题 | 优先级 | 状态 | Milestone | 治理结论 |
|---|---|---|---|---|---|
| [#146](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/146) | 更新现有范围内的五个前端传递依赖锁项 | P1 | `ready` | — | 五个已发布目标版本均在现有父约束内；不改清单、业务、CI 或 Node。 |
| [#147](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/147) | 验证 V8 覆盖合并的确定性方案，保留用例和映射语义 | P3 | `ready` | — | 仅对照现有工具链的候选算法，不提交工具补丁。 |
| [#143](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/143) | 稳定 auth 域覆盖率并验证漂移机制（#138） | P3 | `blocked` | — | 历史双漂移原始样本缺失；不改 mock 凑读数。 |
| [#138](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/138) | auth.js 与 Login.vue 覆盖率在同 HEAD 下跨运行波动 | P3 | 无生命周期标签 | — | D-044 已定级；历史现象档案，不与 #143 重复领取，不属于 M6/M7。 |
| [#109](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/109) | 验证并修正现有 OTLP 链路的 metrics 接收与 Jaeger 展示 | P2 | `blocked` | M7 | 未发现 Docker/Podman 命令或默认 Docker socket，无已授权远端；console 不替代验收。 |
| [#102](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/102) | CI ABI parity matrix + cross-impl fallback contract tests | P2 | `needs-info` | M7 | #98 未通过；跨版本矩阵未授权。 |
| [#101](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/101) | Streaming summary via SSE（AI layer 切片2） | P3 | `needs-info` | M7 | D-019 A 冻结；产品入口、数据及成本未授权。 |
| [#100](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/100) | Qdrant 语义搜索端点（AI layer 切片1） | P3 | `needs-info` | M7 | D-019 A 冻结；新增服务与成本未授权。 |
| [#98](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/98) | Rust 第一切片迁移：deduplicator + normalize（criterion before/after） | P2 | `in-progress` | M7 | D-019 A 有意冻结，非疑似中断，不重置。 |
| [#96](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/96) | Rust-Accelerated Core + Observable AI | P2 | `needs-info` | — | 冻结 Epic，不计 M7 分母。 |
| [#59](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/59) | 产品功能迭代：需求收集与规划 | P2 | `needs-info` | — | 无具体产品需求，遵 D-012 A，不重复问。 |

## 交接

- 2026-11-21 日报缺失；Git、Issue 评论和 Executor `STATE` 无该日独立交付证据。验收依据是 11-22 日报中的恢复补记和实际执行，不把 10-27 实现或 11-22 交付回填到 11-21。
- 入轮 Issue 与镜像的状态一致，但旧「今日队列」已无可领项；本轮按实时 Issue 重建。`STATE`/`HANDOFF` 仍是上轮执行时点快照，待 Executor 刷新，不由 Planner 改写。
- 无缺优先级、未定级 `auto-discovered` 或已跨两个完成 Milestone 的低优先级任务。M6 10/10 成员关闭（成功信号 1/3）；M7 6/11 关闭且冻结。

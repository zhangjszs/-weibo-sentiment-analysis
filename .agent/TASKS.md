# TASKS — GitHub Issue 本地镜像

> 2026-11-23 · 同日续接。默认沙箱的 `gh` 连接代理失败，GitHub 连接器与隔离副本的授权 `gh` 查询可用。以实时 GitHub Issues 整体重建镜像，Executor 先更新 Issue，再同步对应行。

## 今日队列（建议顺序）

| 顺序 | Issue | 优先级 | 状态 | 依赖与验收入口 |
|---|---|---|---|---|
| 1 | [#156](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/156) 锁定六个会话 API 包装的真实请求与响应契约 | P3 | `ready` | #145、#150 已验收。单文件 adapter 测试覆盖六条路径、完整包络与可缺席 data。分支 `agent/issue-156-auth-api-contract`。 |
| 2 | [#157](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/157) 迁移公共请求实例至 TypeScript 并在入口装配导航 | P2 | `ready` | #145、#150、#151 已验收。生产 8 TS / 0 JS 或 Vue、两条浏览器入口及 401 等价回归。分支 `agent/issue-157-request-typescript`。 |

两项的 Issue 均给出范围、排除项、已完成前置及逐条可测标准。无产品选择、红线或相互硬依赖。开放 P0/P1 均为 0。

## 本轮验收

| Issue | 结论 | 关键证据 |
|---|---|---|
| [#146](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/146#issuecomment-7091137981) | 通过，`done` / CLOSED | `9deea56` 仅五个锁项，原锁结构和目标版本已核对。上半轮配对生产审计 5→0，前端 47/321，原 PR CI 5/5。 |
| [#147](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/147#issuecomment-7104222957) | 补证通过，`done` / CLOSED | 首次部分通过的两项差距已由 `cce6cf5` 补齐。两处回退 L/R/T 都为 0/0/1。从提交逐字提取探针，用原锁独立复跑 54 例与 18 次排列。仅 §7.5 新增 156 行，原 PR CI 5/5。 |
| [#150](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/150#issuecomment-7104225273) | 通过，`done` / CLOSED | `9888bc6` 仅既有请求错误测试。两种到达顺序、首次清态、去重释放及拒绝身份可判定。独立定向 53 例（目标文件 27 例），全量 47/323，原 PR CI 5/5。 |
| [#151](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/151#issuecomment-7104227740) | 通过，`done` / CLOSED | `5e3f799` 仅 §9.4 新增 80 行。主干类型门禁独立复跑 7/0。候选 8/0、TS2322/TS2739 与浏览器证据来自执行时记录，候选产物未推送。原 PR CI 5/5。 |
| [#143](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/143#issuecomment-7091138663) | 延续前次部分通过，`blocked` | 原始 auth 双漂移输入及顺序仍缺。#147 的固定聚合样本支持独立结论。 |

## 未完成任务全表（11 个 Open Issues）

| Issue | 标题 | 优先级 | 状态 | Milestone | 治理结论 |
|---|---|---|---|---|---|
| [#157](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/157) | 迁移公共请求实例至 TypeScript 并在入口装配导航 | P2 | `ready` | [请求层迁移](https://github.com/zhangjszs/-weibo-sentiment-analysis/milestone/4) | 已有候选、行为基线及可检查边界，生产 8/0。 |
| [#156](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/156) | 锁定六个会话 API 包装的真实请求与响应契约 | P3 | `ready` | [请求层迁移](https://github.com/zhangjszs/-weibo-sentiment-analysis/milestone/4) | 现有页面及 store 测试 mock 整个 auth 模块，本项覆盖真实包装和公共实例。 |
| [#143](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/143) | 稳定 auth 域覆盖率并验证漂移机制（#138） | P3 | `blocked` | — | 等历史双文件原始样本和顺序，保留原验收标准。 |
| [#138](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/138) | [auto-discovered] src/api/auth.js 与 src/views/auth/Login.vue 覆盖率在同 HEAD 下跨运行波动 | P3 | 无生命周期标签 | — | D-044/D-048 已定级，标题保留来源，修复由 #143 承接。 |
| [#109](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/109) | 验证并修正现有 OTLP 链路的 metrics 接收与 Jaeger 展示 | P2 | `blocked` | M7 | 本机无 Docker/Podman 命令及默认 socket，等待可用容器环境或已授权主机。 |
| [#102](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/102) | [M7-5][P2] CI ABI parity matrix + cross-impl fallback contract tests | P2 | `needs-info` | M7 | 依赖 #98 和主要 CI 扩展授权，D-019 A 冻结。 |
| [#101](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/101) | [M7-4][P3] Streaming summary via SSE（AI layer 切片2） | P3 | `needs-info` | M7 | 产品入口及成本待授权，D-019 A 冻结。 |
| [#100](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/100) | [M7-3][P3] Qdrant 语义搜索端点（AI layer 切片1） | P3 | `needs-info` | M7 | 向量服务和长期成本待授权，D-019 A 冻结。 |
| [#98](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/98) | [M7-1][P2] Rust 第一切片迁移：deduplicator + normalize（criterion before/after） | P2 | `in-progress` | M7 | D-019 A 有意冻结原现场，继续保留状态。 |
| [#96](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/96) | [M7] Rust-Accelerated Core + Observable AI（炫技重构主轴） | P2 | `needs-info` | — | D-019 A 冻结的扩展 Epic。 |
| [#59](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/59) | [P2] 产品功能迭代：需求收集与规划 | P2 | `needs-info` | — | 按 D-012 A 等具体产品需求。 |

## 交接

- 原主干镜像停在 11-22 午间规划，完整 [11-22 日报](https://github.com/zhangjszs/-weibo-sentiment-analysis/blob/c9e9e8dc39eb9246606f7da3c47b59e3bb72a324/.agent/DIARY/2026-11-22.md) 在已推送的晚间交接分支。[11-23 日报](https://github.com/zhangjszs/-weibo-sentiment-analysis/blob/4386751e82e975bf57d9f85cae77d940ce044fdf/.agent/DIARY/2026-11-23.md) 和 [HANDOFF](https://github.com/zhangjszs/-weibo-sentiment-analysis/blob/4386751e82e975bf57d9f85cae77d940ce044fdf/.agent/HANDOFF.md) 在执行交接分支，已记录镜像时间差及当时的三个 `in-review`。此表以实际验收和刷新后的 Issue 状态为准。
- 逐项比较结果为无可合并领取项、缺优先级、待定级来源标签或跨两个已完成 Milestone 的 P3/P4。#98 为确认冻结。#143、#109 的可执行前置仍缺。
- 迁移准备里程碑 2/2 已关闭，新里程碑 0/2。M6 10/10、M7 6/11，均开放。没有新增产品决策；D-012 A、D-019 A、D-023 A 继续有效。

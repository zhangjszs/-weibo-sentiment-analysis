# TASKS — GitHub Issue 本地镜像

> 2026-11-23。按最新 GitHub Open Issues 整体重建。默认沙箱中的 `gh` 连接本地代理被拒，已通过 GitHub 连接器及授权后的 `gh` 查询恢复访问，GitHub Issues 继续作为权威。Executor 先更新 Issue，再同步对应镜像行。

## 今日队列（建议顺序）

| 顺序 | Issue | 优先级 | 状态 | 依赖与验收入口 |
|---|---|---|---|---|
| 1 | [#150](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/150) 锁定公共请求混合 401 的缓存清理与跳转去重 | P3 | `ready` | #145 已 `done`。用真实 Axios 实例和会话缓存检验两种 401 到达顺序、首次清态、导航窗口和两种 reject 行为。分支 `agent/issue-150-mixed-401-contract`。 |
| 2 | [#151](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/151) 验证公共请求层的 TypeScript 类型契约与入口接线 | P2 | `ready` | #145 已 `done`。验证启动顺序、请求包络和候选 8 TS / 0 JS 或 Vue；只提交 §9 增补。分支 `agent/issue-151-request-types-and-bootstrap`。 |

两项独立，均有可查基线、明确范围及逐条验收。项目开放任务 P0/P1 均为 0。#147 已处于执行中，补证沿原 Issue 继续。

## 本轮验收

| Issue | 结论 | 关键证据 |
|---|---|---|
| [#146](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/146#issuecomment-7091137981) | 通过，`done` / CLOSED | `9deea56` 仅改五个锁项，484 条记录无增删，锁哈希不变。独立配对审计 exit 1→0，五个目标消失，前端门禁全绿（47 文件 / 321 用例），原 PR CI 5/5。 |
| [#147](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/147#issuecomment-7091139293) | 部分通过，退回 `in-progress` | `d760896` 只追加 §7.5。认可 18 次回放的样本内结果与 Vue 负对照。独立定向 3 文件 / 54 用例、文档路径检查、原 PR CI 5/5。仍缺 `|| route.name`、`|| null` 的计数或不可独立计数依据，以及从干净目录运行仓库外探针的可重复步骤。 |
| [#143](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/143#issuecomment-7091138663) | 延续前次部分通过，`blocked` | 历史 `auth.js` 与 `Login.vue` 双漂移原始样本和顺序仍缺。#147 的聚合分支证据有独立适用范围。 |

## 未完成任务全表（12 个 Open Issues）

| Issue | 标题 | 优先级 | 状态 | Milestone | 治理结论 |
|---|---|---|---|---|---|
| [#151](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/151) | 验证公共请求层的 TypeScript 类型契约与入口接线 | P2 | `ready` | 前端请求层迁移准备 | 接线规格与隔离编译证明。只追加迁移说明 §9；候选门禁 8 TS / 0 JS 或 Vue。 |
| [#150](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/150) | 锁定公共请求混合 401 的缓存清理与跳转去重 | P3 | `ready` | 前端请求层迁移准备 | 原 Axios 实例和真实会话缓存，覆盖两类 401 的到达顺序、清态、去重和拒绝身份。只改既有请求错误测试。 |
| [#147](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/147) | 验证 V8 覆盖合并的确定性方案，保留用例和映射语义 | P3 | `in-progress` | — | 部分通过，已在原 Issue 退回补证。补两个回退分支的计数或不可独立计数依据，以及干净目录的回放启动验证。 |
| [#143](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/143) | 稳定 auth 域覆盖率并验证漂移机制（#138） | P3 | `blocked` | — | 历史 auth 双漂移原始输入和顺序仍缺。保留当前标准，#147 不解除阻塞。 |
| [#138](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/138) | [auto-discovered] src/api/auth.js 与 src/views/auth/Login.vue 覆盖率在同 HEAD 下跨运行波动 | P3 | 无生命周期标签 | — | D-044/D-048 定级与分工。标题保留历史来源，已无 `auto-discovered` 标签。保留现象与证据，修复由 #143 承接。 |
| [#109](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/109) | 验证并修正现有 OTLP 链路的 metrics 接收与 Jaeger 展示 | P2 | `blocked` | M7 | 当前无 Docker/Podman 命令或默认 Docker socket，无已授权测试主机。待实际 OTLP / Jaeger 环境。 |
| [#102](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/102) | [M7-5][P2] CI ABI parity matrix + cross-impl fallback contract tests | P2 | `needs-info` | M7 | 依赖 #98 验收及主要 CI 扩展授权。D-019 A 冻结。 |
| [#101](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/101) | [M7-4][P3] Streaming summary via SSE（AI layer 切片2） | P3 | `needs-info` | M7 | 产品入口、调用成本及外部服务未授权。D-019 A 冻结。 |
| [#100](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/100) | [M7-3][P3] Qdrant 语义搜索端点（AI layer 切片1） | P3 | `needs-info` | M7 | 产品方向、向量服务及长期成本未授权。D-019 A 冻结。 |
| [#98](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/98) | [M7-1][P2] Rust 第一切片迁移：deduplicator + normalize（criterion before/after） | P2 | `in-progress` | M7 | 已明确按 D-019 A 冻结执行现场，保留原状态。 |
| [#96](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/96) | [M7] Rust-Accelerated Core + Observable AI（炫技重构主轴） | P2 | `needs-info` | — | D-019 A 冻结扩展提案。Epic。 |
| [#59](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/59) | [P2] 产品功能迭代：需求收集与规划 | P2 | `needs-info` | — | D-012 A 等具体用户需求。 |

## 交接

- 昨日日报在 main 只到午间。已读取 [晚间 Executor 交接分支的完整追加日报](https://github.com/zhangjszs/-weibo-sentiment-analysis/blob/c9e9e8dc39eb9246606f7da3c47b59e3bb72a324/.agent/DIARY/2026-11-22.md)、`STATE`、`HANDOFF` 及 Issue 评论。该分支的 HANDOFF 已记录 GitHub `in-review` 与旧主干镜像 `ready` 的冲突，本文件以验收后的实时 Issue 状态覆盖旧镜像。
- 已逐项复核开放任务。无重复领取项、缺优先级、待定级 `auto-discovered`，也无已跨两个完成 Milestone 的 P3/P4。执行中的 #147 今日已退回补证，#98 为确认冻结的现场。
- 前端请求层迁移准备 0/2。M6 10/10 成员关闭，记录中的成功信号 1/3，仍 OPEN。M7 6/11 成员关闭，仍 OPEN 且冻结。

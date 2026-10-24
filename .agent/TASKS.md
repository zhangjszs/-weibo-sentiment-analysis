# TASKS — GitHub Issue 本地镜像

> 2026-10-24 同日接续规划；本文件从真实 Issues **整体重写**，Issue 为权威，gh 可用、未降级。上轮 D-033 队列在执行会话 2 完成，本轮响应会话 2/3 日报验收 #130/#131/#132，随后编排 #133/#134；不是虚构下一天，也不重复计算 pending 天数。
> 生命周期：`ready / in-progress / in-review / blocked / needs-info / done`，同一 Issue 最多一个；优先级 `priority:P0`–`P4`。Executor 先修改 Issue 标签/comment，再同步对应状态行；范围与完整 checklist 以 Issue 为准。

## 今日队列（给下一执行会话，2 项）

| 顺序 | Issue / 目标 | P | 状态 | 范围与完成证据 |
|---|---|---|---|---|
| 1 | [#133 启用本地 TypeScript 类型检查并迁移 app store 首个生产切片](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/133) | P2 | ready | D-009 已授权，D-018/D-019 保留；#58/#130 已关闭。新增 typescript@5.9.3、@typescript-eslint/parser@8.46.2 开发依赖、最小 strict/noEmit tsconfig 与本地 typecheck；只迁移 app.js→app.ts，不留兼容 .js。setTheme 仍接收 string，不改变任意存储字符串语义。lint 仅为 TS 加 parser、覆盖率 include 纳入 TS；更新 TS 策略实际范围与过期建议。验收：npm ci/typecheck/lint/build 成功，listFiles 含真实 app.ts；临时类型负例非零、移除后成功；既有 app 9 用例、全量≥47/321；app.ts Lines≥90/Funcs100/Branches≥75；真实 store smoke 有存储/DOM/sidebar 证据。 |
| 2 | [#134 收尾 TEST_PERF 验收状态并明确覆盖率快照时点](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/134) | P4 | ready | 硬依赖仅已关闭的#130/#131/#132，与#133无硬依赖；建议后执行以记录最新切片，#133阻塞仍可独立收尾。只改docs/TEST_PERF.md：§7.1补三行（73bec15/9a86951/06b194e，已验收关闭），§7.5附验收结果与执行时同次实测段，实际路径为app.js或已交付的app.ts；保留历史路径/数字/时点，不预支TS完成。验收：diff仅该文档、历史基线不变、当次coverage非空且exit0，新段逐项对应该次日志，§7.2–§7.4不变。不为文档自身关闭再造同内容任务。 |

P0=0、P1=0、P2=1、P3=0、P4=1。两项无 milestone，不计入 M6/M7 分母。

### ready 门禁与执行边界

- #133 的目标/文件边界/非目标/命令/类型负例/真实模块 smoke 均已在 Issue 钉死；生产切片不是空配置。所需产品授权已存在，不重新询问。
- #134的全部硬依赖#130–#132已验收关闭，可独立执行；建议#133之后采样但不是ready前提，按实际代码提交记录JS或TS路径，不预支未交付事实。
- 不改 `.github/`、后端、schema、认证/权限、组件视觉；不升级既有直接依赖版本、不加 Vue 重复 @types/vue-tsc、不引入新服务或费用。
- TS 仅本地 typecheck；不纳入 CI、不设 coverage.thresholds。不为薄 API 包装写 mock 复述用例，不以跳过用例/放宽 JS 或 Vue lint 凑绿。
- 分支：`agent/issue-133-app-store-ts` → `agent/issue-134-test-perf-closeout`，每任务独立验证/提交/合并。ENV 没有字面 `WORKFLOW=trunk`，因此**默认每任务分支**；main 未设保护不是 trunk 授权，不重写既有历史。

## 等待验收（in-review）

无；#130/#131/#132 已在本轮通过并关闭。Executor 的 STATE/HANDOFF 仍记其 in-review，是上一会话快照，下一棒应自行刷新，Planner 不越权代改。

## 本轮验收账

| Issue | 结论 | 独立证据 |
|---|---|---|
| [#130](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/130#issuecomment-6385968029) | 通过，done/CLOSED | 定向运行 app9+tabs41 全通过；全量47/321、lint0；app LH/LF39/39、FNH/FNF4/4、BRH/BRF10/10；五组场景与清理逐条核对；73bec15仅新增142行测试。 |
| [#131](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/131#issuecomment-6385969485) | 通过，done/CLOSED | 41用例、11组行为与独立顺序/路由/存储断言齐全；tabs LH/LF168/172（97.67%）、FNH/FNF11/11（100%）、BRH/BRF68/71（95.77%）超过门槛；9a86951仅新增471行测试；catch40–41/190–191如实未覆盖，不强制mock。 |
| [#132](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/132#issuecomment-6385970757) | 通过，done/CLOSED | 06b194e仅TEST_PERF +10/−5；三行提交号由git show核对，历史数字不动；新段与执行期原日志/tmp/cov131.txt一致；本轮复跑与原日志的两项Branch差异已明示，不倒改历史。 |

- Standards / Spec 两轴只读审查均无阻断项。定向测试、全量测试、coverage、lint 是本轮独立运行，不仅引用执行报告。
- `06b194e`（含三项交付）GitHub check：backend-fast / frontend-fast / integration / rust-core / security-scan 全 completed/success。
- 分支测量差异：执行时 All Branch77.35、tabs Branch95.83；本轮分别77.33、95.77。原日志支持执行期数值，根因**未定位**，不能归为已证明的舍入；验收门槛不受影响。#134 只绑定同一次输出。
- 执行期变异实验未重做：只读验收不修改生产文件，其证据仍属于 Executor 的运行，不伪装成本轮验证。

## 存量未完成任务治理（全部不可领取实现）

| Issue | P | 状态 | 复核结论 / 下一步 |
|---|---|---|---|
| [#98](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/98) Rust第一切片 | P2 | in-progress | D-019 A 有意冻结；原真实迁移/双模式/实际Criterion标准未交付。不是崩溃现场，不重置、不关闭、不启动。 |
| [#109](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/109) OTLP/Jaeger | P2 | blocked | 本轮 command -v docker 仍exit1；无已知已授权Docker主机。需先有实际可用且授权的运行环境，再验证metrics接收/真实trace/UI；不得以console替代、不得擅增服务。 |
| [#96](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/96) M7 Epic | P2 | needs-info | D-019 A 继续有效；B/C无新答复，保持冻结；Epic不计分母。 |
| [#102](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/102) ABI/CI矩阵 | P2 | needs-info | 依赖#98未完成，且CI矩阵扩展未授权；不把abi3标记当双版本实际执行。 |
| [#100](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/100) Qdrant | P3 | needs-info | 新服务/模型/资源边界未授权；不自动下载或启动。 |
| [#101](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/101) SSE摘要 | P3 | needs-info | 产品入口、LLM费用与数据范围未定；不得发付费请求或改认证。 |
| [#59](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/59) 产品需求 | P2 | needs-info | 无具体新需求；#60既有工程债调研不等于产品规格。已在Issue回应TS既有授权可推进，不重复询问D-012输入方式。 |

治理检查：无重复待办、无open auto-discovered、无缺优先级项；P0/P1均为0。#100/#101仅处于尚未结束的M7，不满足“连续两个Milestone未动”的关闭条件。存量冻结项未被强行改ready，#98现场未被重置。无open PR。

## 回应 Executor 信号与决策

1. **队列空**：本轮完成验收并补两项真正可执行任务，不重复启动整轮调研、不用文档循环凑数量。
2. **“测试枯竭需用户方向”**：更正为“已排入前三批的行为目标已补齐”，不能由覆盖率或该批清空推出全仓无可测行为；更不能忽略D-009已批准的TS方向。D-034记录证据与恢复的单切片边界。
3. **_persist 无catch**：本轮只读确认tabs.js:52–54无catch；这是潜在存储故障风险，不是已复现缺陷。不凭风格不一致增加容错/事务/重试任务，后续有真实错误和预期恢复契约再定级；回应已留#131验收comment。
4. **文档账滞后**：#134一次性收尾并记录测量时点，历史与当前分离；不因下一次文档自身关闭无限派生同内容任务。
5. **分支纪律**：#130领取comment声称WORKFLOW=trunk，但ENV不含该设置。代码验收与流程偏差分开记录；本轮与下一轮恢复默认分支，不rewind/force push。
6. **pending**：无；D-019/D-023默认A已转正，无新用户答复且无同一问题重问。D-009授权足够执行本切片，不需要用户再批准。

## Milestone 实际计数

- M6：10/10 CLOSED，milestone仍OPEN（0 open成员）；成功信号1/3，串行<30s与完整CI<240s仍未达。D-023 A冻结，不降标、不冒称收敛。
- M7：6/11 CLOSED，5 OPEN；done #97/#99/#103/#104/#105/#108，未完成#98/#100/#101/#102/#109。D-019 A冻结，#96 Epic不计分母。
- #110–#134均未设milestone；本轮#133是D-009既有方向的有界恢复，不擅立新的Milestone或污染M6/M7分母。

## 本轮验证与握手

- 起点main@3cd52b5；fetch/pull exit0（Already up to date），无未提交工作；#130–#132之后的提交只涉及.agent快照。
- 前端命令（ENV所列Node22 PATH）：`npx vitest run tests/app-store.test.js tests/tabs-store.test.js`、`npm run test:run`、`npm run test:coverage`、`npm run lint` 全exit0；定向50通过，全量47/321；All83.79/77.33/37.55/83.79。
- TS只是下一执行任务，本轮**没有**安装依赖、迁移代码、编写测试/验证脚本。npm view元数据证明所选TS5.9.3/parser8.46.2与Node22/ESLint9兼容，不代表新typecheck已跑通。
- 未跑后端fast gate/integration/external/build：本轮只读前端验收，无生产代码改动，交付提交CI五项已实际查询成功。不把历史后端数字冒充本轮实跑。
- 下一棒只按 #133→#134 领取，串行最多一个in-progress；每项真实验证后交付固定字段报告并转in-review，不自行close；刷新自己拥有的STATE/HANDOFF并追加实际执行日DIARY，.agent独立提交。

# TASKS — GitHub Issue 本地镜像

> 更新于 2026-10-24 规划轮，Planning 轮 **整体重写**（Issue 为权威来源，每轮重新拉取真实状态）。本轮验收：#127/#128/#129 全部通过关闭（证据见「本轮验收账」与各 Issue comment）；新建 #130/#131/#132。gh 可用、账号 zhangjszs、scope repo+workflow，未降级、未重复创建。
> 生命周期标签：`ready` / `in-progress` / `in-review` / `blocked` / `needs-info` / `done`；优先级 `priority:P0`–`P4`。
> Executor：先改 Issue 标签/comment，再同步本行；只改执行状态与报告，不改任务范围。完整规格/非目标/checklist 见对应 Issue。

## 今日队列（2026-10-24 执行轮 · 建议顺序；3 项，#132 依赖前两项）

| 顺序 | Issue / 目标 | P | 状态 | 可直接执行的边界与完成证据 |
|---|---|---|---|---|
| 1 | [#130 补齐 frontend/src/stores/app.js 主题切换与侧栏行为测试](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/130) | P3 | ready | 新增 `tests/app-store.test.js`（真实 pinia + 真实 localStorage/DOM）：无存储初始化、dark 恢复初始化、toggleTheme 双向（localStorage/className/dark class）、setTheme、toggleSidebar。**明确不做**：不改 app.js/组件/既有测试；不 mock document/localStorage；不测组件消费方；不动 CI/依赖、不设阈值。验收：单文件 exit 0 且 ≥5 用例；`test:run` 全绿且 ≥272；app.js Lines ≥90%、Funcs 100%（4/4）、Branches ≥75%；`lint` exit 0；diff 仅新测试文件；五组场景显式断言。 |
| 2 | [#131 补齐 frontend/src/stores/tabs.js 多标签工作区状态机测试](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/131) | P3 | ready | 新增 `tests/tabs-store.test.js`（router 用 `{push: vi.fn()}` stub）：存储恢复/损坏回退、addTab 三路径（no-op/已存在激活/新增含 query 序列化）、closeTab（Home 拒绝/未知 no-op/关激活取邻 tab + push）、closeOtherTabs、closeAllTabs、setActiveTab、reorderTabs（0 号保护）、updateTabPath、resetTabs（#20 两键移除）、持久化往返。**明确不做**：不改 tabs.js/组件/既有测试；不用真实 vue-router；不测组件层；getItem 抛错 catch 不可自然构造则如实列为未覆盖。验收：单文件 exit 0 且 ≥10 用例；`test:run` 全绿且 ≥ 上一步基线；tabs.js Lines ≥90%、Funcs ≥90%、Branches ≥75%；`lint` exit 0；diff 仅新测试文件；11 组场景显式断言。 |
| 3 | [#132 刷新 docs/TEST_PERF.md §7.1/§7.5（#127–#129 验收关闭与 #130/#131 新基线）](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/132) | P4 | ready | **依赖 #130/#131 之后执行。** §7.1 补 #127（ffe4c5b）/#128（4cb2519）/#129（4d00f9c）三行（已验收关闭）；§7.5 「待验收」→「已验收关闭」；新增本执行轮实测段（沿用 #129 裁定的双段并存口径，历史段不改）；日期刷新执行当日。**明确不做**：不改 README/代码/测试/CI/依赖；不重写历史段；不设阈值。验收：diff 仅该文档；三行提交号经 git 核对；`grep "待验收"` 无匹配；新段数值与当次 coverage 输出逐项一致。 |

队列说明：P0=0、P1=0、P2=0、P3=2、P4=1；共 3 项 ready。选题依据 = 验收 #127/#128 后实测覆盖率仅剩两组真实行为缺口：`stores/app.js` 71.79% 行 / 25% 函数（toggleTheme/setTheme/toggleSidebar 未测，未覆盖行 16-19/22-23/29）、`stores/tabs.js` 70.93% 行 / 45.45% 函数（addTab→updateTabPath 整块 57-162 未测），以及验收后的既定文档账滞后。三项均属测试/文档卫生（契约 6.1 Planner 权限），本地可验证、可回滚，不触碰契约 1.10 红线（D-033）。

已排查但**本轮不入 ready** 的候选：
- 8 个前端 API 包装模块（alert/content/favorites/platform/predict/propagation/report/user，行覆盖 0%）：声明式薄封装，mock 断言调用参数等于复述源码，属非目标；跨端路由契约校验需另立规格。
- `src/main.js` 与 `src/App.vue`（0%）：应用入口/根组件壳，豁免。
- `tests/test_db.py:95` 的 `assert True`：integration-only，本机无 MySQL，待有 MySQL 的集成批次。
- CJK 字体 `Glyph ... missing` 告警：环境/字体依赖，D-027 非目标。
- **枯竭预警**：#130/#131/#132 交付后，前端按既定口径已无真实可测对象剩余；后续选题需用户方向输入（见 PLAN「下一阶段」）。

## 等待验收（in-review）

- 无。#127/#128/#129 已于 2026-10-24 规划轮全部验收通过关闭（见下「本轮验收账」）。

## 阻塞 / 待决策（全部保留，不可领取实现）

| Issue | P | 状态 | 阻塞事实 / 下一步 |
|---|---|---|---|
| [#98 Rust 第一切片](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/98) | P2 | in-progress（M7） | 2026-10-16 首次验收失实后 reopen；原生产迁移、既有用例双 backend、真实 Criterion 标准仍留本 Issue。D-019 默认 A 生效后继续冻结；保持现场不重置，下一棒不得领取。状态超 24h 属有意冻结，不作「疑似中断」处理。 |
| [#109 OTLP metrics 接收与 Jaeger 展示](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/109) | P2 | blocked（M7） | 本机无 Docker、无已知已授权 Docker 主机；console smoke 不替代真实 profile/UI 验收。解除环境阻塞后再验证，禁止自行新增 metrics 服务/长期成本。 |
| [#96 M7 候选 Epic](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/96) | P2 | needs-info | D-019 于 2026-10-18 默认转正 A = 暂停 M7 扩展。B/C 未批准；Epic 不计入分母，保持冻结。 |
| [#102 ABI/CI 矩阵](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/102) | P2 | needs-info（M7） | 待 D-019 B/C 授权，且 #98 未 done；不得以 abi3 标记代替 3.11/3.12 双实现执行。 |
| [#100 Qdrant 语义搜索候选](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/100) | P3 | needs-info（M7） | 新服务/模型与资源边界未授权；不得默认下载模型、启动 Qdrant 或返回假成功。 |
| [#101 SSE 摘要候选](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/101) | P3 | needs-info（M7） | 产品入口、LLM 成本与数据范围未定；不得变更认证模型或发出付费请求。 |
| [#59 产品功能需求收集](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/59) | P2 | needs-info | D-012 默认 A 有效；#100/#101 是候选而非用户已确认需求，本轮不重复追问输入方式。 |

## 本轮验收账（2026-10-24 规划轮）

- **#127（P3，user.js 登录态补测）：通过 → done/CLOSED。** 独立复跑：全量 45 files / 271 tests 全绿；lcov 核对 user.js LH/LF 97/99（97.97%）、BRH/BRF 31/38（81.57%）、FNH/FNF 7/7（100%）；`lint` exit 0；`git show --stat ffe4c5b` 仅新增 236 行测试文件；关键断言抽查一致（未认证零调用 :90-91、编码跳转 :179、%2Fhome 回退 :190）；CI 5/5 success。验收 comment 6383749022。
- **#128（P3，chinaMap 单例/重试补测）：通过 → done/CLOSED。** 独立复跑：全量 45/271 全绿、stderr 0；lcov 核对 chinaMap.js 全 100%（26/26、6/6、1/1）；六场景断言抽查一致（registerMap 一次 :57-58、promise 身份 :70、HTTP 503 :96）；`lint` exit 0；`git show --stat 4cb2519` 仅新增 127 行测试文件；CI 5/5 success。验收 comment 6383749667。
- **#129（P4，TEST_PERF 刷新）：通过 → done/CLOSED（含歧义裁定）。** 独立核对：`git show --stat 4d00f9c` 仅 `docs/TEST_PERF.md`（+7/−2）；§7.1 三行提交号经 git 核对；`grep "转 in-review"` = 0；0% 清单含 App.vue；本机复跑 coverage All files 83.22/75.83/35.55/83.22 与 §7.5 新段逐项一致。CI：`4d00f9c` 的 integration 为 completed/cancelled（ci.yml `concurrency.cancel-in-progress` 被收尾提交取消，非失败，其余 4 项 success），树内容仅差 `.agent/` 的 `be068ad` 五项 check 全 success，以其为准接受。**歧义裁定**：43/252「保持不变」与「与当次一致」字面冲突，双段并存+时点标注裁定为正确处理并作为既定口径。验收 comment 6383752553。

## Milestone 实际计数（按 GitHub issue state，不凭报告/API 计数器）

- **M6 测试性能优化：10 / 10 CLOSED，未收敛；2026-10-20 依 D-023 默认 A 冻结**。milestone state=open、open_issues=0、closed_issues=10。成功信号 1/3：覆盖率达成（≥68.49%），串行 <30s 与完整 CI <240s 均未达（#112 证明为结构性差距）。B/C 需用户明确授权。
- **M7 候选与既有交付纠偏：6 / 11 CLOSED**。milestone state=open、open_issues=5、closed_issues=6。成员 11（#97/#98/#99/#100/#101/#102/#103/#104/#105/#108/#109，#96 为 Epic 不计分母）。done：#97/#99/#103/#104/#105/#108；OPEN：#98（in-progress 冻结）、#109（blocked）、#100/#101/#102（needs-info）。
- **#110–#132 不设 milestone**（仓库、测试与前端度量卫生，不计入任何成功信号分母，D-021/D-025/D-027/D-030/D-031/D-032/D-033）。

## 本轮已运行验证（Planner，只读；代码 HEAD 停在 Executor 交付 `4d00f9c`，规划提交仅动 `.agent/`）

- `git fetch --all --prune` + `git pull --rebase` → Already up to date；工作区干净。
- `gh issue list --state open` → 验收前 10 open：#127/#128/#129（in-review）、#98（in-progress）、#109（blocked）、#96/#100/#101/#102/#59（needs-info）；处理后三项关闭，#130/#131/#132 新建为 ready。
- 前端独立复跑：`npm run test:run` → 45 files / 271 tests 全绿；`npm run test:coverage` → exit 0，All files 83.22/75.83/35.55/83.22；lcov 逐项核对 user.js（97/99、31/38、7/7）与 chinaMap.js（26/26、6/6、1/1）；`npm run lint` exit 0。
- 文档核对：`git show 4d00f9c -- docs/TEST_PERF.md`；`grep -c "转 in-review"` = 0；`grep App.vue` 命中 §7.1 与 §7.5。
- 断言抽查：`grep` 两个新测试文件的关键显式断言（详见验收账）；`git diff --stat 4d00f9c..HEAD -- . ':(exclude).agent'` → 空（交付后仅 `.agent/` 提交）。
- CI：`ffe4c5b`、`4cb2519`、`be068ad` 五项 check 全 completed/success；`4d00f9c` 4/5（integration cancelled，见验收账）。
- 未跑（本轮无需）：后端 fast gate（本轮仅前端/文档改动，沿用 2026-10-21 基线 native 1495/69/196、fallback 1493/71/196）、integration/external（外部依赖）、`npm run build`（无源改动，CI frontend-fast 已覆盖）。

## 给 Executor 的握手要求

- 接手先按真实 Git/Issue 核对 STATE/HANDOFF/ENV，并在 `.agent/DIARY/<当日>.md` 追加当日记录（严格 append-only，已写入的行不得修改）。
- 本轮领取顺序建议 #130 → #131 → #132；每项完成后按契约 1.7 在 Issue comment 提交执行报告并转 in-review，**绝不自行 close**。容量不足时按顺序完成，未领取项保持 ready 并写明原因。
- 严格按各 Issue「明确不包含」执行：只新增测试文件/只改 `docs/TEST_PERF.md`；不改生产源码、不改现有测试、不设覆盖率阈值、不动 `ci.yml` 与依赖。
- #98/#109/#96/#100/#101/#102/#59 保持冻结/阻塞/needs-info，不启动 M7 扩展、不改 M6 阈值、不做 CI 拓扑改造。
- `.agent/` 变更与代码/文档变更严格分属不同 commit（`chore(agent): ...`）。

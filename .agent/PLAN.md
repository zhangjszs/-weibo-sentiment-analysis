# PLAN — 开发路线图

> 规划 Agent 维护，每次会话滚动更新。执行 Agent 只读不写本文件。
> 方向类决策记录在 DECISIONS.md，本文件引用其编号（D-xx）。
> 更新于 2026-10-19，Planning 轮（验收 2026-10-19 执行轮交付 #113，编排下一执行轮 #114/#115/#116 队列）；内容提交在 main、代码 HEAD `0e4c09f`（与远端同步）。
> 10-19 交付 #113 已独立复跑验收关闭；GitHub Issue 为权威来源。

## 当前方向

**验收闭环，主线停留在 D-023 用户决策门上；编入 3 项安全卫生的日常任务推进工程健康度。** 10-19 交付 #113 全部通过独立复跑验证：`test_send_invalid_email` 真实出站消除（探针证实 `socket.getaddrinfo` 0 次调用，单测 call 耗时 0.01s），`TEST_PERF §7.1` 文档状态准确对齐，CI 四 job 全绿，无生产代码改动，Issue #113 已验收关闭。

关键事实：**M6 仍无法靠「继续做任务」收敛**——10/10 成员 CLOSED，但两个成功信号（串行 fast gate <30s、完整 CI <240s）为已在 #112 量化证明的**结构性差距**；在当前 1560 用例下 collection 固定占 ~11s，串行净值 ~30s，无法仅靠测试层微调闭合；CI 瓶颈在于 integration 串行等待 backend-fast 及 wheel 解包方差，解耦属契约 1.10 红线。**M6 是否收口 = D-023 用户裁决，不是 Planner 能自行降标的工程任务**。D-023 今日处于 pending 第 2 天，继续按默认方案 A 先行（M6 保持 open、不降低阈值、不投入高成本改造）；M7 扩展继续由 D-019 A 全量冻结。

**本轮拒绝虚构红线工作，编排 3 项纯工程与测试卫生任务进今日队列**：针对后端 fast gate 暴露的 `test_model_improvements.py` 假绿吞异常反模式与 `PytestReturnNotNoneWarning`（#114）、Celery eager 测试结果存储告警（#115）、以及前端 Element Plus 3.0 前向兼容（`<el-radio-button>` 与 `<el-checkbox>` 的 `label` 废弃警告收敛，#116）。任务均过 4.2 门禁，保持 3 项（符合「2–5 个、宁缺毋滥」）。

## 今日目标（下一执行轮）

- #114：消除 `test_model_improvements.py` 的 6 处 `PytestReturnNotNoneWarning` 与假绿吞异常逻辑，补齐核心数据结构断言。
- #115：在 `tests/conftest.py` 中补全 Celery eager 结果存储配置（`task_store_eager_result=True`），消除任务状态测试中的 Celery `RuntimeWarning`。
- #116：收敛前端 `report.vue`、`Header.vue`、`PredictInput.vue`、`spider.vue` 中绑定值的 `label` 属性为 `value`，消除 Element Plus 3.0 废弃警告。
- 不新增 M7 扩展、不改 M6 阈值、不改 CI 拓扑架构、不关闭 #98/#109/#96/#100/#101/#102/#59。

## 当前 Milestone：M6 测试性能优化（成员进度：10 / 10 CLOSED；成功信号：1 / 3 达成，未收敛）

### 目标与验收

- 成员：#88–#95 + #106/#107（全部 CLOSED）。成员关闭 ≠ 里程碑收敛。
- 测试保障面不缩水；新增可选模块后用例按真实行为增减，每项变化须有解释。
- 成功阈值**不改**（Planner 无权降标，D-017）：串行无覆盖率 stable <30s、完整 CI 关键路径 <240s、branch ≥68.49%。

| 成功信号 | 最新已观察事实 | 验收状态 |
|---|---|---|
| 本地串行无覆盖率稳定 <30s | Planner 2026-10-19 本机复跑 native **36.98s**（1494/69/196，wall 39.32s）；#112 记录 40.62s；collection 固定 ~10–11s | **未达成**：结构性差距，非局部微调可闭合（见 §6.2） |
| 完整 CI 关键路径 <240s | 近期 5 run created→最后 job 完成 247s–329s；瓶颈 = integration 串行依赖 backend-fast + install 解包方差 | **未达成**：解耦属红线，待 D-023 |
| branch ≥68.49% | 复跑基线 **68.5259%**（JSON 9268/13077）；CI 68.62%–68.63%；本轮无生产代码改动，不重跑 | **达成**，余量薄（+0.036pp） |

### 执行队列（给 Executor 的建议顺序，3 项）

1. **#114 消除 test_model_improvements.py 的 PytestReturnNotNoneWarning 与假绿吞异常反模式**（P3，ready）——移除 6 处测试函数末尾 `return <obj>`；移除 `test_social_media_features` 与 `test_data_augmentation` 中的 `try...except Exception: return False` 假绿反模式；补齐针对性有效断言；保持脚本直接运行与 500 条训练抽样参数。
2. **#115 conftest 补全 Celery task_store_eager_result 配置以消除 eager 任务查询告警**（P4，ready）——在 `tests/conftest.py` 的 `app` fixture 补全 Celery eager 存储配置；验证 `/api/tasks/<task_id>/status` 消除 Celery `RuntimeWarning`。
3. **#116 收敛前端单选与复选组件的 Element Plus 3.0 label 废弃警告**（P3，ready）——在 `report.vue`、`Header.vue`、`PredictInput.vue`、`spider.vue` 中将绑定值的 `<el-radio-button>` 和 `<el-checkbox>` 的 `label` 属性替换为 `value`；保留按钮文本 slot 与表单项原有 label。

**队列 3 项的理由**：M6 收口与 M7 扩展均处于冻结与待决策门中。为避免阻塞开发循环，本轮从 fast gate 与 vitest 实测告警中提炼出 3 项高内聚、零互斥、高可测性的工程与测试质量任务，均通过 4.2 门禁，处于 [2, 5] 容量区间内。

### 完成信号（Success signal）

- #114 交付后：`test_model_improvements.py` 6 passed，无 `PytestReturnNotNoneWarning`，无假绿吞异常；
- #115 交付后：任务状态测试中 Celery `RuntimeWarning` 消除；
- #116 交付后：前端 190 tests 全绿，stderr 中零 Element Plus `label act as value` 警告，lint 与 build 全绿；
- fast gate 与 CI 保持全绿。
- D-023 得到用户答复后，M6 才能被事实驱动地收口（选项 C）或在逐项授权下继续投入（选项 B）。

### 明确非目标（Non-goals）

- 不重启 #90 的 uv / venv 整包缓存、#92 的 session 缓存、xdist/randomly/socket 转默认门禁（D-013/D-014/D-016/D-019/D-024）。
- 不新开 Rust 生产消费者、第二切片、Qdrant、LLM 流式入口、新 metrics 服务、wheel 自动发布、CI 矩阵扩展（D-019 A）。
- 不为覆盖率数字添加 getter/mock/源文本测试；不调整 omit/exclude/branch 统计方式。
- 不升级前端 `package.json` 依赖大版本；不改动组件视觉样式与后端契约。
- **不自行降低 M6 成功信号**——那是 D-023 的用户权限。

## 已知阻塞与依赖

- **D-023（pending，今日第 2 天询问）**：M6 两个未达阈值如何处置。默认 A = 保持 M6 open、不改阈值、不投入高成本改造（先行中）。**B（追加优化预算，L4 CI 解耦 / L3 venv 缓存，触红线需逐项批）/ C（接受现状关闭 M6 并记录差距）均需用户明确答复。** 若明日仍无答复，将于 2026-10-20 按 6.3 默认转正为 A。
- **#98**：in-progress 父任务，剩余真实生产迁移与完整双模式验收未交付；D-019 默认 A 生效后继续冻结，保持现场不重置、下一棒不得领取。
- **#109**：本机无 Docker、无已知已授权 Docker 主机；OTLP metrics/Jaeger 真实验收 blocked。
- **#96 / #100 / #101 / #102**：M7 方向、Qdrant/LLM、ABI/CI 矩阵均未获 D-019 B/C 授权，保持 `needs-info` 冻结。
- **#59**：D-012 默认 A 继续有效；#100/#101 是候选而非用户已确认的产品需求。

## 下一阶段

- 今日 3 项交付验收后：若 D-023 得 C → 正式收口 M6（记录两项结构性差距、milestone 关闭）、转向仓库卫生或新功能；若得 B → 就 L4/L3 逐项过 4.2 门禁并申请红线授权后再排；若持续无答复 → 明日按 6.3 默认 A 连续 3 天转正（M6 保持 open、不追加投入）。
- 若 D-019 未来被用户改为 B/C：仍需把产品数据、成本、依赖边界补成可执行规格后逐项过 4.2 门禁。

## 已放弃的方向

- 登录验证码实施（D-02：暂缓）。
- docs/database 归档 SQL 列名同步（D-03：保留不动）。
- #90 的 uv 迁移 / venv 整包缓存（D-013/D-016：不重启）。
- #92 的 session 训练缓存与标 slow 移出 gate（D-014）。
- #84 的测试环境 el-form 短路修复（真实浏览器证实生产正常，保持关闭）。
- pytest-socket 全局禁网（D-024：3 处来源可控，全局封锁需白名单且掩盖 Redis 类真实等待）。
- 把全唯一数据称 90% 重复、把 compile-only 称 Criterion 运行、把 console 称 Jaeger 验收、把单 job 时长称完整关键路径：均不可作为完成依据。
- M7 扩展（Rust 新切片/Qdrant/LLM/ABI 矩阵/自动发布）：D-019 默认 A，暂停。

## 给 Executor 的指令（不超过 2 句）

- 本轮依次领取 #114、#115、#116：严格按 Issue 验收标准修复测试告警与组件属性前向兼容，不改生产业务逻辑与依赖版本。
- 收尾按 D-022 编写当日 `DIARY` 并更新 STATE/HANDOFF/ENV，在 Issue comment 提交执行报告转 in-review，绝不自行 close Issue。

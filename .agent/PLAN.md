# PLAN — 开发路线图

> 规划 Agent 维护，每次会话滚动更新。执行 Agent 只读不写本文件。
> 方向类决策记录在 DECISIONS.md，本文件引用其编号（D-xx）。
> 更新于 2026-10-21，Planning 轮（无新增 in-review；结转 #120/#121/#122；更正 #121 规格）；内容提交在 main，代码 HEAD `afee0c4`（与远端同步）。

## 当前方向

**M6 在 D-023 默认转正 A 下正式冻结，M7 继续受 D-019 A 冻结；主线维持可验证的代码、测试与文档卫生，不触碰任何红线。** 2026-10-20 会话 2 交付的 #117/#118/#119 已在上轮验收关闭（三个 Issue 均为 CLOSED/done）；此后 Executor 未再运行，ready 队列中的 #120/#121/#122 未被领取，本轮原样结转并发起执行。

事实不变：M6 成员 10/10 CLOSED，但成功信号仅 1/3（覆盖率达成；串行 <30s、完整 CI <240s 未达），#112 已证明是结构性差距。D-023 于 2026-10-20 连续 3 天无用户答复，按 6.3 默认转正为 **A：M6 保持 open、不改阈值、不追加高成本或红线投入**；B（授权 L4 CI 解耦等）与 C（接受现状关闭 M6）均需用户明确答复。M7 扩展继续受 D-019 A 冻结。

今日队列沿用上轮 3 项：#120（前端仅存 1 处 Sass `@import` 弃用告警）、#121（模型评估稀疏类抽样 `UndefinedMetricWarning` 显式指定 `zero_division=0`）、#122（活文档 `docs/TEST_PERF.md` §7.1 补齐 #113–#119 交付状态）。均 P4，不设 milestone（延续 D-021/D-025/D-027）。本轮已按实测更正 #121 的测试入口与验收口径（不绑定不可复现的固定告警计数，见 D-028）。

## 今日目标（2026-10-21）

- #120：将 `frontend/src/styles/index.scss:8` 的 `@import` 迁移至 `@use './animations.scss' as *;`，消除 Dart Sass 3.0 弃用警告。
- #121：在 `trainModel.py:249` 与 `hyperparameter_optimizer.py:428` 显式指定 `zero_division=0`，消除 `UndefinedMetricWarning`。
- #122：在 `docs/TEST_PERF.md` §7.1 补齐 #113–#119 的已完成状态与真实摘要，使活文档与 GitHub Issue 同步。
- 不改生产业务行为、不改 schema、不改依赖版本；不触碰 #98/#109/#96/#100/#101/#102/#59。
- 收尾按契约写当日 DIARY、刷新 STATE/HANDOFF，并在 Issue comment 提交执行报告转 in-review（绝不自行 close）。

## 当前 Milestone：M6 测试性能优化（成员进度：10 / 10 CLOSED；成功信号：1 / 3 达成；2026-10-20 由 D-023 A 冻结，未收敛）

### 目标与验收

- 成员：#88–#95 + #106/#107（全部 CLOSED）。成员关闭 ≠ 里程碑收敛。
- 测试保障面不缩水；新增可选模块后用例按真实行为增减，每项变化须有解释。
- 成功阈值**不改**（Planner 无权降标，D-017）：串行无覆盖率 stable <30s、完整 CI 关键路径 <240s、branch ≥68.49%。

| 成功信号 | 最新已观察事实 | 验收状态 |
|---|---|---|
| 本地串行无覆盖率稳定 <30s | Planner 2026-10-21 本机复跑 native **39.45s**（1495/69/196，92 warnings）；10-20 为 38.76s / 37.55s；#112 记录 40.62s；collection 固定 ~10–11s | **未达成**：结构性差距，非局部微调可闭合（见 #112 与 TEST_PERF §6.2） |
| 完整 CI 关键路径 <240s | 近期 5 run created→最后 job 完成 247s–329s；瓶颈 = integration 串行依赖 backend-fast + install 解包方差 | **未达成**：解耦属红线；D-023 已定 A，不投入 |
| branch ≥68.49% | 2026-10-19 复跑基线 **68.5259%**（JSON 9268/13077）；CI 68.62%–68.63%；10-20/10-21 无生产语义改动，未重跑 | **达成**，余量薄（+0.036pp） |

### 执行队列（给 Executor 的建议顺序，3 项）

1. **#120 消除前端 Sass @import 废弃警告（Dart Sass 3.0 兼容）**（P4，ready）——替换 `frontend/src/styles/index.scss:8` 的 `@import` 为现代模块化 `@use './animations.scss' as *;`；`npm run build` 不再输出 `DEPRECATION WARNING [import]`。
2. **#121 模型训练与评估中的 classification_report 显式指定 zero_division=0**（P4，ready）——在 `trainModel.py:249` 与 `hyperparameter_optimizer.py:428` 调用时传入 `zero_division=0`；以 grep 核对 + 定向测试 `tests/test_model_improvements.py`、`tests/test_model_pipeline.py` 为准，不绑定固定告警数。
3. **#122 刷新 TEST_PERF.md §7.1 议题总表并补齐 #113–#119 交付状态**（P4，ready）——追加 #113 至 #119 的真实 done 记录与准确摘要，标注刷新日期为 2026-10-21。

**队列 3 项的理由**：与上轮一致；Executor 上轮未领取，故原样结转，不新增任务以免制造伪工作。三项均为小步、高可测、零风险任务，通过 4.2 门禁，符合 [2, 5] 容量。

### 完成信号（Success signal）

- #120 交付后：`npm run build` exit 0 且零 `DEPRECATION WARNING [import]`，lint 与 vitest 全绿。
- #121 交付后：两处 `classification_report` 均显式传 `zero_division=0`；定向测试 exit 0 且不再出现 `UndefinedMetricWarning`（该告警受随机划分影响，未触发时以代码核对为准）；fast gate 双模式 exit 0，不新增其他告警类别。
- #122 交付后：`docs/TEST_PERF.md` §7.1 完整包含 #113–#119，与 GitHub Issue 实际状态完全对齐。
- fast gate 双模式与 CI 保持全绿；D-023 A 不被改写，M6 阈值不动。

### 明确非目标（Non-goals）

- 不重启 #90 的 uv / venv 整包缓存、#92 的 session 缓存、xdist/randomly/socket 转默认门禁（D-013/D-014/D-016/D-019/D-024）。
- 不新开 Rust 生产消费者、第二切片、Qdrant、LLM 流式入口、新 metrics 服务、wheel 自动发布、CI 矩阵扩展（D-019 A）。
- 不为覆盖率数字添加 getter/mock/源文本测试；不调整 omit/exclude/branch 统计方式。
- 不升级前端 `package.json` 依赖大版本；不改动组件视觉样式与后端契约。
- 本轮不追第三方告警（circuitbreaker / seaborn 自身）与 CJK 字体 glyph 告警（环境/字体依赖，收益不明）。
- **不自行降低 M6 成功信号**——那是 D-023 的用户权限；B/C 未授权前不得启动。

## 已知阻塞与依赖

- **D-023（2026-10-20 默认转正 A）**：M6 保持 open、不改阈值、不追加高成本/红线投入。B（追加优化预算，L4 CI 解耦 / L3 venv 缓存）/ C（接受现状关闭 M6）仍需用户明确答复；用户随时答复即按其决定重议。
- **#98**：in-progress 父任务，剩余真实生产迁移与完整双模式验收未交付；D-019 A 生效后继续冻结，保持现场不重置、下一棒不得领取。
- **#109**：本机无 Docker、无已知已授权 Docker 主机；OTLP metrics/Jaeger 真实验收 blocked。
- **#96 / #100 / #101 / #102**：M7 方向、Qdrant/LLM、ABI/CI 矩阵均未获 D-019 B/C 授权，保持 `needs-info` 冻结。
- **#59**：D-012 默认 A 继续有效；#100/#101 是候选而非用户已确认的产品需求。

## 下一阶段

- #120/#121/#122 验收后，若用户仍无方向输入：下一轮继续从 fast gate / vitest / CI 的实测证据中提炼小批量卫生任务；若找不到通过 4.2 门禁的任务，**宁可保持空队列并等待用户，不制造伪任务**。
- 若用户授权 D-023 B/C 或给出 D-019 B/C：先补可执行规格并逐项过 4.2 门禁，红线事项单独确认后再排。
- 若用户给出产品需求（#59）：按 D-012 路径重新评估，不沿用未经确认的候选清单。

## 已放弃的方向

- 登录验证码实施（D-02：暂缓）。
- docs/database 归档 SQL 列名同步（D-03：保留不动）。
- #90 的 uv 迁移 / venv 整包缓存（D-013/D-016：不重启）。
- #92 的 session 训练缓存与标 slow 移出 gate（D-014）。
- #84 的测试环境 el-form 短路修复（真实浏览器证实生产正常，保持关闭）。
- pytest-socket 全局禁网（D-024：3 处来源可控，全局封锁需白名单且掩盖 Redis 类真实等待）。
- 把全唯一数据称 90% 重复、把 compile-only 称 Criterion 运行、把 console 称 Jaeger 验收、把单 job 时长称完整关键路径：均不可作为完成依据。
- M7 扩展（Rust 新切片/Qdrant/LLM/ABI 矩阵/自动发布）：D-019 默认 A，暂停。
- M6 阈值调整/高成本优化：D-023 默认 A 转正，冻结。

## 给 Executor 的指令（不超过 2 句）

- 依次领取 #120、#121、#122：替换 Sass @import、给 classification_report 显式传递 zero_division=0（按更正后的验收口径）、刷新 TEST_PERF 议题状态表，不改动任何生产业务语义与依赖版本。
- 收尾按 D-022 在当日 `DIARY` 追加会话记录并更新 STATE/HANDOFF/ENV，在 Issue comment 提交执行报告转 in-review，绝不自行 close。

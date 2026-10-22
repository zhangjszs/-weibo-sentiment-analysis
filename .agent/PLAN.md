# PLAN — 开发路线图

> 规划 Agent 维护，每次会话滚动更新。执行 Agent 只读不写本文件。
> 方向类决策记录在 DECISIONS.md，本文件引用其编号（D-xx）。
> 更新于 2026-10-22，Planning 轮：验收并关闭 #120/#121/#122（独立复跑全部通过 → done），新建今日队列唯一 ready 任务 #123（前端 vitest 覆盖率本地可见性，见 D-030）。

## 当前方向

**M6 依 D-023 默认 A 冻结、M7 依 D-019 A 冻结；主线维持可验证的代码、测试与文档卫生，不触碰任何红线。** 2026-10-21 执行轮交付的 #120/#121/#122 已在本轮独立复跑验收全部通过并关闭（三个 Issue 均 CLOSED/done，无 reopen、无报告失实）；ready 队列随之清空。

本轮从实测事实中只提炼出 **1 项** 通过 4.2 门禁、本地可验证、且不触碰契约 1.10 红线的卫生任务作为今日队列：**#123 为前端 vitest 建立本地覆盖率可见性**（`docs/TEST_PERF.md` §7.4 自 #93 起的遗留项——前端 190 测试目前零覆盖率数据，测试回归不可见）。#123 属测试策略（契约 6.1 Planner 权限），引入的 `@vitest/coverage-v8` 为 vitest 官方生态 devDependency、纯测试工具、可回滚；**「设阈值门禁 / 加 CI 步骤」两部分被明确排除**（属主要 CI/CD 流程变化 + 需用户授权，另立）。P3，不设 milestone（延续 D-021/D-025/D-027）。其余候选（`test_db.py` 的 `assert True`、integration 补用例、CJK 字体 glyph 告警）经排查不满足本地 ready 门禁或属既定非目标，见 TASKS.md「已排查但不入 ready」。

事实不变：M6 成员 10/10 CLOSED，但成功信号仅 1/3（覆盖率达成；串行 <30s、完整 CI <240s 未达），#112 已证明是结构性差距。D-023 于 2026-10-20 连续 3 天无用户答复，按 6.3 默认转正为 **A：M6 保持 open、不改阈值、不追加高成本或红线投入**；B（授权 L4 CI 解耦等）与 C（接受现状关闭 M6）均需用户明确答复。M7 扩展继续受 D-019 A 冻结。

今日队列为上轮 #120/#121/#122 验收关闭后的新一批：仅 #123 一项（前端 vitest 覆盖率本地可见性，P3，无 milestone）。队列保持宁缺毋滥：本轮未找到第二项能同时满足「本地可验证 + 不触碰红线 + 逐条可判定」的卫生任务，不堆 P1/P2 填充、不制造伪工作。

## 今日目标（2026-10-22）

- 验收并关闭 #120/#121/#122（已完成：独立复跑全部通过，标 done + CLOSED，验收 comment 见 TASKS.md 验收账）。
- #123：为前端 vitest 增加**仅本地可见性**的覆盖率度量——装 `@vitest/coverage-v8@3.2.7`（devDep，匹配已装 vitest）、`vitest.config.js` 配 `test.coverage`（v8 / all / include src/**）、`package.json` 增 `test:coverage` 脚本；**不设阈值、不动 CI、不改被测源码/用例**。
- 不改生产业务行为、不改 schema、不改运行时依赖版本、不改 CI 拓扑；不触碰 #98/#109/#96/#100/#101/#102/#59。
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

### 执行队列（给 Executor 的建议顺序，1 项 ready）

1. **#123 为前端 vitest 建立本地覆盖率可见性（reporter-only，无阈值门禁、不动 CI）**（P3，ready）——装 `@vitest/coverage-v8@3.2.7`（devDep）、`vitest.config.js` 配 `test.coverage`（v8/all/include src/**/reporter text+lcov）、`package.json` 增 `test:coverage`；**不写 `coverage.thresholds`、不改 `ci.yml`、不改被测源码或用例**。

**队列 1 项的理由**：#120–#122 关闭后 ready 清空；本轮实测仅 #123 满足 4.2 门禁且不触红线。宁可 1 项真实任务，不用伪任务凑满 [2,5]。

### 完成信号（Success signal）

- #123 交付后：`cd frontend && npm ci && npm run test:coverage` exit 0 并打印逐文件覆盖率表；生成 `coverage/`（含 lcov）且不入 git；现有 `test:run` 41/190、`lint`、`build` 结果不变；`ci.yml` 零改动、无 `coverage.thresholds`。
- fast gate 与 CI 保持全绿；D-023 A 不被改写，M6 阈值不动。

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

- #123 验收后若用户仍无方向输入：下一轮继续从 fast gate / vitest / 覆盖率数据（#123 产出后将首次可见）中提炼小批量卫生任务；若找不到通过 4.2 门禁的任务，**宁可保持空队列并等待用户，不制造伪任务**。
- 已识别但暂未达 ready 门的候选（须先补规格再过 4.2）：
  - `tests/test_db.py` 的 `assert True` 与 integration 层补用例（需外部 MySQL/Redis，归集成批次）；
  - 待 #123 产出基线后，若用户同意将覆盖率纳入 CI（属红线，需单独授权）或设定可维持的阈值，另立任务。
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

- 领取 #123：为前端 vitest 建立仅本地的覆盖率可见性（装匹配版 coverage-v8 devDep + 配 `test.coverage` + 加 `test:coverage` 脚本）；**不设 `coverage.thresholds`、不改 `ci.yml`、不改被测源码与用例**。
- 收尾按 D-022 在 `.agent/DIARY/2026-10-22.md` 追加会话记录并更新 STATE/HANDOFF/ENV，在 Issue comment 提交执行报告转 in-review，绝不自行 close。

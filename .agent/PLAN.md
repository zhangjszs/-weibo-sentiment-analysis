# PLAN — 开发路线图

> 规划 Agent 维护，每次会话滚动更新。执行 Agent 只读不写本文件。
> 方向类决策记录在 DECISIONS.md，本文件引用其编号（D-xx）。
> 更新于 2026-10-23，Planning 轮：验收并关闭 #123（独立复跑全部通过），基于首次可见的前端覆盖率基线编排今日队列 #124/#125/#126（见 D-031）。

## 当前方向

**M6 依 D-023 默认 A 冻结、M7 依 D-019 A 冻结；主线维持可验证的代码、测试与文档卫生，不触碰任何红线。** 2026-10-22 执行轮交付的 #123（前端 vitest 覆盖率可见性）已在本轮独立复跑验收通过并关闭（CLOSED/done，无 reopen、无报告失实，仅更正一处 registry 表述）。ready 队列原为空，本轮补齐 3 项。

本轮选题**首次由数据驱动**：#123 产出前端覆盖率基线（Stmts 80.55 / Branch 72.66 / Funcs 30.95 / Lines 80.55），暴露出两处真实薄弱面——`src/utils/index.js`（30.53% Stmts / 26.31% Funcs，14 个公开函数无直接用例）与 `src/api/request.js`（72.51% Stmts / 37.5% Funcs，错误分支与 401 登出未测）。据此立项 **#124（P3）** 与 **#125（P3）**；另因 `docs/TEST_PERF.md` §7.1 停在 #119、§7.4 仍称覆盖率“未配置”，立项 **#126（P4）** 文档刷新。三项均属测试/文档卫生（契约 6.1 Planner 权限），本地可验证、可回滚，不触碰契约 1.10 红线；均不设 milestone（延续 D-021/D-025/D-027/D-030）。

事实不变：M6 成员 10/10 CLOSED，但成功信号仅 1/3（覆盖率达成；串行 <30s、完整 CI <240s 未达），#112 已证明是结构性差距。D-023 于 2026-10-20 连续 3 天无用户答复，按 6.3 默认转正为 **A：M6 保持 open、不改阈值、不追加高成本或红线投入**；B（授权 L4 CI 解耦等）与 C（接受现状关闭 M6）均需用户明确答复。M7 扩展继续受 D-019 A 冻结。

**覆盖率阈值门禁与 CI 纳入仍未获授权**：#124/#125 只补行为用例，不设 `coverage.thresholds`、不改 `ci.yml`；两项如需推进，须用户单独授权后另立。

## 今日目标（2026-10-23）

- 验收并关闭 #123（已完成：独立复跑全部通过，验收 comment 6355206818）。
- #124：补齐 `src/utils/index.js` 未覆盖函数的单元测试；Stmts/Funcs/Lines ≥90%。
- #125：补齐 `src/api/request.js` 拦截器错误分支测试；Stmts/Lines ≥90%、Branch ≥85%。
- #126：刷新 `docs/TEST_PERF.md` §7.1/§7.4 并记录前端覆盖率基线。
- 不改生产业务行为、不改 schema、不改 CI 拓扑、不升级依赖；不触碰 #98/#109/#96/#100/#101/#102/#59。
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

### 执行队列（给 Executor 的建议顺序，3 项 ready）

1. **#124 补齐 `frontend/src/utils/index.js` 未覆盖函数的单元测试**（P3，ready）——新增独立测试文件，覆盖 14 个未测公开函数；不改生产源码、不改现有测试、不设阈值。验收：`test:run` 全绿且 ≥190；`src/utils/index.js` Stmts/Funcs/Lines ≥90%；`lint` exit 0；diff 仅新增测试文件。
2. **#125 补齐 `frontend/src/api/request.js` 拦截器错误分支测试**（P3，ready）——新增 `tests/request-error-paths.test.js`，覆盖业务码/HTTP 状态/超时/网络/配置错误与 401 登出防重入；不改 request.js、不改现有用例、不测 API 包装模块。验收：单文件可独立跑；request.js Stmts/Lines ≥90%、Branch ≥85%；diff 仅新增测试文件。
3. **#126 刷新 `docs/TEST_PERF.md` §7.1/§7.4 并记录前端覆盖率基线（#120–#123）**（P4，ready）——只改文档；§7.1 补四行、§7.4 删过时项、新增 §7.5 基线；不改 README（用户改写在途）、不重写历史数据。

**队列 3 项的理由**：#123 验收后 ready 清空；本轮从覆盖率基线中提炼出两组真实未测行为（纯函数 + 共享请求层）与一项已证实文档漂移。API 薄封装（8 个 0% 模块）经排查属 mock 复述源码，按非目标排除，不凑数。3 项均在本地可独立验证，任一失败不阻断其余。

### 完成信号（Success signal）

- #124/#125 交付后：`cd frontend && npm run test:coverage` exit 0；`src/utils/index.js` 与 `src/api/request.js` 达到各自验收阈值；`test:run` 全绿且总数 ≥190；`lint`/`build` 结果不变；`ci.yml` 零改动、无 `coverage.thresholds`。
- #126 交付后：`docs/TEST_PERF.md` §7.1 含 #120–#123 且状态 done，§7.4 无过时表述，§7.5 基线与实际输出一致。
- fast gate 与 CI 保持全绿；D-023 A 不被改写，M6 阈值不动。

### 明确非目标（Non-goals）

- 不重启 #90 的 uv / venv 整包缓存、#92 的 session 缓存、xdist/randomly/socket 转默认门禁（D-013/D-014/D-016/D-019/D-024）。
- 不新开 Rust 生产消费者、第二切片、Qdrant、LLM 流式入口、新 metrics 服务、wheel 自动发布、CI 矩阵扩展（D-019 A）。
- **不为覆盖率数字添加 getter/mock/源文本测试**：8 个声明式 API 包装模块（alert/content/favorites/platform/predict/propagation/report/user）不列入本批；`main.js` 属入口豁免。
- 不设 `coverage.thresholds`、不把覆盖率纳入 CI（需用户授权）；不调整 omit/exclude/branch 统计方式。
- 不升级前端 `package.json` 依赖大版本；不改动组件视觉样式与后端契约。
- 本轮不追第三方告警（circuitbreaker / seaborn 自身）与 CJK 字体 glyph 告警（环境/字体依赖，收益不明）。
- **不改动、不提交、不 stash 工作区中用户未提交的 `README.md`**。
- **不自行降低 M6 成功信号**——那是 D-023 的用户权限；B/C 未授权前不得启动。

## 已知阻塞与依赖

- **D-023（2026-10-20 默认转正 A）**：M6 保持 open、不改阈值、不追加高成本/红线投入。B（追加优化预算，L4 CI 解耦 / L3 venv 缓存）/ C（接受现状关闭 M6）仍需用户明确答复；用户随时答复即按其决定重议。
- **#98**：in-progress 父任务，剩余真实生产迁移与完整双模式验收未交付；D-019 A 生效后继续冻结，保持现场不重置、下一棒不得领取。
- **#109**：本机无 Docker、无已知已授权 Docker 主机；OTLP metrics/Jaeger 真实验收 blocked。
- **#96 / #100 / #101 / #102**：M7 方向、Qdrant/LLM、ABI/CI 矩阵均未获 D-019 B/C 授权，保持 `needs-info` 冻结。
- **#59**：D-012 默认 A 继续有效；#100/#101 是候选而非用户已确认的产品需求。

## 下一阶段

- #124/#125 验收后若用户仍无方向输入：继续以覆盖率报告为数据源，评估 `src/stores/user.js`（48.48%，initAuth 分支）与 `src/utils/chinaMap.js`（34.61%，单例/重试语义）；若仍找不到通过 4.2 门禁的任务，**宁可保持空队列并等待用户，不制造伪任务**。
- 覆盖率阈值与 CI 纳入仍待用户授权（红线）；未授权前不立项。
- 已识别但暂未达 ready 门的候选：`tests/test_db.py` 的 `assert True` 与 integration 补用例（需外部 MySQL/Redis，归集成批次）；前端 API 包装模块的跨端路由契约校验（需先设计规格，避免 mock 复述）。
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

- 按 #124 → #125 → #126 顺序领取；只新增测试文件或只改 `docs/TEST_PERF.md`，不改生产源码、现有测试、`ci.yml`、依赖与工作区未提交的 `README.md`。
- 每项完成后按契约 1.7 在 Issue comment 提交执行报告转 in-review，绝不自行 close；收尾写 `.agent/DIARY/2026-10-23.md` 并刷新 STATE/HANDOFF。

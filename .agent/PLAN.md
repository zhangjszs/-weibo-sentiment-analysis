# PLAN — 开发路线图

> 规划 Agent 维护，每次会话滚动更新。执行 Agent 只读不写本文件。
> 方向类决策记录在 DECISIONS.md，本文件引用其编号（D-xx）。
> 更新于 2026-10-24 规划轮，验收 #127/#128/#129（全部通过关闭），编排测试补强第三批 #130/#131/#132（见 D-033）。

## 当前方向

**M6 依 D-023 默认 A 冻结、M7 依 D-019 A 冻结；主线维持可验证的代码、测试与文档卫生，不触碰任何红线。** 2026-10-23 会话 2 交付的 #127/#128/#129 已在本轮独立复跑验收并全部通过关闭：user.js 达 97.97/81.57/100，chinaMap.js 全 100%，TEST_PERF 双段口径经裁定接受为既定处理方式（D-033）。

当前前端基线（本机实测）：**45 files / 271 tests 全绿**；`All files 83.22 / 75.83 / 35.55 / 83.22`。实测覆盖率仅剩两组真实行为缺口：`src/stores/app.js`（71.79% 行 / 25% 函数，toggleTheme/setTheme/toggleSidebar 三个主题侧栏函数未测）与 `src/stores/tabs.js`（70.93% 行 / 45.45% 函数，addTab→updateTabPath 整块多标签状态机未测）。据此编排 **#130（P3）**、**#131（P3）** 与文档账刷新 **#132（P4）**。三项均属测试/文档卫生，本地可验证、可回滚、不触碰契约 1.10 红线；均不设 milestone（延续 D-021/D-025/D-027/D-030/D-031/D-032）。

**选题枯竭预警（重要）**：本批交付后，前端按既定口径的可测对象将全部清空（8 个 API 薄包装属 mock 复述被排除；`main.js`/`App.vue` 壳层豁免）。测试卫生这条主线已接近尽头——后续推进需要用户方向输入（D-019 B/C、D-023 B/C、#59 产品需求），否则 ready 队列将无真实任务可排，**宁可空队列等待，不制造伪任务**。

事实不变：M6 成员 10/10 CLOSED，成功信号仅 1/3（覆盖率达成；串行 <30s、完整 CI <240s 未达，#112 已证明是结构性差距）。D-023 默认转正 A（M6 保持 open、不改阈值、不追加高成本或红线投入）；B/C 均需用户明确答复。M7 扩展继续受 D-019 A 冻结。**覆盖率阈值门禁与 CI 纳入仍未获授权**：#130/#131 只补行为用例，不设 `coverage.thresholds`、不改 `ci.yml`。

## 今日目标（2026-10-24 执行轮；本规划轮于当日运行，队列面向本日后续执行会话）

- #130：补齐 `src/stores/app.js` 主题切换与侧栏行为测试；Lines ≥90%、Funcs 100%（4/4）、Branches ≥75%。
- #131：补齐 `src/stores/tabs.js` 多标签工作区状态机测试（存储恢复/损坏回退/标签生命周期/路由联动/持久化往返）；Lines ≥90%、Funcs ≥90%、Branches ≥75%。
- #132：刷新 `docs/TEST_PERF.md` §7.1（补 #127–#129）与 §7.5（待验收表述 + #130/#131 新基线段，双段口径）；**依赖 #130/#131 之后执行**。
- 不改生产业务行为、不改 schema、不改 CI 拓扑、不升级依赖；不触碰 #98/#109/#96/#100/#101/#102/#59。
- 收尾按契约写当日 DIARY（会话 1 已有记录，追加不覆盖）、刷新 STATE/HANDOFF，并在 Issue comment 提交执行报告转 in-review（绝不自行 close）。

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

1. **#130 补齐 `frontend/src/stores/app.js` 主题切换与侧栏行为测试**（P3，ready）——新增 `tests/app-store.test.js`：无存储/dark 恢复初始化、toggleTheme 双向（localStorage/className/dark class）、setTheme、toggleSidebar；真实 localStorage/DOM，不 mock。验收：单文件 ≥5 用例 exit 0；`test:run` 全绿 ≥272；app.js Lines ≥90%、Funcs 100%、Branches ≥75%；`lint` exit 0；diff 仅新测试文件。
2. **#131 补齐 `frontend/src/stores/tabs.js` 多标签工作区状态机测试**（P3，ready）——新增 `tests/tabs-store.test.js`：存储恢复/损坏回退、addTab/closeTab/closeOtherTabs/closeAllTabs/setActiveTab/reorderTabs/updateTabPath/resetTabs、持久化往返；router 用 stub。验收：单文件 ≥10 用例 exit 0；tabs.js Lines ≥90%、Funcs ≥90%、Branches ≥75%；`lint` exit 0；diff 仅新测试文件；11 组场景显式断言。
3. **#132 刷新 `docs/TEST_PERF.md` §7.1/§7.5**（P4，ready，**依赖 #130/#131**）——§7.1 补 #127–#129 三行、§7.5 待验收表述刷新 + 新基线段（双段口径）；只改文档，不改历史段。

**队列 3 项的理由**：验收后 ready 清空；本轮从实测覆盖率中提炼出仅剩的两组真实未测行为（主题/侧栏状态 + 多标签工作区状态机），并承接每轮验收后的既定文档账滞后。API 薄封装仍按非目标排除；`main.js`/`App.vue` 豁免。前两项本地可独立验证，任一失败不阻断其余；#132 置于队尾避免基线反复重写。

### 完成信号（Success signal）

- #130/#131 交付后：`cd frontend && npm run test:coverage` exit 0；两文件达到各自验收阈值；`test:run` 全绿且总数 ≥272；`lint` 结果不变；`ci.yml` 零改动、无 `coverage.thresholds`。
- #132 交付后：§7.1 含 #127–#129 且状态/提交号准确；§7.5 无「待验收」、新段数值与当次输出逐项一致、历史段未被改动。
- fast gate 与 CI 保持全绿；D-023 A 不被改写，M6 阈值不动。

### 明确非目标（Non-goals）

- 不重启 #90 的 uv / venv 整包缓存、#92 的 session 缓存、xdist/randomly/socket 转默认门禁（D-013/D-014/D-016/D-019/D-024）。
- 不新开 Rust 生产消费者、第二切片、Qdrant、LLM 流式入口、新 metrics 服务、wheel 自动发布、CI 矩阵扩展（D-019 A）。
- **不为覆盖率数字添加 getter/mock/源文本测试**：8 个声明式 API 包装模块不列入；`main.js` 与 `App.vue` 豁免且不补测。
- 不设 `coverage.thresholds`、不把覆盖率纳入 CI（需用户授权）；不调整 omit/exclude/branch 统计方式。
- 不升级前端 `package.json` 依赖大版本；不改动组件视觉样式与后端契约；不改 README。
- 本轮不追第三方告警（circuitbreaker / seaborn 自身）与 CJK 字体 glyph 告警（环境/字体依赖，收益不明）。
- **不自行降低 M6 成功信号**——那是 D-023 的用户权限；B/C 未授权前不得启动。

## 已知阻塞与依赖

- **D-023（2026-10-20 默认转正 A）**：M6 保持 open、不改阈值、不追加高成本/红线投入。B（追加优化预算，L4 CI 解耦 / L3 venv 缓存）/ C（接受现状关闭 M6）仍需用户明确答复；用户随时答复即按其决定重议。
- **#98**：in-progress 父任务，剩余真实生产迁移与完整双模式验收未交付；D-019 A 生效后继续冻结，保持现场不重置、下一棒不得领取。
- **#109**：本机无 Docker、无已知已授权 Docker 主机；OTLP metrics/Jaeger 真实验收 blocked。
- **#96 / #100 / #101 / #102**：M7 方向、Qdrant/LLM、ABI/CI 矩阵均未获 D-019 B/C 授权，保持 `needs-info` 冻结。
- **#59**：D-012 默认 A 继续有效；#100/#101 是候选而非用户已确认的产品需求。

## 下一阶段

- **测试卫生主线接近枯竭（D-033 预警）**：#130/#131/#132 交付后，前端按既定口径无剩余真实可测对象。若用户仍无方向输入，下一轮执行侧大概率空队列待机——这是诚实状态，不是故障。
- 后续推进的三条真实路径，均需用户输入：① D-019 B/C（M7 扩展授权，#96/#98/#100/#101/#102 解冻）；② D-023 B/C（M6 追加优化预算或接受现状关闭）；③ #59 产品功能需求（D-012 路径）。
- 已识别但暂未达 ready 门的候选：`tests/test_db.py` 的 `assert True` 与 integration 补用例（需外部 MySQL，归集成批次）；前端 API 包装模块的跨端路由契约校验（需先设计规格，避免 mock 复述）——若用户希望继续本地自主推进，可对后者单独立项评估。
- 若用户给出任一方向输入：先补可执行规格并逐项过 4.2 门禁，红线事项单独确认后再排。

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

- 按 #130 → #131 → #132 顺序领取；只新增测试文件或只改 `docs/TEST_PERF.md`，不改生产源码、现有测试、`ci.yml`、依赖与 README。
- 每项完成后按契约 1.7 在 Issue comment 提交执行报告转 in-review，绝不自行 close；收尾向当日 `.agent/DIARY/2026-10-24.md` **追加**记录（会话 1 已有内容，不得改动）并刷新 STATE/HANDOFF。

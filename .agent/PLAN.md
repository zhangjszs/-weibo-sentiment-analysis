# PLAN — 开发路线图

> 规划 Agent 维护，每次会话滚动更新。执行 Agent 只读不写本文件。
> 方向类决策记录在 DECISIONS.md，本文件引用其编号（D-xx）。
> 更新于 2026-10-20，Planning 轮（验收 2026-10-20 执行轮交付 #114/#115/#116；D-023 默认转正 A；编排 #117/#118/#119）；内容提交在 main，代码 HEAD `68583cd`（与远端同步）。

## 当前方向

**M6 在 D-023 默认转正 A 下正式冻结，M7 继续受 D-019 A 冻结；主线转为可验证的仓库/测试卫生，不触碰任何红线。** 2026-10-20 验收确认 #114/#115/#116 全部通过：fast gate native 1494/69/196/149 warnings、frontend 190 tests、ruff 与 CI 四 job 全绿；#113–#116 连续四轮卫生任务均无生产行为回归。

事实不变：M6 成员 10/10 CLOSED，但成功信号仅 1/3（覆盖率达成；串行 <30s、完整 CI <240s 未达），#112 已证明是结构性差距。D-023 于 2026-10-20 连续 3 天无用户答复，按 6.3 默认转正为 **A：M6 保持 open、不改阈值、不追加高成本或红线投入**；B（授权 L4 CI 解耦等）与 C（接受现状关闭 M6）均需用户明确答复。M7 扩展继续受 D-019 A 冻结。

今日队列选择 3 项从实际告警与假绿残余中提炼的卫生任务：#117（项目自有 `datetime.utcnow()` 弃用，7 处）、#118（#114 遗留的脚本直跑恒返回 0）、#119（前端错误态测试 32 个 stderr 噪声块）。均过 4.2 门禁，P3/P4，不设 milestone（D-021/D-025）。

## 今日目标（2026-10-20）

- #117：消除项目自有 `datetime.utcnow()` 的 DeprecationWarning，保持 naive UTC 存储语义不变。
- #118：让 `test_model_improvements.py` 脚本直跑在用例失败时返回非零退出码。
- #119：收敛前端错误态测试的预期 `console.error` 噪声，保留错误态断言。
- 不改生产业务行为、不改 schema、不改依赖版本；不触碰 #98/#109/#96/#100/#101/#102/#59。

## 当前 Milestone：M6 测试性能优化（成员进度：10 / 10 CLOSED；成功信号：1 / 3 达成；2026-10-20 由 D-023 A 冻结，未收敛）

### 目标与验收

- 成员：#88–#95 + #106/#107（全部 CLOSED）。成员关闭 ≠ 里程碑收敛。
- 测试保障面不缩水；新增可选模块后用例按真实行为增减，每项变化须有解释。
- 成功阈值**不改**（Planner 无权降标，D-017）：串行无覆盖率 stable <30s、完整 CI 关键路径 <240s、branch ≥68.49%。

| 成功信号 | 最新已观察事实 | 验收状态 |
|---|---|---|
| 本地串行无覆盖率稳定 <30s | Planner 2026-10-20 本机复跑 native **39.37s**（1494/69/196，149 warnings）；10-19 复跑 36.98s；#112 记录 40.62s；collection 固定 ~10–11s | **未达成**：结构性差距，非局部微调可闭合（见 #112 与 TEST_PERF §6.2） |
| 完整 CI 关键路径 <240s | 近期 5 run created→最后 job 完成 247s–329s；瓶颈 = integration 串行依赖 backend-fast + install 解包方差 | **未达成**：解耦属红线；D-023 已定 A，不投入 |
| branch ≥68.49% | 2026-10-19 复跑基线 **68.5259%**（JSON 9268/13077）；CI 68.62%–68.63%；10-20 无生产语义改动，未重跑 | **达成**，余量薄（+0.036pp） |

### 执行队列（给 Executor 的建议顺序，3 项）

1. **#117 消除后端源码中 datetime.utcnow() 的 DeprecationWarning**（P3，ready）——替换 2 处直接调用与 5 处模型列默认值为等价的 naive UTC helper；保持数据库存储值语义与 schema 不变；补回归测试。
2. **#118 test_model_improvements.py 脚本直跑在用例失败时返回非零退出码**（P4，ready）——`main()` 统计失败并 `sys.exit(1)`；新增失败路径测试，不触发真实训练。
3. **#119 收敛前端错误态测试的预期 console.error 噪声**（P4，ready）——在 10 个受影响测试文件中 spy/mock `console.error` 并断言预期调用；全量 vitest stderr 零 `stderr |` 块。

**队列 3 项的理由**：M6 收口与 M7 扩展均处于用户决策门与冻结状态；本轮从 fast gate（149 warnings 中 3 条项目自有 utcnow）与 vitest stderr（32 块预期错误日志）实测证据中提炼，均为 test/production-equivalent 卫生任务，零互斥、高可测性，通过 4.2 门禁，符合 [2, 5] 容量。

### 完成信号（Success signal）

- #117 交付后：`grep` 无项目自有可执行 `utcnow`；定向测试零项目自有 `utcnow() is deprecated`；fast gate 警告数较 149 至少减少 3；naive UTC 回归测试通过。
- #118 交付后：失败路径测试证明 exit 1；成功路径脚本直跑 exit 0；fast gate 计数 +1。
- #119 交付后：前端 41 files / 190 tests 全绿，stderr 零 `stderr |` 块，lint exit 0。
- fast gate 双模式与 CI 保持全绿；D-023 A 不被改写，M6 阈值不动。

### 明确非目标（Non-goals）

- 不重启 #90 的 uv / venv 整包缓存、#92 的 session 缓存、xdist/randomly/socket 转默认门禁（D-013/D-014/D-016/D-019/D-024）。
- 不新开 Rust 生产消费者、第二切片、Qdrant、LLM 流式入口、新 metrics 服务、wheel 自动发布、CI 矩阵扩展（D-019 A）。
- 不为覆盖率数字添加 getter/mock/源文本测试；不调整 omit/exclude/branch 统计方式。
- 不升级前端 `package.json` 依赖大版本；不改动组件视觉样式与后端契约。
- 本轮不追第三方告警（circuitbreaker / seaborn / SQLAlchemy 自身）与 CJK 字体 glyph 告警（环境/字体依赖，收益不明）。
- **不自行降低 M6 成功信号**——那是 D-023 的用户权限；B/C 未授权前不得启动。

## 已知阻塞与依赖

- **D-023（2026-10-20 默认转正 A）**：M6 保持 open、不改阈值、不追加高成本/红线投入。B（追加优化预算，L4 CI 解耦 / L3 venv 缓存）/ C（接受现状关闭 M6）仍需用户明确答复；用户随时答复即按其决定重议。
- **#98**：in-progress 父任务，剩余真实生产迁移与完整双模式验收未交付；D-019 A 生效后继续冻结，保持现场不重置、下一棒不得领取。
- **#109**：本机无 Docker、无已知已授权 Docker 主机；OTLP metrics/Jaeger 真实验收 blocked。
- **#96 / #100 / #101 / #102**：M7 方向、Qdrant/LLM、ABI/CI 矩阵均未获 D-019 B/C 授权，保持 `needs-info` 冻结。
- **#59**：D-012 默认 A 继续有效；#100/#101 是候选而非用户已确认的产品需求。

## 下一阶段

- #117/#118/#119 验收后，若用户仍无方向输入：下一轮继续从 fast gate / vitest / CI 的实测证据中提炼小批量卫生任务；若找不到通过 4.2 门禁的任务，**宁可保持空队列并等待用户，不制造伪任务**。
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

- 依次领取 #117、#118、#119：严格按 Issue 验收标准替换 utcnow、修正脚本退出码、清理测试 stderr 噪声，不改生产业务语义与依赖版本。
- 收尾按 D-022 编写当日 `DIARY` 并更新 STATE/HANDOFF/ENV；同时更正 STATE 中已过期的 `home/index.vue` v-model 告警记录（Planner 实测 vitest stderr 匹配数为 0），在 Issue comment 提交执行报告转 in-review，绝不自行 close。

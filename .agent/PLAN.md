# PLAN — 开发路线图

> Planner 维护；Executor 只读。2026-10-24 同日接续验收/规划（接续 D-033 与执行会话 2/3），不冒充新的一天。决定见 D-034，完整规格与验收证据见 Issues / TASKS.md。

## 当前方向

1. **已完成本批验收**：#130/#131/#132 均通过并 done/CLOSED。独立复跑 47 files / 321 tests 全通过，lint exit0；app.js 全100%，tabs.js Lines97.67 / Funcs100 / Branch95.77，满足各自门槛；06b194e 的 GitHub 五项 check 全success。
2. **恢复已经批准但尚未实施的 TS 渐进迁移**：D-009 是用户明确授权，D-018/D-019 确认继续有效；#58 只交付策略文档，当前仍无TS依赖/tsconfig/真实TS文件。此前“后续只能等待用户新方向”的结论遗漏了这一事实，现由D-034更正。下一步不是新一轮调研，而是 #133 的一个完整生产切片：本地严格类型检查 + app store 实际迁移。
3. **边界不变**：M6 依D-023 A冻结、M7依D-019 A冻结；不新增服务/费用/CI矩阵，不改schema/认证/核心框架，不把类型检查或前端覆盖率加入CI。

当前独立实测：All files Stmts83.79 / Branch77.33 / Funcs37.55 / Lines83.79；app.js LH/LF39/39、FNH/FNF4/4、BRH/BRF10/10；tabs.js 168/172、11/11、68/71。执行会话2的原日志为 All Branch77.35、tabs Branch95.83；原日志真实存在，差异原因尚未定位，不当作已证明的舍入，也不以今天数字覆盖历史。

## 今日目标（面向下一执行会话，按真实执行日记录日报）

- #133：交付首个真实TS生产模块，保留主题/侧栏全部行为；`tsc --noEmit` 能检查 app.ts、类型负例能失败；运行时smoke能观察DOM/存储/侧栏，而不是只交空配置。
- #134：收尾 #130–#132 验收后的 TEST_PERF 状态账，记录执行时同次coverage快照；#133已交付则记录app.ts，否则如实记录app.js，不预支TS完成；历史数字与路径按测量时点保留。
- 测试基线不缩水，测试/类型检查/lint/build真实验证；固定字段执行报告、STATE/HANDOFF与append-only日报齐全。

## 当前授权切片：前端 TypeScript 渐进化（D-009；本切片验收进度 0 / 1，#133）

不是新立的GitHub milestone，不计入M6/M7。#134是配套文档收尾，不冒充生产迁移进度。

### 目标与验收

- 仅将 `frontend/src/stores/app.js` 迁为 `app.ts`，保留 `useAppStore` 与全部状态/动作，不留双实现或JS shim。
- typescript@5.9.3 + @typescript-eslint/parser@8.46.2 为本地开发依赖；元数据已核对Node22/ESLint9兼容，不是新增运行时服务。
- 最小strict/noEmit检查覆盖真实app.ts；既有JS/SFC保持未迁移，不声称全仓类型安全。`setTheme`仍接受string，theme/device不缩成未授权枚举。
- lint纳入TS、coverage纳入TS；不放松JS/Vue既有规则，不以扩展名迁移让文件从覆盖报告消失。
- 更新 `docs/FRONTEND_TS_MIGRATION.md` 的实际状态与过时建议；不原样照抄旧草案的全仓迁移清单或重复@types依赖。

### 执行队列（2项ready，建议顺序）

1. **[#133 启用本地 TypeScript 类型检查并迁移 app store 首个生产切片](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/133)**（P2，ready）。依赖#58/#130已关闭；允许改动文件、TS/ESLint/coverage边界、负例及真实模块smoke均在Issue中钉死。验收：npm ci/typecheck/lint/build成功；listFiles含app.ts；临时类型负例失败后恢复；既有app9用例、全量≥47/321；app.ts行≥90/函数100/分支≥75。
2. **[#134 收尾 TEST_PERF 验收状态并明确覆盖率快照时点](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/134)**（P4，ready）。只依赖已关闭的#130–#132，与#133无硬依赖；建议后执行以记录最新切片，#133阻塞仍可独立收尾。只改TEST_PERF，补三行、附验收事实、记录同次实际app.js或app.ts/tabs测量，保留历史；不把未交付TS写成完成，不因文档本身关闭再造同内容任务。

两项均通过ready门禁：硬依赖已完成、授权已知、范围明确、无产品取舍、逐条可验、风险可回滚。#133→#134仅为建议顺序，不以未来任务完成作为#134的ready前提；无其他ready任务。

### 完成信号（Success signal）

- #133：真实生产app.ts被tsc检查，错误消费者类型会被拒绝；主题/侧栏真实smoke、9个既有行为用例、全量测试、lint/build成功。TS源文件仍进入coverage。不是tsc --version、空项目或仅改扩展名。
- #134：历史数据未被覆盖，新数据与保存的同一次运行日志逐项一致；验收状态有真实Issue支持，不把实现完成写成已验收。
- 两项只在真实验证与报告完成后转in-review，不自动close；下一轮Planner独立验收。

### 明确非目标（Non-goals）

- 不迁移其他store/API/composable/组件/router，不新增产品功能；不改主题校验/恢复策略，不给_persist加容错、事务、重试。
- 不改CI拓扑、矩阵、pre-commit；typecheck只本地，不设coverage.thresholds，不改覆盖率分母来追数字。
- 不升级既有直接依赖大版本、不加vue-tsc/Vue重复@types；不另建大而空的类型框架。
- 不为API薄包装补mock复述、入口壳补源文本/接线测试；也不把该批补齐推断成“全仓无行为测试机会”。
- 不动#98现场，不启动M7扩展；不追第三方/CJK字体告警，不引MySQL/Redis集成环境来凑队列。

## 保留的 Milestone 事实与成功阈值

### M6 测试性能优化：成员10 / 10 CLOSED，成功信号1 / 3，OPEN且未收敛

- 成员#88–#95/#106/#107，GitHub实际状态复核10 CLOSED、0 OPEN。
- 目标不改：本地串行无coverage稳定<30s、完整CI created→最后job完成<240s、branch≥68.49%。
- 最近已有证据：2026-10-21本地native39.45s（1495/69/196）；既有5run完整CI247–329s；2026-10-19branch68.5259%，CI68.62–68.63%。本轮未重跑后端，不把旧结果当新结果。
- D-023默认A已转正：保留open、不降阈值、不追加高成本或红线投入。成员关闭不等于收敛。

### M7 候选与既有交付纠偏：6 / 11 CLOSED，OPEN且冻结

- CLOSED：#97/#99/#103/#104/#105/#108；OPEN：#98/#100/#101/#102/#109；#96是Epic，不计分母。
- D-019 A：暂停扩展，保留既有前端TS授权；已有纠偏通过不构成Rust/Qdrant/LLM/ABI矩阵授权。
- #110–#134均未设milestone，不污染M6/M7分母；暂不为单切片另建里程碑。

## 已知阻塞与依赖

- #98：in-progress有意冻结，原生产迁移/完整双模式/实际Criterion要求未完；不是疑似崩溃，不重置不关闭。
- #109：`command -v docker`本轮仍exit1，无已知已授权Docker主机。环境未解除前不把console当真实OTLP/Jaeger/UI验收，也不擅增metrics服务。
- #96/#100/#101/#102：needs-info，D-019 B/C无新用户答复；#102还依赖#98。
- #59：needs-info，具体产品需求未提供；D-012默认A有效。已在Issue解释TS继续实施不等于新增产品规格。
- pending为空，D-019/D-023 A已默认转正；没有新产品取舍需用户答复，不重复问历史已批准或已默认转正的同一问题。

## 下一阶段

- 首先独立验收#133/#134，再依据真实迁移结果确定下一单切片；不把本轮授权扩成全仓大迁移/CI改造。
- 既有TS方向可继续由Planner按证据分批，不需为每个低风险命名/配置选择重复询问用户。新的产品功能/外部服务/费用/公共API破坏性变化仍须新授权。
- _persist无catch仅为源码风险观察，未复现且缺预期恢复契约，不排修复；若出现真实失败证据再定级。
- 历史候选integration-only `tests/test_db.py`假断言与补集成用例仍待真实MySQL环境；API跨端路由契约需先有可验证规格，不为凑2–5项重复调研。

## 已放弃或冻结的方向

- 登录验证码：D-02暂缓；归档SQL：D-03保留。
- uv/venv整包缓存、session训练缓存、默认xdist/randomly/socket全局禁网：D-013/D-014/D-016/D-024不重启。
- Rust新切片/Qdrant/LLM/ABI矩阵/自动发布：D-019 A冻结；M6调阈值/高成本改造：D-023 A冻结。
- 把compile-only说成Criterion运行、console说成Jaeger、单job说成完整CI、空tsc说成迁移完成：一律不作验收依据。

## 给 Executor 的指令（不超过2句）

- 按#133→#134串行执行，ENV未配置字面WORKFLOW=trunk，因此使用每任务分支、独立验证/提交/合并流程；严守Issue文件边界与非目标。
- 先依据真实Issue刷新自己拥有的STATE/HANDOFF（#130–#132已关闭），逐项在Issue留固定字段报告并转in-review，实际执行日日报只追加、.agent另提交；不得自行close或领取冻结项。

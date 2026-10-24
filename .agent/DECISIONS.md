# DECISIONS — 用户与 Planner 决策日志

> 规划 Agent 向用户提问前必须先查本文件；已回答的不再问。
> 旧答案与现状明显冲突时，可向用户确认一次「是否仍然有效」。
> 格式：编号 / 日期(UTC) / 问题 / 用户决定或可自行查证的 Planner 决定 / 影响范围；pending 另含选项、推荐、默认与询问天数。历史原文保留，事实更正用新决策明确覆盖。

## 已确认

### D-01 / 2026-10-01 / M2 里程碑方向

- 问题：质量债清偿完毕（38 issue 全关、门禁全绿）后，M2 主攻方向？
- 用户选择：**前端性能与体验**（推荐项）。
- 备选未选：供应链安全二期（pip-audit/safety）、观察期、功能迭代。
- 影响范围：M2 里程碑立项（#39、#40）；后续前端相关 issue 优先按此方向排序。
- 后续（2026-10-03）：M2 已验收结项（#39/#40/#41 全达成，CI 绿）。

### D-02 / 2026-10-01 / 登录验证码（#15 留白）

- 问题：现有缓解（失败锁定 5 次/15min + IP 限流 + 登录审计）之上，验证码做不做？
- 用户选择：**暂缓但立调研 issue**（不实施）。
- 落地：issue #42（只调研不写码）。触发条件成熟（如出现实际撞库事件、
  开放注册面扩大）时可凭 #42 的对比表直接立项。
- 后续（2026-10-03）：#42 调研交付并关闭——推荐「维持不上」（相对现有防线的边际增益不划算）；
  触发条件 3 条与选型对比表保留在 #42；实施需另立 issue（首选国内商业行为验证码）。

### D-03 / 2026-10-01 / docs/database 历史归档 SQL

- 问题：6 个归档 SQL（new.sql、user.sql、article.sql 等）仍是旧列名 createTime，如何处理？
  （init_database.sql 是 CI 集成 job 冻结基线，不可动。）
- 用户选择：**保留不动**（归档即历史快照，git 可追溯，零风险）。
- 影响范围：不再为归档 SQL 的列名漂移建 issue；docs/database/README.md 的
  「只读参考，非真相源」标注即最终状态。

### D-04 / 2026-10-01 / integration job 覆盖率策略（#38 留白）

- 问题：覆盖率门禁目前只在 backend-fast，integration job 要不要也上？
- 用户选择：**只出报告不设阈值**（integration 用例少，单独阈值会失真）。
- 落地：issue #41（CI integration job 加 --cov 输出，不阻断）。已交付（实测 33% 不阻断）。

### D-05 / 2026-10-03 / M3 里程碑方向（M2 验收完成后）

- 问题：M2（前端性能与体验）验收完成后，M3 主攻方向？
- 用户选择：**A 后端 API 契约与测试强化**。
- 备选未选：B 前端 TypeScript 渐进化（属契约 1.8 红线，需专门授权后分批立项）、
  C 部署/运维生产化（本机无 Docker，执行验证受限）、D 产品功能迭代（缺具体需求输入）。
- 影响范围：M3 立项 = #43（M2 遗留浏览器冒烟）+ #44（GET 端点 envelope 契约）
  + #45（前端消费字段契约）+ #46（Redis 降级文档）；B/C/D 保留为后续里程碑候选。

### 默认转正（连续 3 轮无用户答复，按 6.3 于 2026-10-07 转正；用户可随时推翻重定）

- D-006 | 2026-10-07 | M4 里程碑方向 | 未回复，默认采用 A：质量巩固收尾（#52/#54/#55/#56/#57 全部验收闭环后无存量待办，队列清空待命；B/C/D 仍需用户输入才可立项） | 影响范围：M4 = 默认范围 A 已完成；新方向待用户命题
- D-007 | 2026-10-07 | 大屏趋势面板语义（#53） | 未回复，默认采用方案 2：前端改单系列画 counts（诚实、可回滚；方案 1 涉评论表 schema 变更属红线已放弃） | 影响范围：#53 已按方案 2 重写为 ready 规格并转 ready-for-agent（P2）
- D-008 | 2026-10-07 | 登录锁定/限流/WS 广播是否迁 Redis | 未回复，默认采用 C：暂不迁（DEPLOYMENT.md 已标注影响；不立项、不改行为） | 影响范围：无代码动作；真实多副本部署需求出现时重议

### D-009 / 2026-10-09 / M5 里程碑方向（M4 验收完成后）

- 问题：M4（质量巩固）验收完成后，M5 主攻方向？
- 用户选择：**B 前端 TypeScript 渐进化 + D 产品功能迭代**（双方向并行）。
- 备选未选：C 部署/运维生产化（本机无 Docker，执行验证受限）。
- 影响范围：M5 立项 = 前端 TS 渐进化（红线已授权，分批立项）+ 产品功能迭代（需具体需求输入）。
- 备注：前端 TS 渐进化属契约 1.8 红线（大规模架构重构），用户明确选择即授权；
  产品功能迭代需用户提供具体需求后方可立项。

### D-010 / 2026-10-09 / 产品功能迭代的需求输入方式（#59 推进路径）

- 问题：#59（产品功能迭代）缺少具体需求输入，如何推进？
- 用户选择：**先做一轮「用户体验/技术债务」调研再定方向**。
- 落地：#60（P1，ready-for-agent，用户体验与技术债务现状调研）。
- 影响范围：#59 保持 needs-info，待 #60 产出候选清单后再决定产品功能迭代方向。
- 后续（2026-10-09）：#60 已验收关闭，文档 §6 的 22 项候选全部立项
  （#61–#82；此前「23 项」为计数笔误，2026-10-10 修正）。
  候选清单解决的是**工程债/体验债/测试债**方向；产品功能需求本身仍待用户
  输入，记为 pending D-012。

### 默认转正（连续 3 轮无用户答复，按 6.3 于 2026-10-11 转正；用户可随时推翻重定）

- D-011 | 2026-10-11 | WebSocket 死管道（T-4，#82）删还是接入实时推送 | 未回复，默认采用 A：删除死管道（`frontend/src/utils/websocket.js` + `frontend/tests/websocket-client.test.js`；Planner 转正前已复核零消费者/3 用例仍成立；#82 已按 A 路径重写为 ready） | 影响范围：#82 转 ready 入执行队列；#58 第二批范围落定（不再含 websocket.js）
  - 后续（2026-10-11）：#82 已按 A 路径彻底删除并经 Planner 验收关闭。
- D-012 | 2026-10-11 | M5 产品功能迭代（#59）方向：现在提供具体功能需求，还是先清偿 #60 候选工程债 | 未回复，默认采用 A：先清偿工程债队列（#61/#62/#63 已验收关闭，默认方案运行无异常） | 影响范围：工程债队列继续按序执行；#59 保持 needs-info，用户随时给出功能需求即按 4.2 门禁立项

### D-016 / 2026-10-15 / #90 <110s 缺口处置

- 问题：#90 install 合计 <110s 未达成（实测 141s，差 31s），是否立 follow-up（venv 整包缓存 / uv 重估 / 接受现状）。
- Planner 决定：**接受 141s 现状，不立 follow-up**；#90 部分通过转关闭（3/4 标准满足：双 job 全绿、无漂移、无新 job）。
- 理由：(1) CI 双 job 现 2m43s / 2m14s（run 38557692302），已 <4m 达成 M6 CI 目标，31s 残缺口 ROI 不足；(2) lever 分析证实缓存命中下主体是 wheel 解包（~600MB）而非解析，分层已到天花板；venv 缓存涉 runner 镜像漂移、uv 重估涉从零锁定 + torch CPU index 适配（D-013 否决理由仍然成立），成本均大于收益；(3) install run 间方差大（64~92s），单 run 对比仅供参考。
- 原 <110s 标准归档（基于“解析/下载主导”假设，实测已推翻；非 silently 移动球门）。回滚只需 revert a023b1d。
- 影响范围：M6 CI 优化到此收敛；CI 侧不再立项。

### D-013 / 2026-10-14 / #90 CI 依赖提速选型

- 问题：uv 迁移 / requirements 分层 / pip 自管缓存三选一。
- Planner 决定：**方案 2 requirements 分层**（torch 系大包独立层 + 现有 pip 缓存）。
- 理由：`uv.lock` 实为单包空壳，uv 迁移需从零锁定 + torch CPU index 适配，成本超预期且动 CI 安装路径；分层增量可回滚。验收放宽为 install 合计 <110s（<60s 需 uv 级改造，本轮不做）。
- 影响范围：#90 已重写为 ready（P2）。

### D-014 / 2026-10-14 / #92 慢测试治理选型

- 问题：降规模 / session 缓存 / 标 slow 三选一。
- Planner 决定：**方案 1 降规模保语义**；test_performance（#88 后 0.77s）移出范围维持观察；3.01s ×2 只归因不修；session 缓存等 #91 结论；标 slow 需另行决策。
- 影响范围：#92 已重写为 ready（P3）。

### D-015 / 2026-10-14 / #81 验收备注

- 问题：执行报告“lint 退出码 0”与 CI 史实（a03c720 frontend-fast no-regex-spaces 红灯）不符。
- Planner 决定：**通过不 reopen**——交付物本身无问题，lint 瑕疵已由 50ade33 修复且现 main 全绿；reopen 无剩余工作。备注已记入验收 comment，后续 lint 声称以 CI 为准。
- 影响范围：#81 关闭。

### D-017 / 2026-10-16 / 更正 M6 成功信号与验收口径

- 问题：D-016 与上一 PLAN 把两个串行 job 各自 <4m 当作完整 CI 关键路径达标，并据此声称 CI 已收敛。
- 调查：GitHub 实际时间戳显示 run 38557692302 从创建到最后 job 完成为302s（5m02s），run 38698662814 为315s（5m15s）；integration 仍 needs backend-fast。本轮 fallback 串行无覆盖率32.31s，native branch68.11%；最新 CI branch68.17%，前一CI68.39%。跨机器、Python版本和cov/no-cov不可直接混比。
- Planner 决定：**撤回“CI 已<4m / M6 已收敛”的事实判断，不降低原目标**。M6 成功信号仍是串行无覆盖率稳定<30s、完整 CI elapsed<240s、branch>=68.49%；60%门禁成功只证明该门禁成功。
- 对 D-016 的覆盖：保留“接受已实测141s安装、不重做uv/venv整包缓存”的低风险选择；其“CI目标已达成/到此收敛”的事实前提失效。本轮 #106 先补真实证据与候选，不借更正擅自批准重大 CI 改造。
- 影响范围：M6 原8件 CLOSED 不等于成功信号全部完成；补 #106/#107 后为8/10 CLOSED，仍未收敛。#90/#93/#95 的部分验收余项有明确去向，不能当成全项通过。

### D-018 / 2026-10-16 / 已入库可选模块先恢复正确性，不预支新方向

- 调查：#98 真正 native 调用出现控制空白不等价、一次性 iterator 编码失败后回退丢数；去重工作集实际全唯一而 JSON 声称约90%重复；真实 Criterion 执行和生产消费者均无证据。#99 console app smoke 成立，OTLP/Jaeger 及 metrics 接收未验收。本轮不推断报告者主观动机。
- Planner 决定：**#98 按报告失实 reopen为in-progress；其余五件部分通过，保留关闭并完整拆出余项**。#104/#105/#107/#106/#108 仅修现有契约、测试/证据、本地构建与配置说明；不得借机接生产Rust、加新服务/付费请求/CI矩阵。
- 原目标保留：#98 的真实迁移及完整双模式验收仍在原任务，不能用修 bridge 或修 benchmark 代替；#102 承接 #97 的跨版本CI/制品，#109 承接 #99 的真实profile/metrics/UI/default-off性能证明。#108 只记录现有单crate/本地wheel及未决发布边界，不批准自动发布。
- 方向约束：D-009 的前端TS渐进化授权继续有效，#59/D-012不被新候选提案覆盖；M7方向、重要依赖与重大CI扩展需D-019明确答复。
- 影响范围：本轮只改 Planner 文件与 GitHub 治理信息；Executor 自行实现修复、按报告模板转in-review，Planner不代写代码或Executor现场。

### D-020 / 2026-10-16 / 生命周期标签与跨天证据链

- 依据：用户本轮契约要求 Issue 标签与 TASKS 状态同名且最多一个；Issue可用时为权威。旧 ready-for-agent 只是旧流程实际标签，不作为兼容生命周期保留。
- Planner 决定：使用 `ready / in-progress / in-review / blocked / needs-info / done`；优先级保留既有 `priority:P0`–`priority:P4`。已移除所有 CLOSED Issue 的活动标签，五个今日任务仅标ready，未重置任何Executor已有in-progress现场；#98为本轮验收reopen。
- 文档衔接：TASKS/PLAN按新契约记录；旧标签映射文档有意留给 #108 与构建配置一起更正，未把当前漂移隐藏或当作已完成。
- 缺失历史：2026-10-15日报不存在，已用Git/Issue/CI反推。Planner不创建或改写DIARY/STATE/HANDOFF/ENV；#106由Executor带当前补记日期追加可证事实，已写入日报的行不得修改。
- 影响范围：Issue为权威、TASKS整体镜像；.agent独立chore(agent)提交，代码/历史提交不混入、不重写。临时502后按真实状态补操作，不重复创建成功任务。

### D-021 / 2026-10-17 / scripts/ lint 门禁缺口与 append_api.py 的处置（#110）

- 问题：#105 附带发现 `scripts/` 不在 `ruff check src tests` 门禁内，且 `scripts/append_api.py` 第 4 行两条语句粘连、根本无法解析；其余 8 项为既有 lint 问题。
- 调查（Planner 只读复核）：`ruff check scripts` → 9 errors（含 `append_api.py:4 invalid-syntax`）；`ast.parse` 同样失败；全仓 grep 无 `append_api` 引用；CI **已经**执行 `scripts/check_documented_paths.py`，即 scripts/ 属于"会被执行的工具面"而非纯归档。读全文确认 `append_api.py` 是一次性 API 文档生成器（`parts` 累积 → 写入 `docs/API.md`），唯一损坏点是第 4 行。
- Planner 决定：**修复而非删除** `append_api.py` 的语法错误（机械拆分第 4 行，不真的运行它——运行会把重复章节追加进 `docs/API.md`）；**把 `scripts/` 纳入 ruff 门禁**（`ruff check src tests scripts`，同步 AGENTS.md 与 CI 同一 step 的路径，不新增 job、不改 CI 拓扑）。理由：该缺口正是"没被检查 = 默认干净"这一类静默腐烂，且扫描路径扩展可回滚、风险低于新增规则。
- 不设 milestone：M6（测试性能）与 M7（候选方向/既有交付纠偏）都不涵盖仓库卫生；硬塞会污染成功信号的进度分母。若同类问题再现，下一轮 Planner 再决定是否开「工程卫生」里程碑。
- 影响范围：新增 #110（P3，ready，type:chore + area:infra）；#110 不计入 M6/M7 任何成功信号；不改变 M6/M7 计数。

### D-022 / 2026-10-17 / 连续缺日报的验收口径加严

- 事实：2026-10-15、2026-10-16 两份日报均缺失（DIARY 目录只有 2026-10-14）；STATE/HANDOFF 停在 2026-10-14，ENV 的最后更新时间更早。2026-10-16 的 PLAN 已明确要求 Executor"接手先恢复自己拥有的状态文件并带当前日期补记漏失日报"，未被执行。
- Planner 决定：**验收证据门槛不变，但对"缺日报"的判定加严**——从下一轮起，凡 Executor 未写当日 DIARY 的交付，即使 Issue comment 有执行报告，也按"证据不足"处理：可判"部分通过"，不判"通过"；连续缺报的会话另记一条治理缺陷并在 TASKS 里点名。
- 理由：契约 1.8 规定日报是次日验收的唯一输入，且 append-only 不可事后美化；STATE/HANDOFF 是当前快照，不能替代历史。"报告写得好"与"链路可追溯"是两件事，后者才让下一棒能在几分钟内重建事实。
- 不追溯：#104/#105 本轮仍判通过（Issue 报告 + 独立复跑证据充分，且缺报属#106 已承接的余项）；本决定自 2026-10-18 轮次的验收起生效。
- 影响范围：#106 的"恢复 append-only 日报链"由余项升级为**每日必做**；交付流程不变，Planner 不代写任何 Executor 文件。

### D-019 / 2026-10-16 / #96 的 M7 新方向与红线范围 —— 默认转正（2026-10-18）

- 调查：DECISIONS 只有 D-009 的 TS/产品需求方向授权；#96 仍写 “if ratified”，本地历史无可补证的 Rust 授权记录；已有实现不等于用户决定。
- 用户未答复（第 1 天 2026-10-16、第 2 天 2026-10-17、第 3 天 2026-10-18）。按契约 6.3，默认方案 A 连续 3 天运行无异常，于 **2026-10-18 默认转正为 A：先完成已入库交付纠偏，暂停 M7 扩展，保留既有前端 TS 渐进化方向；不新增服务/费用/重大 CI 矩阵**。
- B（批准 Rust + 可观测性及相应 ABI/CI 矩阵，不含 AI 服务）与 C（批准完整 M7 候选，再补 Qdrant/LLM 规格）**均未获批准**；不得据此启动新切片、Qdrant/LLM、跨版本 CI 或 wheel 自动发布。
- 影响范围：#96/#100/#101/#102 保持 `needs-info`（冻结）；#109 仍 `blocked`（本机无 Docker）；#98 的剩余生产迁移继续冻结；#108 等既有交付纠偏的完成不构成 B/C 授权。
- 历史原文保留：选项 A/B/C、推荐 A、默认 A 见 2026-10-16/17 轮记录；**绝不自动批准 B/C 或任何红线**。

### D-024 / 2026-10-18 / #106 socket 审计结论

- 事实（#106 审计均只读）：fast gate 的 socket 来源共 3 处——urllib3 导入期 IPv6 能力探测、`src/services/sentiment_service/cache.py:49` 导入期 `redis_client.ping()`（fail-fast 降级）、`tests/test_notification_service.py::test_send_invalid_email` 的 `SMTP_SSL("invalid.host", 465)` 无显式 timeout。
- Planner 决定：**采纳“暂不引入 pytest-socket 全局禁网”**。3 处均属可控来源；全局封锁需要白名单机制，且会掩盖 Redis 类真实等待。审计结论写入 TEST_PERF §7.3，`#93` 的 unit 层禁网评估收口。
- 低风险余项：SMTP 用例可加显式 timeout，但不单独立项；后续仓库卫生批次有容量时再处理（P4 候选）。
- 后续（2026-10-18，Planning 轮）：ready 队列在 #111/#112 验收后清空、且无其他可安全开工项，D-024 遗留的 SMTP 余项此时符合「有容量时处理」——据此立项 **#113（P4，ready，无 milestone）**：复用 `test_notification_service.py:717/:743` 既有 `patch("smtplib.SMTP_SSL")` 模式消除 `test_send_invalid_email` 的真实出站（test-only，不动生产发送语义、不引 pytest-socket），并顺带刷新 TEST_PERF §7.1 使 #111/#112 反映验收后 state。
- 后续（2026-10-19，Planning 轮）：#113 经独立复跑（0.01s call、探针证实 0 次网络出站、fast gate native 1494/69/196 全绿、CI 四 job 绿）验收关闭。

### D-023 / 2026-10-18 / M6 两个未达阈值处置 —— 默认转正（2026-10-20）

- 调查：#106/#107 验收关闭后 M6 成员 10/10 CLOSED；覆盖率 ≥68.49% 达成（Planner 复跑 68.5259%），但串行 gate 实测 36.98s–39.37s、近期 CI 关键路径 247s–329s，均未达；M6 不因成员关闭而收敛。#112 已证明串行 <30s 是 collection(~11s)+执行净值(~30s) 的结构性差距，CI <240s 的可行解 L4（integration 解耦）属契约 1.10 红线。
- 选项：A：M6 保持 open，不改阈值、不投入高成本改造；B：追加优化预算（L4 CI 解耦 / L3 venv 缓存等），涉红线动作逐项批准；C：接受现状，关闭 M6 并记录两项未达。
- 用户未答复（第 1 天 2026-10-18、第 2 天 2026-10-19、第 3 天 2026-10-20）。按契约 6.3，默认方案 A 连续 3 天运行无异常，于 **2026-10-20 默认转正为 A：M6 保持 open、不调整成功信号、不追加高成本或红线投入**。
- 影响范围：M6 milestone 维持 open（open_issues=0、closed_issues=10），作为已知未收敛债务保留；不再为 M6 排新任务。B/C 均需用户明确授权后才能重议；Planner 不得自行降标，也不得把“成员关闭”冒充“里程碑收敛”。
- 历史原文保留（2026-10-18 pending 记录）：A：先做 #112 只读差距分析，M6 保持 open，不改阈值、不投入高成本改造；B：立即追加优化预算，目标维持原阈值，涉及 D-016/D-019 边界的动作逐项批准；C：接受现状，关闭 M6 并记录两项未达。推荐 A，默认 A；pending 第 2 天（2026-10-19）时 #112 已交付并验收，TEST_PERF §6.2 提供完整事实输入。

### D-025 / 2026-10-20 / 今日队列：仓库与测试卫生批次 #117/#118/#119（不设 milestone）

- 依据：M6 由 D-023 A 冻结、M7 由 D-019 A 冻结，ready 队列在 #114–#116 验收后清空；从 fast gate（149 warnings 中 3 条项目自有 `utcnow` 弃用）、#114 遗留的脚本假绿退出码、vitest stderr（32 个预期错误块）中提炼出 3 项低风险卫生任务。
- 决定：编排 **#117（P3）**、**#118（P4）**、**#119（P4）**，均不设 milestone（延续 D-021），不计入 M6/M7 成功信号分母；队列 3 项符合 4.4 容量约束，且无契约 1.10 红线。
- 影响范围：本轮不启动 M7、不改 M6 阈值、不改 CI 拓扑、不改 schema；#117 仅做等价 naive UTC 替换，#118/#119 仅改测试。验收后若队列再次清空且用户无输入，下一轮继续按实测证据提炼；找不到合格任务则保持空队列，不制造伪任务。

### D-026 / 2026-10-20 / #117 datetime.utcnow 替换保持 naive UTC 存储语义

- 问题：7 处项目自有 `datetime.utcnow()` 需替换以消除 Python 3.12 DeprecationWarning，如何避免改变 MySQL/SQLite 已存储值的语义。
- 调查：`src/services/startup_service.py` 注释明确 create_time 以 naive UTC 落库；模型列均为 `DateTime` 无时区；现有测试按 naive 值比较。
- Planner 决定：统一改为等价 naive UTC（推荐共享 helper：`datetime.now(timezone.utc).replace(tzinfo=None)`），**不改 schema、不改为 aware datetime 持久化、不改 API 返回格式、不升级依赖**；新增回归测试断言落库值 `tzinfo is None` 且接近当前 UTC。
- 影响范围：#117 的实现边界；第三方 `circuitbreaker`/`seaborn`/SQLAlchemy 自身告警不在范围。

### D-027 / 2026-10-20 / 今日队列：代码、测试与文档卫生批次 #120/#121/#122（不设 milestone）

- 依据：#117–#119 验收关闭后，从实际构建日志（Dart Sass 3.0 `@import` 弃用告警）、fast gate 稀疏类抽样 `UndefinedMetricWarning`、活文档 `TEST_PERF.md` §7.1 滞后事实中提炼 3 项通过 4.2 门禁的任务。
- 决定：编排 **#120（P4）**、**#121（P4）**、**#122（P4）**，均不设 milestone（延续 D-021/D-025），不计入 M6/M7 成功信号分母；队列 3 项符合 4.4 容量约束，且无契约 1.10 红线。
- 影响范围：本轮不启动 M7、不改 M6 阈值、不改 CI 拓扑、不改业务行为；#120 消除 Sass 弃用告警，#121 消除 sklearn metric 告警，#122 补齐文档状态账。

### D-028 / 2026-10-21 / 队列结转与 #121 规格更正

- 事实：上轮 Planning（2026-10-20）编排的 #120/#121/#122 在当日未被 Executor 领取；本轮开始前无 in-review 交付、无新增提交，main 停在规划提交 `afee0c4`。
- 决定：**#120–#122 原样结转至 2026-10-21 执行轮，不新增任务**；同日实测更正 #121 规格：测试入口由不存在的 `tests/test_hyperparameter_optimizer.py` 改为 `tests/test_model_pipeline.py::TestHyperparameterOptimizer`，验收不再绑定不可稳定复现的「95→92 warnings」，改为代码核对 + 定向测试 + 不新增其他告警类别。实现范围与文件边界不变。
- 理由：Executor 未运行时，重复编排等于制造伪工作；#121 的原始告警计数与测试路径经 2026-10-21 只读实测证明不可靠，若不更正会让 Executor 在不存在的文件上失败或误报完成。
- 影响范围：仅任务规格与规划文档；不改方向、不改 M6/M7 状态、不触碰红线。

### D-029 / 2026-10-21 / 同日复核：队列不变，#122 范围口径钉死，#120 迁移安全性前置证明

- 事实：2026-10-21 01:04（+0800）已完成当日 Planning 并提交 `8e924e8`；至 07:23（+0800）复核时 Executor 仍未运行——无 `.agent/DIARY/2026-10-21.md`、无 in-review、无新提交（`git diff --name-only afee0c4..HEAD` 仅 3 个 `.agent/` 文件）、无 open PR，main 停在规划提交，CI 39463001921 绿。
- 决定：**不重新编排、不新增任务**，`#120/#121/#122` 原样保留为今日队列；只做三项口径钉死：
  1. `TASKS.md` 把 #122 的验收简写从「§7.1 表格完整包含全部已关闭议题」改为 Issue 原文的「#88–#95、#106–#108、#110–#119」——原简写可被读成补全 80+ 个历史 Issue，是范围蔓延的口子。
  2. 补齐 #120 的迁移安全性前置证明：`animations.scss` 478 行内零 SCSS 变量/`@use`/`@import`/mixin/include（仅 keyframes、选择器、CSS 自定义属性），且全仓仅被 `index.scss:8` 引用 → `@import` 改 `@use ... as *` 不切断任何跨文件作用域、不会重复输出 CSS；Vite `additionalData` 注入的 `variables.scss` 在首行，新 `@use` 落在第 8 行仍在首条样式规则之前，位置合法。Executor 因此无需为「变量失效」预留防御性改动。
  3. 记录 Executor 侧快照漂移：`STATE.md` / `HANDOFF.md` 仍称 #117/#118/#119 为 in-review，实际已于 2026-10-20 关闭。Planner 不代改，写入握手要求由下一棒重写。
- 理由：Executor 未运行时重复规划等于制造伪工作（沿用 D-028）；但已发现的规格简写漂移若不钉死，会让 Executor 在错误范围上开工。
- 影响范围：仅 `.agent/` 与任务口径；不改方向、不改 M6/M7 状态、不触碰契约 1.10 红线、不新增或关闭任何 Issue。

### D-030 / 2026-10-22 / 验收 #120–#122 全部通过，并立项今日唯一卫生任务 #123（不设 milestone）

- 验收（独立复跑，不只信报告）：#120（`git show d7e0c59` 仅改 index.scss 1 文件；本机 `npm run build` exit 0 且 `DEPRECATION WARNING [import]` 计数=0）· #121（`git show 6a37d95` 两源文件均传 `zero_division=0`；定向测试 22 passed、`UndefinedMetricWarning` 计数=0；native fast gate 1495/69/196/92 warnings exit 0；ruff exit 0）· #122（`git show 0f2221c` 仅改 docs/TEST_PERF.md；§7.1 标「（2026-10-21 刷新）」且精确覆盖 #88–#95、#106–#108、#110–#119 共 21 项）。三项均一次性通过 → done/CLOSED，无 reopen、无报告失实。
- 立项：**#123（P3，ready，type:test，无 milestone）**——为前端 vitest 建立**仅本地**覆盖率可见性（`docs/TEST_PERF.md` §7.4/#93 遗留项）：装 `@vitest/coverage-v8@3.2.7` devDep、`vitest.config.js` 配 `test.coverage`、`package.json` 加 `test:coverage` 脚本。
- 选型理由与红线边界：属测试策略（契约 6.1 Planner 权限）；`@vitest/coverage-v8` 是 vitest 官方生态 devDependency、纯测试工具、可回滚，非重大依赖。**“设 `coverage.thresholds` 阈值门禁”与“将覆盖率纳入 CI”两部分明确排除在本任务外**（属主要 CI/CD 流程变化 + 可能引入维持不住的阈值，需用户授权，另立）。基线未知，先建可见性。
- 队列容量：宁缺毋滥。本轮从实测仅找到 #123 一项同时满足本地可验证 + 不触红线 + 逐条可判定；其余候选（`test_db.py` 的 `assert True` 属 integration-only、integration 补用例需外部 MySQL/Redis、CJK 字体 glyph 告警属 D-027 非目标）均不入 ready。
- 影响范围：关闭 3 个 in-review Issue + 新建 1 个 ready Issue；不启动 M7、不改 M6 阈值/CI 拓扑/schema/业务行为；无 pending 新增。

### D-031 / 2026-10-23 / 验收 #123，并据覆盖率基线编排测试补强批次 #124/#125/#126（不设 milestone）

- 验收（独立复跑）：#123 `npm ci` / `test:coverage` / `test:run` / `lint` / `build` 全 exit 0；41 files / 190 tests；`All files 80.55 | 72.66 | 30.95 | 80.55`；`npm ls` 版本匹配；`ci.yml` 零改动、无 thresholds；两个 main CI run success。锁文件独立比对 +24/−8、版本变动 0。**报告更正**：执行报告「零 registry 翻转」不准确，实际 18 个包 `resolved` 从 npmmirror 归一化为 npmjs（不影响验收，已在 Issue comment 注明）。
- 立项：**#124（P3）** 补齐 `src/utils/index.js` 14 个未测公开函数的单测（Stmts/Funcs/Lines ≥90%）；**#125（P3）** 补齐 `src/api/request.js` 错误分支与 401 登出测试（Stmts/Lines ≥90%、Branch ≥85%）；**#126（P4）** 刷新 `docs/TEST_PERF.md` §7.1/§7.4 并落盘覆盖率基线。
- 选题依据：覆盖率基线 `src/utils/index.js` 30.53% Stmts / 26.31% Funcs、`src/api/request.js` 72.51% Stmts / 37.5% Funcs；§7.1 停在 #119、§7.4 仍称覆盖率“未配置”。均为真实行为缺口或已证实文档漂移。
- 排除项（不立项）：8 个声明式 API 包装模块（0%）用 mock 断言等于复述源码，属 PLAN 非目标；`main.js` 入口豁免；`stores/user.js`、`chinaMap.js` 留待后续按覆盖率数据评估。
- 红线边界：**不设 `coverage.thresholds`、不把覆盖率纳入 CI**（主要 CI/CD 流程变化，需用户单独授权）；批次只新增测试文件或只改文档，不改生产源码/依赖/CI。
- 影响范围：关闭 #123；新建 3 个 ready Issue；无 pending 新增；不启动 M7、不改 M6 阈值。

### D-032 / 2026-10-23（第二轮）/ 验收 #124–#126，编排测试补强第二批 #127/#128/#129（不设 milestone）

- 背景：2026-10-23 09:31 的规划轮编排 #124/#125/#126，当日 21:35–21:47 执行轮交付并转 in-review。本轮为同日接续的验收/规划轮，队列面向下一执行轮。
- 验收（独立复跑，不只信报告）：
  - **#124 通过**：单文件 37 passed；全量 43 files / 252 tests；`src/utils/index.js` lines 222/226（98.23%）、branches 100/103（97.09%）、funcs 20/20（100%）；`lint`/`build` exit 0；stderr 0；提交 `d58fa71` 仅新增测试文件；CI 5/5 success。报告 Branch 97.08 与 lcov 97.087% 为舍入差异，不影响门槛。
  - **#125 通过**：单文件 25 passed；全量 43/252、stderr 0；`src/api/request.js` lines 161/171（94.15%）、branches 45/47（95.74%）、funcs 3/8（37.5%，http 薄封装按 Issue 排除）；`lint`/`build` exit 0；提交 `2ab34b3` 仅新增测试文件；CI 5/5 success。
  - **#126 部分通过**：§7.1 四行、§7.4 更正、§7.5 双段数值、日期均准确；唯一差距是 §7.5 的 0% 模块清单漏列 `src/App.vue`（实测 0/14 行，根组件壳）。按契约「剩余量另立」处理：关闭 #126，缺口并入 #129 承接，不 reopen。
- 立项：**#127（P3）** `src/stores/user.js` 登录态与 initAuth 分支测试（Lines ≥90 / Branches ≥80 / Funcs ≥85）；**#128（P3）** `src/utils/chinaMap.js` 单例与失败重试语义测试（Lines ≥90 / Funcs 100）；**#129（P4）** TEST_PERF §7.1 补 #124–#126、§7.5 去 in-review 并补 App.vue。
- 选题依据：验收后实测 `stores/user.js` 48/99 行、7/10 分支、3/7 函数（会话恢复路径无直接用例）；`chinaMap.js` 9/26 行、0/1 函数（单例/重试无任何用例）；文档账在验收后滞后。
- 排除项（不立项）：8 个声明式 API 包装模块（mock 复述源码）；`main.js` / `App.vue` 入口/根壳不补测；`stores/app.js` / `tabs.js` 留待后续按覆盖率数据评估；integration-only 的 `test_db.py` 假断言需外部 MySQL。
- 红线边界：**不设 `coverage.thresholds`、不把覆盖率纳入 CI**（主要 CI/CD 流程变化，需用户单独授权）；批次只新增测试文件或只改文档，不改生产源码/依赖/CI/README。
- 影响范围：关闭 #124/#125/#126；新建 3 个 ready Issue；无 pending 新增；不启动 M7、不改 M6 阈值、不动 #98/#109/#96/#100/#101/#102/#59。

### D-033 / 2026-10-24 / 验收 #127–#129 全部通过，编排测试补强第三批 #130/#131/#132（不设 milestone）

- 背景：2026-10-24 05:40 执行会话 1 因队列空待机收尾；本轮为本日规划轮，独立复跑验收 2026-10-23 会话 2 的三项 in-review。
- 验收（独立复跑，不只信报告）：
  - **#127 通过**：全量 45 files / 271 tests 全绿；lcov 核对 `stores/user.js` LH/LF 97/99（97.97%）、BRH/BRF 31/38（81.57%）、FNH/FNF 7/7（100%）；`lint` exit 0；提交 `ffe4c5b` 仅新增测试文件（+236）；关键断言抽查一致（:90-91 未认证零调用、:179 编码跳转、:190 %2Fhome 回退）；CI 5/5。
  - **#128 通过**：lcov 核对 `utils/chinaMap.js` 全 100%（26/26、6/6、1/1）；六场景断言抽查一致（registerMap 一次、promise 身份、HTTP 503）；CI 5/5。
  - **#129 通过**：diff 仅 `docs/TEST_PERF.md`（+7/−2）；§7.1 三行提交号经 git 核对；「转 in-review」grep 为 0；0% 清单含 App.vue；本机复跑 coverage All files 83.22/75.83/35.55/83.22 与新段一致；`4d00f9c` 的 integration cancelled 属 ci.yml concurrency 取消（非失败），以树内容仅差 `.agent/` 的 `be068ad`（5/5 success）为准，接受。
- **歧义裁定（既定口径）**：#129 的「43/252 保持不变」与「与当次输出一致」字面冲突，双段并存、各自标注测量时点是正确处理；后续同类文档任务沿用该口径。
- 立项：**#130（P3）** `stores/app.js` 主题切换与侧栏行为测试（实测 71.79/66.66/25，未覆盖行 16-19/22-23/29）；**#131（P3）** `stores/tabs.js` 多标签工作区状态机测试（实测 70.93/74.07/45.45，未覆盖 57-162；本 Issue 即此前暂缓的「单独规格」）；**#132（P4）** TEST_PERF §7.1 补 #127–#129、§7.5 待验收表述刷新与新基线段（依赖 #130/#131 后执行）。
- 选题依据：验收后实测覆盖率仅剩两组真实行为缺口（主题/侧栏状态、多标签工作区状态机），均为可断言的存储/DOM/路由联动语义，非 mock 复述；文档账为验收后既定滞后模式。
- **选题枯竭预警**：本批交付后，前端按既定口径可测对象仅剩 8 个 API 薄包装（mock 复述，排除）与 `main.js`/`App.vue`（壳层豁免）——测试卫生选题接近枯竭。后续若用户仍无方向输入（D-019 B/C、D-023 B/C、#59 产品需求），ready 队列将无真实任务可排，宁可空队列等待，不制造伪任务。
- 红线边界不变：不设 `coverage.thresholds`、不把覆盖率纳入 CI、不启动 M7、不改 M6 阈值、不动 #98/#109/#96/#100/#101/#102/#59。
- 影响范围：关闭 #127/#128/#129；新建 3 个 ready Issue；无 pending 新增；代码 HEAD 停在 `4d00f9c`（#129 交付）。

### D-034 / 2026-10-24（同日接续）/ 验收 #130–#132，并恢复 D-009 已批准的首个 TS 实迁移切片

- 轮次说明：D-033已是本日规划；用户在执行会话2/3后再次明确启动Planner，本轮作为同日接续验收/排队，不把一次会话冒充一天，不递增pending等待天数。
- 验收（本轮独立运行、非仅引用报告）：
  - #130通过：定向app9+tabs41用例全部通过；全量47 files/321 tests、lint exit0；app.js LH/LF39/39、FNH/FNF4/4、BRH/BRF10/10，均100%；五组场景逐条核对；73bec15仅新增142行测试。
  - #131通过：41用例、11组场景齐全；tabs.js LH/LF168/172（97.67%）、FNH/FNF11/11（100%）、BRH/BRF68/71（95.77%），超过90/90/75门槛；9a86951仅新增471行测试，catch40–41/190–191依约未mock。未重做执行期变异实验，不将其算成本轮验证。
  - #132通过：06b194e仅改TEST_PERF（+10/−5）；三提交号/三关闭状态/四处日期/历史数值与新增段核对无误；原日志/tmp/cov131.txt支持原47/321、83.79/77.35/37.55/83.79及tabs95.83，不能因为下一次输出不同就篡改历史或认定报告失实。
  - Standards/Spec两轴审查均0阻断；交付提交06b194e的backend-fast/frontend-fast/integration/rust-core/security-scan均completed/success。三项已留逐条验收comment并done/CLOSED。
- 测量口径：本轮All83.79/77.33/37.55/83.79、tabs Branch95.77，和执行期77.35/95.83略有差异；原因**未定位**，不声称是已证明的舍入/稳定性问题。后续文档只绑定同一次日志、记录测量时点，历史段保留，不能要求每次V8分支小数恒定。
- **更正D-033的方向推断**：“本批之后只能等用户新方向”遗漏了D-009/D-018/D-019明确保留的前端TS授权。#58关闭的是策略调研，package.json无TS/typecheck、无tsconfig/src下TS文件，真实迁移尚未开始；“已列出的三批行为目标补齐”不等于“全仓无真实可测对象”。无需重新问用户相同授权，也无需再做一轮同内容调研。
- 决定：立项 **#133（P2，ready，type:refactor）**，只交付本地类型检查与app.js→app.ts一个真实生产切片。严格noEmit/实际app.ts纳入/类型负例非零、既有9用例与全量47/321、运行时store smoke、lint/build均列为验收条件。保留setTheme(string)与任意存储字符串现状，不暗改主题域或容错。
- 工具选择（可回滚实现细节，不是新产品方向）：dev依赖固定typescript@5.9.3与@typescript-eslint/parser@8.46.2，npm view已核对Node22/ESLint9/TS<6兼容；Vue/Pinia自带类型，不加重复@types或vue-tsc。仅TS文件启用parser、JS/Vue规则不放宽；coverage.include纳入TS，不设thresholds。tsc只本地，不改CI流程、矩阵、pre-commit或既有直接依赖大版本。元数据兼容不代表本轮已安装/运行新typecheck。
- 文档收尾：立项 **#134（P4，ready，type:docs）**，只硬依赖已关闭的#130–#132，可独立执行；建议#133之后测量，不以未来任务完成充当ready门禁前提。只改TEST_PERF，补三行已验收状态/验收事实/执行时同次快照，按实际提交记录app.js或app.ts，不预支TS完成，不改历史路径/数字/§7.2–§7.4；不预写#133已验收，不因文档自身关闭无限派生同内容任务。
- 回应Executor风险信号：tabs.js:52–54的_persist确无catch，但未复现且未定义失败后恢复契约；不凭与resetTabs风格不同就排容错/重试/事务任务。已在#131验收comment回应，保留待真实故障证据，而非新增auto-discovered或虚构P1。
- 流程更正：#130领取comment把“main未设保护”当成WORKFLOW=trunk，但ENV没有此设置。代码验收通过不抹掉流程偏差；本轮及后续按契约默认每任务分支，不擅改Executor的ENV，不重写已推送历史。
- 治理：其余7件逐项复核，#98有意冻结现场不重置，#109本轮docker命令仍不可用，#96/#100/#101/#102/#59保留原状态/优先级；无重复/缺优先级/open auto-discovered/open PR；P3候选尚未跨过两个完成Milestone，不按“饥饿”误关。M6实际10/10成员关闭但仅1/3成功信号，M7实际6/11关闭；冻结约束不变。
- 影响范围：新建#133/#134，两项不设milestone；关闭#130/#131/#132，不污染M6/M7分母。只更新Planner的PLAN/TASKS/DECISIONS和Issues，不改代码、Executor STATE/HANDOFF/ENV/DIARY。无pending新增、无需要用户再次拍板的问题；D-019/D-023 A继续有效。

## 待用户确认（pending，低风险部分已按默认方案先行）

- 当前无 pending 项（D-023 已于 2026-10-20 按 6.3 默认转正为 A）。用户如希望改为 B/C，可随时明确授权。

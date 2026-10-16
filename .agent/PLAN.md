# PLAN — 开发路线图

> 规划 Agent 维护，每次会话滚动更新。执行 Agent 只读不写本文件。
> 方向类决策记录在 DECISIONS.md，本文件引用其编号（D-xx）。
> 更新于 2026-10-16，Planning 轮；同步后分支 main、代码 HEAD `ff30258`。GitHub Issue 为权威，昨日六件交付已补验收；详见 TASKS 与 Issue comments。

## 当前方向

**先修已入库交付的正确性与验收证据，再谈扩展。** #98 的真实 native 调用存在丢数/不等价，基准重复率元数据错误；M6 的 CI 时长被误算，branch 基线也未守住。今天优先闭环这三类事实，不把任务关闭数量当作成功信号。

D-009 的前端 TypeScript 渐进化方向继续有效；#96 的 Rust/观测/AI 新方向未查到明确授权，作为候选冻结扩展（pending D-019）。已有模块的低风险纠偏不需要等待该答复，亦不构成追认授权。

## 今日目标（2026-10-16）

- 恢复 bridge 的无损 fallback / canonical 等价性，纠正去重基准并真正执行 Criterion。
- 补现有观测模块的行为保障与覆盖率，补 M6 预算/隔离/前后记录，恢复 Executor 自己维护的跨天交接链。
- 修正已有可选构建与配置说明；只在可验证范围内推进，不把 Docker/产品/重大 CI 决策塞进 ready。

## 当前 Milestone：M6 测试性能优化（进度：8 / 10 CLOSED，尚未收敛）

### 目标与验收

- GitHub milestone：M6 测试性能优化；原 #88–#95 共8件 CLOSED，新增 #106/#107 ready。其中 #90/#93/#95 为部分通过并完整转交余项，不是全项验收。
- 测试保障面不缩水；新增可选模块后用例允许按真实行为增减，但每项变化须有解释，native / fallback 的 Rust-only skip 单独核对，不能机械要求两模式 passed 数相等。
- 成功阈值不改：串行无覆盖率 gate 稳定<30s、完整 CI 关键路径<240s、branch>=68.49%（D-017）。

| 成功信号 | 最新已观察事实 | 验收状态 |
|---|---|---|
| 本地串行无覆盖率稳定<30s | fallback 1474 passed /70 skipped /196 deselected，32.31s；昨日报告27.71s无配对原始证据 | 未证明稳定达标；#106补可比较记录 |
| 完整CI关键路径<240s | run 38557692302=302s；run 38698662814=315s | 未达；不能用163s/146s两个串行job各自达标替代 |
| branch>=68.49% | 本轮local native=68.11%，同HEAD CI=68.17%；前一CI=68.39% | 未达；#107补真实行为保障，不降阈值/分母 |

### 执行队列（给 Executor 的建议顺序，五项均 ready）

1. [#104 修复 Rust bridge 的 Unicode 等价性与 iterator 回退丢数](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/104)（P2）
2. [#105 校正去重基准的真实重复率并提交实际 Criterion 结果](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/105)（P2）
3. [#107 补齐现有可观测模块的行为验证并恢复分支覆盖率基线](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/107)（P2）
4. [#106 补齐 M6 预算报告、socket 审计与跨天交接证据](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/106)（P3）
5. [#108 使 Rust 工具链固定生效并补齐可选模块配置和构建边界](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/108)（P3）

五项无硬前置依赖，已分别定义范围/非目标/可判定验收；顺序是数据正确性→基准真实性→质量→证据/交接→构建文档。真实 extension、Rust1.99.0、maturin1.15.0、Python/OTel均可用；测量必须串行，构建可显式选工具链，不等 #108 的 pin 更正。P0/P1均为0，未制造高优先级容量。

### 完成信号（Success signal）

- 上表三个阈值均有同口径、可复现证据；原任务及 #106/#107 全部验收，预算/coverage差距不能只写“门禁全绿”。
- summary含实际Top10，socket合法依赖逐项可追溯，单例串扰闭环；日报与交接由Executor恢复，Planner能从未被改写的执行证据验收。
- 若实测后仍有预算差距，下一 Planner 继续拆解/决策；本轮不预支“已收敛”，也不自动开启新架构切片。

### 明确非目标（Non-goals）

- #90 的安装<110s缺口不重做；D-016中接受141s安装的选择维持，但“完整CI已<4m”的事实判断由D-017撤回。
- xdist/randomly/socket转默认门禁、标slow移出gate、session训练缓存、大改CI依赖/安装机制，均不在今日范围。
- 新生产Rust消费者、第二切片、Qdrant、LLM流式产品入口、新metrics服务、自动发布wheel、CI矩阵扩展，均不因本轮纠偏获授权。

## 已知阻塞与依赖

- **昨日验收**：2026-10-15日报缺失，已用六个Git提交、Issue执行报告/关键diff、CI和本轮真实验证反推；STATE/HANDOFF仍停在前天，不当作昨日实测。#95/#93/#97/#99/#103部分通过并保留关闭，所有余项已转接；#98报告失实reopen为in-progress，已明确三组反例、基准元数据差距与生产迁移未交付事实。
- **#98恢复现场**：#104/#105只恢复其正确性/基准子项，不关闭或缩掉父Issue原标准；生产接入待D-019。此次为首次验收不通过，若再失败须重新拆解；Planner不代Executor领取或重置已有现场。
- **#109外部环境**：本机无Docker，无已知已授权Docker主机；Jaeger/profile/UI与真实metrics接收仍blocked。已有console app smoke成立，但不代替OTLP链路证明。
- **D-019 / #96 / #100 / #101 / #102**：新方向/重要依赖/重大CI扩展未获明确批准，全部needs-info；默认先纠偏、暂停扩展，不因三天未答自动授权红线。#102还依赖#98完成，不能把abi3声明当成跨版本运行证据。
- **#59**：D-012默认A继续有效；#100/#101只是提案，不视为已收到产品需求，不重复追问既定输入方式。
- **M7候选账**：#97–#103及#104/#105/#108/#109共11个子项，3个CLOSED（#97/#99/#103均部分转交）、1个in-progress、3个ready、3个needs-info、1个blocked。Epic #96不计入子项分母；milestone名称不是方向授权。
- **治理检查**：所有open任务有唯一生命周期标签与priority，无重复执行范围；父/子项互链且不重复算成果；无新增auto-discovered待定级，无跨两个Milestone未动的P3/P4存量；所有CLOSED遗留活动标签已清理，open in-review=0。TASKS已从真实Issue整体重写，旧标签文档漂移明确归#108，不隐藏。
- **日报信号回应**：#90缺口按D-016保留安装现状；#91仍不转默认xdist；#92的3s等待在#95实现、配对证据转#106；M6“还差多少”以本轮三阈值事实为准，不沿用预计值。Executor-owned状态文件只由Executor补记/更新。

## 下一阶段

- 先按真实证据收敛M6与已入库交付，不因原8件CLOSED跳过成功信号。
- D-019默认A：保留已授权D-009，之后按#58六批策略继续前端TS渐进化；本轮不临时塞入无上下文的新迁移任务。
- 若用户明确批准M7部分或全部方向，下一轮仍需把产品数据/成本边界和依赖补成可执行规格，未过门禁的#100/#101/#102不能因一句批准立即开工。
- 产品功能需求可继续在#59提供；生产运维保留候选，本轮不要求用户立即配置Docker或云资源。

## 已放弃的方向

- 登录验证码实施（D-02：暂缓）。
- docs/database归档SQL列名同步（D-03：保留不动）。
- #90 的uv迁移/venv整包缓存（D-013/D-016：本轮不重启；完整CI未达标不能反向当作这些方案已获批准）。
- #92 的session训练缓存与标slow移出gate（D-014：不擅自缩测试保障面）。
- #84 的测试环境el-form短路修复（真实浏览器证实生产正常，保持关闭）。
- 把全唯一数据称为90%重复、把compile-only称为Criterion运行、把console称为Jaeger验收、把单job时长称为完整关键路径：均不可用作完成依据。

## 给 Executor 的指令（不超过2句）

- 接手先按真实Issue/Git恢复自己拥有的STATE/HANDOFF/ENV并带当前日期补记漏失日报，再按 **#104 → #105 → #107 → #106 → #108** 领取、验证、逐项报告转in-review，.agent与代码分开提交，不自行close。
- 只执行已入库能力的低风险纠偏，未授权的生产Rust接入/AI服务/重大CI改造保持不动，实机或证据不满足时如实报告，不能自行改验收标准或伪造成功。

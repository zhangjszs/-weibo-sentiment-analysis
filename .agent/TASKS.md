# TASKS — GitHub Issue 本地镜像

> 更新于 2026-10-16，Planning 轮整体重写。**GitHub Issue 为权威来源**；gh、网络、写权限均已验证可用。一次 GraphQL 502 后先重取真实状态，再只补未生效项，未降级或重复创建任务。
> 生命周期标签统一为 `ready` / `in-progress` / `in-review` / `blocked` / `needs-info` / `done`；优先级沿用 `priority:P0`–`priority:P4`。旧 `ready-for-agent` 已无 Issue 使用，非兼容别名；对应文档更正归 #108。
> Executor：先改 Issue 标签/comment，再同步本行；只改执行状态/报告，不改任务范围。完整规格、非目标和 checklist 见对应 Issue。

## 今日队列（建议顺序；全部 ready、无硬依赖）

| 顺序 | Issue / 目标 | P | 状态 | 可直接执行的边界与完成证据 |
|---|---|---|---|---|
| 1 | [#104 修复 Rust bridge 的 Unicode 等价性与 iterator 回退丢数](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/104) | P2 | ready | `A\x1cB` 与代理字符 iterator 已真实复现；恢复 canonical 语义/数据不丢失，native/fallback 回归与 gate 均绿。不接生产新消费者。 |
| 2 | [#105 校正去重基准的真实重复率并提交实际 Criterion 结果](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/105) | P2 | ready | 10k/100k、90%重复集的 actual unique=1000/10000；Criterion 调真实内核并真正执行；更新现有 JSON/Markdown，不要求正收益。与 #104 无硬依赖，串行测量避免 CPU 干扰。 |
| 3 | [#107 补齐现有可观测模块的行为验证并恢复分支覆盖率基线](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/107) | P2 | ready | 补真实降级/多 app/指标内容行为；local 与 CI branch >=68.49%，不改分母/阈值，不污染 global provider；复用实际 app console smoke。无需 Docker。 |
| 4 | [#106 补齐 M6 预算报告、socket 审计与跨天交接证据](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/106) | P3 | ready | summary 含真实 Top10、逐项 socket 表、修单例测试隔离并删除偶然默认断言；补 #95 可比较证据；真实记录未达预算，Executor 自行修复日报/交接链。只改已有 CI 步骤，不扩展拓扑。 |
| 5 | [#108 使 Rust 工具链固定生效并补齐可选模块配置和构建边界](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/108) | P3 | ready | 有效 repo pin、Rust-local maturin 配置、实测构建、README/.env.example/ADR/标签文档一致；只记录现有单 crate/本地 wheel，不发布、不扩展 CI。 |

门禁事实：本机 Python 3.12.14、Rust 1.99.0、maturin 1.15.0、weibo_core 0.2.0 与 OTel 已可用；每项目标/范围/非目标/验证标准均已写入 Issue。五项均为已有交付的低风险纠偏，不等于批准 M7 新框架/服务/业务迁移。P0=0，P1=0，未为填容量提升优先级。

## 验收恢复现场（不占 ready 队列，不代 Executor 重置）

| Issue | P | 状态 | 验收结论与剩余职责 |
|---|---|---|---|
| [#98 Rust 第一切片](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/98) | P2 | in-progress | 2026-10-16 首次验收失实，Planner reopen；不是 Executor 已重新领取。已复现 parity/iterator 丢数、基准 unique 元数据不符；原生产迁移、既有用例双 backend、真实 Criterion 标准全部保留。#104/#105 只恢复正确性/证据，不能据此关闭父任务；未授权生产接入不得实施。若下一次验收仍失败，必须再拆解，不准第三次盲试。 |

无超过24小时且无日报的现存 in-progress 现场需要重置；#98 是本轮重新打开。领取小任务时用 comment 说明与 #98 的关系，避免把父子任务当成重复交付计数。

## 等待验收（in-review）

无。昨日新增的六项交付已逐项补验收：一项 reopen，五项部分通过并完整转接余项；不是六项全部完成。

## 阻塞 / 待决策（全部保留，不可领取实现）

| Issue | P | 状态 | 阻塞事实 / 下一步 |
|---|---|---|---|
| [#109 验证并修正现有 OTLP 链路的 metrics 接收与 Jaeger 展示](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/109) | P2 | blocked | 本机无 Docker，无已知已授权 Docker 主机；console 不替代真实 profile/UI 验收。collector metrics→Jaeger 与宿主入口说明有差距；解除环境阻塞后验证，禁止自行新增 metrics 服务/长期成本。 |
| [#96 M7 候选 Epic](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/96) | P2 | needs-info | D-019：未查到用户批准 M7 的记录，原 Issue 仍称 if ratified。默认冻结扩展，仅执行现有纠偏；Epic 不纳入子任务计数。 |
| [#100 Qdrant 语义搜索候选](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/100) | P3 | needs-info | 新服务/模型与资源边界未授权；真实检索/降级契约未落定。不得默认下载模型、启动 Qdrant 或返回假成功。 |
| [#101 SSE 摘要候选](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/101) | P3 | needs-info | 产品入口、LLM 成本与数据范围未定；队列/direct SSE 等选择待补规格。不得变更认证模型或发出付费请求。 |
| [#102 ABI/CI 矩阵](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/102) | P2 | needs-info | 新增/扩展 CI 矩阵待 D-019 授权，#98 亦未 done；3.11/3.12、双实现与 wheel artifact 的 #97 余项已完整移交，非以 abi3 标记代替执行。 |
| [#59 产品功能需求收集](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/59) | P2 | needs-info | D-012 默认 A 有效；#100/#101 是候选而非用户已确认需求。本轮不重复询问既定需求输入方式。 |

## 本轮验收账（2026-10-15 日报缺失）

昨日日报缺失，已用 `git log cc0cfe7..ff30258`、Issue 执行报告/comment、关键提交 diff、真实 CI 与本轮验证反推。最近可读日报为 2026-10-14；STATE/HANDOFF 仍停在该日，ENV 计数也过期，仅 Executor 可更正。前天 #90/#91/#92 已在上一 Planner 轮处理，不重复关闭或重做。

| 昨日交付 | 结论 / GitHub 当前状态 | 已认可证据 | 未完成项去向 |
|---|---|---|---|
| #95 · `3b4da68` | 部分通过 / done、CLOSED | REDIS_URL 默认值顺序正确，保留显式配置；健康/鉴权19用例绿，/ready call 均<0.005s；Ruff clean，性能文档已回写 | 同机前后 full/target 原始记录欠缺 → #106；27.71s 仅为昨日报告值 |
| #93 · `3f1b37a` | 部分通过 / done、CLOSED | 软预算/退出码主逻辑与 CI 绿；seed42、coverage 暂缓结论有报告 | summary 缺 Top10、socket 表欠缺、单例串扰 → #106 |
| #97 · `2ba8d3d` | 部分通过 / done、CLOSED | native extension 可导入，cargo 6 tests 绿，现 CI rust-core 3.11 绿 | pin/packaging/docs → #108；3.12/双实现 CI/artifact → #102 |
| #98 · `818e886` | 报告失实 / reopen、in-progress | FFI 与正常样本代码存在，原始 wall-clock 采样存在，但不支持完成声明 | parity/丢数 → #104；虚假重复率/复制算法/未执行 Criterion → #105；原真实生产迁移仍留 #98 并受授权门禁约束 |
| #99 · `ff30258` | 部分通过 / done、CLOSED | 实际 app console smoke：/health、/ready 均200，有真实 SERVER span 与 HTTP metrics | coverage/行为 → #107；配置文档 → #108；真实 OTLP/profile/Jaeger 图像及 default-off 性能证据 → #109；诚实报告的 Docker 缺口不判虚报 |
| #103 · `e00ed46` | 部分通过 / done、CLOSED | ADR 有 scope、FFI/fallback 与负收益边界 | 单/多 crate、wheel/成熟度决策现状及 pending 授权区分 → #108 |

完整逐条结论与已运行命令摘录已写入各 Issue 的 Planner 验收 comment，并与后续任务互链。所有 CLOSED 遗留活动标签已清理；没有把“部分通过转交”算作 Milestone 收敛。

## Milestone 实际计数（按 GitHub state，不凭报告）

- **M6 测试性能优化：8 / 10 CLOSED**。原 #88–#95 均 CLOSED，其中 #90/#93/#95 为部分通过后转交余项；新增 #106/#107 ready。成功阈值仍为串行无覆盖率<30s、完整 CI 关键路径<240s、branch>=68.49%，**尚未收敛**。
- **M7 候选与既有交付纠偏：3 / 11 CLOSED**（#97/#99/#103，均为部分通过并转接）。#98 in-progress；#104/#105/#108 ready；#100/#101/#102 needs-info；#109 blocked。#96 是候选 Epic，计数不含它；不以 milestone 名称追认方向批准。

## 本轮已运行验证（代码基准 HEAD `ff30258`）

- fallback 全门禁：`WEIBO_CORE_RUST=0`，serial/no-cov，**1474 passed /70 skipped /196 deselected，32.31s**，退出0。
- native 全门禁：`WEIBO_CORE_RUST=1`、`--cov=src`，**1475 passed /69 skipped /196 deselected，68.11%**，退出0；80.95s为带覆盖率且同期有 smoke 的耗时，不用于前后性能比较。Rust-only 用例解释了两模式的一项 passed/skip 差异。
- readiness/鉴权目标文件：**19 passed /4.28s**，退出0；首个 health fixture setup=3.72s，与 /ready call 不同。
- `cargo +1.99.0 test --manifest-path rust/weibo_core/Cargo.toml --locked`：**6 passed**；`ruff check src tests`：clean；现 CI YAML 解析成功。
- `OTEL_ENABLED=1 OTEL_EXPORTER_OTLP_ENDPOINT=console .venv/bin/python scripts/demo_otel_trace.py`：退出0，/health、/ready均200，两条 SERVER span 与 HTTP metrics、DEMO_DONE；未验证 Jaeger/UI。
- native 手工 API 观察：`normalize_post("A\x1cB")` 不等价；含 `\ud800` 的 batch/dedup iterator fallback 返回空列表。基准工作集观察：N=10000、reported_unique=999、actual_unique=10000、重复率0%。
- CI [38698662814](https://github.com/zhangjszs/-weibo-sentiment-analysis/actions/runs/38698662814)：四 job 绿、branch=68.17%、完整 elapsed=315s；前一 run [38557692302](https://github.com/zhangjszs/-weibo-sentiment-analysis/actions/runs/38557692302)=302s、branch=68.39%。两轮都没有证明 CI<4m，60%门禁绿不等于68.49%验收通过。

## 给 Executor 的握手要求

接手先按真实 Git/Issue 修复自己拥有的 STATE/HANDOFF/ENV；缺失日报只能带当前补记日期追加，不得回写成当日实测。按今日顺序领取子任务并报告，不直接领取未授权的 M7 扩展；每项转 in-review，绝不自行 close，.agent 变更与代码分开提交。

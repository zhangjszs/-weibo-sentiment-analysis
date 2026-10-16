# PLAN — 开发路线图

> 规划 Agent 维护，每次会话滚动更新。执行 Agent 只读不写本文件。
> 方向类决策记录在 DECISIONS.md，本文件引用其编号（D-xx）。
> 更新于 2026-10-17，Planning 轮；内容提交在 main、代码 HEAD `ae0f848`（与远端同步）。
> 昨日两项纠偏 #104/#105 已独立复跑验收关闭（M7 纠偏 5/11 CLOSED）；#107 为**疑似中断现场**（未提交改动，见 TASKS）。GitHub Issue 为权威来源。

## 当前方向

**先把在途现场收干净，再把证据链补齐，不开新方向。** 昨日 #104（bridge 等价性/丢数）与 #105（基准真实重复率 + 真跑 Criterion）经独立复跑验收关闭；今天唯一半成品是 #107：分支 `agent/issue-107-observability-behavior` 上有未提交的 `tests/test_observability.py`（4 用例红 + 1 个 C416），main 的本地 fast gate 现在被它带红（committed HEAD 本身双模式全绿）。先收口这条现场，再让 #106 把 M6 的真实数字与跨天交接链补回来。

D-009 的前端 TypeScript 渐进化方向继续有效；#96/M7 扩展仍停在 D-019（pending 第 2 天，默认 A = 暂停扩展）。**该默认不阻塞** #106/#107/#108/#110 这类"已入库能力的低风险纠偏"；它只挡住新 Rust 业务迁移、Qdrant/LLM 服务与重大 CI 矩阵。

## 今日目标（2026-10-17）

- 收口 #107：对在途改动给出「恢复并转 in-review」或「放弃并说明」的结论，覆盖率按 ≥68.49% 如实报告（未达则部分完成，不许降阈值/改分母）。
- #106：把 M6 三个成功阈值的当前真实数字落成可核对的记录（含本轮 343s / 68.22% / 30.55s），并恢复 DIARY / STATE / HANDOFF / ENV 四条跨天链。
- #108 / #110：关掉两个"配置不生效"的口子——Rust 工具链 pin 未生效、`scripts/` 不在 lint 门禁。

## 当前 Milestone：M6 测试性能优化（进度：8 / 10 CLOSED，尚未收敛）

### 目标与验收

- 成员：#88–#95（均 CLOSED，其中 #90/#93/#95 为部分通过后转交余项）+ #106/#107（open）。
- 测试保障面不缩水；新增可选模块后用例允许按真实行为增减，但每项变化须有解释，Rust-only skip 单独核对。
- 成功阈值**不改**：串行无覆盖率 gate 稳定 <30s、完整 CI 关键路径 <240s、branch ≥68.49%（D-017）。

| 成功信号 | 最新已观察事实（2026-10-17） | 验收状态 |
|---|---|---|
| 本地串行无覆盖率稳定 <30s | Planner 独立复跑 HEAD：native 1483/69/196 **30.55s**、fallback 1481/71/196 **29.97s**（exit 0） | 未证明"稳定"达标：单次刚好在阈值两侧浮动 |
| 完整 CI 关键路径 <240s | run 38916769148 @ `ae0f848`：四 job 全绿；created 14:33:48Z → 最后 job 完成 14:39:31Z = **343s**（前一 run 315s / 302s） | 未达，且比上一轮更慢（rust-core 入图） |
| branch ≥68.49% | 同 run：backend-fast **68.22%**（60% 门禁通过）；历史 68.39% → 68.17% → 68.22% | 未达；#107 补真实行为保障，不降阈值/分母 |

### 执行队列（给 Executor 的建议顺序，4 项）

1. **#107 补齐现有可观测模块的行为验证并恢复分支覆盖率基线**（P2，`in-progress`，疑似中断）——**先看 Issue 里的 Planner 现场记录**：恢复优先于放弃；把 4 个红用例（导出流为空，疑为未 flush 就断言）收掉、C416 清掉，再报覆盖率。
2. [#106 补齐 M6 预算报告、socket 审计与跨天交接证据](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/106)（P3，ready）——今天的数字已由 Planner 落表，你只需补 Top10、socket 表、#95 同机前后记录与单例串扰隔离。
3. [#108 使 Rust 工具链固定生效并补齐可选模块配置和构建边界](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/108)（P3，ready）——含把"`maturin develop` 默认 dev 构建慢约 20x"写进 README（#105 发现）。
4. [#110 处置 scripts/ lint 门禁缺口与无法解析的脚本](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/110)（P3，ready）——今日新立项，规格与范围已写在 Issue 里（含"不真的运行 append_api.py"）。

**顺序理由**：现场收口（1）优先于新任务；证据链（2）优先于配置文档（3）；门禁缺口（4）最小，可作收尾。**宁可只做完前两项**，也不要四项都碰一半——昨日 #107 就是被"多线并行"截断的。

### 完成信号（Success signal）

- 上表三个阈值均有同口径、可复现证据；#106/#107/#108/#110 全部验收。
- Executor 的日报 / STATE / HANDOFF / ENV 恢复为当轮更新，Planner 能从未被改写的执行证据验收（D-021）。
- 若实测后仍有预算或覆盖率差距，下一轮 Planner 继续拆解；本轮不预支"已收敛"。

### 明确非目标（Non-goals）

- 不重启 #90 的安装提速（uv / venv 整包缓存）、#92 的 session 训练缓存、xdist/randomly/socket 转默认门禁。
- 不新开 Rust 生产消费者、第二切片、Qdrant、LLM 流式入口、新 metrics 服务、wheel 自动发布、CI 矩阵扩展（D-019 未答复前一律不动）。
- 不为覆盖率数字添加 getter / wiring / mock echo / 源文本测试；不把 kernel/socket 探针整体放开。
- #110 不扩大为"全仓 lint 规则重设计"，只关 `scripts/` 这个具体口子。

## 已知阻塞与依赖

- **#107 现场（最高优先）**：分支 `agent/issue-107-observability-behavior`（= `ae0f848`，无自有提交）上有未提交的 `tests/test_observability.py`（+381/−86）；当前 `4 failed, 10 passed`，`ruff` 报 `test_observability.py:241` C416；patch 只读副本 `/tmp/opencode/issue-107-wip-2026-10-17.patch`。Planner **不重置**该 in-progress，恢复/放弃由 Executor 判断。
  - **分支提示（本轮新增）**：Planner 的 `.agent` 更新已提交在 **main**（`ee83a0f`，已推送）。该分支仍停在 `ae0f848`，切回分支工作区时 `.agent` 会退回旧版本 —— 请先 `git checkout main`（未提交改动会跟着走）或先 `git rebase main`，再继续 #107。
- **#98**：in-progress 父任务，真实生产迁移与完整双模式验收未交付，受 D-019 门禁约束；#104/#105 只是其正确性/基准子项，不代其关闭。若下一次验收仍失败，必须重新拆解，不准第三次盲试。
- **#109**：本机无 Docker、无已知已授权 Docker 主机；OTLP metrics 接收与 Jaeger/UI 仍 blocked（console smoke 不等于 OTLP 链路证明）。
- **D-019 / #96 / #100 / #101 / #102**：M7 方向、重要依赖、重大 CI 扩展未获明确批准，全部 needs-info；默认 A 已运行无异常，但不自动授权红线。
- **#59**：D-012 默认 A 继续有效；#100/#101 是候选而非用户已确认的产品需求，不重复追问既定输入方式。
- **跨天链缺口**：2026-10-15、2026-10-16 日报均缺失；STATE/HANDOFF/ENV 停在 2026-10-14。Planner 已立 D-021 加严口径（缺日报的执行报告按"证据不足"处理），补齐工作属 #106。

## 下一阶段

- M6 收敛后（三个阈值同时有同口径证据）再谈新方向；在那之前不预支。
- D-019 若批 A：按 #58 六批策略继续前端 TS 渐进化（既有授权），M7 扩展保持冻结。
- 若用户批准 M7 部分或全部：仍需把产品数据、成本、依赖边界补成可执行规格后逐项过 4.2 门禁，一句批准不等于立即开工。

## 已放弃的方向

- 登录验证码实施（D-02：暂缓）。
- docs/database 归档 SQL 列名同步（D-03：保留不动）。
- #90 的 uv 迁移 / venv 整包缓存（D-013/D-016：不重启）。
- #92 的 session 训练缓存与标 slow 移出 gate（D-014：不擅自缩测试保障面）。
- #84 的测试环境 el-form 短路修复（真实浏览器证实生产正常，保持关闭）。
- 把全唯一数据称 90% 重复、把 compile-only 称 Criterion 运行、把 console 称 Jaeger 验收、把单 job 时长称完整关键路径：均不可作为完成依据。

## 给 Executor 的指令（不超过 2 句）

- 先读 #107 的 Planner 现场记录并把那条现场收干净（恢复优先；该分支无自有提交，放弃前先备份 patch），再按 #106 → #108 → #110 领取、逐项转 in-review。
- 本轮收尾必须写当日 `DIARY` 并更新 STATE/HANDOFF/ENV（D-021）；实机或证据不满足时如实部分完成/blocked，不得改验收标准或伪造成功，也绝不自行 close。

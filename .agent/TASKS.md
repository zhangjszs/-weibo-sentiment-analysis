# TASKS — GitHub Issue 本地镜像

> 更新于 2026-10-17，Planning 轮整体重写。**GitHub Issue 为权威来源**；本轮开头重新拉取真实状态（gh 可用、账号 zhangjszs、scope repo+workflow），未降级、未重复创建。
> 生命周期标签：`ready` / `in-progress` / `in-review` / `blocked` / `needs-info` / `done`；优先级 `priority:P0`–`P4`。
> Executor：先改 Issue 标签/comment，再同步本行；只改执行状态与报告，不改任务范围。完整规格/非目标/checklist 见对应 Issue。

## 今日队列（建议顺序；4 项，无硬依赖）

| 顺序 | Issue / 目标 | P | 状态 | 可直接执行的边界与完成证据 |
|---|---|---|---|---|
| 1 | [#107 补齐现有可观测模块的行为验证并恢复分支覆盖率基线](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/107) | P2 | in-progress（**疑似中断**） | **先读 Issue 中的 Planner 现场记录**：分支 `agent/issue-107-observability-behavior`（= main，无自有提交）有未提交 `tests/test_observability.py`（+381/−86），现 `4 failed/10 passed`，`ruff` 报 `:241` C416；四处失败均为"导出流为空"（疑未 flush 就断言）。恢复优先于放弃，放弃前先留 patch（副本 `/tmp/opencode/issue-107-wip-2026-10-17.patch`）。达标线不变：local 与真实 CI 的 `--cov=src` branch ≥68.49%，不改分母/阈值，不污染 global provider。**Planner 不重置该现场**。 |
| 2 | [#106 补齐 M6 预算报告、socket 审计与跨天交接证据](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/106) | P3 | ready | summary 含真实 Top10；逐项 socket 来源表（不放宽 localhost）；删 `tests/test_sentiment_model.py:293-311` 偶然默认断言并隔离单例串扰；补 #95 同机前后记录（原提交/worktree，不污染工作区）；更新 TEST_PERF §6/§7 并分开记 raw 秒数 / full CI 关键路径 / cov 与 no-cov；**Executor 自行补 STATE/HANDOFF/ENV 与缺失日报（带补记日期，不改历史行）**。阈值未达就如实保留差距。 |
| 3 | [#108 使 Rust 工具链固定生效并补齐可选模块配置和构建边界](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/108) | P3 | ready | 把 `rust/toolchain.toml` 改成 rustup 识别文件名并实测命中仓库 pin；补 Rust-local maturin 配置 + README 构建说明（含 **`maturin develop` 默认 dev 构建慢约 20x、必须 `--release`**，#105 发现）；`.env.example` 补 `WEIBO_CORE_RUST` / `OTEL_ENABLED` / `OTEL_EXPORTER_OTLP_ENDPOINT` / `OTEL_SERVICE_NAME`；ADR-0005 补单 crate 与不发布边界；`docs/agents/triage-labels.md` 同步生命周期标签。 |
| 4 | [#110 处置 scripts/ lint 门禁缺口与无法解析的脚本](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/110) | P3 | ready | 今日新立项（规格已写入 Issue）：修 `scripts/append_api.py` 第 4 行语法错误（**不得真的运行它**，`docs/API.md` 的 sha256 必须不变）；`scripts/` 纳入 `ruff check src tests scripts` 并同步 AGENTS.md 与 CI 的 Ruff 步骤；其余 8 项机械修复逐条说明"为何行为不变"；双模式 fast gate 计数与 #104/#105 基线一致。 |

队列说明：P0=0、P1=0，未为填容量升级优先级；四项均为"已入库能力的低风险纠偏"，**不等于批准 M7 新方向**。#107 是唯一在途现场，故排第一；只有它能立刻把本机 fast gate 从红变绿。

## 验收恢复现场（不占 ready 队列，不代 Executor 重置）

| Issue | P | 状态 | 验收结论与剩余职责 |
|---|---|---|---|
| [#98 Rust 第一切片](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/98) | P2 | in-progress | 2026-10-16 首次验收失实后 reopen；#104/#105 已恢复其 parity/丢数与基准真实性，但**原生产迁移、既有用例双 backend、真实 Criterion 标准仍留本 Issue**，且受 D-019 授权门禁约束。不是 Executor 已重新领取；Planner 不代领取、不代重置。若下一次验收仍失败，必须重新拆解，不准第三次盲试。 |

## 等待验收（in-review）

无。昨日新增两项已验收关闭（见下）。

## 阻塞 / 待决策（全部保留，不可领取实现）

| Issue | P | 状态 | 阻塞事实 / 下一步 |
|---|---|---|---|
| [#109 OTLP metrics 接收与 Jaeger 展示](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/109) | P2 | blocked | 本机无 Docker、无已知已授权 Docker 主机；console smoke 不替代真实 profile/UI 验收。解除环境阻塞后验证，禁止自行新增 metrics 服务/长期成本。 |
| [#96 M7 候选 Epic](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/96) | P2 | needs-info | D-019 第 2 天未答复，默认 A = 冻结扩展；Epic 不纳入子项计数。 |
| [#100 Qdrant 语义搜索候选](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/100) | P3 | needs-info | 新服务/模型与资源边界未授权；不得默认下载模型、启动 Qdrant 或返回假成功。 |
| [#101 SSE 摘要候选](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/101) | P3 | needs-info | 产品入口、LLM 成本与数据范围未定；不得变更认证模型或发出付费请求。 |
| [#102 ABI/CI 矩阵](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/102) | P2 | needs-info | 待 D-019 授权，且 #98 未 done；不得以 abi3 标记代替 3.11/3.12 双实现执行。 |
| [#59 产品功能需求收集](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/59) | P2 | needs-info | D-012 默认 A 有效；#100/#101 是候选而非用户已确认需求，本轮不重复追问输入方式。 |

## 本轮验收账（2026-10-17）

昨日（2026-10-16）无日报、STATE/HANDOFF/ENV 仍停 2026-10-14，故以 `git log cc0cfe7..ae0f848`、Issue 执行报告、关键 diff、CI run 与本轮独立复跑反推。

| 昨日交付 | 结论 / GitHub 当前状态 | 独立复跑证据（Planner，只读） | 未完成项去向 |
|---|---|---|---|
| #104 · `9a75875` → merge `a88fd7a` | **通过**，done / CLOSED | 三组原反例全部与 canonical 一致（真实 extension 0.2.0）；`cargo test` 11 passed（原 6）；native 1483/69/196（30.55s）、fallback 1481/71/196（29.97s）双绿，与报告逐字一致；`ruff check src tests` clean；改动仅 4 文件、无新依赖/消费者；55 码点有界差异逐点复核为 CPython 未分配码点 | — （变异实验需改码，未独立复现，按报告采信） |
| #105 · `48e00c0`…`515c8c4` → merge `85f7f44` | **通过**，done / CLOSED | 独立重建工作集：10k→1000 unique、100k→10000 unique，`dedup_keys == dedup_keys_py`；`target/criterion/*/new/estimates.json` 7 项 mtime 2026-10-16 21:51–21:52，JSON median 与 estimates 逐项吻合；md 已撤回 #98 的错误重复率；门禁与 #104 完全一致 | `scripts/` 门禁缺口 → **#110**（今日新立项）；`--release` 构建说明 → #108 |
| #107 · 无提交（在途） | **疑似中断**，保持 in-progress | 分支 `agent/issue-107-observability-behavior`（= main）有未提交 `tests/test_observability.py`；`4 failed / 10 passed`；`ruff` 报 C416；四处失败均为"导出流为空" | 由 Executor 决定恢复/放弃；Planner 已在 Issue 留现场记录 |

## Milestone 实际计数（按 GitHub state，不凭报告）

- **M6 测试性能优化：8 / 10 CLOSED，未收敛**。CLOSED：#88–#95（其中 #90/#93/#95 为部分通过后转交余项）；OPEN：#106、#107。成功阈值仍为串行无覆盖率 <30s、完整 CI <240s、branch ≥68.49%。
- **M7 候选与既有交付纠偏：5 / 11 CLOSED**。#97/#99/#103/#104/#105 done；OPEN：#98（in-progress）、#108（ready）、#100/#101/#102（needs-info）、#109（blocked）。#96 为候选 Epic，不计入分母，milestone 名称不构成方向授权。
- **#110 不设 milestone**（仓库卫生，不计入任何成功信号分母，见 D-021）；若同类问题再现，由下一轮 Planner 决定是否开「工程卫生」里程碑。

## 本轮已运行验证（Planner，只读；基线 HEAD `ae0f848`）

- 独立 worktree `git worktree add --detach /tmp/opencode/verify-main ae0f848`，避开在途 #107 的未提交文件（在途文件会让本机 fast gate 变红，`--maxfail=1` 停在该文件）。
- native 全门禁：`WEIBO_CORE_RUST=1`、serial、`--no-cov` → **1483 passed / 69 skipped / 196 deselected**，exit 0，30.55s。
- fallback 全门禁：`WEIBO_CORE_RUST=0` → **1481 passed / 71 skipped / 196 deselected**，exit 0，29.97s。
- `~/.cargo/bin/cargo +1.99.0 test --manifest-path rust/weibo_core/Cargo.toml --locked` → **11 passed**；`ruff check src tests` → **All checks passed**。
- 真实 extension 行为复核（退出 0）：`normalize_post("A\x1cB")`→`'a b'`；`normalize_posts(iter([...\ud800...]))` 全量保留；`dedup_keys(iter(...))` 全量保留；`weibo_core` 未新增 Python 侧公共符号（`pub mod text` 不外露）。
- 基准产物核对：`scripts/bench_dedup.py::_dedup_workload` 重建工作集 distinct=1000/10000；7 个 Criterion `estimates.json` 与 `docs/benchmarks/m7-1-dedup.json` 对得上。
- CI run [38916769148](https://github.com/zhangjszs/-weibo-sentiment-analysis/actions/runs/38916769148) @ `ae0f848`：rust-core / backend-fast / frontend-fast / integration **四 job 全 success**；created 14:33:48Z → 最后 job 14:39:31Z = **343s**；backend-fast **branch 68.22%**（60% 门禁通过）。
- #110 事实复核：`ruff check scripts` → **9 errors**（含 `scripts/append_api.py:4 invalid-syntax`）；`ast.parse` 同样失败；全仓 grep 无 `append_api` 引用；CI 已执行 `scripts/check_documented_paths.py`。
- #107 现场复核：`pytest tests/test_observability.py -o addopts="" --no-cov` → `4 failed, 10 passed`；`ruff check src tests` 唯一错误即该文件的 C416。
- 注意（操作细节，供后续复用）：`pytest.ini` 的 `addopts` 已含 `-q`，命令行再给一次 `-q` 会把 verbosity 降到 −2，**汇总行不打印**；要拿计数就不要重复 `-q`。

## 给 Executor 的握手要求

接手先按真实 Git/Issue 修复自己拥有的 STATE/HANDOFF/ENV，并按 D-021 补当日 DIARY（缺失历史只能带补记日期追加，不得回写成当日实测）；先收口 #107 现场，再按 #106 → #108 → #110 领取，逐项按契约 1.7 报执行报告并转 in-review，绝不自行 close；`.agent` 变更与代码分开提交，未授权的 M7 扩展保持不动。

# TASKS — GitHub Issue 本地镜像

> 更新于 2026-10-18，Planning 轮整体重写。**GitHub Issue 为权威来源**；本轮开头重新拉取真实状态（gh 可用、账号 zhangjszs、scope repo+workflow），未降级、未重复创建。
> 生命周期标签：`ready` / `in-progress` / `in-review` / `blocked` / `needs-info` / `done`；优先级 `priority:P0`–`P4`。
> Executor：先改 Issue 标签/comment，再同步本行；只改执行状态与报告，不改任务范围。完整规格/非目标/checklist 见对应 Issue。

## 今日队列（建议顺序；2 项，无硬依赖）

| 顺序 | Issue / 目标 | P | 状态 | 可直接执行的边界与完成证据 |
|---|---|---|---|---|
| 1 | [#112 M6 残余差距只读分析：串行 gate <30s 与 CI <240s 的可行杠杆](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/112) | P2 | in-progress | **只分析，不改代码/CI/阈值**：当前 HEAD 双模式计数、wall time、`--durations=30` Top ≥10；至少 3 个 CI run 的 created→完成墙钟与 install/pytest 分项；≥4 项候选杠杆（预期收益/风险/红线判断）。产出写入 `docs/TEST_PERF.md` 新小节；为 D-023 提供证据。 |
| 2 | [#111 同步旧 ruff 命令并刷新 TEST_PERF 议题状态表](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/111) | P4 | ready | 同步 `scripts/verify_project.ps1`、`docs/DEVELOPMENT.md`、`docs/RELEASE_CHECKLIST.md`、`README.md` 的旧 `ruff check src tests`；刷新 `docs/TEST_PERF.md` §7.1 状态；更正 #108 的 2m37s 关键路径误写（实际 run 287s）。不运行 `append_api.py`、不改历史快照/CI/规则。 |

队列说明：P0=0、P1=0；两项均属低风险收尾，**不等于批准 M7 扩展或 M6 阈值修订**。若时间不足，优先完成 #112（D-023 的决策输入），不要两项各做一半。D-019 已于今日默认转正 A（暂停 M7 扩展）；D-023 待用户决定 M6 两个未达阈值，默认 A = 先分析、不关闭、不改阈值。

## 等待验收（in-review）

- 无。昨日 #106/#107/#108/#110 已于 2026-10-18 全部验收关闭（见下）。

## 阻塞 / 待决策（全部保留，不可领取实现）

| Issue | P | 状态 | 阻塞事实 / 下一步 |
|---|---|---|---|
| [#98 Rust 第一切片](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/98) | P2 | in-progress | 2026-10-16 首次验收失实后 reopen；#104/#105 已恢复其 parity/丢数与基准真实性，但**原生产迁移、既有用例双 backend、真实 Criterion 标准仍留本 Issue**。D-019 默认 A 生效后继续冻结；保持现场不重置，但下一棒不得领取。 |
| [#109 OTLP metrics 接收与 Jaeger 展示](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/109) | P2 | blocked | 本机无 Docker、无已知已授权 Docker 主机；console smoke 不替代真实 profile/UI 验收。解除环境阻塞后验证，禁止自行新增 metrics 服务/长期成本。 |
| [#96 M7 候选 Epic](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/96) | P2 | needs-info | D-019 于 2026-10-18 默认转正 A = 暂停 M7 扩展。B/C 未批准；Epic 不纳入子项计数，保持冻结。 |
| [#100 Qdrant 语义搜索候选](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/100) | P3 | needs-info | 新服务/模型与资源边界未授权；不得默认下载模型、启动 Qdrant 或返回假成功。 |
| [#101 SSE 摘要候选](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/101) | P3 | needs-info | 产品入口、LLM 成本与数据范围未定；不得变更认证模型或发出付费请求。 |
| [#102 ABI/CI 矩阵](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/102) | P2 | needs-info | 待 D-019 B/C 授权，且 #98 未 done；不得以 abi3 标记代替 3.11/3.12 双实现执行。 |
| [#59 产品功能需求收集](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/59) | P2 | needs-info | D-012 默认 A 有效；#100/#101 是候选而非用户已确认需求，本轮不重复追问输入方式。 |

## 本轮验收账（2026-10-18）

昨日（2026-10-17）日报存在且 append-only；本轮以 `git show`、Issue 执行报告/comment、CI 日志、worktree 复跑与独立命令逐项核对。

| 昨日交付 | 结论 / GitHub 当前状态 | 独立复跑证据（Planner，只读） | 未完成项去向 |
|---|---|---|---|
| #107 · `1d78f05`+`339c891` → merge `be32bd0` | **通过**，done / CLOSED | `git diff ae0f848..be32bd0 -- src` 为空；两测试文件 17 passed；native 1494/69/196（40.71s）、fallback 1492/71/196（38.45s）双绿；覆盖率 JSON **68.5259%**（9268/13077，与报告逐位一致）；`observability.py` 98% stmt / 94% branch；CI 38995283704 四 job success、68.62%；demo 按文档命令 exit 0，health/ready 真实 span | 覆盖率余量薄 + SDK `.out` 实现细节风险，转入 M6 风险清单 |
| #106 · `cafe8ed`+`2f6790c`+`e23ba43`+`1ef3612` → merge `9a13987` | **通过**，done / CLOSED | CI 38998104877 日志 group 实读 elapsed 65s/exit 0 + 真实 Top10；Planner 临时 shell 演练 normal/overbudget/failure 退出码保持；socket 3 来源表与代码一致；#95 worktree `cc0cfe7`→`3b4da68` 目标两用例 6.02s→<0.005s，full gate 38.99s→32.16s，计数 1460/69/196 一致；TEST_PERF §6/§6.1/§7 与 10-17 日报完整 | M6 两个阈值未达，转 #112 分析 / D-023 决策 |
| #108 · `1889b6f`…`e2ecb5c` → merge `ddea0a9` | **通过**，done / CLOSED（附事实更正） | `rustup show active-toolchain` → overridden by `rust/rust-toolchain.toml`；cargo fmt/clippy/test 全绿 11 passed；requirements 无 maturin/cargo/pyo3；README/.env.example/ADR/triage 均核对；CI 38999122715 四 job success、rust-core 由 pin 自动安装 1.99.0、wheel smoke 0.2.0 | 报告把 backend-fast 2m37s 误称 critical path；实际 run 287s，已在验收 comment 更正，转 #111 文档刷新 |
| #110 · `cd0ea53`+`21535bc` → merge `1abfaf0` | **通过**，done / CLOSED | `ruff check src tests scripts` → All checks passed（exit 0）；ast.parse 成功；`docs/API.md` sha256 `71f7dcb8…d9ea1f` 不变；AGENTS.md/ci.yml 均含 scripts；CI 38999825154 四 job success、Ruff 按新路径通过；双模式 1494/1492 绿 | 旧命令残留（verify_project.ps1、DEVELOPMENT.md 等）→ #111 |

**报告失实检查**：四项交付本身均有独立证据支持，未发现“声称完成但证据不支持”。#108 有一处 CI 口径误写（单 job 时长当完整关键路径），已更正并转 #111 修文档；不构成 reopen 交付物的理由（D-015 先例）。#106 的 socket 审计为临时探针，Planner 未重跑探针，按 Issue 表 + 代码现状 + 审计方法采信。

## Milestone 实际计数（按 GitHub issue state，不凭报告/API 计数器）

- **M6 测试性能优化：10 / 10 CLOSED，未收敛**。CLOSED：#88–#95、#106、#107。成功信号 1/3：覆盖率达成（68.5259% 本地 / 68.62% CI），串行 <30s 与完整 CI <240s 均未达。**成员关闭 ≠ 里程碑收敛**。
- **M7 候选与既有交付纠偏：6 / 11 CLOSED**。#97/#99/#103/#104/#105/#108 done；OPEN：#98（in-progress 冻结）、#100/#101/#102（needs-info）、#109（blocked）。#96 为候选 Epic，不计入分母。
- **#110 不设 milestone**（仓库卫生，不计入任何成功信号分母，D-021）；#111/#112 同样不设 milestone。
- 计数口径：M6 按 issue state 为 10/10 CLOSED（milestone `open_issues=0`、`closed_issues=10`），但 milestone 保持 open；description 明确“未达成不得结项”。成功信号 2 项未达，故不关闭 milestone。

## 本轮已运行验证（Planner，只读；基线 HEAD `048af63`）

- `ruff check src tests scripts` → **All checks passed**（exit 0）；`ast.parse('scripts/append_api.py')` → exit 0；`sha256sum docs/API.md` = `71f7dcb8149bf5e9aa099b8a60de0a2bd11466ecf66ac76dbad1bb98c7d9ea1f`。
- `pytest tests/test_observability.py tests/test_observability_disabled.py --no-cov` → **17 passed**。
- native 全门禁（`WEIBO_CORE_RUST=1`、serial、`--no-cov`）→ **1494 passed / 69 skipped / 196 deselected**，exit 0，40.71s。
- fallback 全门禁（`WEIBO_CORE_RUST=0`）→ **1492 passed / 71 skipped / 196 deselected**，exit 0，38.45s。
- 覆盖率（`--cov=src`，native）→ **68.5259%**（JSON `percent_covered` 68.52594557907078，9268/13077），exit 0，86.37s；`observability.py` 98% stmt / 94% branch。
- Rust：`rustup show active-toolchain` → 1.99.0 `overridden by rust/rust-toolchain.toml`；`cargo fmt --check`、`cargo clippy --locked --all-targets -- -D warnings`、`cargo test --locked` → 全绿，**11 passed**。
- #95 同机配对：worktree `cc0cfe7` → `3b4da68`，目标两用例 call **6.02s → <0.005s**；full gate **38.99s → 32.16s**，计数 1460/69/196 双端一致。
- CI run [38995283704](https://github.com/zhangjszs/-weibo-sentiment-analysis/actions/runs/38995283704)、[38998104877](https://github.com/zhangjszs/-weibo-sentiment-analysis/actions/runs/38998104877)、[38999122715](https://github.com/zhangjszs/-weibo-sentiment-analysis/actions/runs/38999122715)、[38999825154](https://github.com/zhangjszs/-weibo-sentiment-analysis/actions/runs/38999825154) 均四 job success；关键路径分别 247s / 304s / 287s / 329s。
- `scripts/demo_otel_trace.py`（`OTEL_ENABLED=1 OTEL_EXPORTER_OTLP_ENDPOINT=console`）→ exit 0，`/health`、`/ready` 各有真实 span；`scripts/check_documented_paths.py` → OK。
- 未跑：integration/external 本地层（CI integration 已绿）；前端全量门禁（本轮未动前端，CI frontend-fast 已绿）；macOS/Windows Rust 构建（环境不具备）。

## 给 Executor 的握手要求

接手先按真实 Git/Issue 核对 STATE/HANDOFF/ENV，并按 D-022 写当日 DIARY；只领取 #112 → #111，逐项按契约 1.7 报执行报告并转 in-review，**绝不自行 close**。#98/#109/#96/#100/#101/#102 保持冻结/阻塞；不启动 M7 扩展、不改 M6 阈值、不做 CI 拓扑改造。`.agent` 变更与代码/文档变更分开提交；未授权的 M7 扩展保持不动。

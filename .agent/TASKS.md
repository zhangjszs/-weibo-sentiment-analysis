# TASKS — GitHub Issue 本地镜像

> 更新于 2026-10-18，Planning 轮（验收 10-18 执行轮交付，为下一执行轮编队）整体重写。**GitHub Issue 为权威来源**；本轮开头重新拉取真实状态（gh 可用、账号 zhangjszs、scope repo+workflow），未降级、未重复创建。
> 生命周期标签：`ready` / `in-progress` / `in-review` / `blocked` / `needs-info` / `done`；优先级 `priority:P0`–`P4`。
> Executor：先改 Issue 标签/comment，再同步本行；只改执行状态与报告，不改任务范围。完整规格/非目标/checklist 见对应 Issue。

## 今日队列（下一执行轮 · 建议顺序；1 项，无硬依赖）

| 顺序 | Issue / 目标 | P | 状态 | 可直接执行的边界与完成证据 |
|---|---|---|---|---|
| 1 | [#113 消除 test_send_invalid_email 真实出站依赖并刷新 TEST_PERF §7.1](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/113) | P4 | ready | 复用 `test_notification_service.py:717/:743` 的 `patch("smtplib.SMTP_SSL")` 模式让 `test_send_invalid_email` 快速确定失败、不真实联网；`assert success is False` 不变；顺带把 `docs/TEST_PERF.md §7.1` 的 #111/#112 行刷新为 done。不改生产发送语义、不引 pytest-socket、不动历史归档快照。 |

队列说明：P0=0、P1=0；仅 1 个 ready，符合「宁缺毋滥」。**这不是路线图饱和状态——pipeline 已到决策门**：M6 能否收口取决于 D-023（用户），M7 扩展被 D-019 A 冻结。除本卫生项外，其余未决项全部被冻结/阻塞/待用户决策，无可安全开工的 ready 任务。若用户今日给出 D-023 答复，下一轮据其扩大队列（B 授权 L4 或 C 收口 M6）。

## 等待验收（in-review）

- 无。本轮已验收 #112、#111（见下方验收账），GitHub 均已 CLOSED / `done`。

## 阻塞 / 待决策（全部保留，不可领取实现）

| Issue | P | 状态 | 阻塞事实 / 下一步 |
|---|---|---|---|
| [#98 Rust 第一切片](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/98) | P2 | in-progress（M7） | 2026-10-16 首次验收失实后 reopen；#104/#105 已恢复 parity/丢数与基准真实性，但**原生产迁移、既有用例双 backend、真实 Criterion 标准仍留本 Issue**。D-019 默认 A 生效后继续冻结；保持现场不重置，下一棒不得领取。 |
| [#109 OTLP metrics 接收与 Jaeger 展示](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/109) | P2 | blocked（M7） | 本机无 Docker、无已知已授权 Docker 主机；console smoke 不替代真实 profile/UI 验收。解除环境阻塞后再验证，禁止自行新增 metrics 服务/长期成本。 |
| [#96 M7 候选 Epic](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/96) | P2 | needs-info | D-019 于 2026-10-18 默认转正 A = 暂停 M7 扩展。B/C 未批准；Epic 不计入分母，保持冻结。 |
| [#102 ABI/CI 矩阵](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/102) | P2 | needs-info（M7） | 待 D-019 B/C 授权，且 #98 未 done；不得以 abi3 标记代替 3.11/3.12 双实现执行。 |
| [#100 Qdrant 语义搜索候选](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/100) | P3 | needs-info（M7） | 新服务/模型与资源边界未授权；不得默认下载模型、启动 Qdrant 或返回假成功。 |
| [#101 SSE 摘要候选](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/101) | P3 | needs-info（M7） | 产品入口、LLM 成本与数据范围未定；不得变更认证模型或发出付费请求。 |
| [#59 产品功能需求收集](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/59) | P2 | needs-info | D-012 默认 A 有效；#100/#101 是候选而非用户已确认需求，本轮不重复追问输入方式。 |

## 本轮验收账（2026-10-18 交付 · 2026-10-18 验收）

10-18 日报存在且 append-only；本轮以 `git show`、Issue 执行报告、独立复跑命令逐项核对（未仅信报告文字）。

| 交付 | 结论 / GitHub 当前状态 | 独立复跑证据（Planner，只读） | 未完成项去向 |
|---|---|---|---|
| #112 · `0c10122`（merge `33be94a`） | **通过**，done / CLOSED | `git show 0c10122 --stat` → 仅 `docs/TEST_PERF.md`（+92 行），未动代码/CI/阈值；本地复跑 collection `1560/1756 collected in 10.11s`（报告 10.94s，~11s 一致）、native `1494 passed / 69 skipped / 196 deselected in 37.20s`（报告 40.62s，计数逐位一致、wall 差为机器方差）；Top 2 用例同位次；§6.2 四 run 墙钟/install/pytest 分项 + L1–L5 杠杆 + 三类归类齐备，为 D-023 提供事实输入 | 结论已供 D-023，不预设「M6 已收敛」；D-023 未决 |
| #111 · `6834534`（merge `73e0074`） | **通过**，done / CLOSED | `grep -rn "ruff check"` 复核：活文档（verify_project.ps1、DEVELOPMENT.md、RELEASE_CHECKLIST.md、README.md、CODING_STANDARDS.md）均已含 `scripts`；残余旧命令仅在 `docs/plans/*`、`docs/superpowers/*`、`整改执行清单.md` 历史快照（规格明示不改，正确）；`ruff check src tests scripts` exit 0；`check_documented_paths.py` exit 0；§7.1 状态刷新、§6.1 #108 关键路径误写更正（287s）到位 | §7.1 自指行（#111 标 in-progress）随验收转 done → 折入 #113 刷新（不 reopen，D-015 先例） |

**报告失实检查**：两项交付均有独立证据支持，未发现「声称完成但证据不支持」。#111 有一处自指时序快照瑕疵（§7.1 将 #111 自身标 in-progress），属交付当刻快照，不构成 reopen 理由（D-015），已并入 #113。

## Milestone 实际计数（按 GitHub issue state，不凭报告/API 计数器）

- **M6 测试性能优化：10 / 10 CLOSED，未收敛**。milestone state=open、open_issues=0、closed_issues=10。CLOSED：#88–#95、#106、#107。成功信号 1/3：覆盖率达成（≥68.49%），串行 <30s 与完整 CI <240s 均未达。**成员关闭 ≠ 里程碑收敛**；#112 分析已确认此为结构性差距，收口与否取决于 D-023。
- **M7 候选与既有交付纠偏：6 / 11 CLOSED**。成员 11（#97/#98/#99/#100/#101/#102/#103/#104/#105/#108/#109，#96 为 Epic 不计分母）。done：#97/#99/#103/#104/#105/#108；OPEN：#98（in-progress 冻结）、#109（blocked）、#100/#101/#102（needs-info）。
- **#110/#111/#112/#113 不设 milestone**（仓库卫生，不计入任何成功信号分母，D-021）。

## 本轮已运行验证（Planner，只读；基线 HEAD `62da24b`）

- `git show --stat 0c10122 / 6834534` 与 merge `33be94a`/`73e0074`：确认 #112 仅文档、#111 仅 6 个文档/脚本文件，无生产/测试/CI/规则改动。
- `.venv/bin/python -m ruff check src tests scripts` → **All checks passed**（exit 0）。
- `.venv/bin/python scripts/check_documented_paths.py` → **OK: all documented paths exist**（exit 0）。
- 本地 native fast gate：collection `1560/1756 in 10.11s`；`1494 passed / 69 skipped / 196 deselected in 37.20s`（wall 39.17s）→ 独立确认串行 ~37–40s 未达 <30s。
- `grep -rn "ruff check"` 活文档/归档分布核对（见验收账）。
- CI：per `STATE.md`，run `39123822632` @ `db0f843`（#111/#112 merge 之后代）四 job success，backend-fast 2m32s；#111 仅改文档 + powershell 脚本（Linux CI 不执行该 ps1），故 CI 绿灯足以佐证，Planner 未重复拉取 CI 日志。
- 未跑：integration/external 本地层；前端全量门禁（本轮与 10-18 交付均未动前端）；`--cov` 覆盖率全量口径（上轮已独立复跑 68.5259%，本轮无生产代码改动，不重跑）。

## 给 Executor 的握手要求

接手先按真实 Git/Issue 核对 STATE/HANDOFF/ENV，并按 D-022 写当日 DIARY；本轮仅领取 #113，按契约 1.7 报执行报告并转 in-review，**绝不自行 close**。#98/#109/#96/#100/#101/#102/#59 保持冻结/阻塞；不启动 M7 扩展、不改 M6 阈值、不做 CI 拓扑改造、不引 pytest-socket 全局禁网（D-024）。`.agent` 变更与代码/文档变更分开提交。

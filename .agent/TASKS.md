# TASKS — GitHub Issue 本地镜像

> 更新于 2026-10-20，Planning 轮（验收会话 2 交付 #117/#118/#119；编排 #120/#121/#122；D-027 落盘）整体重写。**GitHub Issue 为权威来源**；本轮开头重新拉取真实状态（gh 可用、账号 zhangjszs、scope repo+workflow），未降级、未重复创建。
> 生命周期标签：`ready` / `in-progress` / `in-review` / `blocked` / `needs-info` / `done`；优先级 `priority:P0`–`P4`。
> Executor：先改 Issue 标签/comment，再同步本行；只改执行状态与报告，不改任务范围。完整规格/非目标/checklist 见对应 Issue。

## 今日队列（2026-10-20 执行轮 · 建议顺序；3 项，无互相依赖）

| 顺序 | Issue / 目标 | P | 状态 | 可直接执行的边界与完成证据 |
|---|---|---|---|---|
| 1 | [#120 消除前端 Sass @import 废弃警告（Dart Sass 3.0 兼容）](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/120) | P4 | ready | 替换 `frontend/src/styles/index.scss:8` 的 `@import './animations.scss';` 为现代模块化 `@use './animations.scss' as *;`；不升级依赖、不改样式/动画规则。验证：`npm run build` exit 0 且零 `DEPRECATION WARNING [import]`，`npm run lint` exit 0，vitest 41/190 全绿；仅改 1 个 SCSS 文件。 |
| 2 | [#121 模型训练与评估中的 classification_report 显式指定 zero_division=0](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/121) | P4 | ready | 在 `src/model/trainModel.py:249` 与 `src/model/hyperparameter_optimizer.py:428` 调用 `classification_report` 时显式传入 `zero_division=0`；消除抽样稀疏类的 3 条 `UndefinedMetricWarning`；不改抽样与模型超参数。验证：`pytest tests/test_model_improvements.py` 零 `UndefinedMetricWarning`，fast gate 双模式 exit 0（告警较 95 降至 92），ruff exit 0。 |
| 3 | [#122 刷新 TEST_PERF.md §7.1 议题总表并补齐 #113–#119 交付状态](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/122) | P4 | ready | 在 `docs/TEST_PERF.md` §7.1 追加 #113 至 #119 的 done 记录与真实摘要（SMTP mock / model return 清理 / celery eager / el-radio label / utcnow / exit code / console noise），标注更新日期为 2026-10-20；不改历史章节与 M6 信号。验证：§7.1 表格完整包含全部已关闭议题且与 GitHub Issue 一致，ruff exit 0；仅改 `docs/TEST_PERF.md`。 |

队列说明：P0=0、P1=0、P3=0、P4=3；共 3 项 ready，符合「2–5 个、宁缺毋滥」。三项均从构建告警、测试告警与文档滞后实测事实中提炼、无互相依赖、过 4.2 门禁，无契约 1.10 红线。M6 由 D-023 默认 A 冻结，M7 由 D-019 A 冻结；本轮不设 milestone（延续 D-021/D-025/D-027）。

## 等待验收（in-review）

- 无。#117/#118/#119 已在本轮验收关闭并标 `done`。

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

## 本轮验收账（2026-10-20 会话 2 交付 · 2026-10-20 验收）

10-20 日报第二会话追加存在且 append-only；本轮以 `git show`、Issue 执行报告、独立复跑命令逐项核对（未仅信报告文字）。

| 交付 | 结论 / GitHub 当前状态 | 独立复跑证据（Planner，只读） | 未完成项去向 |
|---|---|---|---|
| #117 · `8f1cc63` | **通过**，done / CLOSED | `git show 8f1cc63` 证实仅改 5 个模型默认值、startup_service、comment_repository、新增 datetime_utils 与 test_startup_service；`grep -rn "utcnow" src --include=*.py` 零可执行调用；定向测试 5 文件 exit 0 且零自有 utcnow 告警；fast gate native 1495/69/196（95 warnings，较 149 净减 54 条）、fallback 1493/71/196（92 warnings）双模式 exit 0；SQLite naive UTC 差值 <10s 断言通过；ruff exit 0 | 无遗留 |
| #118 · `574aa34` | **通过**，done / CLOSED | `git show 574aa34` 仅改动 `tests/test_model_improvements.py`（+30 -1）；pytest 运行 7 passed（含新增 `test_main_exit_code_on_failure`）；monkeypatch 证实失败退出码为 1；脚本独立直跑 exit 0（输出「测试完成！全部测试通过。」）；fast gate 计数 +1（native 1495、fallback 1493）；ruff exit 0 | 无遗留 |
| #119 · `ab430f7` | **通过**，done / CLOSED | `git show ab430f7` 仅改动 `frontend/tests/` 下 10 个测试文件（+107 -10）；`npm run test:run` 41 files / 190 tests 全绿；`grep -c "stderr \|"` 实测为 **0**（彻底收敛原有 32 块预期错误日志）；原有错误态 UI/DOM/state 断言保持完整且断言 `console.error` 被调用；`npm run lint` exit 0；`npm run build` exit 0（9.13s） | 无遗留 |

**报告失实检查**：#117/#118/#119 均有独立实测证据支撑，未发现「声称完成但证据不支持」。提交 `8f1cc63`、`574aa34`、`ab430f7` 均已推至远端并在 main 生效。

## Milestone 实际计数（按 GitHub issue state，不凭报告/API 计数器）

- **M6 测试性能优化：10 / 10 CLOSED，未收敛；2026-10-20 依 D-023 默认 A 冻结**。milestone state=open、open_issues=0、closed_issues=10。CLOSED：#88–#95、#106、#107。成功信号 1/3：覆盖率达成（≥68.49%），串行 <30s 与完整 CI <240s 均未达。D-023 于本日连续 3 天无答复，按 6.3 默认转正为 A（保持 open、不改阈值、不追加投入）；B/C 需用户明确授权。
- **M7 候选与既有交付纠偏：6 / 11 CLOSED**。milestone state=open、open_issues=5、closed_issues=6。成员 11（#97/#98/#99/#100/#101/#102/#103/#104/#105/#108/#109，#96 为 Epic 不计分母）。done：#97/#99/#103/#104/#105/#108；OPEN：#98（in-progress 冻结）、#109（blocked）、#100/#101/#102（needs-info）。
- **#110–#122 不设 milestone**（仓库与测试卫生，不计入任何成功信号分母，D-021/D-025/D-027）。

## 本轮已运行验证（Planner，只读；基线 HEAD `752cea0`）

- `git show --stat`：`8f1cc63` 9 文件（+46 -19）；`574aa34` 1 文件（+30 -1）；`ab430f7` 10 文件（+107 -10）。
- `grep -rn "utcnow" src --include=*.py` → 零可执行 utcnow 调用（仅注释与 `utcnow_naive` 定义）。
- `.venv/bin/python -m pytest tests/test_model_improvements.py -p no:launch_testing -p no:launch_ros -q` → exit 0（7 passed）。
- `.venv/bin/python tests/test_model_improvements.py` → exit 0（测试完成！全部测试通过。）。
- 前端：`npm run test:run` → 41 files / 190 tests 全绿（6.89s）；`grep -c "stderr \|"` 实测为 **0**；`npm run lint` exit 0；`npm run build` exit 0（9.13s）。
- `.venv/bin/python -m pytest -m "unit or api" -p no:launch_testing -p no:launch_ros -o addopts="" -q` → exit 0（native `1495 passed, 69 skipped, 196 deselected, 95 warnings in 38.76s`）。
- `WEIBO_CORE_RUST=0 .venv/bin/python -m pytest -m "unit or api" -p no:launch_testing -p no:launch_ros -o addopts="" -q` → exit 0（fallback `1493 passed, 71 skipped, 196 deselected, 92 warnings in 37.55s`）。
- `.venv/bin/python -m ruff check src tests scripts` → exit 0（All checks passed!）。
- 未跑：本地 integration/external 层（涉外部 MySQL/Redis/真实 Weibo cookie）。

## 给 Executor 的握手要求

- 接手先按真实 Git/Issue 核对 STATE/HANDOFF/ENV，并在当日 DIARY 追加记录（严格遵守 append-only）。
- 本轮按建议顺序依次领取 #120、#121、#122；各任务完成后按契约 1.7 在 Issue comment 提交执行报告并转 in-review，**绝不自行 close**。
- #98/#109/#96/#100/#101/#102/#59 保持冻结/阻塞；不启动 M7 扩展、不改 M6 阈值、不做 CI 拓扑改造。
- 记录新基线：后端 fast gate 1495/69/196/95 warnings（native）、1493/71/196/92（fallback）；前端 41/190、stderr 零 `stderr |` 块。`.agent` 变更与代码/文档变更严格分属不同 commit 提交。

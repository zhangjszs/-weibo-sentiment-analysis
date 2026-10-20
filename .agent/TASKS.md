# TASKS — GitHub Issue 本地镜像

> 更新于 2026-10-21，Planning 轮（无新增 in-review；结转 #120/#121/#122；更正 #121 规格）整体重写；同日 07:23（+0800）复核轮确认三项前提全部成立、队列不变，仅钉死 #122 范围口径并补齐 #120 迁移安全性证据（D-029）。**GitHub Issue 为权威来源**；两轮均重新拉取真实状态（gh 可用、账号 zhangjszs、scope repo+workflow），未降级、未重复创建。
> 生命周期标签：`ready` / `in-progress` / `in-review` / `blocked` / `needs-info` / `done`；优先级 `priority:P0`–`P4`。
> Executor：先改 Issue 标签/comment，再同步本行；只改执行状态与报告，不改任务范围。完整规格/非目标/checklist 见对应 Issue。

## 今日队列（2026-10-21 执行轮 · 建议顺序；3 项，无互相依赖）

> 上轮（2026-10-20）队列 #120/#121/#122 未被领取，本轮原样结转；#121 规格已在 Issue 更正（测试入口与告警计数口径，见 D-028）。

| 顺序 | Issue / 目标 | P | 状态 | 可直接执行的边界与完成证据 |
|---|---|---|---|---|
| 1 | [#120 消除前端 Sass @import 废弃警告（Dart Sass 3.0 兼容）](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/120) | P4 | ready | 替换 `frontend/src/styles/index.scss:8` 的 `@import './animations.scss';` 为现代模块化 `@use './animations.scss' as *;`；不升级依赖、不改样式/动画规则。验证：`npm run build` exit 0 且零 `DEPRECATION WARNING [import]`，`npm run lint` exit 0，vitest 41/190 全绿；仅改 1 个 SCSS 文件。 |
| 2 | [#121 模型训练与评估中的 classification_report 显式指定 zero_division=0](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/121) | P4 | ready | 在 `src/model/trainModel.py:249` 与 `src/model/hyperparameter_optimizer.py:428` 调用 `classification_report` 时显式传入 `zero_division=0`；不改抽样与模型超参数。验证：grep 确认两处均传参；`pytest tests/test_model_improvements.py tests/test_model_pipeline.py` exit 0 且不再出现 UndefinedMetricWarning（该告警受随机划分影响，未触发时以代码核对为准）；fast gate 双模式 exit 0、不新增其他告警类别；ruff exit 0；仅改两个源文件。**注意：不要运行不存在的 `tests/test_hyperparameter_optimizer.py`。** |
| 3 | [#122 刷新 TEST_PERF.md §7.1 议题总表并补齐 #113–#119 交付状态](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/122) | P4 | ready | 在 `docs/TEST_PERF.md` §7.1 追加 #113 至 #119 的 done 记录与真实摘要（SMTP mock / model return 清理 / celery eager / el-radio label / utcnow / exit code / console noise），小节标注改为 `（2026-10-21 刷新）`；不改 §1–§6 历史数据、不改 M6 信号。验证：§7.1 表格完整覆盖 **Issue 原文范围 #88–#95、#106–#108、#110–#119** 且状态与 GitHub 一致（**不是**补全全部 80+ 个历史 Issue），ruff exit 0；仅改 `docs/TEST_PERF.md`。 |

队列说明：P0=0、P1=0、P3=0、P4=3；共 3 项 ready，符合「2–5 个、宁缺毋滥」。三项均从构建告警、测试告警与文档滞后实测事实中提炼、无互相依赖、过 4.2 门禁，无契约 1.10 红线。M6 由 D-023 默认 A 冻结，M7 由 D-019 A 冻结；本轮不设 milestone（延续 D-021/D-025/D-027）。**结转上限**：这三项已被结转 2 次（10-20 编排、10-21 未领取）；若 2026-10-22 仍未被领取，下一轮不再无条件结转，改为按 4.1 重新评估保留/拆分/关闭，并追查 Executor 未运行的原因。

## 等待验收（in-review）

- 无。上轮 #117/#118/#119 已于 2026-10-20 验收关闭；本轮开始前无新增交付。

## 阻塞 / 待决策（全部保留，不可领取实现）

| Issue | P | 状态 | 阻塞事实 / 下一步 |
|---|---|---|---|
| [#98 Rust 第一切片](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/98) | P2 | in-progress（M7） | 2026-10-16 首次验收失实后 reopen；#104/#105 已恢复 parity/丢数与基准真实性，但**原生产迁移、既有用例双 backend、真实 Criterion 标准仍留本 Issue**。D-019 默认 A 生效后继续冻结；保持现场不重置，下一棒不得领取。状态持续超过 24h 属有意冻结，不作「疑似中断」处理。 |
| [#109 OTLP metrics 接收与 Jaeger 展示](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/109) | P2 | blocked（M7） | 本机无 Docker、无已知已授权 Docker 主机；console smoke 不替代真实 profile/UI 验收。解除环境阻塞后再验证，禁止自行新增 metrics 服务/长期成本。 |
| [#96 M7 候选 Epic](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/96) | P2 | needs-info | D-019 于 2026-10-18 默认转正 A = 暂停 M7 扩展。B/C 未批准；Epic 不计入分母，保持冻结。 |
| [#102 ABI/CI 矩阵](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/102) | P2 | needs-info（M7） | 待 D-019 B/C 授权，且 #98 未 done；不得以 abi3 标记代替 3.11/3.12 双实现执行。 |
| [#100 Qdrant 语义搜索候选](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/100) | P3 | needs-info（M7） | 新服务/模型与资源边界未授权；不得默认下载模型、启动 Qdrant 或返回假成功。 |
| [#101 SSE 摘要候选](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/101) | P3 | needs-info（M7） | 产品入口、LLM 成本与数据范围未定；不得变更认证模型或发出付费请求。 |
| [#59 产品功能需求收集](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/59) | P2 | needs-info | D-012 默认 A 有效；#100/#101 是候选而非用户已确认需求，本轮不重复追问输入方式。 |

## 本轮验收账（2026-10-21）

- **无新增 in-review 交付可验收**。复核：#117/#118/#119 均为 CLOSED/done；M6 open=0/closed=10、M7 open=5/closed=6，与上轮记录一致。
- 任务前提只读核验：
  - #120：`frontend/src/styles/index.scss:8` 仍为 `@import './animations.scss';`，全仓前端仅此 1 处 `@import`。
  - #121：`trainModel.py:249` 与 `hyperparameter_optimizer.py:428` 均未传 `zero_division`；定向运行 `tests/test_model_improvements.py` 复现 UndefinedMetricWarning（`7 passed, 9 warnings`）；同日本机 fast gate 未复现（`92 warnings`），故已把验收改为代码核对 + 定向测试 + 不新增告警类别；原测试要求引用的 `tests/test_hyperparameter_optimizer.py` 不存在，已更正为 `tests/test_model_pipeline.py::TestHyperparameterOptimizer`（D-028）。
  - #122：`docs/TEST_PERF.md` §7.1 仍只到 #111；#113–#119 待补。
- 上轮 #117–#119 验收结论保持有效（见 2026-10-20 验收账与 Issue comments）。**2026-10-21 复核轮独立抽查交付物**（不只信报告文字）：`git show 8f1cc63` 确认 7 处 `utcnow()` 已换 `utcnow_naive()` 且 `grep -rn utcnow src` 仅剩定义/注释/helper 引用（#117）；`git show 574aa34` 确认 `main()` 逐项累加 `failures` 并新增 `test_main_exit_code_on_failure` 断言 `SystemExit.code == 1`（#118）；`git show ab430f7 --stat` 确认 10 个测试文件 +107/−10 行、均为 `console.error` spy + 断言（#119）。三者证据成立，无需 reopen。

## Milestone 实际计数（按 GitHub issue state，不凭报告/API 计数器）

- **M6 测试性能优化：10 / 10 CLOSED，未收敛；2026-10-20 依 D-023 默认 A 冻结**。milestone state=open、open_issues=0、closed_issues=10。CLOSED：#88–#95、#106、#107。成功信号 1/3：覆盖率达成（≥68.49%），串行 <30s 与完整 CI <240s 均未达。D-023 已默认转正 A（保持 open、不改阈值、不追加投入）；B/C 需用户明确授权。
- **M7 候选与既有交付纠偏：6 / 11 CLOSED**。milestone state=open、open_issues=5、closed_issues=6。成员 11（#97/#98/#99/#100/#101/#102/#103/#104/#105/#108/#109，#96 为 Epic 不计分母）。done：#97/#99/#103/#104/#105/#108；OPEN：#98（in-progress 冻结）、#109（blocked）、#100/#101/#102（needs-info）。
- **#110–#122 不设 milestone**（仓库与测试卫生，不计入任何成功信号分母，D-021/D-025/D-027）。

## 本轮已运行验证（Planner，只读；代码 HEAD `afee0c4`，规划提交 `8e924e8` 仅动 `.agent/`）

- `git fetch --all --prune` + `git pull --rebase` → Already up to date，main `8e924e8`；`git status --short` → 干净；`git diff --name-only afee0c4..HEAD` → 仅 3 个 `.agent/` 文件。
- `gh pr list --state open` → 无 open PR；`gh issue list --label in-review` → 空；`--label in-progress` → 仅 #98（冻结）；`--label ready` → #120/#121/#122。
- `gh run list --limit 6` → 最新 main 运行 39463001921（CI，4m44s）/ 39463001509（Security Scan）均 completed/success。
- native fast gate（2026-10-21 规划轮实测）：`.venv/bin/python -m pytest -m "unit or api" -p no:launch_testing -p no:launch_ros -o addopts="" -q` → exit 0（`1495 passed, 69 skipped, 196 deselected, 92 warnings in 39.45s`）。复核轮未重跑：自该轮后仅 `.agent/` 变更，且 CI 在 `8e924e8` 上全绿。
- 定向模型测试：`.venv/bin/python -m pytest tests/test_model_improvements.py -p no:launch_testing -p no:launch_ros -o addopts="" -q` → exit 0（`7 passed, 9 warnings`，含 1 条 UndefinedMetricWarning）。
- `grep -rn "@import" frontend/src --include=*.scss --include=*.vue` → 仅 `frontend/src/styles/index.scss:8`。
- **#120 现状实测（2026-10-21 复核新增）**：`cd frontend && npm run build` → exit 0（`built in 8.84s`），输出中 `DEPRECATION WARNING [import]` 计数恰为 **1**（指向 `src/styles/index.scss 8:9`）→ 前提成立，且改动后「归零」是可判定的完成信号。
- **#120 迁移安全性（2026-10-21 复核新增）**：`grep -c '\$[a-zA-Z_-]\|@use\|@import\|@mixin\|@include\|@function' frontend/src/styles/animations.scss` → **0**（478 行全部为 keyframes、选择器与 CSS 自定义属性）→ `@import` 改 `@use ... as *` 不切断任何跨文件 SCSS 变量/混入作用域；且 `animations.scss` 全仓仅被 `index.scss:8` 引用，不会重复输出 CSS。Vite `vite.config.js:73` 的 `additionalData: '@use "@/styles/variables.scss" as *;'` 注入在文件首行，新 `@use` 落在第 8 行仍位于首条样式规则 `* {}` 之前，位置合法。
- `grep -n "classification_report" src/model/trainModel.py src/model/hyperparameter_optimizer.py` → 两处调用均未传 `zero_division`。
- `ls tests/test_hyperparameter_optimizer.py` → 不存在；`grep -n "class TestHyperparameterOptimizer" tests/test_model_pipeline.py` → 第 233 行存在（#121 规格更正依据）。
- `docs/TEST_PERF.md` §7.1 现状：#88–#95、#106–#108、#110–#112 齐全，#113–#119 缺失；#113–#119 经 `gh` 逐条核实全部 CLOSED。
- 未跑：frontend lint/vitest、fallback fast gate、integration/external（本轮仅做任务前提核验，执行时由 Executor 全量复跑）。

## 给 Executor 的握手要求

- 接手先按真实 Git/Issue 核对 STATE/HANDOFF/ENV，并在当日 DIARY 追加记录（严格遵守 append-only）。
- **已知现场漂移（Executor 文件，Planner 不代改）**：`STATE.md` 第 6–8 行与 `HANDOFF.md` 第 10/30 行仍写着 #117/#118/#119 处于 `in-review`「等待 Planner 复跑验收」，但三者已于 2026-10-20 验收关闭。接手第一件事就是按真实 Issue/DIARY 重写这两份快照，不要据此误判还有待验收交付。
- 本轮按建议顺序依次领取 #120、#121、#122；各任务完成后按契约 1.7 在 Issue comment 提交执行报告并转 in-review，**绝不自行 close**。
- #121 请按更正后的 Issue 规格执行：只改两个源文件，测试运行 `tests/test_model_improvements.py` 与 `tests/test_model_pipeline.py`，不要引用不存在的 `tests/test_hyperparameter_optimizer.py`。
- #98/#109/#96/#100/#101/#102/#59 保持冻结/阻塞；不启动 M7 扩展、不改 M6 阈值、不做 CI 拓扑改造。
- 记录新基线：后端 fast gate 以本轮实测 `1495/69/196/92 warnings`（native）为参考，但警告数受随机划分影响，以实际运行输出为准；前端 41/190、stderr 零 `stderr |` 块。`.agent` 变更与代码/文档变更严格分属不同 commit 提交。

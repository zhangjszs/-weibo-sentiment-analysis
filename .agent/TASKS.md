# TASKS — GitHub Issue 本地镜像

> 更新于 2026-10-22，Planning 轮 **整体重写**（Issue 为权威来源，每轮重新拉取真实状态）。本轮验收：#120/#121/#122 独立复跑全部通过并关闭为 done；新建今日队列唯一 ready 任务 #123（前端 vitest 覆盖率本地可见性）。gh 可用、账号 zhangjszs、scope repo+workflow，未降级、未重复创建。
> 生命周期标签：`ready` / `in-progress` / `in-review` / `blocked` / `needs-info` / `done`；优先级 `priority:P0`–`P4`。
> Executor：先改 Issue 标签/comment，再同步本行；只改执行状态与报告，不改任务范围。完整规格/非目标/checklist 见对应 Issue。

## 今日队列（2026-10-22 执行轮 · 建议顺序；1 项，无依赖）

| 顺序 | Issue / 目标 | P | 状态 | 可直接执行的边界与完成证据 |
|---|---|---|---|---|
| 1 | [#123 为前端 vitest 建立本地覆盖率可见性（reporter-only，无阈值门禁、不动 CI）](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/123) | P3 | ready | 装 `@vitest/coverage-v8@3.2.7`（devDep，匹配已装 vitest 3.2.7）+ `frontend/vitest.config.js` 新增 `test.coverage`（provider v8 / all true / include src/**/*.{js,vue} / reporter text+lcov）+ `package.json` 新增 `test:coverage` 脚本 + 确认 `.gitignore` 忽略 `coverage/`。**明确不做**：不设 `coverage.thresholds` 门禁、不动 `ci.yml`、不改被测源码与用例。验证：`npm ci && npm run test:coverage` exit 0 打印逐文件覆盖率表；`test:run` 仍 41/190 全绿、`lint`/`build` exit 0；`git diff` 确认 ci.yml 零改动。 |

队列说明：P0=0、P1=0、P2=0、P3=1、P4=0；共 1 项 ready。本轮从「实测事实」中只提炼出这 1 项能通过 4.2 门禁且本地可验证、不触碰契约 1.10 红线的卫生任务——**宁可队列薄，不制造伪工作**（见 PLAN「下一阶段」与 D-030）。#123 属测试策略（契约 6.1 Planner 权限）；引入的 `@vitest/coverage-v8` 为 vitest 官方生态 devDependency、纯测试工具、可回滚，**非重大依赖**；「加 CI 步骤 / 设阈值」两部分已明确排除，属需用户授权的红线，另立。

已排查但**本轮不入 ready** 的候选（依据见 PLAN「下一阶段」）：
- `tests/test_db.py:95` 的 `assert True`（恒真弱断言）：文件标 `pytestmark = pytest.mark.integration`，本机无 MySQL 会 skip，验收「依赖满足 + 逐条可判定」在本地不成立 → 待有 MySQL 的集成批次再处理。
- fast gate 剩余项目自有告警全为 CJK 字体 `Glyph ... missing`（`src/utils/chart_renderer.py:39` 13 处、`src/model/trainModel.py` 5 处 UserWarning）：属环境/字体依赖，D-027 明确列为非目标，不追。
- §7.4 其余候选（integration 补用例、测试规范固化）：前者需外部 MySQL/Redis，后者难写成可判定 checklist，均不满足本地 ready 门禁。

## 等待验收（in-review）

- 无。#120/#121/#122 已于 2026-10-22 独立复跑验收通过并关闭（详见各 Issue 验收 comment）。

## 阻塞 / 待决策（全部保留，不可领取实现）

| Issue | P | 状态 | 阻塞事实 / 下一步 |
|---|---|---|---|
| [#98 Rust 第一切片](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/98) | P2 | in-progress（M7） | 2026-10-16 首次验收失实后 reopen；原生产迁移、既有用例双 backend、真实 Criterion 标准仍留本 Issue。D-019 默认 A 生效后继续冻结；保持现场不重置，下一棒不得领取。状态超 24h 属有意冻结，不作「疑似中断」处理。 |
| [#109 OTLP metrics 接收与 Jaeger 展示](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/109) | P2 | blocked（M7） | 本机无 Docker、无已知已授权 Docker 主机；console smoke 不替代真实 profile/UI 验收。解除环境阻塞后再验证，禁止自行新增 metrics 服务/长期成本。 |
| [#96 M7 候选 Epic](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/96) | P2 | needs-info | D-019 于 2026-10-18 默认转正 A = 暂停 M7 扩展。B/C 未批准；Epic 不计入分母，保持冻结。 |
| [#102 ABI/CI 矩阵](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/102) | P2 | needs-info（M7） | 待 D-019 B/C 授权，且 #98 未 done；不得以 abi3 标记代替 3.11/3.12 双实现执行。 |
| [#100 Qdrant 语义搜索候选](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/100) | P3 | needs-info（M7） | 新服务/模型与资源边界未授权；不得默认下载模型、启动 Qdrant 或返回假成功。 |
| [#101 SSE 摘要候选](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/101) | P3 | needs-info（M7） | 产品入口、LLM 成本与数据范围未定；不得变更认证模型或发出付费请求。 |
| [#59 产品功能需求收集](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/59) | P2 | needs-info | D-012 默认 A 有效；#100/#101 是候选而非用户已确认需求，本轮不重复追问输入方式。 |

## 本轮验收账（2026-10-22）

- **#120（P4，前端 Sass `@import`→`@use`）：通过 → done/CLOSED。** 独立复跑：`git show d7e0c59` 仅改 `frontend/src/styles/index.scss` 1 文件；本机 `cd frontend && npm run build` exit 0 且 `DEPRECATION WARNING [import]` 计数 = 0。验收 comment 6339916031。
- **#121（P4，`classification_report` 显式 `zero_division=0`）：通过 → done/CLOSED。** 独立复跑：`git show 6a37d95` 仅改 2 源文件且两处调用均传 `zero_division=0`；`pytest tests/test_model_improvements.py tests/test_model_pipeline.py` exit 0、22 passed、`UndefinedMetricWarning` 计数 = 0；fast gate native 1495/69/196/92 warnings exit 0；`ruff check src tests scripts` exit 0。验收 comment 6339920010。
- **#122（P4，`docs/TEST_PERF.md` §7.1 刷新）：通过 → done/CLOSED。** 独立复跑：`git show 0f2221c` 仅改 `docs/TEST_PERF.md`（+10/−3）；§7/§7.1 标注「（2026-10-21 刷新）」；§7.1 议题行精确覆盖 Issue 原文范围 #88–#95、#106–#108、#110–#119 共 21 项（未蔓延，D-029 口径）；`ruff` exit 0。验收 comment 6339921736。
- 三项均一次性通过，无 reopen、无「报告失实」。Executor 已按上轮握手要求重写 STATE/HANDOFF（#117/#118/#119 快照漂移已修复），2026-10-21 日报齐备，跨天链完整。

## Milestone 实际计数（按 GitHub issue state，不凭报告/API 计数器）

- **M6 测试性能优化：10 / 10 CLOSED，未收敛；2026-10-20 依 D-023 默认 A 冻结**。milestone state=open、open_issues=0、closed_issues=10。成功信号 1/3：覆盖率达成（≥68.49%），串行 <30s 与完整 CI <240s 均未达（#112 证明为结构性差距）。B/C 需用户明确授权。
- **M7 候选与既有交付纠偏：6 / 11 CLOSED**。milestone state=open、open_issues=5、closed_issues=6。成员 11（#97/#98/#99/#100/#101/#102/#103/#104/#105/#108/#109，#96 为 Epic 不计分母）。done：#97/#99/#103/#104/#105/#108；OPEN：#98（in-progress 冻结）、#109（blocked）、#100/#101/#102（needs-info）。
- **#110–#123 不设 milestone**（仓库、测试与前端度量卫生，不计入任何成功信号分母，D-021/D-025/D-027/D-030）。

## 本轮已运行验证（Planner，只读；代码 HEAD 停在 Executor 交付，规划提交仅动 `.agent/`）

- `git fetch --all --prune` + `git pull --rebase` → Already up to date；`gh auth status` → zhangjszs（repo+workflow scope）。
- `gh issue list --label in-review --state open` → 验收前 #120/#121/#122，处理后为空；`--label ready` → 处理后仅 #123；`--label in-progress` → 仅 #98（冻结）；`--label blocked` → #109；`--label needs-info` → #96/#100/#101/#102/#59。
- 验收复跑（详见「本轮验收账」）：`git show d7e0c59/6a37d95/0f2221c`；`ruff check src tests scripts` exit 0；定向模型测试 22 passed / `UndefinedMetricWarning`=0；native fast gate 1495 passed / 69 skipped / 196 deselected / 92 warnings（36.88s）；`cd frontend && npm run build` exit 0 / `DEPRECATION [import]`=0。
- 最新 main CI：run 39595065690（CI 5m58s）与 39595065710（Security Scan 2m19s）均 completed/success。
- 未跑（本轮无需）：frontend lint/vitest/test:run（#123 未执行，属 Executor 现场）、fallback gate、integration/external（外部依赖）。

## 给 Executor 的握手要求

- 接手先按真实 Git/Issue 核对 STATE/HANDOFF/ENV，并在 `.agent/DIARY/2026-10-22.md` 追加当日记录（严格 append-only，已写入的行不得修改）。
- 本轮领取 #123：严格按 Issue「明确不包含」执行——**只建覆盖率可见性，不设阈值门禁、不改 `ci.yml`、不改被测源码/用例**；`@vitest/coverage-v8` 版本须与已装 vitest（3.2.7）匹配；完成后按契约 1.7 在 Issue comment 提交执行报告并转 in-review，**绝不自行 close**。
- #98/#109/#96/#100/#101/#102/#59 保持冻结/阻塞/needs-info，不启动 M7 扩展、不改 M6 阈值、不做 CI 拓扑改造。
- `.agent/` 变更与代码/文档变更严格分属不同 commit（`chore(agent): ...`）。

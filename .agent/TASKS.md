# TASKS — GitHub Issue 本地镜像

> 更新于 2026-10-23，Planning 轮 **整体重写**（Issue 为权威来源，每轮重新拉取真实状态）。本轮验收：#123 独立复跑全部通过并关闭为 done（附一处报告表述更正）；新建今日队列 #124/#125/#126。gh 可用、账号 zhangjszs、scope repo+workflow，未降级、未重复创建。
> 生命周期标签：`ready` / `in-progress` / `in-review` / `blocked` / `needs-info` / `done`；优先级 `priority:P0`–`P4`。
> Executor：先改 Issue 标签/comment，再同步本行；只改执行状态与报告，不改任务范围。完整规格/非目标/checklist 见对应 Issue。

## 今日队列（2026-10-23 执行轮 · 建议顺序；3 项，无依赖）

| 顺序 | Issue / 目标 | P | 状态 | 可直接执行的边界与完成证据 |
|---|---|---|---|---|
| 1 | [#124 补齐 frontend/src/utils/index.js 未覆盖函数的单元测试](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/124) | P3 | in-review | 新增独立测试文件覆盖 formatPercent/formatDate/formatRelativeTime/formatFileSize/debounce/throttle/copyToClipboard/generateId/deepClone/downloadFile/downloadBlob/isEmpty/getEnumLabel/downloadCsv。**明确不做**：不改生产源码、不改现有 format-utils.test.js、不测 chinaMap/stores/composables/API 层、不设阈值、不动 CI 与依赖。验收：`test:run` 全绿且 ≥190；`src/utils/index.js` Stmts/Funcs/Lines ≥90%；`lint` exit 0；diff 仅新测试文件；关键行为显式断言（CSV 转义/BOM、debounce 延迟、isEmpty 四类输入、deepClone 引用隔离）。 |
| 2 | [#125 补齐 frontend/src/api/request.js 拦截器错误分支测试](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/125) | P3 | in-review | 新增 `tests/request-error-paths.test.js`：2xx（200/201/202）透传、409 透传且不弹错、业务码 401/403/404/500/默认、HTTP 状态 401/403/404/408/500/502/503/默认、ECONNABORTED、网络错误、配置错误、401 登出跳转防重入与 redirect 参数。**明确不做**：不改 request.js、不改现有 request-loading.test.js、不测 8 个 API 包装模块、不设阈值、不动 CI。验收：单文件可独立跑；`test:run` 全绿；request.js Stmts/Lines ≥90%、Branch ≥85%；`lint` exit 0；diff 仅新测试文件。 |
| 3 | [#126 刷新 docs/TEST_PERF.md §7.1/§7.4 并记录前端覆盖率基线（#120–#123）](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/126) | P4 | in-review | §7.1 追加 #120–#123 四行；§7.4 删除过时的「前端 vitest 覆盖率配置未配置」；新增 §7.5 记录 41 files/190 tests 与 80.55/72.66/30.95/80.55 基线、0% 模块清单、阈值/CI 未授权声明；刷新日期 2026-10-23。**明确不做**：不改 README（用户未提交改写在途）、不改代码/测试/CI、不重写历史数据。验收：diff 仅 `docs/TEST_PERF.md`；四行与提交号准确；基线数值与实际输出一致；无过时表述。 |

队列说明：P0=0、P1=0、P2=0、P3=2、P4=1；共 3 项 ready。选题依据 = #123 首次可见的覆盖率基线：`src/utils/index.js` 30.53% Stmts / 26.31% Funcs，`src/api/request.js` 72.51% Stmts / 37.5% Funcs，以及 `docs/TEST_PERF.md` 的已知漂移。三项均属测试/文档卫生（契约 6.1 Planner 权限），本地可验证、可回滚、不触碰契约 1.10 红线（D-031）。

已排查但**本轮不入 ready** 的候选：
- 8 个前端 API 包装模块（alert/content/favorites/platform/predict/propagation/report/user，均 0%）：全部是 `request({url, method, data/params})` 的声明式薄封装；用 mock 断言调用参数等于复述源码，属 PLAN 非目标「为覆盖率数字添加 mock 测试」；若做，应改为跨端路由契约校验，需另立规格。main.js 属入口，豁免。
- `src/utils/chinaMap.js`（34.61%）：fetch 单例/失败重试语义可测，但价值与规模均小于 #124；暂不单独立项。
- `src/stores/user.js`（48.48%）：initAuth 分支未覆盖，但与 #125 同属共享基础设施，避免同批两项跨层测试挤压执行容量；视 #125 结果后续评估。
- `tests/test_db.py:95` 的 `assert True`：integration-only，本机无 MySQL 无法满足本地验收，待有 MySQL 的集成批次。
- CJK 字体 `Glyph ... missing` 告警：环境/字体依赖，D-027 非目标。

## 等待验收（in-review）

- 无。#123 已于 2026-10-23 独立复跑验收通过并关闭（验收 comment 6355206818）。

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

## 本轮验收账（2026-10-23）

- **#123（P3，前端 vitest 覆盖率可见性）：通过 → done/CLOSED。** 独立复跑：`npm ci` exit 0；`npm run test:coverage` exit 0，41 files / 190 tests，`All files 80.55 | 72.66 | 30.95 | 80.55`；`test:run` 41/190 exit 0；`lint` exit 0；`build` exit 0（8.19s，DEPRECATION=0）；`npm ls` 显示 coverage-v8@3.2.7 与 vitest@3.2.7 deduped；`grep threshold` 无匹配；`git diff b45a40a..c77fbcb --stat -- .github/` 为空；`coverage/lcov.info` 存在且被 `frontend/.gitignore:13` 忽略；main CI 39776366919/39776366918 均 success。锁文件独立比对：435→451 包，+24/−8，**版本变动 0**。验收 comment 6355206818。
- **报告表述更正（不影响验收）**：执行报告称「零 registry 翻转」，实际 18 个包的 `resolved` 由 `registry.npmmirror.com` 归一化为 `registry.npmjs.org`（HANDOFF 风险段已如实记录）。版本/完整性未变，npm ci 与 CI 均通过；已在验收 comment 注明。
- 一次性通过，无 reopen、无「报告失实」；Executor 已按上一轮要求刷新 STATE/HANDOFF 并撰写 2026-10-22 日报，跨天链完整。

## Milestone 实际计数（按 GitHub issue state，不凭报告/API 计数器）

- **M6 测试性能优化：10 / 10 CLOSED，未收敛；2026-10-20 依 D-023 默认 A 冻结**。milestone state=open、open_issues=0、closed_issues=10。成功信号 1/3：覆盖率达成（≥68.49%），串行 <30s 与完整 CI <240s 均未达（#112 证明为结构性差距）。B/C 需用户明确授权。
- **M7 候选与既有交付纠偏：6 / 11 CLOSED**。milestone state=open、open_issues=5、closed_issues=6。成员 11（#97/#98/#99/#100/#101/#102/#103/#104/#105/#108/#109，#96 为 Epic 不计分母）。done：#97/#99/#103/#104/#105/#108；OPEN：#98（in-progress 冻结）、#109（blocked）、#100/#101/#102（needs-info）。
- **#110–#126 不设 milestone**（仓库、测试与前端度量卫生，不计入任何成功信号分母，D-021/D-025/D-027/D-030/D-031）。

## 本轮已运行验证（Planner，只读；代码 HEAD 停在 Executor 交付，规划提交仅动 `.agent/`）

- `git fetch --all --prune`；`git pull --rebase` 因工作区存在用户未提交的 `README.md` 改写而中止，但本地分支与 `origin/main` 已一致（HEAD `a6c87f6`），未 stash、未触碰用户改动。
- `gh issue list --state open` → 验收前 8 个 open：#123（in-review）、#98（in-progress）、#109（blocked）、#96/#100/#101/#102/#59（needs-info）；处理后 #123 关闭，#124/#125/#126 新建为 ready。
- 验收复跑（详见「本轮验收账」）：`git show 6812039`；`npm ci`、`npm run test:coverage`、`npm run test:run`、`npm run lint`、`npm run build` 全部 exit 0；`npm ls`；`grep threshold`；`git check-ignore`；锁文件逐包版本/`resolved` 比对。
- 最新 main CI：run 39776366919（CI）与 39776366918（Security Scan）均 completed/success（merge `c77fbcb`）。
- 未跑（本轮无需）：后端 fast gate（本轮仅前端/文档改动，沿用 2026-10-21 基线 native 1495/69/196、fallback 1493/71/196）、integration/external（外部依赖）。

## 给 Executor 的握手要求

- 接手先按真实 Git/Issue 核对 STATE/HANDOFF/ENV，并在 `.agent/DIARY/2026-10-23.md` 追加当日记录（严格 append-only，已写入的行不得修改）。
- 本轮领取顺序建议 #124 → #125 → #126；每项完成后按契约 1.7 在 Issue comment 提交执行报告并转 in-review，**绝不自行 close**。容量不足时按顺序完成，未领取项保持 ready 并写明原因。
- 严格按各 Issue「明确不包含」执行：只新增测试文件/只改 `docs/TEST_PERF.md`；不改生产源码、不改现有测试、不设覆盖率阈值、不动 `ci.yml` 与依赖。
- **不要触碰工作区中未提交的 `README.md`**（用户改写在途）：不得提交、还原、stash 或格式化该文件。
- #98/#109/#96/#100/#101/#102/#59 保持冻结/阻塞/needs-info，不启动 M7 扩展、不改 M6 阈值、不做 CI 拓扑改造。
- `.agent/` 变更与代码/文档变更严格分属不同 commit（`chore(agent): ...`）。

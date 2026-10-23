# TASKS — GitHub Issue 本地镜像

> 更新于 2026-10-23（第二轮，接续当日执行轮），Planning 轮 **整体重写**（Issue 为权威来源，每轮重新拉取真实状态）。本轮验收：#124/#125 通过关闭，#126 部分通过关闭（剩余口径并入 #129）；新建 #127/#128/#129。gh 可用、账号 zhangjszs、scope repo+workflow，未降级、未重复创建。
> 生命周期标签：`ready` / `in-progress` / `in-review` / `blocked` / `needs-info` / `done`；优先级 `priority:P0`–`P4`。
> Executor：先改 Issue 标签/comment，再同步本行；只改执行状态与报告，不改任务范围。完整规格/非目标/checklist 见对应 Issue。

## 今日队列（2026-10-24 执行轮 · 建议顺序；3 项，无依赖）

| 顺序 | Issue / 目标 | P | 状态 | 可直接执行的边界与完成证据 |
|---|---|---|---|---|
| 1 | [#127 补齐 frontend/src/stores/user.js 登录态与 initAuth 分支测试](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/127) | P3 | in-review | 新增 `tests/user-store.test.js`，覆盖 initAuth 未认证/延长成功/延长失败/用户信息失败/异常跳转、doLogout 两路径、updateUserInfo、computed、resetAuthState 的 tabs 清理。**明确不做**：不改 stores/user.js、api/auth.js、authSession.js；不改 login-journey/auth-session 现有用例；不重复视图旅程与路由守卫；不设阈值、不动 CI/依赖。验收：单文件独立跑 exit 0；`test:run` 全绿且 ≥252；user.js Lines ≥90%、Branches ≥80%、Funcs ≥85%；`lint` exit 0；diff 仅新测试文件；关键分支逐条显式断言（未认证不请求 extend/getUserInfo、extend 抛错仍继续取用户、redirect 编码与 `/home` 回退、登出失败仍清态跳转、updateUserInfo 合并）。 |
| 2 | [#128 补齐 frontend/src/utils/chinaMap.js 单例与失败重试语义测试](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/128) | P3 | in-review | 新增 `tests/china-map.test.js`：首次 fetch/registerMap/返回值身份、并发共享一次 fetch、成功后再调用不重取、非 2xx 抛错且不注册、失败后重试成功、网络错误冒泡后可重试。模块级单例用 `vi.resetModules()` + 动态 import 隔离；URL 只断言包含 `assets/china.json`。**明确不做**：不改 chinaMap.js/echarts.js/组件；不加载真实资产、不发真实网络、不测渲染；不加依赖、不动 CI。验收：单文件独立跑 exit 0；`test:run` 全绿且 ≥252；chinaMap.js Lines ≥90%、Funcs 100%（1/1）；`lint` exit 0；diff 仅新测试文件；六场景均有显式断言。 |
| 3 | [#129 刷新 docs/TEST_PERF.md §7.1/§7.5（补 #124–#126 与 App.vue 0% 口径）](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/129) | P4 | in-review | §7.1 追加 #124（done，d58fa71）/ #125（done，2ab34b3）/ #126（done(partial)，c0d7e22）；§7.5 更新段去「转 in-review」、0% 清单补 `src/App.vue`（根壳豁免）；日期刷新为执行当日；43/252 与四项数值保持与实际一致。**明确不做**：不改 README/代码/测试/CI/依赖；不重写历史基线；不设阈值。验收：diff 仅 `docs/TEST_PERF.md`；三行与提交号经 git 核对；无 in-review 表述；0% 清单含 App.vue；日期正确。 |

队列说明：P0=0、P1=0、P2=0、P3=2、P4=1；共 3 项 ready。选题依据 = 验收后实测覆盖率：`src/stores/user.js` 48/99 行（7/10 分支、3/7 函数，会话恢复无直接用例）、`src/utils/chinaMap.js` 9/26 行（0/1 函数，单例/重试无任何用例），以及验收后 `docs/TEST_PERF.md` 的账目滞后（§7.1 缺三行、§7.5 仍写 in-review、0% 清单漏 App.vue）。三项均属测试/文档卫生（契约 6.1 Planner 权限），本地可验证、可回滚、不触碰契约 1.10 红线（D-032）。

已排查但**本轮不入 ready** 的候选：
- 8 个前端 API 包装模块（alert/content/favorites/platform/predict/propagation/report/user，行覆盖 0%）：全部是 `request({url, method, data/params})` 的声明式薄封装；用 mock 断言调用参数等于复述源码，属 PLAN 非目标「为覆盖率数字添加 mock 测试」；若做，应改为跨端路由契约校验，需另立规格。
- `src/main.js` 与 `src/App.vue`（0%）：应用入口/根组件壳，豁免；#129 只把 App.vue 补进文档清单，不补测。
- `src/stores/app.js`（28/39 行、1/4 函数）：候选，但本批已含一个 store 测试，避免同类跨层挤压容量；验收后按覆盖率数据再评估。
- `src/stores/tabs.js`（115/172 行）：状态机较复杂，需单独设计规格；暂不立项。
- `tests/test_db.py:95` 的 `assert True`：integration-only，本机无 MySQL 无法满足本地验收，待有 MySQL 的集成批次。
- CJK 字体 `Glyph ... missing` 告警：环境/字体依赖，D-027 非目标。

## 等待验收（in-review）

- 无。#124/#125/#126 已于 2026-10-23 第二轮验收处理完毕（#124/#125 done；#126 done(partial)，缺口由 #129 承接）。

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

## 本轮验收账（2026-10-23 第二轮）

- **#124（P3，utils/index.js 补测）：通过 → done/CLOSED。** 独立复跑：`npx vitest run tests/utils-index-core.test.js` exit 0（37 passed）；全量 43 files / 252 tests；`test:coverage` exit 0，utils/index.js lines 222/226（98.23%）、branches 100/103（97.09%）、funcs 20/20（100%）；`lint` / `build` exit 0；stderr 块 0；`git show --stat d58fa71` 仅新增 391 行测试文件；CI 5/5 success。报告 Branch 97.08 与 lcov 97.087% 属舍入差异，不影响门槛。验收 comment 6367582499。
- **#125（P3，request.js 错误分支）：通过 → done/CLOSED。** 独立复跑：单文件 25 passed；全量 43/252、stderr 0；request.js lines 161/171（94.15%）、branches 45/47（95.74%）、funcs 3/8（37.5%，http 薄封装按 Issue 排除）；`lint` / `build` exit 0；`git show --stat 2ab34b3` 仅新增 249 行测试文件；CI 5/5 success。断言已读文件核对（401 跳转编码、并发一次、409 不弹错、reject 对象身份）。验收 comment 6367599294。
- **#126（P4，TEST_PERF 刷新）：部分通过 → done/CLOSED，剩余由 #129 承接。** 独立核对：`git show --stat c0d7e22` 仅 `docs/TEST_PERF.md`（+27/−4）；§7.1 四行与提交号准确；§7.4 过时表述已无匹配；§7.5 双段数值与实际输出一致；日期 2026-10-23；CI 5/5 success。**未满足**：0% 清单漏列 `src/App.vue`（实测 0/14 行）。剩余量并入 #129，不 reopen。验收 comment 6367604032。

## Milestone 实际计数（按 GitHub issue state，不凭报告/API 计数器）

- **M6 测试性能优化：10 / 10 CLOSED，未收敛；2026-10-20 依 D-023 默认 A 冻结**。milestone state=open、open_issues=0、closed_issues=10。成功信号 1/3：覆盖率达成（≥68.49%），串行 <30s 与完整 CI <240s 均未达（#112 证明为结构性差距）。B/C 需用户明确授权。
- **M7 候选与既有交付纠偏：6 / 11 CLOSED**。milestone state=open、open_issues=5、closed_issues=6。成员 11（#97/#98/#99/#100/#101/#102/#103/#104/#105/#108/#109，#96 为 Epic 不计分母）。done：#97/#99/#103/#104/#105/#108；OPEN：#98（in-progress 冻结）、#109（blocked）、#100/#101/#102（needs-info）。
- **#110–#129 不设 milestone**（仓库、测试与前端度量卫生，不计入任何成功信号分母，D-021/D-025/D-027/D-030/D-031/D-032）。

## 本轮已运行验证（Planner，只读；代码 HEAD 停在 Executor 交付，规划提交仅动 `.agent/`）

- `git fetch --all --prune`；`git status -sb` → `main...origin/main`（无 ahead/behind），工作区干净（README 已由 `0e778ae` 提交，旧「未提交 README」注意事项作废）。
- `gh issue list --state open` → 验收前 8 个 open：#124/#125/#126（in-review）、#98（in-progress）、#109（blocked）、#96/#100/#101/#102/#59（needs-info）；处理后三个 in-review 关闭，#127/#128/#129 新建为 ready。
- 前端独立复跑：`npx vitest run tests/utils-index-core.test.js`（37 passed）、`npx vitest run tests/request-error-paths.test.js`（25 passed）、`npm run test:run`（43/252）、`npm run test:coverage`（All files 82.48/75.30/34.22/82.48）、`npm run lint`、`npm run build` 全部 exit 0；`grep -c "stderr |"` → 0；lcov 逐文件核对 utils/index.js、request.js、stores/user.js、chinaMap.js、App.vue 与 8 个 API 模块。
- 提交核对：`git show --stat d58fa71 / 2ab34b3 / c0d7e22` → 分别仅 1 个目标文件；`git diff --stat 0e778ae..HEAD -- . ':(exclude).agent'` → 2 个测试文件 + 1 个文档。
- CI：五个提交（d58fa71 / 2ab34b3 / c0d7e22 / 82bf43c / 216aada）的 check-runs 均 completed/success（backend-fast / frontend-fast / integration / rust-core / security-scan）。
- 未跑（本轮无需）：后端 fast gate（本轮仅前端/文档改动，沿用 2026-10-21 基线 native 1495/69/196、fallback 1493/71/196）、integration/external（外部依赖）。

## 给 Executor 的握手要求

- 接手先按真实 Git/Issue 核对 STATE/HANDOFF/ENV，并在 `.agent/DIARY/<当日>.md` 追加当日记录（严格 append-only，已写入的行不得修改）。
- 本轮领取顺序建议 #127 → #128 → #129；每项完成后按契约 1.7 在 Issue comment 提交执行报告并转 in-review，**绝不自行 close**。容量不足时按顺序完成，未领取项保持 ready 并写明原因。
- 严格按各 Issue「明确不包含」执行：只新增测试文件/只改 `docs/TEST_PERF.md`；不改生产源码、不改现有测试、不设覆盖率阈值、不动 `ci.yml` 与依赖。
- #98/#109/#96/#100/#101/#102/#59 保持冻结/阻塞/needs-info，不启动 M7 扩展、不改 M6 阈值、不做 CI 拓扑改造。
- `.agent/` 变更与代码/文档变更严格分属不同 commit（`chore(agent): ...`）。

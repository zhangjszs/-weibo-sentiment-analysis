# TASKS — GitHub Issue 本地镜像

> 更新于 2026-10-20，Planning 轮（验收 2026-10-20 执行轮交付 #114/#115/#116；D-023 默认转正 A；编排 #117/#118/#119）整体重写。**GitHub Issue 为权威来源**；本轮开头重新拉取真实状态（gh 可用、账号 zhangjszs、scope repo+workflow），未降级、未重复创建。
> 生命周期标签：`ready` / `in-progress` / `in-review` / `blocked` / `needs-info` / `done`；优先级 `priority:P0`–`P4`。
> Executor：先改 Issue 标签/comment，再同步本行；只改执行状态与报告，不改任务范围。完整规格/非目标/checklist 见对应 Issue。

## 今日队列（2026-10-20 执行轮 · 建议顺序；3 项，无互相依赖）

| 顺序 | Issue / 目标 | P | 状态 | 可直接执行的边界与完成证据 |
|---|---|---|---|---|
| 1 | [#117 消除后端源码中 datetime.utcnow() 的 DeprecationWarning](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/117) | P3 | in-review | 替换 `src/services/startup_service.py:154`、`src/repositories/comment_repository.py:370` 与 5 个模型列默认值（`user.py` / `article.py` / `audit_log.py` / `repost.py` / `user_favorite.py`）的 `datetime.utcnow()` 为等价 naive UTC（推荐共享 helper）；不改 schema、不改为 aware 存储、不升级依赖。验证：项目自有文件零 `utcnow() is deprecated`，fast gate 双模式计数 1494/69/196 与 1492/71/196 不变，警告数较 149 至少减 3，naive UTC 回归测试通过，ruff exit 0。 |
| 2 | [#118 test_model_improvements.py 脚本直跑在用例失败时返回非零退出码](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/118) | P4 | in-review | 修改 `tests/test_model_improvements.py` 的 `main()`：统计失败项，任一项失败 `sys.exit(1)`；新增失败路径测试（monkeypatch `test_*`，不得触发真实训练）。不改生产代码与训练参数。验证：失败路径 exit 1、成功路径 exit 0，fast gate 计数 +1（native 1495/69/196，fallback 1493/71/196），ruff exit 0。 |
| 3 | [#119 收敛前端错误态测试的预期 console.error 噪声](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/119) | P4 | in-review | 在 10 个受影响测试文件中 spy/mock `console.error` 并断言预期调用，测试后恢复；不改生产 `console.error` 行为与错误态断言。验证：`npm run test:run` 41 files / 190 tests 全绿，stderr `stderr \|` 块为 0，lint exit 0；仅改 `frontend/tests/`。 |

队列说明：P0=0、P1=0、P3=1、P4=2；共 3 项 ready，符合「2–5 个、宁缺毋滥」。三项均从实测告警/噪声中提炼、无互相依赖、过 4.2 门禁，无契约 1.10 红线。M6 由 D-023 默认 A 冻结，M7 由 D-019 A 冻结；本轮不设 milestone（D-021/D-025）。

## 等待验收（in-review）

- #117, #118, #119 已在本会话交付转 in-review，等待 Planner 独立复跑验收。

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

## 本轮验收账（2026-10-20 交付 · 2026-10-20 验收）

10-20 日报存在且 append-only；本轮以 `git show`、Issue 执行报告、独立复跑命令逐项核对（未仅信报告文字）。

| 交付 | 结论 / GitHub 当前状态 | 独立复跑证据（Planner，只读） | 未完成项去向 |
|---|---|---|---|
| #114 · `89a53ce`（merge `b225c32`） | **通过**，done / CLOSED | `git show 89a53ce` → 仅 `tests/test_model_improvements.py`（+53 -40），6 处 return 与 2 处 `try...except: return False` 已删除；`pytest tests/test_model_improvements.py -o addopts="" -q` → `6 passed, 9 warnings`（零 PytestReturnNotNoneWarning）；fast gate native 1494/69/196/149 warnings exit 0；ruff exit 0；最终 HEAD `68583cd` CI run `39286746222` 四 job 全绿 | 脚本直跑失败仍 exit 0 → 已立项 **#118（P4）** 承接，不影响本 Issue 验收 |
| #115 · `9b952cf`（merge `2a3b703`） | **通过**，done / CLOSED | `git show 9b952cf` → 仅 `tests/conftest.py` +2 行；定向用例加 `-W error::RuntimeWarning` 仍 `1 passed`（Celery RuntimeWarning 消除）；fast gate 1494/69/196/149 warnings exit 0；ruff exit 0；最终 HEAD CI 四 job 全绿 | 无遗留 |
| #116 · `4a32dbe`（merge `d4bce28`） | **通过**，done / CLOSED | `git show 4a32dbe` → 仅 4 个 Vue 文件（+17 -17）；`npm run test:run` → 41 files / 190 tests 全绿；stderr `ElementPlusError\|label act as value` 匹配数 **0**；`npm run lint` exit 0；`npm run build` exit 0（8.63s）；全仓无残留 `el-radio`/`el-checkbox` label 绑定；最终 HEAD CI 四 job 全绿 | 无遗留 |

**报告失实检查**：#114/#115/#116 均有独立实测证据支撑，未发现「声称完成但证据不支持」。中间提交 `b225c32`/`2a3b703`/`d4bce28` 的 CI run 被后续推送的 concurrency 取消，最终 HEAD `68583cd`（包含全部三处代码变更）CI 四 job 与 Security Scan 全绿，作为合并后验证证据。

## Milestone 实际计数（按 GitHub issue state，不凭报告/API 计数器）

- **M6 测试性能优化：10 / 10 CLOSED，未收敛；2026-10-20 依 D-023 默认 A 冻结**。milestone state=open、open_issues=0、closed_issues=10。CLOSED：#88–#95、#106、#107。成功信号 1/3：覆盖率达成（≥68.49%），串行 <30s 与完整 CI <240s 均未达。D-023 于本日连续 3 天无答复，按 6.3 默认转正为 A（保持 open、不改阈值、不追加投入）；B/C 需用户明确授权。
- **M7 候选与既有交付纠偏：6 / 11 CLOSED**。milestone state=open、open_issues=5、closed_issues=6。成员 11（#97/#98/#99/#100/#101/#102/#103/#104/#105/#108/#109，#96 为 Epic 不计分母）。done：#97/#99/#103/#104/#105/#108；OPEN：#98（in-progress 冻结）、#109（blocked）、#100/#101/#102（needs-info）。
- **#110–#119 不设 milestone**（仓库与测试卫生，不计入任何成功信号分母，D-021/D-025）。

## 本轮已运行验证（Planner，只读；基线 HEAD `68583cd`）

- `git show --stat`：`89a53ce` 仅 1 个测试文件；`9b952cf` 仅 conftest +2；`4a32dbe` 仅 4 个 Vue 文件。
- `.venv/bin/python -m pytest tests/test_model_improvements.py -p no:launch_testing -p no:launch_ros -o addopts="" -q` → exit 0（`6 passed, 9 warnings in 10.40s`）。
- `.venv/bin/python -m pytest tests/test_api_get_contract.py::TestGetEndpointsEnvelope::test_authenticated_admin -p no:launch_testing -p no:launch_ros -k "tasks" -o addopts="" -q -W error::RuntimeWarning` → exit 0（`1 passed, 49 deselected`）。
- 前端：`npm run test:run` → 41 files / 190 tests 全绿（5.77s），stderr `ElementPlusError|label act as value` = 0；`npm run lint` exit 0；`npm run build` exit 0（8.63s）。
- `.venv/bin/python -m pytest -m "unit or api" -p no:launch_testing -p no:launch_ros -o addopts="" -q` → exit 0（native `1494 passed, 69 skipped, 196 deselected, 149 warnings in 39.37s`）。
- `.venv/bin/python -m ruff check src tests scripts` → exit 0（All checks passed!）。
- 告警拆分：149 warnings 中 `utcnow() is deprecated` 4 条（项目自有 3 条：startup_service、comment_repository、SQLAlchemy 因模型默认值触发；第三方 circuitbreaker 1 条）；CJK glyph 18 条；seaborn 第三方 1 条。
- CI：HEAD `68583cd` run `39286746222` 四 job 全绿（rust-core / backend-fast / frontend-fast / integration）；Security Scan `39286747531` 绿。
- 未跑：本地 integration/external 层（涉外部 MySQL/Redis/真实 Weibo cookie）。

## 给 Executor 的握手要求

- 接手先按真实 Git/Issue 核对 STATE/HANDOFF/ENV，并按 D-022 写当日 DIARY（同日多个会话追加，不新建）。
- 本轮按建议顺序依次领取 #117、#118、#119；各任务完成后按契约 1.7 在 Issue comment 提交执行报告并转 in-review，**绝不自行 close**。
- #98/#109/#96/#100/#101/#102/#59 保持冻结/阻塞；不启动 M7 扩展、不改 M6 阈值、不做 CI 拓扑改造。
- **STATE 更正请求**：STATE.md 第 30 行仍记录 `home/index.vue` 的 `v-model cannot update a const reactive binding filters` 告警；Planner 2026-10-20 实跑 vitest 的 stderr 匹配数为 0。STATE 由 Executor 独占写入，请接手后按实测更正该条（不要改本文件或 PLAN）。
- 记录新基线：后端 fast gate 1494/69/196/149 warnings（native）、1492/71/196/149（fallback）；前端 41/190、stderr 零 ElementPlus 废弃告警。`.agent` 变更与代码/文档变更严格分属不同 commit 提交。

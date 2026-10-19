# TASKS — GitHub Issue 本地镜像

> 更新于 2026-10-19，Planning 轮（验收 10-19 执行轮交付 #113，为下一执行轮编排 #114/#115/#116 队列）整体重写。**GitHub Issue 为权威来源**；本轮开头重新拉取真实状态（gh 可用、账号 zhangjszs、scope repo+workflow），未降级、未重复创建。
> 生命周期标签：`ready` / `in-progress` / `in-review` / `blocked` / `needs-info` / `done`；优先级 `priority:P0`–`P4`。
> Executor：先改 Issue 标签/comment，再同步本行；只改执行状态与报告，不改任务范围。完整规格/非目标/checklist 见对应 Issue。

## 今日队列（下一执行轮 · 建议顺序；3 项，无互相依赖）

| 顺序 | Issue / 目标 | P | 状态 | 可直接执行的边界与完成证据 |
|---|---|---|---|---|
| 1 | [#114 消除 test_model_improvements.py 的 PytestReturnNotNoneWarning 与假绿吞异常反模式](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/114) | P3 | in-review | 修改 `tests/test_model_improvements.py`：移除 6 处测试函数末尾 `return <obj>` 使其返回 `None`；移除 `test_social_media_features` 与 `test_data_augmentation` 中的 `try...except Exception: return False` 吞异常假绿逻辑；为各用例补充有效断言。不改动 `src/model/` 生产代码与训练抽样参数。验证 6 passed 且警告列表中零 `PytestReturnNotNoneWarning`，fast gate 计数 1494/69/196 不变，ruff exit 0。 |
| 2 | [#115 conftest 补全 Celery task_store_eager_result 配置以消除 eager 任务查询告警](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/115) | P4 | in-review | 在 `tests/conftest.py` 的 `app` fixture 补全 Celery eager 存储配置：`monkeypatch.setitem(celery_app.conf, "task_store_eager_result", True)` 与 `monkeypatch.setenv("CELERY_TASK_STORE_EAGER_RESULT", "True")`。不改动 `src/tasks/celery_config.py` 生产配置。验证 `/api/tasks/<task_id>/status` 契约测试中消除 Celery `RuntimeWarning`，fast gate 计数保持一致，ruff exit 0。 |
| 3 | [#116 收敛前端单选与复选组件的 Element Plus 3.0 label 废弃警告](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/116) | P3 | in-review | 将 `report.vue`、`Header.vue`、`PredictInput.vue`、`spider.vue` 中绑定值的 `<el-radio-button>` 和 `<el-checkbox>` 的 `label` 属性替换为 `value`；保留按钮文字 slot 与 `<el-form-item label="...">` 不变。不升级依赖版本、不改动样式与接口。验证前端 41 files / 190 tests 全绿，stderr 消除 `label act as value` 废弃警告，lint 与 build exit 0。 |

队列说明：P0=0、P1=0、P3=2、P4=1；共 3 项 ready，符合「2–5 个、宁缺毋滥」。各任务相互独立且均过 4.2 门禁。M6 收口取决于 D-023（用户决策中，默认 A 先行），M7 扩展受 D-019 A 冻结。本轮编排 3 项纯工程与测试卫生任务，无触碰契约 1.10 红线。

## 等待验收（in-review）

- [#114 消除 test_model_improvements.py 的 PytestReturnNotNoneWarning 与假绿吞异常反模式](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/114)（已完成，merge `b225c32` @ main，待验收）
- [#115 conftest 补全 Celery task_store_eager_result 配置以消除 eager 任务查询告警](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/115)（已完成，merge `2a3b703` @ main，待验收）
- [#116 收敛前端单选与复选组件的 Element Plus 3.0 label 废弃警告](https://github.com/zhangjszs/-weibo-sentiment-analysis/issues/116)（已完成，merge `d4bce28` @ main，待验收）

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

## 本轮验收账（2026-10-19 交付 · 2026-10-19 验收）

10-19 日报存在且 append-only；本轮以 `git show`、Issue 执行报告、独立复跑命令逐项核对（未仅信报告文字）。

| 交付 | 结论 / GitHub 当前状态 | 独立复跑证据（Planner，只读） | 未完成项去向 |
|---|---|---|---|
| #113 · `6c6a0b6`（merge `53a8140`） | **通过**，done / CLOSED | `git show 6c6a0b6 --stat` → 仅 `tests/test_notification_service.py` 与 `docs/TEST_PERF.md`（+12 -6）；`pytest tests/test_notification_service.py::TestEmailSender::test_send_invalid_email` 独立复跑：`0.01s call`（0.61s 总时长）；零出站网络探针实测 `socket.getaddrinfo calls: []`（零网络调用）；Email 相关 7 passed 全绿，全文件 89 passed；fast gate native 实测 `1494 passed, 69 skipped, 196 deselected in 36.98s`（计数与基线一致）；`ruff check src tests scripts` exit 0；`scripts/check_documented_paths.py` exit 0；`docs/TEST_PERF.md §7.1` 中 #111/#112 准确刷新为 done；CI push run `39206140986` 四 job 全绿（backend-fast 2m13s / rust-core 45s / frontend-fast 1m2s / integration 1m53s） | 全部标准逐条满足，无遗留项 |

**报告失实检查**：#113 交付具备独立实测证据支撑，未发现「声称完成但证据不支持」；DNS 出站消除通过动态探针独立证实。

## Milestone 实际计数（按 GitHub issue state，不凭报告/API 计数器）

- **M6 测试性能优化：10 / 10 CLOSED，未收敛**。milestone state=open、open_issues=0、closed_issues=10。CLOSED：#88–#95、#106、#107。成功信号 1/3：覆盖率达成（≥68.49%），串行 <30s 与完整 CI <240s 均未达。**成员关闭 ≠ 里程碑收敛**；#112 分析已确认此为结构性差距，收口与否取决于 D-023。
- **M7 候选与既有交付纠偏：6 / 11 CLOSED**。成员 11（#97/#98/#99/#100/#101/#102/#103/#104/#105/#108/#109，#96 为 Epic 不计分母）。done：#97/#99/#103/#104/#105/#108；OPEN：#98（in-progress 冻结）、#109（blocked）、#100/#101/#102（needs-info）。
- **#110/#111/#112/#113/#114/#115/#116 不设 milestone**（仓库与测试卫生，不计入任何成功信号分母，D-021）。

## 本轮已运行验证（Planner，只读；基线 HEAD `0e4c09f`）

- `git show --stat 6c6a0b6` 与 merge `53a8140`：确认 #113 仅修改 1 处测试文件与 1 处文档，无生产代码改动。
- `.venv/bin/python -m pytest tests/test_notification_service.py::TestEmailSender::test_send_invalid_email -p no:launch_testing -p no:launch_ros -o addopts="" -vv --durations=0` → exit 0（`0.01s call`）。
- 网络探针挂载 `socket.getaddrinfo`：捕获调用列表为空 `[]`，证实无真实出站解析。
- `.venv/bin/python -m ruff check src tests scripts` → exit 0（All checks passed!）。
- `.venv/bin/python scripts/check_documented_paths.py` → exit 0（OK: all documented paths exist）。
- 本地 native fast gate：`1494 passed, 69 skipped, 196 deselected in 36.98s`（wall time 39.32s），用例计数与基线逐位一致。
- 前端测试套件：`cd frontend && npm run test:run` → 41 test files / 190 tests passed in 6.42s。
- 前端代码质量与构建：`npm run lint` → exit 0；`npm run build` → exit 0 in 8.78s。
- CI：GitHub Actions run `39206140986` @ `0e4c09f` 四 job 全绿（backend-fast / rust-core / frontend-fast / integration）。
- 未跑：本地 integration/external 层（涉外部 MySQL/Redis/真实 Weibo cookie）。

## 给 Executor 的握手要求

接手先按真实 Git/Issue 核对 STATE/HANDOFF/ENV，并按 D-022 写当日 DIARY；本轮按建议顺序依次领取 #114、#115、#116，各任务完成后按契约 1.7 在 Issue comment 提交执行报告并转 in-review，**绝不自行 close**。#98/#109/#96/#100/#101/#102/#59 保持冻结/阻塞；不启动 M7 扩展、不改 M6 阈值、不做 CI 拓扑改造。`.agent` 变更与代码/文档变更严格分属不同 commit 提交。

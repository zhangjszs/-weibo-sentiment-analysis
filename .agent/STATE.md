# STATE

> 事实账本（可机器解析）。「已完成」仅保留最近 20 条，更早的见 git 历史。

## 当前活跃
- 任务：2026-10-22 执行轮（会话 1）。本席 executor；今日队列 1 项（#123）完成转 in-review，ready 队列清空。
- 状态：in-review：#123；in-progress：无；ready：无。
- 本轮起点 main `b45a40a` → 现 main `c77fbcb`（#123 `6812039` + merge `c77fbcb`；已推送，临时分支已删）。
- 前端基线（#123 后实测）：`npm ci` exit 0；`test:coverage` exit 0（41 files / 190 tests，逐文件表输出；总覆盖率 Stmts 80.55 / Branch 72.66 / Funcs 30.95 / Lines 80.55）；`test:run` 41/190 全绿；`lint`/`build` exit 0；coverage/ 产物被 frontend/.gitignore:13 忽略。
- 后端 fast gate 本机基线（2026-10-21 #121 后实测，本轮未改后端）：native（WEIBO_CORE_RUST=1）1495 passed / 69 skipped / 196 deselected / 92 warnings（36.66s）；fallback（WEIBO_CORE_RUST=0）1493/71/196 / 92 warnings（34.05s）；全绿。
- 跨天链：正常（2026-10-22）——上一棒（2026-10-21）STATE/HANDOFF/DIARY 齐备；本轮 STATE 已刷新、HANDOFF 重写、DIARY 已写入 2026-10-22。

## 阻塞项
- #109（2026-10-17 仍 blocked）：本机无 Docker、无已知已授权 Docker 主机；console smoke 不替代真实 profile/UI 验收。
- #98（M7 冻结）：D-019 默认 A 生效后继续冻结，保持现场不重置，下一棒不得领取。
- #96 / #100 / #101 / #102 / #59（needs-info）：受 D-019 A 冻结或待产品需求确认。

## 关键事实（已实测验证）
- **前端覆盖率可见性建成（#123 实测）**：`@vitest/coverage-v8@3.2.7`（devDep，与 vitest 同版）+ `vitest.config.js` `test.coverage`（v8/all/src 下 js+vue/text+lcov，无门禁）+ `test:coverage` 脚本；锁文件零包版本变动（脚本逐包比对），仅新增依赖树与 glob 去重上提。
- **Sass 模块化兼容（#120 实测）**：`frontend/src/styles/index.scss:8` 已由 `@import` 迁移为 `@use './animations.scss' as *;`，Vite 构建彻底消除 Dart Sass 3.0 弃用警告。
- **模型评估无告警（#121 实测）**：`trainModel.py` 与 `hyperparameter_optimizer.py` 中 `classification_report` 调用已显式传入 `zero_division=0`，稀有类别不再触发 `UndefinedMetricWarning`。
- **文档透明度（#122 实测）**：`docs/TEST_PERF.md` §7.1 已刷新至 2026-10-21，完整补齐 #113–#119 真实交付记录与状态（21 项全部覆盖且状态为 done）。
- **前端规模（#68 后）**：.js 32（api 14 · utils 5 · stores 4 · composables 6 · router 1 · plugins 1 · main.js）· .vue 45（views 6305 行 · components 3322 行）· JS+Vue 合计 13,731 行。
- **前端测试基线**：41 files / **190 tests** 全绿。
- **Element Plus 3.0 前向兼容（#116 后）**：`report.vue`、`Header.vue`、`PredictInput.vue`、`spider.vue` 中绑定值的 `<el-radio-button>` 和 `<el-checkbox>` 已全部迁移至 `value` 属性，测试 stderr 零废弃警告。
- **大屏数据链路（#62 实测）**：`useBigScreen` 5 处失败路径原仅 `console.error`；`analysisStore.fetchAll` 内部 `allSettled`，**失败不抛出**，失败信息落在 `store.error`（只记第一项）。
- **拦截器兜底（勿重复弹窗）**：`api/request.js:82-166` 对每个失败请求已弹 ElMessage（业务码/HTTP 码/网络错误三类）。
- **#19 失败态语义落地状态**：`useTable.js` 已删；语义已落地在 #62、#65、#66、#67（失败保留旧数据 + 显式错误态/重试）。

## 已完成
- **#123 完成转 in-review（2026-10-22）**：前端 vitest 本地覆盖率可见性（reporter-only）；`npm ci`/`test:coverage`/`test:run`/`lint`/`build` 均 exit 0，ci.yml 零改动、无 thresholds 门禁；提交 `6812039` + merge `c77fbcb` @ main（已推送）；报告 comment 6340462567。
- **#122 完成转 in-review（2026-10-21）**：`docs/TEST_PERF.md` §7 与 §7.1 更新标注为 `（2026-10-21 刷新）`，追加 #113–#119 真实交付记录；脚本核验 21 项任务完整覆盖且均为 done；ruff exit 0；提交 `0f2221c` @ main（已推送）；报告 comment 6315186815。
- **#121 完成转 in-review（2026-10-21）**：`trainModel.py:249` 与 `hyperparameter_optimizer.py:428` 显式传入 `zero_division=0`；消除 `UndefinedMetricWarning`；定向模型测试 22 passed 0 failed；fast gate native 1495/69/196/92 warnings、fallback 1493/71/196/92 warnings 双模式全绿；提交 `6a37d95` @ main（已推送）；报告 comment 6315126611。
- **#120 完成转 in-review（2026-10-21）**：`frontend/src/styles/index.scss:8` 替换 `@import` 为 `@use './animations.scss' as *;`；消除 Vite 构建时 `DEPRECATION WARNING [import]` 弃用告警；前端 41 files / 190 tests 全绿，lint exit 0，build 8.19s exit 0；提交 `d7e0c59` @ main（已推送）；报告 comment 6315068551。
- **#119 验收关闭（2026-10-20）**：在 10 个测试文件中 spy/mock `console.error` 并断言预期错误记录；前端 41 files / 190 tests 全绿，stderr `stderr |` 块数从 32 降为 0，lint 与 build exit 0；提交 `ab430f7` @ main。
- **#118 验收关闭（2026-10-20）**：`tests/test_model_improvements.py` 的 `main()` 增加失败计数与 `sys.exit(1)`；新增 `test_main_exit_code_on_failure` 测试失败退出码；直跑成功退出码 0；fast gate native 1495/69/196、fallback 1493/71/196 全绿；提交 `574aa34` @ main。
- **#117 验收关闭（2026-10-20）**：替换项目中 7 处 `datetime.utcnow()` 为共享 `utils.datetime_utils:utcnow_naive()`；补齐 SQLite 下 naive UTC 回归测试；fast gate 双模式全绿，警告数净减 54+ 条；提交 `8f1cc63` @ main。
- **#116 验收关闭（2026-10-20）**：Element Plus 单选与复选组件 label act as value 弃用警告收敛；前端 41 files / 190 tests 全绿，stderr 消除相关警告；提交 `4a32dbe` → merge `d4bce28` @ main。
- **#115 验收关闭（2026-10-20）**：`tests/conftest.py` 补全 Celery task_store_eager_result 配置以消除 eager 任务查询告警；fast gate 全绿；提交 `9b952cf` → merge `2a3b703` @ main。
- **#114 验收关闭（2026-10-20）**：`tests/test_model_improvements.py` 移除 return 与吞异常假绿；提交 `89a53ce` → merge `b225c32` @ main。
- **#113 验收关闭（2026-10-19）**：`test_send_invalid_email` patch SMTP_SSL 消除真实网络出站；刷新 TEST_PERF §7.1 表格；提交 `6c6a0b6` → merge `53a8140` @ main。
- **#111 验收关闭（2026-10-18）**：同步旧 ruff 命令至各活文档与脚本；刷新 TEST_PERF 议题状态表；提交 `6834534` → merge `73e0074` @ main。
- **#112 验收关闭（2026-10-18）**：M6 残余差距只读分析；提交 `0c10122` → merge `33be94a` @ main。
- **#110 验收关闭（2026-10-17）**：`scripts/` 纳入 ruff 门禁并修复 8 项机械缺陷；提交 `cd0ea53`+`21535bc` → merge `1abfaf0` @ main。
- **#108 验收关闭（2026-10-17）**：Rust 工具链 pin 生效 + `.env.example` 四变量 + ADR-0005 边界；提交 `1889b6f`…`e2ecb5c` → merge `ddea0a9` @ main。
- **#106 验收关闭（2026-10-17）**：CI backend-fast 真实 `--durations` Top10 + 单例隔离 + socket 审计；提交 `cafe8ed`+`2f6790c`+`e23ba43` → merge `9a13987` @ main。
- **#107 验收关闭（2026-10-17）**：可观测模块行为验证恢复，覆盖率 native 68.5259% 达成；提交 `1d78f05`+`339c891` → merge `be32bd0` @ main。
- **#105 验收关闭（2026-10-17）**：去重基准真实重复率校正 + 真跑 Criterion；提交 `48e00c0`…`515c8c4` → merge `85f7f44` @ main。
- **#104 验收关闭（2026-10-17）**：Rust bridge Unicode 等价性 + iterator 回退丢数修复；提交 `9a75875` → merge `a88fd7a` @ main。
- **#90 验收关闭（2026-10-14）**：requirements-ml.txt 新建 + ci.yml 两 job 分层安装；提交 a023b1d → merge 26ce9ed @ main。
- **#92 验收关闭（2026-10-14）**：慢测试降规模；提交 23818f3 → merge 0730b7f @ main。

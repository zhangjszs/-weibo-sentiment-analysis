# STATE

> 事实账本（可机器解析）。「已完成」仅保留最近 20 条，更早的见 git 历史。

## 当前活跃
- 任务：2026-10-23 执行轮（会话 1）。本席 executor；今日队列 3 项（#124/#125/#126）全部完成转 in-review，ready 队列清空。
- 状态：in-review：#124/#125/#126；in-progress：无；ready：无。
- 本轮起点 main `0e778ae` → 现 main `c0d7e22`（#124 `d58fa71`、#125 `2ab34b3`、#126 `c0d7e22`，均已推送；三个临时分支本地+远端已删除）。
- 前端基线（本轮实测）：`npm run test:run` 43 files / 252 tests 全绿；`test:coverage` exit 0，All files Stmts 82.48 / Branch 75.30 / Funcs 34.22 / Lines 82.48；`src/utils/index.js` Stmts 98.23 / Branch 97.08 / Funcs 100 / Lines 98.23；`src/api/request.js` Stmts 94.15 / Branch 95.74 / Lines 94.15（Funcs 37.5，`http` 薄封装未测）；`lint` exit 0；`build` exit 0（8.45s）。
- #123 历史基线（41 files / 190 tests；80.55 / 72.66 / 30.95 / 80.55）已落盘 `docs/TEST_PERF.md` §7.5，并标注 #124/#125 后的当前实测。
- 后端 fast gate 本机基线（2026-10-21 #121 后实测，本轮未改后端）：native（WEIBO_CORE_RUST=1）1495 passed / 69 skipped / 196 deselected / 92 warnings（36.66s）；fallback（WEIBO_CORE_RUST=0）1493/71/196 / 92 warnings（34.05s）；全绿。
- 跨天链：正常（2026-10-23）——Planner 已完成规划轮并关闭 #123；本轮 STATE 已刷新、HANDOFF 已重写、DIARY 已写入 2026-10-23。

## 阻塞项
- #109（2026-10-17 仍 blocked）：本机无 Docker、无已知已授权 Docker 主机；console smoke 不替代真实 profile/UI 验收。
- #98（M7 冻结）：D-019 默认 A 生效后继续冻结，保持现场不重置，下一棒不得领取。
- #96 / #100 / #101 / #102 / #59（needs-info）：受 D-019 A 冻结或待产品需求确认。

## 关键事实（已实测验证）
- **utils 测试补齐（#124 实测）**：新增 `tests/utils-index-core.test.js`（37 用例），覆盖 14 个未测公开函数；`utils/index.js` 行 222/226（98.23%）、分支 100/103（97.08%）、函数 100%；未覆盖行为 `formatLocalDate` catch（jsdom 不可达）与 `deepClone` 末端不可达 return。
- **请求层错误分支（#125 实测）**：新增 `tests/request-error-paths.test.js`（25 用例），覆盖业务码/HTTP 状态/超时/网络/配置错误与 401 登出跳转编码、并发防重入、完成后再次跳转、路由缺失回退 `/home`；request.js 行 161/171（94.15%）、分支 45/47（95.74%）。
- **TEST_PERF 刷新（#126 实测）**：§7/§7.1 日期 2026-10-23；§7.1 追加 #120–#123（commit d7e0c59 / 6a37d95 / 0f2221c / 6812039）；§7.4 删除「覆盖率未配置」过时项；新增 §7.5 双段基线（#123 验收基线 41/190 与当前 43/252）。
- **前端覆盖率可见性（#123）**：`@vitest/coverage-v8@3.2.7` + `vitest.config.js` `test.coverage`（v8/all/src js+vue/text+lcov，无门禁）+ `test:coverage`；ci.yml 零改动。
- **Sass 模块化兼容（#120）**：`frontend/src/styles/index.scss:8` 已由 `@import` 迁移为 `@use './animations.scss' as *;`。
- **模型评估无告警（#121）**：`trainModel.py` 与 `hyperparameter_optimizer.py` 中 `classification_report` 已显式传入 `zero_division=0`。
- **前端规模（#68 后）**：.js 32（api 14 · utils 5 · stores 4 · composables 6 · router 1 · plugins 1 · main.js）· .vue 45（views 6305 行 · components 3322 行）· JS+Vue 合计 13,731 行。
- **Element Plus 3.0 前向兼容（#116 后）**：`<el-radio-button>` / `<el-checkbox>` 绑定值已全部迁移至 `value` 属性。
- **大屏数据链路（#62 实测）**：`useBigScreen` 5 处失败路径原仅 `console.error`；`analysisStore.fetchAll` 内部 `allSettled`，失败不抛出，失败信息落在 `store.error`（只记第一项）。
- **拦截器兜底（勿重复弹窗）**：`api/request.js:82-166` 对每个失败请求已弹 ElMessage（业务码/HTTP 码/网络错误三类）。
- **#19 失败态语义落地状态**：`useTable.js` 已删；语义已落地在 #62、#65、#66、#67（失败保留旧数据 + 显式错误态/重试）。

## 已完成
- **#126 完成转 in-review（2026-10-23）**：`docs/TEST_PERF.md` §7.1 追加 #120–#123、§7.4 删过时项、新增 §7.5 覆盖率基线（双段：41/190 与 43/252）；刷新日期 2026-10-23；提交 `c0d7e22` @ main（已推送）；报告 comment 6366159758。
- **#125 完成转 in-review（2026-10-23）**：新增 `tests/request-error-paths.test.js`（25 用例）；test:run 43/252 全绿；request.js Stmts 94.15 / Branch 95.74 / Lines 94.15；lint/build exit 0；提交 `2ab34b3` @ main（已推送）；报告 comment 6366056757。
- **#124 完成转 in-review（2026-10-23）**：新增 `tests/utils-index-core.test.js`（37 用例）；test:run 42/227 全绿；utils/index.js Stmts 98.23 / Funcs 100 / Lines 98.23；lint/build exit 0；提交 `d58fa71` @ main（已推送）；报告 comment 6365951526。
- **#123 验收关闭（2026-10-23）**：前端 vitest 本地覆盖率可见性（reporter-only）；41/190 基线 80.55/72.66/30.95/80.55；提交 `6812039` + merge `c77fbcb`。
- **#122 验收关闭（2026-10-22）**：`docs/TEST_PERF.md` §7/§7.1 刷新并追加 #113–#119；提交 `0f2221c`。
- **#121 验收关闭（2026-10-22）**：`classification_report` 显式 `zero_division=0`，消除 UndefinedMetricWarning；提交 `6a37d95`。
- **#120 验收关闭（2026-10-22）**：`index.scss` 以 `@use` 替代 `@import`，消除 Dart Sass 3.0 弃用警告；提交 `d7e0c59`。
- **#119 验收关闭（2026-10-20）**：10 个测试文件 spy/mock `console.error`，stderr 块数 32→0；提交 `ab430f7`。
- **#118 验收关闭（2026-10-20）**：`test_model_improvements.py` main() 失败退出码；提交 `574aa34`。
- **#117 验收关闭（2026-10-20）**：7 处 `datetime.utcnow()` → `utcnow_naive()`；提交 `8f1cc63`。
- **#116 验收关闭（2026-10-20）**：Element Plus label act as value 弃用警告收敛；提交 `4a32dbe` → merge `d4bce28`。
- **#115 验收关闭（2026-10-20）**：conftest 补 Celery task_store_eager_result；提交 `9b952cf` → merge `2a3b703`。
- **#114 验收关闭（2026-10-20）**：`test_model_improvements.py` 移除 return 与吞异常假绿；提交 `89a53ce` → merge `b225c32`。
- **#113 验收关闭（2026-10-19）**：`test_send_invalid_email` patch SMTP_SSL；提交 `6c6a0b6` → merge `53a8140`。
- **#111 验收关闭（2026-10-18）**：同步旧 ruff 命令至活文档与脚本；提交 `6834534` → merge `73e0074`。
- **#112 验收关闭（2026-10-18）**：M6 残余差距只读分析；提交 `0c10122` → merge `33be94a`。
- **#110 验收关闭（2026-10-17）**：`scripts/` 纳入 ruff 门禁并修复 8 项机械缺陷；提交 `cd0ea53`+`21535bc` → merge `1abfaf0`。
- **#108 验收关闭（2026-10-17）**：Rust 工具链 pin + `.env.example` 四变量 + ADR-0005；提交 `1889b6f`…`e2ecb5c` → merge `ddea0a9`。
- **#106 验收关闭（2026-10-17）**：CI backend-fast `--durations` Top10 + 单例隔离 + socket 审计；提交 `cafe8ed`+`2f6790c`+`e23ba43` → merge `9a13987`。
- **#107 验收关闭（2026-10-17）**：可观测模块行为验证恢复，覆盖率 68.5259%；提交 `1d78f05`+`339c891` → merge `be32bd0`。

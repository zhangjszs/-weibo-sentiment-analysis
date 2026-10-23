# STATE

> 事实账本（可机器解析）。「已完成」仅保留最近 20 条，更早的见 git 历史。

## 当前活跃
- 任务：2026-10-23 执行轮（会话 2）。本席 executor；今日队列 3 项（#127/#128/#129）全部完成转 in-review，ready 队列清空。
- 状态：in-review：#127/#128/#129；in-progress：无；ready：无。
- 本轮起点 main `4674d77` → 代码 HEAD `4d00f9c`（#127 `ffe4c5b`、#128 `4cb2519`、#129 `4d00f9c`，均已推送；三个临时分支本地+远端已删除）。
- CI（契约 4.1c）：`ffe4c5b` / `4cb2519` 五项 check 全 success；`4d00f9c` integration 被 `concurrency.cancel-in-progress` 取消（非失败），由 HEAD `.agent` 提交 `be068ad` 的 run 39978638943 覆盖验证（五项全 success）。
- 前端基线（本轮实测）：`npm run test:run` 45 files / 271 tests 全绿（stderr 块 0）；`test:coverage` exit 0，All files Stmts 83.22 / Branch 75.83 / Funcs 35.55 / Lines 83.22；`src/stores/user.js` Lines 97/99（97.97%）/ Branches 31/38（81.57%）/ Funcs 7/7（100%）；`src/utils/chinaMap.js` Lines 26/26（100%）/ Branches 6/6 / Funcs 1/1；`src/App.vue` 0/14 行（根组件壳豁免）；`lint` exit 0。
- 后端 fast gate 本机基线（2026-10-21 #121 后实测，本轮未改后端）：native（WEIBO_CORE_RUST=1）1495 passed / 69 skipped / 196 deselected / 92 warnings（36.66s）；fallback（WEIBO_CORE_RUST=0）1493/71/196 / 92 warnings（34.05s）；全绿。
- 跨天链：正常（2026-10-23）——会话 1 完成 #124/#125/#126；Planner 验收并立项 #127/#128/#129；会话 2（本席）完成三件套；STATE 已刷新、HANDOFF 已重写、DIARY 已追加 2026-10-23。

## 阻塞项
- #109（2026-10-17 仍 blocked）：本机无 Docker、无已知已授权 Docker 主机；console smoke 不替代真实 profile/UI 验收。
- #98（M7 冻结）：D-019 默认 A 生效后继续冻结，保持现场不重置，下一棒不得领取。
- #96 / #100 / #101 / #102 / #59（needs-info）：受 D-019 A 冻结或待产品需求确认。

## 关键事实（已实测验证）
- **user store 会话恢复（#127 实测）**：新增 `tests/user-store.test.js`（13 用例，236 行），覆盖 initAuth 未认证/extend 成功/非 200/抛错/getUserInfo 非 200/checkSession 异常与 redirect 编码回退、doLogout 两路径、updateUserInfo 合并、三个 computed 与 resetAuthState tabs 清理；`stores/user.js` 行 97/99（97.97%）、分支 31/38（81.57%）、函数 7/7；未覆盖为 applyUserInfo 非对象兜底与 pinia 未就绪 catch（极端时序不可构造）。
- **chinaMap 单例语义（#128 实测）**：新增 `tests/china-map.test.js`（6 用例，127 行），锁定首次 fetch、并发共享同一 promise、成功后不重取、非 2xx 抛错且不注册、失败后 ready 复位可重试、网络错误原样冒泡；`utils/chinaMap.js` Lines/Branches/Funcs 全 100%。模块隔离用 `vi.resetModules()` + 动态 import；`vi.mock('@/utils/echarts')` 可拦截相对路径 `./echarts`（同一模块 id，已实证）。
- **TEST_PERF 账目（#129 实测）**：§7.1 追加 #124/#125/#126 三行；§7.5 0% 清单补 `src/App.vue`；「转 in-review」表述清除；新增会话 2 实测段（45/271，83.22/75.83/35.55/83.22）并保留 43/252 历史时点值——Issue 的「保持不变」与「与当次一致」在队列扩充后不可同时满足，按两段并存处理。
- **前端覆盖率可见性（#123）**：`@vitest/coverage-v8@3.2.7` + `vitest.config.js` `test.coverage`（v8/all/src js+vue/text+lcov，无门禁）+ `test:coverage`；ci.yml 零改动。
- **Sass 模块化兼容（#120）**：`frontend/src/styles/index.scss:8` 已由 `@import` 迁移为 `@use './animations.scss' as *;`。
- **模型评估无告警（#121）**：`trainModel.py` 与 `hyperparameter_optimizer.py` 中 `classification_report` 已显式传入 `zero_division=0`。
- **拦截器兜底（勿重复弹窗）**：`api/request.js:82-166` 对每个失败请求已弹 ElMessage（业务码/HTTP 码/网络错误三类）。

## 已完成
- **#129 完成转 in-review（2026-10-23 会话 2）**：`docs/TEST_PERF.md` §7.1 补 #124–#126 三行、§7.5 补 App.vue 豁免与会话 2 实测；提交 `4d00f9c` @ main（已推送）；报告 comment 6368410830 + 更正 6368412699。
- **#128 完成转 in-review（2026-10-23 会话 2）**：新增 `tests/china-map.test.js`（6 用例）；test:run 45/271 全绿；chinaMap.js 三项 100%；lint/prettier exit 0；提交 `4cb2519` @ main（已推送）；报告 comment 6368275972。
- **#127 完成转 in-review（2026-10-23 会话 2）**：新增 `tests/user-store.test.js`（13 用例）；test:run 44/265 全绿；user.js Lines 97.97 / Branches 81.57 / Funcs 100；lint/prettier exit 0；提交 `ffe4c5b` @ main（已推送）；报告 comment 6368149791。
- **#126 验收关闭（2026-10-23 第二轮，done(partial)）**：缺口由 #129 承接；提交 `c0d7e22`。
- **#125 验收关闭（2026-10-23 第二轮）**：提交 `2ab34b3`。
- **#124 验收关闭（2026-10-23 第二轮）**：提交 `d58fa71`。
- **#123 验收关闭（2026-10-23）**：前端 vitest 本地覆盖率可见性（reporter-only）；41/190 基线 80.55/72.66/30.95/80.55；提交 `6812039` + merge `c77fbcb`。
- **#122 验收关闭（2026-10-22）**：`docs/TEST_PERF.md` §7/§7.1 刷新并追加 #113–#119；提交 `0f2221c`。
- **#121 验收关闭（2026-10-22）**：`classification_report` 显式 `zero_division=0`；提交 `6a37d95`。
- **#120 验收关闭（2026-10-22）**：`index.scss` 以 `@use` 替代 `@import`；提交 `d7e0c59`。
- **#119 验收关闭（2026-10-20）**：10 个测试文件 spy `console.error`，stderr 块 32→0；提交 `ab430f7`。
- **#118 验收关闭（2026-10-20）**：`test_model_improvements.py` main() 失败退出码；提交 `574aa34`。
- **#117 验收关闭（2026-10-20）**：7 处 `datetime.utcnow()` → `utcnow_naive()`；提交 `8f1cc63`。
- **#116 验收关闭（2026-10-20）**：Element Plus label act as value 迁移；提交 `4a32dbe` → merge `d4bce28`。
- **#115 验收关闭（2026-10-20）**：conftest 补 Celery task_store_eager_result；提交 `9b952cf` → merge `2a3b703`。
- **#114 验收关闭（2026-10-20）**：`test_model_improvements.py` 移除假绿；提交 `89a53ce` → merge `b225c32`。
- **#113 验收关闭（2026-10-19）**：`test_send_invalid_email` patch SMTP_SSL；提交 `6c6a0b6` → merge `53a8140`。
- **#111 验收关闭（2026-10-18）**：同步旧 ruff 命令；提交 `6834534` → merge `73e0074`。
- **#112 验收关闭（2026-10-18）**：M6 残余差距只读分析；提交 `0c10122` → merge `33be94a`。

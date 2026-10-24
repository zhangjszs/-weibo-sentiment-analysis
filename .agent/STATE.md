# STATE

> 事实账本（可机器解析）。「已完成」仅保留最近 20 条，更早的见 git 历史。

## 当前活跃
- 任务：2026-10-24 执行轮（会话 3）。本席 executor；接手时 #130/#131/#132 仍 in-review 等待 Planner 验收（Issue comment 各 2 条：领取 + 执行报告，无验收反馈）、0 个 ready、无 in-progress 现场可恢复。本轮零代码改动，仅现场核对 + 安静收尾。
- 状态：in-review：#130/#131/#132；in-progress：无（#98 为冻结的父任务）；ready：无。
- 代码 HEAD：`ea362d9`（会话 2 的 `.agent` 收尾提交）；代码交付停在 `06b194e`（#132）。`ea362d9` 的 CI 五项 check（backend-fast / frontend-fast / integration / rust-core / security-scan）已由会话 3 实测全部 completed/success，无遗留待复查 run。
- 前端基线（2026-10-24 会话 2 实测，HEAD 9a86951）：`npm run test:run` 47 files / 321 tests 全绿；`test:coverage` exit 0，All files Stmts 83.79 / Branch 77.35 / Funcs 37.55 / Lines 83.79；`stores/app.js` 全 100%；`stores/tabs.js` 97.67 / 95.83 / 100 / 97.67；`stores/user.js` 97.97 / 81.57 / 100；`utils/chinaMap.js` 全 100%；`lint` exit 0。0% 模块：8 个 api 包装 + main.js + App.vue（豁免）。
- 后端 fast gate 本机基线（2026-10-21 #121 后实测，本轮未改后端）：native（WEIBO_CORE_RUST=1）1495 passed / 69 skipped / 196 deselected / 92 warnings（36.66s）；fallback（WEIBO_CORE_RUST=0）1493/71/196 / 92 warnings（34.05s）；全绿。
- 跨天链：今日队列清空，等待 Planner 验收 #130/#131/#132。**前端按既定口径已无真实可测对象（枯竭预警），后续选题需用户方向输入。**

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
- **#132 完成转 in-review（2026-10-24 会话 2）**：`docs/TEST_PERF.md` §7.1 补 #127/#128/#129 三行、§7.5 状态措辞更新并追加 47/321 新段、四处日期刷新；`grep "待验收"` = 0；提交 `06b194e` @ main（已推送）；报告 comment 6384021932。
- **#131 完成转 in-review（2026-10-24 会话 2）**：新增 `tests/tabs-store.test.js`（41 用例，471 行）；tabs.js Lines 97.67 / Branch 95.83 / Funcs 100，未覆盖 40-41、190-191（getItem/removeItem 抛错 catch，不 mock 不可构造）；变异抽查 3 例失败证明断言有效；提交 `9a86951` @ main（已推送）；报告 comment 6384001211。
- **#130 完成转 in-review（2026-10-24 会话 2）**：新增 `tests/app-store.test.js`（9 用例，142 行）；app.js 四项全 100%；提交 `73bec15` @ main（已推送）；报告 comment 6383985323。
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

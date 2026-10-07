# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `executor-glm-20261007-relay`（GLM 执行棒），UTC 2026-10-07 本轮。
**接管了过期锁**：原 owner glm-20261002T000100Z @ 2026-10-06T09:10Z 领锁后
开工 #54、崩溃前未留任何 comment / 交接，只在 .agent/LOCK 留了时间戳。
其未提交的 #54 中途现场被本棒完整识别（依据：未提交 diff 与 Issue #54
范围逐一吻合、字段契约注释写有「已随 #54 删除」、LOCK 晚于上轮 HANDOFF
收尾时间）、独立复核后收尾。

## 本轮概要

串行完成 2 个 Issue，均转 in-review；ready 队列清空。

### 1. 恢复并完成 #54（commit 053bff2）

接手时工作区留有上一棒两遍演化的未提交改动（第一遍按 Issue 原假设删
stats/today，第二遍发现消费方后保留）。本棒独立复核后收尾：

- **/api/stats/today 保留**：base_page.html 的 loadTodayStats() 真实 fetch
  它，且 base_page.html 被 index.html 等 8 个在用模板 extends → 按 Issue
  自身护栏「有消费方一律保留」。字段契约为 13 端点（验收原文写 12，
  偏离已在执行报告逐条记录）
- 还原上一棒第一遍误删的 TestGetTodayStats 服务单测（177 行）与 a3
  blueprint mock——端点保留后那两处删除不成立，且属验收禁止的「回退」
- 删除生效项：/api/bigscreen/all 路由 + 测试、孤儿组件
  AlertNotification.vue、stats.js 死包装 getBigScreenAllData（零引用）
- 验证：fast gate **1460 passed + 1 xfail**（= 1463 − 3，与删除一致非
  回退）、ruff 0、前端五门禁绿、CI 三 job 绿（run 37547491509）

### 2. 完成 #55（commit a0d44ed）

- 图标告警：选**字符串名 + 全局注册**（19 处 meta.icon 字符串化 +
  删图标 import），否决 markRaw——组件对象被 JSON 持久化破坏后
  missing-template 告警 markRaw 修不了；字符串走 #39 的
  ICON_COMPONENTS 注册表（elementPlus.js 注释早已预写此方向）
- el-empty：home/index.vue 漏冒号（image-size="160" 传字符串），单点修复
- favicon：index.html / sw.js precache+badge / manifest.json 三处统一指向
  已存在的 /vite.svg；sw.js 升 static-v3（addAll 遇 404 整体 install
  失败的坑一并消除）
- 防回归双保险：tabbar-icons.test.js 3 用例（meta.icon 字符串契约做了
  **反例变红**实验）；smoke_console_noise.py 浏览器冒烟做了 **RED→GREEN**
  两轮实证（stash 修复代码 RED：11 条告警 + favicon 404 → 恢复后 GREEN：
  0/0/0 + icon 200）
- 验证：前端 85 tests、五门禁绿、CI 三 job 绿（run 37549117841）

## 未完成 / 进行中

- 无。in-progress 清零，ready 队列空。

## 验证情况

- 后端 fast gate（两项各跑一次）：1460 passed / 69 skipped / 1 xfailed，
  退出码 0；ruff All checks passed
- 前端五门禁：lint 0 / format:check 0 / test:run 85（15 文件）/ build 0 /
  check:bundle 273,352/327,000 + 81,228/97,000 预算内
- 浏览器冒烟：#55 RED + GREEN 各一轮（真实 Playwright + SQLite 后端 +
  admin 手动种子）；#52 的大屏冒烟本轮未重跑（未触碰大屏代码）
- CI：053bff2 → 37547491509 全绿；a0d44ed → 37549117841 全绿；两次
  Security Scan 均绿
- 未跑：integration 本地跑（依赖 MySQL/Redis，以 CI integration job 实证）

## 风险与注意事项

- **in-review 积压 11 项**（#43~#47、#48~#51、#54、#55）待验收——最大
  风险是批量返工与后续改动叠加
- #54 验收标准原文写「收缩至 12 端点」，实际 13（保留 stats/today 的
  偏离有据，Planner 验收请按其执行报告的偏离结论核对）
- AUTO_CREATE_DEMO_ADMIN 的 NOW() 方言问题仍未立项（两轮冒烟均手动
  种 admin 绕过）；smoke 脚本自举步骤见 ENV/STATE
- manifest.json / sw.js 通知 icon 仍引用不存在的 /logo.png（PWA 元数据
  与通知场景，无 console 噪音，两轮报告均已注明）
- 跑冒烟会在 .pytest_tmp/ 留 sqlite 库文件（已 ignore，勿提交 src/data/）

## 给下一棒的第一步建议

- ready 队列为空：先看 Planner 是否已验收 / 补队列；无 ready 就按契约
  正常收尾，不要自行开工作
- 若 #53 转 ready（需 D-007 决策先行）：strict-xfail 钉在
  tests/test_api_field_contract.py，修好后 XPASS 会强制转正

## 给 Planner 的信号

- **需要 Planner 介入：in-review 积压 11 项待验收；ready 队列空。**
- #53 仍 needs-info（D-07 产品决策）；M4 正式方向 D-06 pending。
- #54 的 /api/stats/today 保留结论如不认可（想连 base_page.html 遗留
  模板层一并清理），需要单独立项——模板层清理超出 #54 范围。

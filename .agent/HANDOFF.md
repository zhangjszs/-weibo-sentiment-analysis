# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `executor-glm-20261007-r2`（GLM 执行棒），UTC 2026-10-07 本轮。
LOCK 在本轮开始时不存在（无接管现场），从 main 5207550 起步。

## 本轮概要

串行完成 2 个 Issue（#56、#57），均转 in-review；ready 队列清空。
这是 D-006 默认范围 A「质量巩固」的最后两项存量待办——A 收尾后队列清空。

### 1. 完成 #56（commit ce11292 → main dc0bb05）

- `ensure_demo_admin` 的引导 INSERT 由裸 SQL（`NOW()`）改为 ORM 创建：
  `create_time` 显式落 naive UTC（与 `UserRepository.create` 显式传参惯例
  及 User 模型列默认值语义一致）；守卫与 DEMO_ADMIN_PASSWORD 语义不动
- ORM 提交失败时在异常分支回滚 scoped session（防挂起对象污染后续 commit）
- 原 mock INSERT 的单测替换为真实 SQLite 内存库引导测试
  `test_ensure_demo_admin_creates_user_sqlite`（admin 行存在 + create_time
  非空 + `verify_password` 通过）；SELECT 与 INSERT 都重定向到同一 StaticPool
  测试库（`utils.query.engine` 与 `database.db_session` 两处 patch——querys
  在模块导入时绑 engine，只 patch database 侧不够）
- **RED→GREEN 实证**：临时自举脚本走 `create_app` 真实启动路径 + SQLite
  文件库，修复前 `no such function: NOW` + user 表 0 行；修复后 admin 行
  create_time 非空。脚本已删（一次性）

### 2. 完成 #57（commit 1890232 → main 0c9bbaf）

- manifest.json：删两条 /logo.png 悬空 PNG 条目，保留已有 /vite.svg
  （sizes "any"）——SVG "any" 已覆盖任意尺寸，不堆叠冗余条目
- sw.js：push 通知 `icon: '/logo.png'` → `/vite.svg`（与 badge 一致）；
  precache 清单与缓存版本未动（Issue 明确排除）
- 取舍理由已写入执行报告「歧义处理」

## 未完成 / 进行中

- 无。in-progress 清零，ready 队列空。

## 验证情况

- #56：fast gate **1460 passed / 69 skipped / 1 xfailed** 退出码 0（基线
  持平：mock 测试 1:1 替换为强化版）；ruff 0；RED→GREEN 自举脚本两轮
- #57：前端五门禁全绿（lint 0 / format:check 0 / test:run 85 tests·15
  files / build 0 / check:bundle 预算内）；grep 证据：public/ 引用仅剩
  /vite.svg 且文件存在，logo.png 仅剩 3 处打包资产引用（文件已核验存在）
- CI：dc0bb05 → CI run 37575319130 三 job success + Security Scan success；
  0c9bbaf → CI run 37575800738 三 job success + Security Scan success
- 未跑：浏览器冒烟（两枚 smoke 脚本本轮未重跑——改动不涉及大屏与 console
  场景）；integration 本地跑（依赖 MySQL/Redis，以 CI integration job 实证）

## 风险与注意事项

- **in-review 积压 2 项**（#56、#57）待验收，量小请尽快核对
- #56 后冒烟自举手册已更新（ENV.md）：admin 引导在 SQLite 直接可用；
  smoke_*.py 脚本内仍保留手动种 admin 代码（本轮未跑冒烟，未验证前不入库），
  下次跑冒烟可顺势简化并实证
- 引导 create_time 语义从「DB 服务器时钟」变为「应用进程 UTC 时钟」——单机
  等价，跨机部署时与全表其他 ORM 造数路径一致（报告已注明）
- PWA 安装图标现为单一 SVG 条目（诚实可用但非品牌 PNG）；产品要品牌启动
  图标需先有真实资产
- 工作区留有未跟踪 `src/data/commentsData.csv`（跑后端测试的既有产物，
  勿提交，STATE 有记）

## 给下一棒的第一步建议

- ready 队列空：先看 Planner 是否验收 #56/#57 或补队列；无 ready 就按契约
  正常收尾，不要自行开工作
- #53 仍 needs-info（D-007 第 2 次询问）：strict-xfail 钉在
  tests/test_api_field_contract.py，修复落地时 XPASS 强制转正；若 D-007
  默认方案 2 转正，改动点是 useBigScreen.js 的 trend 数据消费
- D-006（M4 正式方向）pending：A 已无存量待办，B/C/D 均需用户输入或授权

## 给 Planner 的信号

- **需要 Planner 介入：验收 #56/#57（in-review）；ready 队列空，A 收尾后
  无存量待办。**
- D-006 / D-007 / D-008 均第 2 次询问 pending；#53 等 D-007。
- smoke_*.py 的手动种 admin 简化是唯一已知低风险顺延项（下次冒烟时做）。

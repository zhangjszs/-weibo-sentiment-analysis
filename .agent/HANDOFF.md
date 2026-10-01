# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `DeepSeek-V4.1-Flash-20261001T163621Z`（DeepSeek-V4.1-Flash），
UTC 2026-10-01T16:36 ~ 17:1x。第十棒，本会话一轮：#38。

## 本会话做了什么（一个 issue 关闭）

| Issue | 内容 | 要点 |
|-------|------|------|
| #38 | user.createTime 驼峰统一为 create_time（收 #16 留白） | 幂等迁移 + 6 处同步；#16 另一半留白（password 拓宽）澄清为不成立 |

## 本轮的改动（commit 3c9bf26）

- **新增幂等迁移 `f6a7b8c9d0e1`**：仅当 `createTime` 存在且 `create_time` 不存在时
  `ALTER TABLE user RENAME COLUMN`（`sa.inspect` 跨 MySQL/SQLite）。
  - CI 全新库由新版冻结 SQL 建表（已是 create_time）→ **跳过**；
  - 旧部署库 → 真改名；空库跑链 → 跳过。downgrade 反向幂等。
- ORM 去掉 `Column("createTime", ...)` 映射；`startup_service` INSERT、
  `user.py` SELECT（顺带删 `AS` 别名）两处裸 SQL 同步；
  冻结 SQL `init_database.sql`（建表+INSERT）、`docs/API.md` 示例、
  `tests/test_db.py` 打印键名同步。
- **澄清 #16 留白**：「password String(100) 拓宽」不成立——已是 String(100)
  （bcrypt 60 字符足够），DB 列 varchar(255)。#16 留白至此全部收口。

**验证**：
- 迁移两路径实测（临时 SQLite）：legacy 库真改名 / 全新库跳过，链跑到 head；
- fast gate **1261 passed**；integration 本地 **189 passed**；
- CI run 36896365335 三 job 全绿（integration 在 MySQL 上实测
  冻结 SQL + 迁移跳过路径）；Security Scan 36896365424 ✅。

## 留白项（有意不做，供下一棒/人工决策）

1. **integration job 无覆盖率**：覆盖率门禁只加在 backend-fast；integration 单独
   覆盖率会低于全局阈值，需先定策略（独立阈值或仅报告）。
2. **pip-audit 未阻断**（见 #32）：依赖 CVE 门禁属独立策略，须先清点 CVE 白名单。
3. **safety 需仓库配置 `SAFETY_API_KEY`** 才能真跑（人工操作 secret）。
4. 功能类（重）：验证码（需产品决策）、WS 刷新后取 token（需先核实是否真缺——
   `getAuthToken()` 兜底存在，可能已不成立）、nginx `/socket.io` 握手 101（需 Docker）。
5. `docs/database/new.sql`、`user.sql` 等**历史归档 SQL 仍是旧列名**——属归档，
   未改；若确认无价值可整目录清理（需人工拍板）。
6. 前端无 TypeScript / 组件测试（评估文档 22 条）：大工程。

## 坑与经验（重要，接力者必读）

1. **改 schema 列名必须三层同步**：ORM、裸 SQL（grep `git grep` 全仓找）、
   冻结 SQL `init_database.sql`；前端可能也引用（本次幸而零引用）。
2. **幂等迁移是本仓库铁律**：CI 每次都是「冻结 SQL 建全新库 → alembic upgrade head」，
   迁移若不跳过已新结构必然红。写法见 `f6a7b8c9d0e1` / `b2d5a3f9c0e1`。
3. **`pytest ... | tail -N` 会截掉关键的 "N passed" 汇总行**（warnings 块很长），
   判断测试结果要看完整尾部或 `grep -E "passed|failed"`。
4. **`pytest | tail` 管道的退出码是 tail 的**，`&&` 链不会因测试失败而中断——
   判断成败必须看文本，不能信命令链是否走完。
5. 重命名类改动：diff 逐行复核（上一棒 Sidebar 教训仍有效）。
6. 其余：CI/Security Scan 是两个 workflow；本地 pytest 带
   `-p no:launch_testing -p no:launch_ros`；勿盲跑 black；bandit nosec 放闭合行；
   `refactor:`/`chore:`/`docs:` 不自动关 issue（需 `Closes #N`）；
   `gh run watch` 偶发误报，以 `gh run view` 为准。

## 下一步建议

- 无待办 issue。下一棒按协议第七节主动发现（先查重）。
- 候选：requirements 版本固定策略（评估文档 21 条，需先定 `==` vs `~=` 与
  兼容性验证方式）；或 integration 覆盖率策略（见留白 1）。
- 三条门禁保持：后端覆盖率 ≥60、bandit HIGH 阻断、前端 lint 零告警。

## 环境备注

- 后端 `.venv` 齐全（Python 3.12）；fast gate 1261 / integration 189 本地均可跑。
- fast gate：`.venv/bin/python -m pytest -m "unit or api" -p no:launch_testing -p no:launch_ros -q --maxfail=1`
- 迁移本地验证法：`TEST_DATABASE_URL=sqlite:////tmp/x.db .venv/bin/python -m alembic stamp <rev>` 后 `upgrade head`（env.py 已尊重 TEST_DATABASE_URL）。
- 前端：mise node 22 入 PATH；lint 0/0 门禁；73 测试。
- 本地有真实 `.env`（含密钥，**勿提交**）。
- gh 可用（账号 zhangjszs）；bandit/pytest-cov 已装在 `.venv`。
- 本地分支 `wip/20260930T154700Z`（未推送）仍在，请人工确认去留。

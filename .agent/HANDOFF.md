# HANDOFF

> 交给下一棒的叙述。每轮**整体重写**，不追加。
> 机器相关信息（绝对路径）不要写进来。

## 上一棒是谁

Agent `executor-glm-20261005T0714Z`（GLM，Execution Agent），UTC 2026-10-05T07:14 ~ 08:55。
第十二棒（执行）。**本轮消费完 M3 全部 5 个 issue**：#43 浏览器冒烟、#44 GET envelope
契约、#47 写接口契约、#45 字段契约、#46 Redis 降级文档，全部完成并转 **in-review**
（未关闭——验收是 Planning 的职责）。另立 auto-discovered **#52 / #53** 待定级。

## 本会话做了什么

| Issue | 结果 | 要点 |
|-------|------|------|
| **#43** | ✅ 完成待验收 | 登录后页面真实浏览器冒烟（headless Chromium + Playwright，装进 .venv）。登录→表格页×2→**大屏直达**→ip 页：地图渲染/组件解析/API 全 2xx/console 零新增错误全部实证（截图 6 张 + JSON 报告存 .pytest_tmp/smoke/）。#40 顺序依赖修复获真实验证。零代码变更；顺带立 #52（大屏空数据 addColorStop 未捕获异常） |
| **#44** | ✅ 完成待验收 | GET envelope 契约：51 条路由 × 匿名/非管理员/管理员三视角表驱动（url_map 机器枚举）+ 5xx 豁免表机制。**修复 2 缺陷**：任务状态 Redis 不可用 HTML 500 → 503 envelope（TaskStatusUnavailable）；get_database_stats StaticPool 兼容。反例红→绿。commit 7261b53 |
| **#47** | ✅ 完成待验收 | 写路由契约：31 条（url_map 实测，规划时 30）三视角 + issue 列的 10 条成功路径（ORM 造数）+ Cookie 无 Origin 403 防线钉住。**修复 5 条路由** broker 不可用 HTML 500 → 503 envelope（service 层转内建 ConnectionError）。反例红→绿。commit b2a52e3 |
| **#45** | ✅ 完成待验收 | 字段契约第一批：14 端点逐字段钉住，消费方标注到前端文件:行号。**发现 trend 形状漂移 → 立 #53**（strict-xfail 钉住）；level_distribution/time_range null 两处确认为前端防御性读取的合法契约。反例红→绿。commit c5efd93 |
| **#46** | ✅ 完成待验收 | DEPLOYMENT.md 新增「Redis 依赖与降级行为」：6 类逐项 + 附加发现 _spider_state + 失效保证汇总 + 部署建议。关键事实：**登录锁定/限流/WS 广播从来不用 Redis**（多 worker 缺口与 Redis 无关）。零代码变更。commit 8930090 |

提交链：7261b53(#44) → b2a52e3(#47) → c5efd93(#45) → 8930090(#46)，#43 无代码提交。
每轮 CI 三 job 绿（run：#44 push 37280477839、#47 push 37282705661、#45/#46 push 均绿）。

## 未完成 / 进行中

- 无进行中工作。**ready 队列已清空**（候补 #48~#51 未动）。

## 验证情况

- fast gate（`.venv/bin/python -m pytest -m "unit or api" -o addopts="" --maxfail=1 -q`）：
  基线推进 **1261 → 1461 passed（含 1 strict-xfail）**，43→70 skipped（契约视角 by-design skip），
  每步推送前实测零回退；ruff 全绿。
- CI 三 job + Security Scan：本轮 4 个代码 push 全绿（#43/#46 零代码变更也各自验证）。
- 前端三门禁未跑（本轮零前端变更——字段契约只读前端代码，未改）。
- integration 未跑（本轮无 integration 层改动；契约测试全在 unit/api marker）。

## 风险与注意事项

1. **#53 是用户可见失真**：大屏「舆情趋势」面板永远显示硬编码假数据（前端
   拿不到 positive/neutral/negative 就回退静态数组）。修复方向需产品决策
   （后端补评论情感标注链路 vs 前端改单系列），测试已用 strict-xfail 钉住——
   谁修复谁负责把 xfail 转正。
2. **#52**：大屏空数据时 echarts addColorStop 未捕获异常（pageerror 级），
   空库/新装环境每次加载必现，非 M2 回归。
3. **ensure_demo_admin 的 `NOW()` 在 SQLite 崩**（#43 冒烟发现）：demo admin
   引导仅 MySQL 可用；本机冒烟需手动造 admin（方法见 STATE「关键事实」）。
   价值低未立 issue。
4. playwright 只装在 `.venv` 未入 requirements-dev——属本机冒烟工具；
   Planner 若希望冒烟可复现（CI 或他机），需决定是否版本化。
5. 冒烟产物（截图/矩阵/日志）在 `.pytest_tmp/smoke/`（gitignored），验收
   #43 若需原件可在本机取； issues 里已贴完整文字记录。
6. `.agent/LOCK` 已释放；本轮工作区干净，main 与 origin 同步（HEAD 3eeb5eb + 本 chore 提交）。

## 坑与经验（接力者必读，本轮新增）

1. **探测「token 中毒」**：`/api/auth/logout` 在公开白名单且会拉黑所带 Bearer 的
   jti；`/api/session/extend` 轮换也拉黑旧 jti。按字母序对同一 token 批量探测，
   走到这两条后**其余路由全部假 401**。批量探测用新 token 且把这两条排最后。
2. **测试环境 celery = eager/memory，不触真实 broker**：测 broker 降级必须
   patch 任务对象抛 OperationalError（`TestBrokerDegradationContract` 有范例）；
   反例验证同理，坏输入判例暴露不了 broker 路径。
3. Flask `Rule.build()` 部分规则返回空路径 → 308 假响应。枚举路由用正则替换
   `<arg>`/`<converter:arg>`（两个契约测试文件的 `_ARG_RE` 可复用）。
4. `User` 模型自定义 `__init__` 不收 id：造数用 `u = User(...); u.id = 1`。
5. SQLite 文件库自举 schema 必须 `import models` **再** `init_db()`，否则 Base
   空注册建不出表（conftest 同理）。
6. 本机 shell 有 `http_proxy` 系变量，curl localhost 偶发 502 假象——加
   `--noproxy '*'` 或确认 no_proxy 覆盖。
7. 沿用既有教训：lint/pytest 判结果看退出码；`-qq` 吞汇总行（看计数用
   `-o addopts="" -q`）；commit 用 `Refs #N` 不自动关 issue。

## 给下一棒的第一步建议

- **ready 已空，下一棒是 Planning**：验收 in-review 五连（#43/#44/#47/#45/#46，
  执行报告逐条对照验收标准即可独立复核）+ 定级 #52/#53 + 决定候补 #48~#51
  是否递补 ready。
- 若验收通过，M3 五项验收标准全部收口（#44/#47/#45/#46 各对应一条 +
  CI 绿不回退基线），可结项 M3 并按 D-05 备选规划下一阶段。

## 给 Planner 的信号

- **需要 Planning 介入（验收积压）**：in-review 5 项 + auto-discovered 2 项待定级。
- #53 涉及产品决策（大屏趋势图的数据语义），建议进 DECISIONS 待用户确认。
- playwright 是否入版本控制、三个无消费方端点/孤儿组件是否清理，待 Planner 定。

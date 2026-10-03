# PLAN — 开发路线图

> 规划 Agent 维护，每次会话滚动更新。执行 Agent 只读不写本文件。
> 方向类决策记录在 DECISIONS.md，本文件引用其编号（D-xx）。

## 当前方向

M2「前端性能与体验」已验收结项（2026-10-03）。进入 **M3：后端 API 契约与测试强化**（D-05，用户选定 A）。
队列首位先清 M2 遗留的真实浏览器冒烟（#43），随后 #44（GET envelope）→ #47（写接口契约）→ #45（字段契约）→ #46（Redis 降级文档）。
Executor 当前未运行（LOCK 已释放，HEAD `3aab56d`，工作区干净）。ready 共 9 项：前 5 项为建议工作集，其余 4 项为质量候补（用户 2026-10-04 指示扩充 backlog）。

## 里程碑

### M1：质量债清偿与门禁体系（已完成）

- 目标：主干 CI 稳定绿、测试/覆盖率/安全/lint 门禁全部真实生效。
- 验收标准：CI 三 job 连续绿 ✅；后端覆盖率门禁 60% ✅（#34/#35）；
  Security Scan 带 Bandit HIGH 门禁 ✅（#31/#32）；前端 lint --max-warnings 0 ✅（#37）。
- 当前基线：fast gate 1261 passed / CI integration 191 passed / 前端 75 tests。
- 包含 issue：#5~#38（全部 CLOSED，明细见 git 历史）。进度：100%。

### M2：前端性能与体验（已完成，2026-10-03 验收）

- 目标：首屏与路由级传输体积显著下降，且建立可持续的体积观测手段。
- 验收标准（全部达成）：
  - [x] #39 element-plus 按需加载：首屏 raw **-76.1%** / gzip **-72.7%**（1,484,188→354,394B，远超 ≥30%）
  - [x] #40 大 chunk：构成报告（china.json 占 ip chunk 98.6%）+ 运行时按需加载（ip chunk 586,429→4,004B，gzip -99.0%）+ echarts「已最优」论证；顺带修复大屏地图顺序依赖 bug
  - [x] #41 integration job 覆盖率报告（D-04 不设阈值；实测 33% 不阻断）
  - [x] 全程 CI 三 job 绿；前端 75 测试无回退
- 包含 issue：#39(P1) / #40(P2) / #41(P2) 全 CLOSED；#42(P3) 调研交付并关闭（维持不上）。
- 验收证据：本机复验（lint 0/0、75 tests、build 成功、产物字节与报告一致）+ CI run 37026054436 / Security Scan 37026054571。
- 遗留：#43（登录后页面真实浏览器冒烟，队列第 1 位）。

### M3：后端 API 契约与测试强化（进行中，D-05；进度：0 / 5）

- 目标：把「统一 envelope + 前端消费字段」变成 fast gate 中可失败的契约；写接口鉴权/校验路径有系统断言；Redis 降级行为可预判。
- 验收标准（随 issue 收口）：
  - [ ] #44 全部 51 个 `/api/*` GET 端点 envelope 表驱动契约，5xx 有结论
  - [ ] #47 全部 30 个写路由（POST/PUT/DELETE）鉴权/坏输入 envelope + 10 个核心成功路径
  - [ ] #45 第一批 14 个前端消费端点字段契约（防 #38 型漂移）
  - [ ] #46 Redis 不可用降级行为文档（零代码变更）
  - [ ] 全程 CI 三 job 绿；fast gate / 前端三门禁不回退（基线：1261 backend / 75 frontend）
- 包含 issue：#43(遗留验证) / #44(P2) / #45(P2) / #46(P3) / #47(P2)。

### 持续质量尾项（ready 候补，可穿插，不阻塞 M3）

- #48(P3) 前端构建体积回归门禁：入口 JS / 首屏 CSS 预算检查入 CI（守住 M2 收益）
- #49(P3) vitest 接入 Components 插件，消除模板级组件解析盲区
- #50(P3) 文档路径校验脚本修复误报并接入门禁
- #51(P3) Prettier 全量格式化（67 文件）并把 format:check 纳入 CI

### 留白与人工事项（跨里程碑跟踪）

| 事项 | 来源 | 状态 |
|------|------|------|
| 验证码调研 | #15 留白 → D-02 | #42 已交付并关闭（维持不上）；触发条件见 #42，实施需另立 issue |
| safety 接 SAFETY_API_KEY | #32 留白 | 人工操作 GitHub secret，无 key 则 safety 空报告（已有跳过门禁） |
| nginx /socket.io 握手 101 上线验证 | #20 留白 | 需 Docker/线上环境，本地无法验证 |
| WS 刷新后取 token 是否真缺 | #15 留白 | **已核实不成立**（2026-10-03）：App.vue→`initAuth`→`/api/session/extend` 返回新 token 并回填内存（`src/app.py:479`、`stores/user.js:80-84`），AlertNotification watch token 重连（`websocket.js:40`） |
| china.json 精度简化 | #40 留白 | 数据取舍需产品决策；资产可缓存（gzip ~229KB），暂不处理 |
| conftest 两套 SQLite 语义统一 | #28 留白 | 属测试架构取舍，无需求不动 |
| 本地 wip/20260930T154700Z 分支 | HANDOFF 环境备注 | git 已无此分支（疑似已删）；下棒 Executor 核实并清理 HANDOFF 记录 |

## 执行队列（给 Executor 的建议顺序）

> ready 总数 9 超出常规 2–5（用户 2026-10-04 指示扩充 backlog）；工作集仍为前 5 项，其余随前序关闭递补。

1. #43 M2 遗留：登录后页面真实浏览器冒烟（P2）——环境不可用则按 issue 要求转 blocked 后继续下一项，勿停滞
2. #44 API 契约测试第一批：全量 GET 端点 envelope 表驱动校验（P2）
3. #47 写接口契约测试：30 个 POST/PUT/DELETE 路由（P2）
4. #45 前端消费端点字段契约第一批（P2）
5. #46 文档化 Redis 不可用时的降级行为（P3）

候补（随前序腾挪递补）：#48 体积门禁 → #49 vitest Components → #50 文档路径校验 → #51 Prettier 格式化

## 已知阻塞与依赖

- 无外部阻塞。#43 依赖本地可起后端 + 可用浏览器；受限则转 blocked。

## 下一阶段

- M3 完成后候选（D-05 备选，均需用户输入才可 ready）：前端 TypeScript 渐进化（B，红线需授权）、
  部署/运维生产化（C，需可验证环境）、产品功能迭代（D，需具体需求）。

## 已放弃的方向

- 登录验证码实施（D-02：暂缓；调研 #42 已闭合，维持不上；触发条件成熟时另立实施 issue）。
- docs/database 归档 SQL 列名同步（D-03：保留不动）。

## 远景（粗粒度）

- 前端：TypeScript 化与视图层组件测试（大工程，需用户授权后分批立项）。
- 后端：REST API 契约测试全覆盖（M3 推进中）；Redis 降级文档（M3）。
- 运维：镜像多阶段构建瘦身、compose 一键生产化（需可验证环境）。

## 给 Executor 的指令

- 代码提交用 `Refs #N`，不用 `Closes`/`fix: #N`（关闭留给 Planner 验收）；`.agent/` 变更用 `chore(agent):` 且与代码不混提。
- 前端改动三门禁全跑（lint --max-warnings 0 / test:run 基线 75 / build），后端改动跑 fast gate；判结果看退出码。

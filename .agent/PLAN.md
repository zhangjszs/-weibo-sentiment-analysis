# PLAN — 开发路线图

> 规划 Agent 维护，每次会话滚动更新。执行 Agent 只读不写本文件。
> 方向类决策记录在 DECISIONS.md，本文件引用其编号（D-xx）。

## 当前方向

M3 已结项（2026-10-06，9 项 in-review 验收关闭）。M4 默认范围「质量巩固」（D-06
默认 A）三项全部闭环：#52 上轮关闭 + 本轮 Planner 追认、#54/#55 本轮验收关闭。
**M4 正式方向仍待用户决策（D-006，第 2 次询问）**；#53（大屏趋势语义）待 D-007
（第 2 次询问）。队列补入两个遗留小项 #56/#57。无外部阻塞，LOCK 不存在，
main 与 origin 同步（本轮起点 HEAD 1a467af）。

> 澄清 Executor 信号：上棒 HANDOFF/STATE 称「in-review 积压 11 项」系陈旧计数
> ——#43~#51 共 9 项已于上轮 Planner（03d3261）验收关闭，实际待验收仅 #54/#55，
> 现已闭环。STATE 归 Executor 所有，本席不代改，特此在自己文件中记录。

## 里程碑

### M1：质量债清偿与门禁体系（已完成）

- CI 三 job 连续绿；后端覆盖率门禁 60%；Bandit HIGH 门禁；前端 lint --max-warnings 0。
- 包含 #5~#38（全部 CLOSED，明细见 git 历史）。

### M2：前端性能与体验（已完成，2026-10-03 验收）

- #39 element-plus 按需加载（首屏 raw -76.1%）；#40 大 chunk 治理（ip chunk gzip -99.0%）
  + 大屏地图顺序依赖修复；#41 integration 覆盖率报告（D-04 不设阈值）。
- 遗留 #43（浏览器冒烟）已在 M3 期间完成并通过验收。

### M3：后端 API 契约与测试强化（已完成，2026-10-06 验收，D-05）

- #44 GET envelope 契约（51 端点）· #47 写路由契约 31+10 条 · #45 前端消费字段
  契约（14 端点，立 #53）· #46 Redis 降级文档 · #43 浏览器冒烟。
- 附带门禁 3 道（#48 体积预算 / #51 format:check / #50 文档死链）+ #49 vitest
  resolver 单源；九项验收证据见 03d3261 提交轮与各 Issue 验收 comment。

### M4：质量巩固（默认范围已完成；正式方向待 D-006）

- 默认范围（D-06 默认 A）全部闭环：
  - [x] #52 大屏空数据 addColorStop 崩溃（d968188，真实浏览器冒烟 RED→GREEN，
    冒烟脚本入库；因提交标题「fix: #52」被 GitHub 自动关闭，本席已 comment 追认）
  - [x] #54 死代码清理（053bff2，2026-10-07 验收关闭；/api/stats/today 经 Planner
    独立确认有真实消费方——base_page.html 被 8 个在用模板 extends——按护栏保留，
    字段契约 13 端点，偏离有据）
  - [x] #55 console 告警清理（a0d44ed，2026-10-07 验收关闭；19 处 meta.icon
    字符串化 + favicon 三处指向 vite.svg + static-v3 + RED→GREEN 冒烟 + 3 用例契约）
- 收尾小项入队：#56 SQLite 方言（P3）、#57 /logo.png 悬空引用（P4）。
- #53（needs-info，P3）：待 D-007；strict-xfail 钉住，修复落地时 XPASS 强制转正。

## 执行队列（给 Executor 的建议顺序）

1. #56 修复 AUTO_CREATE_DEMO_ADMIN 引导 SQL 的 SQLite 方言崩溃（P3，ready-for-agent）
2. #57 清理 PWA 元数据 /logo.png 悬空引用（P4，ready-for-agent）

- blocked：#53（needs-info，待 D-007 产品决策）。

## 已知阻塞与依赖

- 无外部阻塞。M4 正式方向等用户输入（D-006）；#53 等产品决策（D-007）；
  Redis 迁移方向记 D-08（pending，默认不动）。

## 下一阶段

- M4 收尾后候选同 D-06 备选：B 前端 TypeScript 渐进化（红线需授权）、
  C 部署/运维生产化（需可验证环境）、D 产品功能迭代（需具体需求）。

## 已放弃的方向

- 登录验证码实施（D-02：暂缓，#42 调研已闭合，触发条件成熟时另立实施 issue）。
- docs/database 归档 SQL 列名同步（D-03：保留不动）。

## 留白与人工事项（跨里程碑跟踪）

| 事项 | 状态 |
|------|------|
| safety 接 SAFETY_API_KEY | 人工操作 GitHub secret；无 key 则 safety 空报告（已有跳过门禁） |
| nginx /socket.io 握手 101 上线验证 | 需 Docker/线上环境，本地无法验证 |
| china.json 精度简化 | 数据取舍需产品决策；资产可缓存，暂不处理 |
| conftest 两套 SQLite 语义统一 | 测试架构取舍，无需求不动 |
| AUTO_CREATE_DEMO_ADMIN SQLite 方言 | 已立项 #56（三轮冒烟重复踩坑，2026-10-07） |
| /api/alert/unread-count 无活跃消费方 | 候选清理项暂不立项；若动须先把 src/views/page/templates/ 服务端模板计入消费方调查（#54 教训） |
| playwright 入库与否 | Planner 自决：暂维持 .venv 本地安装（冒烟非周期任务）；转常备验证手段时升格 dev 依赖并入 CI |
| 登录锁定/限流/WS 广播迁 Redis | D-08 pending（#46 已文档化多 worker 缺口）；默认暂不迁、不改行为 |
| docs/项目评估与规划.md:245 建议已用 /api/bigscreen/all | 该端点已随 #54 删除；历史评估文档按 #16 结论不再修 |

## 给 Executor 的指令（不超过 2 句）

- 提交标题勿含「fix: #N」字样（GitHub 会自动关闭 Issue，#52 已踩坑；正文用 `Refs #N`）；`.agent/` 变更用 `chore(agent):` 且与代码不混提。
- 「死代码清理」类调查必须把 `src/views/page/templates/` 服务端模板计入消费方（#54 实证：模板层在 SPA 五层扫描之外）；前端改动五门禁全跑、后端跑 fast gate，判结果看退出码（管道用 `PIPESTATUS[0]`）；跑后端测试会在 `src/data/` 留未跟踪产物勿提交。

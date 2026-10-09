# PLAN — 开发路线图

> 规划 Agent 维护，每次会话滚动更新。执行 Agent 只读不写本文件。
> 方向类决策记录在 DECISIONS.md，本文件引用其编号（D-xx）。

## 当前方向

M5 双方向（D-009，2026-10-09 用户选择）：
1. **前端 TypeScript 渐进化**（P1，#58）——红线已授权，先立调研策略 Issue
2. **产品功能迭代**（P2，#59）——需用户提供具体需求，当前 needs-info

M4 已彻底收尾（#52~#57 全部验收关闭）。

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

### M4：质量巩固（默认范围已全部闭环；D-006 默认转正 A，待命）

- 默认范围（D-06 默认 A）全部闭环：
  - [x] #52 大屏空数据 addColorStop 崩溃（d968188，真实浏览器冒烟 RED→GREEN，
    冒烟脚本入库；因提交标题「fix: #52」被 GitHub 自动关闭，本席已 comment 追认）
  - [x] #54 死代码清理（053bff2，2026-10-07 验收关闭；/api/stats/today 经 Planner
    独立确认有真实消费方——base_page.html 被 8 个在用模板 extends——按护栏保留，
    字段契约 13 端点，偏离有据）
  - [x] #55 console 告警清理（a0d44ed，2026-10-07 验收关闭；19 处 meta.icon
    字符串化 + favicon 三处指向 vite.svg + static-v3 + RED→GREEN 冒烟 + 3 用例契约）
  - [x] #56 SQLite 方言引导修复（ce11292→dc0bb05，2026-10-07 验收关闭；Planner
    复核 diff + 复跑单测 5 passed + 端到端冒烟证据 + dc0bb05 CI/安全双绿）
  - [x] #57 /logo.png 悬空引用清理（1890232→0c9bbaf，2026-10-07 验收关闭；Planner
    复核 grep 零悬空 + public/ 三文件 + 0c9bbaf CI/安全双绿）
  - [x] #53 大屏趋势改单系列（1909d9b→c402b4d，2026-10-08 验收关闭；Planner
    复核 diff + 复跑趋势契约/前端映射单测 + grep 零命中 + c402b4d/HEAD
    CI/安全双绿；D-007 方案 2 落地，方案 1 红线已放弃）

### M5：前端 TypeScript 渐进化 + 产品功能迭代（进行中，D-009）

- #58 前端 TS 调研与迁移策略规划（P1，✅ 2026-10-09 验收关闭）
- #60 用户体验与技术债务现状调研（P1，ready-for-agent）
- #59 产品功能迭代需求收集（P2，needs-info，等 #60 产出）

## 执行队列（给 Executor 的建议顺序；状态标签实为 `ready-for-agent`，`ready` 不存在）

1. #60 用户体验与技术债务现状调研（P1）

## 已知阻塞与依赖

- #59：等 #60 产出候选清单后再决定产品功能迭代方向（D-010）
- 无 pending 决策

## 下一阶段

- M5 双方向并行：前端 TS 渐进化按 #58 策略文档分批推进；
  产品功能迭代待用户输入需求后立项。

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
| AUTO_CREATE_DEMO_ADMIN SQLite 方言 | #56 验收关闭（2026-10-07），冒烟前置已简化为自动引导 |
| 大屏趋势情感语义 | #53 已落地关闭（2026-10-08，D-007 方案 2 单系列 counts）；方案 1（情感标注链路）红线已放弃 |
| /api/alert/unread-count 无活跃消费方 | 候选清理项暂不立项；若动须先把 src/views/page/templates/ 服务端模板计入消费方调查（#54 教训） |
| playwright 入库与否 | Planner 自决：暂维持 .venv 本地安装（冒烟非周期任务）；转常备验证手段时升格 dev 依赖并入 CI |
| 登录锁定/限流/WS 广播迁 Redis | D-008 默认转正 C（2026-10-07）：暂不迁、不改行为（#46 已文档化多 worker 缺口） |
| docs/项目评估与规划.md:245 建议已用 /api/bigscreen/all | 该端点已随 #54 删除；历史评估文档按 #16 结论不再修 |

## 给 Executor 的指令（不超过 2 句）

- 提交标题勿含「fix: #N」字样（GitHub 会自动关闭 Issue，#52 已踩坑；正文用 `Refs #N`）；`.agent/` 变更用 `chore(agent):` 且与代码不混提。
- 「死代码清理」类调查必须把 `src/views/page/templates/` 服务端模板计入消费方（#54 实证：模板层在 SPA 五层扫描之外）；前端改动五门禁全跑、后端跑 fast gate，判结果看退出码（管道用 `PIPESTATUS[0]`）；跑后端测试会在 `src/data/` 留未跟踪产物勿提交。
